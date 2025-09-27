# /cibus2/src/profiler.py

import logging
import json
import pandas as pd
import numpy as np
import re
import math
from pathlib import Path
from typing import Dict, Any

# Set up logging for this module
logger = logging.getLogger(__name__)

def read_cobol_layout(layout_file_path: Path) -> pd.DataFrame:
    """
    Reads the COBOL layout from an Excel file and returns a DataFrame.
    """
    try:
        # Assuming the layout is in the first sheet and has a header
        df = pd.read_excel(layout_file_path, engine='openpyxl')
        df.columns = df.columns.str.lower()
        required_cols = ['handoff column name', 'data type with length', 'description']
        if not all(col in df.columns for col in required_cols):
            logger.error(f"Layout file missing required columns: {required_cols}")
            raise ValueError("Layout file is missing required columns.")
        return df
    except Exception as e:
        logger.error(f"Error reading layout file: {e}")
        raise

def get_colspecs(layout_df: pd.DataFrame) -> tuple:
    """
    Generates column specifications (start, end) for pandas from the layout,
    based on COBOL data type specs including COMP, COMP-3, etc.
    """
    colspecs = []
    current_pos = 0
    try:
        for _, row in layout_df.iterrows():
            data_type_spec = str(row['data type with length']).strip().upper()
            
            length = 0
            is_numeric = False
            
            # --- Handle COMP, COMP-3, COMP-4, COMP-5 ---
            if 'COMP-3' in data_type_spec:
                match = re.search(r'S9\((\d+)\)(V9+(\(\d+\))?)?', data_type_spec)
                if match:
                    is_numeric = True
                    s9_len = int(match.group(1))
                    v9_len = 0
                    if match.group(2): # Checks if the V99 part exists
                        if match.group(3): # Checks for V99(n)
                            v9_len = int(match.group(3).strip('()'))
                        else: # Just V99
                            v9_len = len(match.group(2).replace('V', ''))
                    total_digits = s9_len + v9_len
                    length = math.ceil((total_digits + 1) / 2)
            elif any(x in data_type_spec for x in ['COMP-4', 'COMP-5', 'COMP', 'BINARY']):
                match = re.search(r'S9\((\d+)\)', data_type_spec)
                if match:
                    is_numeric = True
                    digits = int(match.group(1))
                    if digits <= 4:
                        length = 2 # Half-word
                    elif digits <= 9:
                        length = 4 # Full-word
                    elif digits <= 18:
                        length = 8 # Double-word
                    else:
                        logger.warning(f"Unsupported COMP length: {digits}")
                        raise ValueError(f"Unsupported COMP length: {digits}")
            
            # --- Handle standard X and S9 ---
            elif 'X' in data_type_spec:
                match = re.search(r'X\((\d+)\)', data_type_spec)
                if match:
                    length = int(match.group(1))
            elif 'S9' in data_type_spec:
                match = re.search(r'S9\((\d+)\)(V9+(\(\d+\))?)?', data_type_spec)
                if match:
                    is_numeric = True
                    s9_len = int(match.group(1))
                    v9_len = 0
                    if match.group(2):
                        if match.group(3):
                            v9_len = int(match.group(3).strip('()'))
                        else:
                            v9_len = len(match.group(2).replace('V', ''))
                    length = s9_len + v9_len

            if length == 0:
                logger.error(f"Could not parse length from spec: {data_type_spec}")
                raise ValueError(f"Invalid data type specification: {data_type_spec}")
            
            colspecs.append((current_pos, current_pos + length))
            current_pos += length
        return colspecs
    except Exception as e:
        logger.error(f"Error parsing data type with length from layout: {e}")
        raise

