# /cibus2/tests/test_db_manager.py

import sys
import os
import pytest
import sqlite3
import shutil
from pathlib import Path
from unittest.mock import patch

# Add the project root to the sys.path to allow imports from src
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import db_manager

# Define a temporary test database path
TEST_DB_PATH = Path('test_db/test_cibus_runs.db')
TEST_DB_DIR = Path('test_db')

@pytest.fixture(autouse=True)
def setup_and_teardown_db():
    """Fixture to ensure a fresh database for each test and clean up afterwards."""
    # Setup: Create a temporary directory and database file
    if TEST_DB_DIR.exists():
        shutil.rmtree(TEST_DB_DIR)
    TEST_DB_DIR.mkdir()

    # We need to patch load_config to return our test db path
    with patch('src.db_manager.load_config') as mock_load_config:
        mock_load_config.return_value = {"database_path": str(TEST_DB_PATH)}
        db_manager.create_db_and_table()
        yield  # Run the test
    
    # Teardown: Remove the temporary directory and all its contents
    shutil.rmtree(TEST_DB_DIR)
    print("\nTemporary database and directory cleaned up.")

def test_insert_run_record():
    """Tests that a record is correctly inserted and the row ID is returned."""
    # Patch the get_db_path to return our test path
    with patch('src.db_manager.get_db_path', return_value=TEST_DB_PATH):
        row_id = db_manager.insert_run_record("layout_test.xlsx", "handoff_test.txt", "output_test.json")
    
    assert row_id is not None
    assert isinstance(row_id, int)
    
    # Verify the record was inserted by querying the database directly
    conn = sqlite3.connect(TEST_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT layout_filename FROM runs WHERE id = ?", (row_id,))
    result = cursor.fetchone()
    conn.close()

    assert result[0] == "layout_test.xlsx"
    print("✅ Test_insert_run_record passed.")

def test_list_run_records(capsys):
    """Tests that the list_run_records function correctly retrieves and prints records."""
    # First, insert a record for the test
    with patch('src.db_manager.get_db_path', return_value=TEST_DB_PATH):
        db_manager.insert_run_record("layout_list.xlsx", "handoff_list.txt", "output_list.json")
    
    # Now, call the list function and capture the stdout
    with patch('src.db_manager.get_db_path', return_value=TEST_DB_PATH):
        db_manager.list_run_records()
    
    # Capture the output
    captured = capsys.readouterr()
    stdout_output = captured.out
    
    # Verify that the correct string is in the output
    assert "Cibus2 Run Records" in stdout_output
    assert "layout_list.xlsx" in stdout_output
    assert "handoff_list.txt" in stdout_output
    print("✅ Test_list_run_records passed.")