# /cibus2/tests/test_generator.py

import sys
import pytest
import json
from pathlib import Path
from unittest.mock import patch
import random
from collections import Counter

# Add the project root to the sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.generator import DataGenerator

# --- Mock JSON for testing categorical and dependencies ---
DUMMY_RULES_JSON_ENUMS = {
  "global_config": {
    "default_row_count": 20,
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
      "description": "Product type code",
      "original_spec": "S9(3)",
      "generation_order": 2,
      "generation": {
        "method": "categorical_weighted",
        "parameters": {
          "values": ["011", "022", "033"],
          "weights": [0.4, 0.4, 0.2],
          "length": 3
        }
      },
      "dependencies": []
    },
    {
      "name": "SUB_PROD_CODE",
      "description": "Sub-product code",
      "original_spec": "S9(4)",
      "generation_order": 3,
      "generation": {
        "method": "conditional_categorical",
        "parameters": {
          "parent_field": "PROD_TYPE_CODE",
          "mappings": {
            "011": {"values": ["0111", "0112"], "weights": [0.5, 0.5]},
            "022": {"values": ["0221", "0222"], "weights": [0.5, 0.5]},
            "033": {"values": ["0331", "0332"], "weights": [0.5, 0.5]},
            "default": {"values": ["0000"], "weights": [1.0]}
          },
          "length": 4
        }
      },
      "dependencies": [
        {"field": "PROD_TYPE_CODE", "rule": "prefix_match"}
      ]
    }
  ]
}

def test_data_generator_init_success(tmp_path):
    """
    Tests that the DataGenerator can be initialized with a valid rules file.
    """
    rules_file = tmp_path / "rules_enums.json"
    with open(rules_file, 'w') as f:
        json.dump(DUMMY_RULES_JSON_ENUMS, f)
    
    generator = DataGenerator(rules_file)
    
    assert generator.rules is not None
    assert generator.rules['global_config']['random_seed'] == 42
    assert len(generator.generation_order) == 3
    assert generator.generation_order[0]['name'] == 'ACCOUNT_NUMBER'
    print("\n✅ test_data_generator_init_success passed.")

def test_generate_enum_and_dependent_fields_correctly(tmp_path):
    """
    Tests that parent-child categorical fields are generated correctly.
    """
    rules_file = tmp_path / "rules_enums.json"
    with open(rules_file, 'w') as f:
        json.dump(DUMMY_RULES_JSON_ENUMS, f)
    
    generator = DataGenerator(rules_file)
    num_records = DUMMY_RULES_JSON_ENUMS['global_config']['default_row_count']
    
    # Generate records
    records = generator.generate_records(num_records)
    
    # Extract fields
    prod_type_codes = [record[9:12] for record in records]
    sub_prod_codes = [record[12:16] for record in records]

    # Verification
    for i in range(num_records):
        prod_code = prod_type_codes[i]
        sub_code = sub_prod_codes[i]
        
        # Assert that the sub_prod_code starts with the prod_type_code
        assert sub_code.startswith(prod_code)

    # Check for correct distribution based on weights
    prod_counts = Counter(prod_type_codes)
    assert len(prod_counts) == 3
    
    print("✅ test_generate_enum_and_dependent_fields_correctly passed.")