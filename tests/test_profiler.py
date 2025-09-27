# /cibus2/tests/test_profiler.py

import sys
import json
import pytest
import pandas as pd
from pathlib import Path

# Add the project root to the sys.path to allow imports from src
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import profiler

# Define dummy data for testing
DUMMY_LAYOUT_DF = pd.DataFrame({
    'Handoff Column Name': ['CUSTOMER_ID', 'CUSTOMER_NAME', 'INVOICE_AMOUNT'],
    'Data Type with Length': ['NUMERIC(10)', 'ALPHA(20)', 'NUMERIC(12)'],
    'Description': ['Unique customer ID', 'Name of the customer', 'Total invoice amount']
})

DUMMY_FLAT_FILE_CONTENT = """
0000000001JOHN DOE            000000100.50
0000000002JANE SMITH          000000050.25
0000000003PETER JONES         000000200.00
"""

def test_run_profiling_success(tmp_path):
    """
    Tests the end-to-end profiling process with a valid layout and data file.
    """
    # Create temporary dummy files in the isolated test path
    layout_path = tmp_path / "dummy_layout.xlsx"
    handoff_path = tmp_path / "dummy_handoff.txt"
    
    # --- CRITICAL FIX ---
    # Create a full output path as a Path object
    output_path = tmp_path / "data/synthetic_data" / "profile.json"
    
    # Write dummy Excel file (requires openpyxl to be installed)
    DUMMY_LAYOUT_DF.to_excel(layout_path, index=False)
    
    # Write dummy flat file
    with open(handoff_path, 'w') as f:
        f.write(DUMMY_FLAT_FILE_CONTENT.strip())
        
    # Run the profiling utility with the full output path
    profile_data = profiler.run_profiling(layout_path, handoff_path, output_path)
    
    # Verify the returned JSON object
    assert "CUSTOMER_ID" in profile_data
    assert "CUSTOMER_NAME" in profile_data
    assert "INVOICE_AMOUNT" in profile_data
    
    # Verify specific metrics for a numeric column
    inv_amount_profile = profile_data['INVOICE_AMOUNT']
    assert inv_amount_profile['original_type'] == 'numeric'
    assert inv_amount_profile['metrics']['mean'] == pytest.approx(116.9167)
    
    # Verify specific metrics for a string column
    cust_name_profile = profile_data['CUSTOMER_NAME']
    assert cust_name_profile['original_type'] == 'alpha'
    assert cust_name_profile['unique_count'] == 3
    
    # Verify the JSON file was created at the correct path
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        file_content = json.load(f)
    assert "CUSTOMER_ID" in file_content
    print("\n✅ test_run_profiling_success passed.")

def test_run_profiling_file_not_found(tmp_path):
    """Tests that the function raises an error for a non-existent file."""
    # Create a dummy output path to satisfy the function signature
    output_path = tmp_path / "output.json"
    
    with pytest.raises(Exception):
        profiler.run_profiling(Path("non_existent.xlsx"), Path("non_existent.txt"), output_path)
    print("✅ test_run_profiling_file_not_found passed.")