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

# --- Mock JSON for testing primary/foreign keys ---
DUMMY_RULES_JSON_KEYS = {
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
      "name": "CLIENT_ID",
      "original_spec": "S9(11)",
      "generation_order": 2,
      "generation": {
        "method": "foreign_key_pool",
        "parameters": {
          "pool_size_ratio": 0.5,
          "prefix": "0990",
          "length": 11,
          "distribution": "poisson",
          "distribution_params": {
            "lambda": 2
          }
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
    rules_file = tmp_path / "rules_keys.json"
    with open(rules_file, 'w') as f:
        json.dump(DUMMY_RULES_JSON_KEYS, f)
    
    generator = DataGenerator(rules_file)
    
    assert generator.rules is not None
    assert generator.rules['global_config']['random_seed'] == 42
    assert len(generator.generation_order) == 2
    assert generator.generation_order[0]['name'] == 'ACCOUNT_NUMBER'
    print("\n✅ test_data_generator_init_success passed.")

def test_create_foreign_key_pool_correctly(tmp_path):
    """
    Tests that the foreign key pool is generated with the correct size and values.
    """
    rules_file = tmp_path / "rules_keys.json"
    with open(rules_file, 'w') as f:
        json.dump(DUMMY_RULES_JSON_KEYS, f)
    
    generator = DataGenerator(rules_file)
    num_records = DUMMY_RULES_JSON_KEYS['global_config']['default_row_count']
    
    pool_size = round(num_records * DUMMY_RULES_JSON_KEYS['fields'][1]['generation']['parameters']['pool_size_ratio'])
    
    assert 'CLIENT_ID' in generator.data_pools
    assert len(generator.data_pools['CLIENT_ID']) == pool_size
    assert generator.data_pools['CLIENT_ID'][0] == '09900000001'
    assert generator.data_pools['CLIENT_ID'][-1] == '09900000010'
    print("✅ test_create_foreign_key_pool_correctly passed.")

def test_generate_keys_correctly(tmp_path):
    """
    Tests that the primary and foreign keys are generated according to rules.
    """
    rules_file = tmp_path / "rules_keys.json"
    with open(rules_file, 'w') as f:
        json.dump(DUMMY_RULES_JSON_KEYS, f)
    
    generator = DataGenerator(rules_file)
    num_records = DUMMY_RULES_JSON_KEYS['global_config']['default_row_count']
    
    records = generator.generate_records(num_records)
    
    account_numbers = [record[0:9] for record in records]
    client_ids = [record[9:20] for record in records]
    
    # --- Verification ---
    # 1. Verify ACCOUNT_NUMBER (primary key)
    assert len(set(account_numbers)) == num_records
    assert account_numbers[0] == '000000001'
    assert account_numbers[-1] == '000000020'
    
    # 2. Verify CLIENT_ID (foreign key)
    pool_size = round(num_records * DUMMY_RULES_JSON_KEYS['fields'][1]['generation']['parameters']['pool_size_ratio'])
    unique_client_ids = set(client_ids)
    
    assert len(unique_client_ids) <= pool_size
    assert unique_client_ids.issubset(set(generator.data_pools['CLIENT_ID']))
    
    client_counts = Counter(client_ids)
    assert max(client_counts.values()) > 1
    
    print("✅ test_generate_keys_correctly passed.")