def run_profiling(layout_file_path: Path, handoff_file_path: Path, output_file_path: Path) -> Dict[str, Any]:
    """
    Orchestrates the data profiling process.
    """
    logger.info("Starting data profiling...")

    # 1. Read layout and determine file structure
    layout_df = read_cobol_layout(layout_file_path)
    colspecs = get_colspecs(layout_df)
    column_names = layout_df['handoff column name'].tolist()
    
    # 2. Read fixed-width file into a DataFrame
    try:
        df = pd.read_fwf(
            handoff_file_path, 
            colspecs=colspecs, 
            names=column_names, 
            header=None,
            dtype='string'  # Read all columns as strings to preserve leading zeros
        )
        logger.info(f"Successfully loaded {len(df)} rows from handoff file.")
    except Exception as e:
        logger.error(f"Error reading fixed-width file: {e}")
        raise

    # 3. Perform profiling and generate JSON output
    profile_data = {}
    for col_name in df.columns:
        series = df[col_name].dropna().astype(str).str.strip()
        
        # Determine the original data type and length from the layout
        layout_row = layout_df[layout_df['handoff column name'] == col_name].iloc[0]
        original_spec = layout_row['data type with length'].upper()
        
        # Get length from layout (re-parsing to be safe)
        length = 0
        is_numeric = False
        if 'COMP-3' in original_spec:
            is_numeric = True
            match = re.search(r'S9\((\d+)\)(V9+(\(\d+\))?)?', original_spec)
            if match:
                s9_len = int(match.group(1))
                v9_len = 0
                if match.group(2):
                    if match.group(3):
                        v9_len = int(match.group(3).strip('()'))
                    else:
                        v9_len = len(match.group(2).replace('V', ''))
                total_digits = s9_len + v9_len
                length = math.ceil((total_digits + 1) / 2)
        elif any(x in original_spec for x in ['COMP-4', 'COMP-5', 'COMP', 'BINARY']):
            is_numeric = True
            match = re.search(r'S9\((\d+)\)', original_spec)
            if match:
                digits = int(match.group(1))
                if digits <= 4: length = 2
                elif digits <= 9: length = 4
                elif digits <= 18: length = 8
        elif 'X' in original_spec:
            match = re.search(r'X\((\d+)\)', original_spec)
            if match: length = int(match.group(1))
        elif 'S9' in original_spec:
            is_numeric = True
            match = re.search(r'S9\((\d+)\)(V9+(\(\d+\))?)?', original_spec)
            if match:
                s9_len = int(match.group(1))
                v9_len = 0
                if match.group(2):
                    if match.group(3):
                        v9_len = int(match.group(3).strip('()'))
                    else:
                        v9_len = len(match.group(2).replace('V', ''))
                length = s9_len + v9_len
        
        col_profile = {
            'original_name': col_name,
            'original_spec': original_spec,
            'length': length,
            'total_count': len(df),
            'null_count': len(df) - len(series),
            'null_percentage': round((len(df) - len(series)) / len(df) * 100, 2)
        }
        
        unique_vals = series.unique()
        unique_count = len(unique_vals)
        col_profile['unique_count'] = unique_count
        col_profile['unique_percentage'] = round(unique_count / len(df) * 100, 2)
        
        if unique_count <= 20 and len(series) > 0:
            col_profile['is_categorical'] = True
            col_profile['enum_values'] = series.value_counts().to_dict()
        else:
            col_profile['is_categorical'] = False
            col_profile['sample_values'] = list(series.sample(min(10, unique_count)))
            
        if is_numeric:
            try:
                numeric_series = pd.to_numeric(series)
                metrics = {'min': numeric_series.min(), 'max': numeric_series.max(), 'mean': numeric_series.mean(), 'median': numeric_series.median(), 'std_dev': numeric_series.std()}
                col_profile['metrics'] = {key: float(value) for key, value in metrics.items()}
            except ValueError:
                logger.warning(f"Could not convert column '{col_name}' to numeric. Skipping numeric profiling.")
                
        profile_data[col_name] = col_profile

    output_file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file_path, 'w') as f:
        json.dump(profile_data, f, indent=4)
    logger.info(f"Profiling complete. Output saved to {output_file_path}")
    return profile_data