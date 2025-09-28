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

        self.data_pools = {}
        self.generated_data = {}
        self.next_sequential_ids = {}

        self._pre_generate_pools()

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

    def _pre_generate_pools(self):
        """
        Pre-generates pools for foreign keys and other complex dependencies.
        """
        num_records = self.rules['global_config'].get('default_row_count', 1000)
        
        for field_spec in self.generation_order:
            if field_spec['generation']['method'] == 'foreign_key_pool':
                field_name = field_spec['name']
                params = field_spec['generation']['parameters']
                self._create_foreign_key_pool(field_name, params, num_records)
            
    def _create_foreign_key_pool(self, field_name: str, params: Dict[str, Any], num_records: int):
        """
        Creates a pool of foreign keys and their distribution based on rules.
        """
        pool_size_ratio = params.get('pool_size_ratio', 1.0)
        prefix = params.get('prefix', '')
        length = params.get('length')
        
        num_unique_keys = round(num_records * pool_size_ratio)
        if num_unique_keys == 0:
            logger.warning(f"Pool size for '{field_name}' is 0. Setting to 1.")
            num_unique_keys = 1

        # Generate sequential keys, ensuring they have the correct length and prefix
        pool_keys = [f"{prefix}{i:0{length - len(prefix)}d}" for i in range(1, num_unique_keys + 1)]
        
        self.data_pools[field_name] = pool_keys
        logger.info(f"Pre-generated a pool of {num_unique_keys} unique keys for {field_name}.")

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
        else:
            logger.error(f"Unknown generation method: {method}")
            raise ValueError(f"Unknown generation method: {method}")

    def _generate_sequential_id(self, field_spec: Dict[str, Any], params: Dict[str, Any]) -> str:
        """
        Generates a unique, sequential ID.
        """
        field_name = field_spec['name']
        start_value = params.get('start_value', 1)
        length = params.get('length')
        
        if field_name not in self.next_sequential_ids:
            self.next_sequential_ids[field_name] = start_value

        current_id = self.next_sequential_ids[field_name]
        self.next_sequential_ids[field_name] += 1
        
        return f"{current_id}".zfill(length)

    def _generate_categorical_weighted(self, field_spec: Dict[str, Any], params: Dict[str, Any]) -> str:
        """
        Generates a value by sampling from a weighted list of categorical values.
        """
        values = params['values']
        weights = params['weights']
        return random.choices(values, weights=weights, k=1)[0]
    
    def _generate_foreign_key_pool(self, field_spec: Dict[str, Any], params: Dict[str, Any]) -> str:
        """
        Generates a foreign key by sampling from a pre-generated pool.
        """
        field_name = field_spec['name']
        pool = self.data_pools[field_name]
        
        return random.choice(pool)

    def _generate_conditional_categorical(self, field_spec: Dict[str, Any], params: Dict[str, Any], record: Dict[str, Any]) -> str:
        """
        Generates a categorical value based on a parent field's value.
        """
        parent_field_name = params['parent_field']
        parent_value = record[parent_field_name]
        
        mapping = params['mappings'].get(parent_value)
        if not mapping:
            logger.warning(f"No mapping found for parent value '{parent_value}'. Using default.")
            mapping = params['mappings']['default']
        
        values = mapping['values']
        weights = mapping['weights']

        return random.choices(values, weights=weights, k=1)[0]

    def _format_record(self, record: Dict[str, Any]) -> str:
        """
        Formats a dictionary record into a single fixed-length string.
        """
        formatted_fields = []
        for field_spec in self.generation_order:
            field_name = field_spec['name']
            value = record[field_name]
            
            length = field_spec['generation']['parameters']['length']
            formatted_fields.append(str(value).zfill(length))
        
        return "".join(formatted_fields)