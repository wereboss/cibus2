# /cibus2/tests/test_profiler.py

import sys
import json
import pytest
import pandas as pd
from pathlib import Path

# Add the project root to the sys.path to allow imports from src
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import profiler

# Define dummy data for testing with COBOL specs
DUMMY_LAYOUT_DF = pd.DataFrame({
    'Handoff Column Name': ['CUSTOMER_ID', 'CUSTOMER_NAME', 'INVOICE_AMOUNT', 'DEPT_CODE', 'SALES_AMOUNT_COMP3', 'COMP4_FIELD'],
    'Data Type with Length': ['S9(10)', 'X(20)', 'S9(11)V99', 'X(4)', 'S9(9)V99 COMP-3', 'S9(8) COMP-4'],
    'Description': ['Numeric ID', 'Customer name', 'Invoice amount with decimal', 'Department code', 'Sales amount packed decimal', 'Binary field']
})

# Corrected to have precise lengths for COBOL specs
DUMMY_FLAT_FILE_CONTENT = """
0000000001JOHN DOE            0000000001050ABCD1234560012
0000000002JANE SMITH          0000000002025EFGH9876540023
0000000003PETER JONES         0000000003000IJKL0000110034
"""

def test_run_profiling_success(tmp_path):
    """
    Tests the end-to-end profiling process with COBOL specs.
    """
    layout_path = tmp_path / "dummy_layout.xlsx"
    handoff_path = tmp_path / "dummy_handoff.txt"
    output_path = tmp_path / "data/synthetic_data" / "profile.json"
    
    # Write dummy Excel file
    DUMMY_LAYOUT_DF.to_excel(layout_path, index=False)
    
    # Write dummy flat file
    with open(handoff_path, 'w') as f:
        f.write(DUMMY_FLAT_FILE_CONTENT.strip())
        
    profile_data = profiler.run_profiling(layout_path, handoff_path, output_path)
    
    # Verify the returned JSON object
    assert "CUSTOMER_ID" in profile_data
    assert "CUSTOMER_NAME" in profile_data
    assert "INVOICE_AMOUNT" in profile_data
    assert "DEPT_CODE" in profile_data
    assert "SALES_AMOUNT_COMP3" in profile_data
    assert "COMP4_FIELD" in profile_data
    
    # Verify lengths based on COBOL specs
    assert profile_data['CUSTOMER_ID']['length'] == 10
    assert profile_data['CUSTOMER_NAME']['length'] == 20
    assert profile_data['INVOICE_AMOUNT']['length'] == 13
    assert profile_data['DEPT_CODE']['length'] == 4
    # COMP-3 length is ceil((9+2+1)/2) = 6
    assert profile_data['SALES_AMOUNT_COMP3']['length'] == 6
    # COMP-4 S9(8) length is 4 bytes
    assert profile_data['COMP4_FIELD']['length'] == 4
    
    # Verify profiling metrics
    assert profile_data['CUSTOMER_ID']['metrics']['mean'] == pytest.approx(2.0)
    assert profile_data['DEPT_CODE']['is_categorical'] is True
    
    # --- CRITICAL FIX ---
    # Correct the expected mean to match the dummy data
    assert profile_data['SALES_AMOUNT_COMP3']['metrics']['mean'] == pytest.approx(370373.6666666667)
    
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        file_content = json.load(f)
    assert "CUSTOMER_ID" in file_content
    print("\n✅ test_run_profiling_success passed.")

def test_run_profiling_file_not_found(tmp_path):
    output_path = tmp_path / "output.json"
    with pytest.raises(Exception):
        profiler.run_profiling(Path("non_existent.xlsx"), Path("non_existent.txt"), output_path)
    print("✅ test_run_profiling_file_not_found passed.")