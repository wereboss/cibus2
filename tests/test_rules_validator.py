# /cibus2/tests/test_rules_validator.py

import pytest
import sys
import json
from pathlib import Path

# Add the project root to the sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.rules_validator import RulesValidator

# --- Mock JSONs for testing ---
VALID_RULES_JSON = {
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
                    "length": 9
                }
            }
        },
        {
            "name": "CLIENT_ID",
            "original_spec": "S9(11)",
            "generation_order": 2,
            "generation": {
                "method": "foreign_key_pool",
                "parameters": {
                    "length": 11
                }
            }
        }
    ]
}

INVALID_TOP_LEVEL_JSON = {
    "global_config": {},
    "fields_typo": []
}

INVALID_FIELD_KEY_JSON = {
    "global_config": {},
    "fields": [
        {
            "name": "ACCOUNT_NUMBER",
            "original_spec": "S9(9)",
            "generation_order": 1
        }
    ]
}

# --- Mock JSON for inferring length ---
MISSING_LENGTH_JSON = {
    "global_config": {"default_row_count": 20},
    "fields": [
        {
            "name": "CLIENT_ID",
            "original_spec": "S9(11)",
            "generation_order": 1,
            "generation": {
                "method": "sequential_unique_id",
                "parameters": {}
            }
        }
    ]
}

# --- Mock JSON for self-correction test ---
FAULTY_CONDITIONAL_JSON = {
    "global_config": {
        "default_row_count": 20
    },
    "fields": [
        {
            "name": "PROD_TYPE_CODE",
            "original_spec": "S9(3)",
            "generation_order": 1,
            "generation": {
                "method": "conditional_categorical",
                "parameters": {
                    "parent_field": ""
                }
            }
        }
    ]
}

def test_validator_success():
    """
    Tests that a valid JSON is successfully validated.
    """
    validator = RulesValidator(VALID_RULES_JSON)
    cleaned_rules = validator.validate_and_clean()
    assert cleaned_rules == VALID_RULES_JSON
    print("\n✅ test_validator_success passed.")

def test_validator_missing_top_level_key():
    """
    Tests that validation fails for a JSON missing a top-level key.
    """
    validator = RulesValidator(INVALID_TOP_LEVEL_JSON)
    with pytest.raises(ValueError, match="JSON is missing critical top-level keys"):
        validator.validate_and_clean()
    print("✅ test_validator_missing_top_level_key passed.")

def test_validator_missing_field_key():
    """
    Tests that validation fails for a field missing a required key.
    """
    validator = RulesValidator(INVALID_FIELD_KEY_JSON)
    with pytest.raises(KeyError, match="Field entry is missing a required key: 'generation'"):
        validator.validate_and_clean()
    print("✅ test_validator_missing_field_key passed.")

def test_validator_infers_length_from_spec():
    """
    Tests that the validator infers a missing length from original_spec.
    """
    validator = RulesValidator(MISSING_LENGTH_JSON)
    cleaned_rules = validator.validate_and_clean()
    field = cleaned_rules['fields'][0]
    assert 'length' in field['generation']['parameters']
    assert field['generation']['parameters']['length'] == 11
    print("✅ test_validator_infers_length_from_spec passed.")

def test_validator_heals_faulty_conditional_field():
    """
    Tests that the validator heals a faulty conditional_categorical field.
    """
    validator = RulesValidator(FAULTY_CONDITIONAL_JSON)
    cleaned_rules = validator.validate_and_clean()

    field = cleaned_rules['fields'][0]
    assert field['name'] == "PROD_TYPE_CODE"
    assert field['generation']['method'] == 'categorical_weighted'
    assert 'parent_field' not in field['generation']['parameters']
    assert 'mappings' not in field['generation']['parameters']
    print("✅ test_validator_heals_faulty_conditional_field passed.")