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
# NOTE: The COMP specifiers are removed to assume character-based unpacked data
DUMMY_LAYOUT_DF = pd.DataFrame({
    'Handoff Column Name': [
        'CUSTOMER_ID', 'CUSTOMER_NAME', 'INVOICE_AMOUNT', 'DEPT_CODE',
        'SALES_AMOUNT', 'COMP4_FIELD', 'INTEREST_RATE'
    ],
    'Data Type with Length': [
        'S9(10)', 'X(20)', 'S9(11)V99', 'X(4)',
        'S9(11)V99', 'S9(4)', 'S9(7)V99(4)'
    ],
    'Description': [
        'Numeric ID', 'Customer name', 'Invoice amount with decimal', 'Department code',
        'Sales amount', 'Binary field (unpacked)', 'Interest rate with 4 decimals'
    ]
})

# Corrected to have precise lengths for COBOL specs and clean data
DUMMY_FLAT_FILE_CONTENT = """
0000000001JOHN DOE            0000000001050ABCD0000000123450000500000012345
0000000002JANE SMITH          0000000002025EFGH0000000234560000600000023456
0000000003PETER JONES         0000000003000IJKL0000000345670000500000034567
0000000004JOHN DOE            0000000004050ABCD0000000456780000600000045678
0000000005JANE SMITH          0000000005025EFGH0000000567890000500000056789
0000000006PETER JONES         0000000006000IJKL0000000678900000600000067890
0000000007JOHN DOE            0000000007050ABCD0000000789010000500000078901
0000000008JANE SMITH          0000000008025EFGH0000000890120000600000089012
0000000009PETER JONES         0000000009000IJKL0000000901230000500000090123
0000000010JOHN DOE            0000000010050ABCD0000001012340000600000101234
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
    assert "SALES_AMOUNT" in profile_data
    assert "COMP4_FIELD" in profile_data
    assert "INTEREST_RATE" in profile_data
    
    # Verify lengths based on COBOL specs
    assert profile_data['CUSTOMER_ID']['length'] == 10
    assert profile_data['CUSTOMER_NAME']['length'] == 20
    assert profile_data['INVOICE_AMOUNT']['length'] == 13
    assert profile_data['DEPT_CODE']['length'] == 4
    assert profile_data['SALES_AMOUNT']['length'] == 13
    assert profile_data['COMP4_FIELD']['length'] == 4
    # S9(7)V99(4) length should be 7 + 4 = 11
    assert profile_data['INTEREST_RATE']['length'] == 11
    
    # Verify profiling metrics
    assert profile_data['CUSTOMER_ID']['metrics']['mean'] == pytest.approx(5.5)
    
    # Assert DEPT_CODE is categorical. Now 4 unique values out of 10 total rows (40% < 50%)
    assert profile_data['DEPT_CODE']['is_categorical'] is True
    
    # Corrected assertions for other numeric columns
    assert profile_data['INVOICE_AMOUNT']['metrics']['mean'] == pytest.approx(55.275)
    assert profile_data['SALES_AMOUNT']['metrics']['mean'] == pytest.approx(5999.95)
    assert profile_data['COMP4_FIELD']['metrics']['mean'] == pytest.approx(5.5)
    assert profile_data['INTEREST_RATE']['metrics']['mean'] == pytest.approx(5.99995)
    
    # Verify JSON file was created
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        file_content = json.load(f)
    assert "CUSTOMER_ID" in file_content
    print("\n✅ test_run_profiling_success passed.")

def test_run_profiling_file_not_found(tmp_path):
    """Tests that the function raises an error for a non-existent file."""
    output_path = tmp_path / "output.json"
    with pytest.raises(Exception):
        profiler.run_profiling(Path("non_existent.xlsx"), Path("non_existent.txt"), output_path)
    print("✅ test_run_profiling_file_not_found passed.")