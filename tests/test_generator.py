# /cibus2/tests/test_generator.py

import sys
import pytest
import json
from pathlib import Path
from unittest.mock import patch
import random

# Add the project root to the sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.generator import DataGenerator

# A simple mock rules JSON for testing the loading functionality
DUMMY_RULES_JSON = {
  "global_config": {
    "default_row_count": 10,
    "scaling_factor": 1.0,
    "random_seed": 42
  },
  "fields": [
    {
      "name": "ACCOUNT_NUMBER",
      "original_spec": "S9(9)",
      "generation_order": 1,
      "generation": {
        "method": "sequential_unique_id",
        "parameters": {
          "prefix": "01",
          "start_value": 1,
          "length": 9,
          "unique": True
        }
      },
      "dependencies": []
    },
    {
      "name": "PROD_TYPE_CODE",
      "original_spec": "S9(3)",
      "generation_order": 2,
      "generation": {
        "method": "categorical_weighted",
        "parameters": {
          "values": ["011", "022", "033"],
          "weights": [0.5, 0.3, 0.2],
          "length": 3
        }
      },
      "dependencies": []
    }
  ]
}

def test_data_generator_init_success(tmp_path):
    """
    Tests that the DataGenerator can be initialized with a valid rules file.
    """
    # Create a dummy rules file
    rules_file = tmp_path / "rules.json"
    with open(rules_file, 'w') as f:
        json.dump(DUMMY_RULES_JSON, f)
    
    # Initialize the generator
    generator = DataGenerator(rules_file)
    
    # Assertions to check if the rules were loaded correctly
    assert generator.rules is not None
    assert generator.rules['global_config']['random_seed'] == 42
    assert len(generator.generation_order) == 2
    assert generator.generation_order[0]['name'] == 'ACCOUNT_NUMBER'
    print("\n✅ test_data_generator_init_success passed.")

def test_generate_sequential_id_correctly(tmp_path):
    """
    Tests that sequential IDs are generated correctly with padding.
    """
    rules_file = tmp_path / "rules.json"
    with open(rules_file, 'w') as f:
        json.dump(DUMMY_RULES_JSON, f)
    
    generator = DataGenerator(rules_file)
    field_spec = DUMMY_RULES_JSON['fields'][0]
    
    first_id = generator._generate_field_value(field_spec, {})
    second_id = generator._generate_field_value(field_spec, {})
    
    assert first_id == "1"
    assert second_id == "2"
    print("✅ test_generate_sequential_id_correctly passed.")

def test_generate_categorical_weighted_correctly(tmp_path):
    """
    Tests that categorical values are generated according to weights.
    We'll mock the random.choices function to ensure determinism.
    """
    rules_file = tmp_path / "rules.json"
    with open(rules_file, 'w') as f:
        json.dump(DUMMY_RULES_JSON, f)
    
    generator = DataGenerator(rules_file)
    field_spec = DUMMY_RULES_JSON['fields'][1]
    
    # Mock random.choices to return a deterministic value
    with patch('random.choices', return_value=['011']):
        generated_value = generator._generate_field_value(field_spec, {})
        assert generated_value == "011"

    with patch('random.choices', return_value=['022']):
        generated_value = generator._generate_field_value(field_spec, {})
        assert generated_value == "022"
    
    print("✅ test_generate_categorical_weighted_correctly passed.")