# /cibus2/src/generator.py

import json
import logging
from pathlib import Path
import random
import re
from typing import Dict, Any, List

# Set up logging for this module
logger = logging.getLogger(__name__)

class DataGenerator:
    """
    A class to generate synthetic data based on a set of rules.
    """
    def __init__(self, rules_file_path: Path):
        """
        Initializes the generator with a rules file.
        """
        self.rules_file_path = rules_file_path
        self.rules = self._load_rules()
        self.generation_order = sorted(self.rules['fields'], key=lambda x: x['generation_order'])
        self._initialize_random_seed()

        # Placeholders for generated data pools (e.g., client IDs)
        self.data_pools = {}
        self.generated_data = {}
        self.next_sequential_ids = {}

    def _load_rules(self) -> Dict[str, Any]:
        """
        Loads the generation rules from a JSON file.
        """
        if not self.rules_file_path.is_file():
            logger.error(f"Rules file not found at {self.rules_file_path}")
            raise FileNotFoundError(f"Rules file not found: {self.rules_file_path}")
        
        with open(self.rules_file_path, 'r') as f:
            rules = json.load(f)
            logger.info("Generation rules loaded successfully.")
        
        return rules

    def _initialize_random_seed(self):
        """
        Initializes the random number generator with a seed from the config.
        """
        seed = self.rules['global_config'].get('random_seed')
        if seed is not None:
            random.seed(seed)
            logger.info(f"Random seed set to {seed}.")

    def generate_records(self, num_records: int) -> List[str]:
        """
        Generates and returns a list of formatted records.
        """
        output_records = []
        for _ in range(num_records):
            record = self._generate_record()
            formatted_record = self._format_record(record)
            output_records.append(formatted_record)
        
        logger.info(f"Successfully generated {len(output_records)} records.")
        return output_records

    def _generate_record(self) -> Dict[str, Any]:
        """
        Generates a single record by iterating through fields in the defined order.
        """
        record = {}
        for field_spec in self.generation_order:
            field_name = field_spec['name']
            record[field_name] = self._generate_field_value(field_spec, record)
        return record

    def _generate_field_value(self, field_spec: Dict[str, Any], record: Dict[str, Any]) -> Any:
        """
        Dispatches to the correct generation method based on the field's rules.
        """
        method = field_spec['generation']['method']
        params = field_spec['generation']['parameters']
        
        if method == "sequential_unique_id":
            return self._generate_sequential_id(field_spec, params)
        elif method == "categorical_weighted":
            return self._generate_categorical_weighted(field_spec, params)
        elif method == "foreign_key_pool":
            return self._generate_foreign_key_pool(field_spec, params)
        elif method == "conditional_categorical":
            return self._generate_conditional_categorical(field_spec, params, record)
        # Add other methods as they are implemented
        else:
            logger.error(f"Unknown generation method: {method}")
            raise ValueError(f"Unknown generation method: {method}")

    def _generate_sequential_id(self, field_spec: Dict[str, Any], params: Dict[str, Any]) -> str:
        """
        Generates a unique, sequential ID.
        """
        field_name = field_spec['name']
        start_value = params.get('start_value', 1)
        
        if field_name not in self.next_sequential_ids:
            self.next_sequential_ids[field_name] = start_value

        current_id = self.next_sequential_ids[field_name]
        self.next_sequential_ids[field_name] += 1
        
        return str(current_id)

    def _generate_categorical_weighted(self, field_spec: Dict[str, Any], params: Dict[str, Any]) -> str:
        """
        Generates a value by sampling from a weighted list of categorical values.
        """
        values = params['values']
        weights = params['weights']
        return random.choices(values, weights=weights, k=1)[0]
    
    def _generate_foreign_key_pool(self, field_spec: Dict[str, Any], params: Dict[str, Any]) -> str:
        raise NotImplementedError("Foreign key pool generation not yet implemented.")

    def _generate_conditional_categorical(self, field_spec: Dict[str, Any], params: Dict[str, Any], record: Dict[str, Any]) -> str:
        raise NotImplementedError("Conditional categorical generation not yet implemented.")

    def _format_record(self, record: Dict[str, Any]) -> str:
        """
        Formats a dictionary record into a single fixed-length string.
        (This will be implemented in a later step)
        """
        formatted_fields = []
        for field_spec in self.generation_order:
            field_name = field_spec['name']
            value = record[field_name]
            # This is a temporary placeholder. The real logic will be implemented later.
            formatted_fields.append(str(value).zfill(field_spec['generation']['parameters']['length']))
        
        return "".join(formatted_fields)