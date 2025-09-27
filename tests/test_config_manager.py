# /cibus2/tests/test_config_manager.py

import sys
import json
import pytest
from pathlib import Path

# Add the project root to the sys.path to allow imports from src
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# The import path should now work correctly
from src import config_manager

def test_load_config_success(tmp_path):
    """Tests that the function successfully loads a valid config file."""
    # Create a dummy config file inside the temporary path
    temp_config_path = tmp_path / "config.json"
    temp_config_path.write_text(json.dumps({
        "database_path": "db/cibus_runs.db",
        "output_folder": "data/synthetic_data"
    }))
    
    config = config_manager.load_config(temp_config_path)
    assert config['database_path'] == "db/cibus_runs.db"
    assert config['output_folder'] == "data/synthetic_data"
    print("\n✅ Test_load_config_success passed.")

def test_load_config_file_not_found(tmp_path):
    """Tests that the function raises FileNotFoundError if the file is missing."""
    temp_config_path = tmp_path / "non_existent.json"
    with pytest.raises(FileNotFoundError):
        config_manager.load_config(temp_config_path)
    print("✅ Test_load_config_file_not_found passed.")

def test_load_config_json_decode_error(tmp_path):
    """Tests that the function raises JSONDecodeError for invalid JSON."""
    temp_config_path = tmp_path / "config.json"
    temp_config_path.write_text("{invalid_json}")
    with pytest.raises(json.JSONDecodeError):
        config_manager.load_config(temp_config_path)
    print("✅ Test_load_config_json_decode_error passed.")

def test_load_config_missing_key_error(tmp_path):
    """Tests that the function raises KeyError if a required key is missing."""
    temp_config_path = tmp_path / "config.json"
    temp_config_path.write_text(json.dumps({"database_path": "db/cibus_runs.db"}))
    # Note the double backslash to escape the backslash itself, which escapes the bracket
    with pytest.raises(KeyError, match="Missing required keys: \\['output_folder'\\]"):
        config_manager.load_config(temp_config_path)
    print("✅ Test_load_config_missing_key_error passed.")