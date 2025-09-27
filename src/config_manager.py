# /cibus2/src/config_manager.py

import json
import logging
from pathlib import Path

# Set up logging for this module
logger = logging.getLogger(__name__)

def load_config(config_path: Path = None):
    """
    Loads configuration parameters from the config.json file.
    
    Args:
        config_path (Path, optional): The path to the config file. 
                                      Defaults to './config.json'.
    
    Returns:
        dict: A dictionary containing the configuration parameters.
    
    Raises:
        FileNotFoundError: If config.json is not found.
        json.JSONDecodeError: If there's an issue parsing the JSON file.
        KeyError: If a required key is missing from the config.
    """
    if config_path is None:
        config_path = Path('./config.json')

    if not config_path.is_file():
        logger.error(f"Configuration file not found at {config_path.resolve()}.")
        raise FileNotFoundError(f"config.json not found at {config_path.resolve()}")

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            logger.info("Configuration file loaded successfully.")
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from config.json: {e}")
        raise
    
    # Validate that all required keys are present
    required_keys = ["database_path", "output_folder"]
    if not all(key in config for key in required_keys):
        missing_keys = [key for key in required_keys if key not in config]
        logger.error(f"Missing required keys in config.json: {missing_keys}")
        raise KeyError(f"Missing required keys: {missing_keys}")

    return config

def create_default_config():
    """
    Creates a default config.json file with a standard structure.
    This is useful for initial project setup.
    """
    default_config = {
        "database_path": "db/cibus_runs.db",
        "output_folder": "data/synthetic_data"
    }
    
    config_path = Path('./config.json')
    if not config_path.exists():
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=4)
        logger.info(f"Default config.json created at {config_path.resolve()}.")