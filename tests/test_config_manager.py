# /cibus2/tests/test_config_manager.py

import sys
import os
import json
import pytest
from pathlib import Path

# Add the project root to the sys.path to allow imports from src
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import config_manager

# Define the path to the config file at the project root
CONFIG_PATH = Path('./config.json')

@pytest.fixture(autouse=True)
def setup_and_teardown_config():
    """
    Fixture to ensure a fresh, valid config.json exists before each test
    and to clean up after.
    """
    initial_content = {
        "database_path": "db/cibus_runs.db",
        "output_folder": "data/synthetic_data"
    }
    
    # Save a fresh, valid config file before the test
    with open(CONFIG_PATH, 'w') as f:
        json.dump(initial_content, f)
    
    yield  # This is where the test runs
    
    # Clean up and ensure the valid config is restored after the test
    if not CONFIG_PATH.exists():
        with open(CONFIG_PATH, 'w') as f:
            json.dump(initial_content, f)

def test_load_config_success():
    """Tests that the function successfully loads a valid config file."""
    config = config_manager.load_config()
    assert config['database_path'] == "db/cibus_runs.db"
    assert config['output_folder'] == "data/synthetic_data"
    print("\n✅ Test_load_config_success passed.")

def test_load_config_file_not_found():
    """Tests that the function raises FileNotFoundError if the file is missing."""
    # Temporarily remove the config file
    os.rename(CONFIG_PATH, 'temp_config.json')
    try:
        with pytest.raises(FileNotFoundError):
            config_manager.load_config()
        print("✅ Test_load_config_file_not_found passed.")
    finally:
        # Restore the config file for other tests
        os.rename('temp_config.json', CONFIG_PATH)

def test_load_config_json_decode_error():
    """Tests that the function raises JSONDecodeError for invalid JSON."""
    with open(CONFIG_PATH, 'w') as f:
        f.write("{invalid_json}")
    with pytest.raises(json.JSONDecodeError):
        config_manager.load_config()
    print("✅ Test_load_config_json_decode_error passed.")

def test_load_config_missing_key_error():
    """Tests that the function raises KeyError if a required key is missing."""
    invalid_content = {"database_path": "db/cibus_runs.db"}  # Missing output_folder
    with open(CONFIG_PATH, 'w') as f:
        json.dump(invalid_content, f)
    with pytest.raises(KeyError, match="Missing required keys: \['output_folder'\]"):
        config_manager.load_config()
    print("✅ Test_load_config_missing_key_error passed.")