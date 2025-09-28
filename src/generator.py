# /cibus2/src/generator.py

import json
import logging
from pathlib import Path
import random
import re
import math
import datetime
import numpy as np
from typing import Dict, Any, List

# Set up logging for this module
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataGenerator:
    """
    A class to generate synthetic data based on a set of rules.
    """
    def __init__(self, rules: Dict[str, Any]):
        """
        Initializes the generator with a rules dictionary.
        """
        self.rules = rules
        self.generation_order = sorted(self.rules['fields'], key=lambda x: x['generation_order'])
        self._initialize_random_seed()

        self.data_pools = {}
        self.generated_data = {}
        self.next_sequential_ids = {}

        self._pre_generate_pools()
        self._pre_generate_dates()

    def _initialize_random_seed(self):
        """
        Initializes the random number generator with a seed from the config.
        """
        seed = self.rules['global_config'].get('random_seed')
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)  # Use numpy's seed as well for distributions
            logger.info(f"Random seed set to {seed}.")

    def _pre_generate_pools(self):
        """
        Pre-generates pools for foreign keys.
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

        pool_keys = [f"{prefix}{i:0{length - len(prefix)}d}" for i in range(1, num_unique_keys + 1)]
        
        self.data_pools[field_name] = pool_keys
        logger.info(f"Pre-generated a pool of {num_unique_keys} unique keys for {field_name}.")

    def _pre_generate_dates(self):
        """
        Pre-generates a list of unique dates if required.
        """
        for field_spec in self.generation_order:
            if field_spec['generation']['method'] == 'uniform_date_range':
                params = field_spec['generation']['parameters']
                if params.get('unique', False):
                    field_name = field_spec['name']
                    start_date = datetime.datetime.strptime(params['start_date'], "%Y-%m-%d").date()
                    end_date = datetime.datetime.strptime(params['end_date'], "%Y-%m-%d").date()
                    date_range = [start_date + datetime.timedelta(days=i) for i in range((end_date - start_date).days + 1)]
                    random.shuffle(date_range)
                    self.data_pools[field_name] = date_range

    def generate_records(self, num_records: int) -> List[str]:
        """
        Generates and returns a list of formatted records.
        """
        output_records = []
        for i in range(num_records):
            logger.debug(f"Generating record {i+1} of {num_records}...")
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
            try:
                field_name = field_spec['name']
                logger.debug(f"  Generating value for field: {field_name}")
                record[field_name] = self._generate_field_value(field_spec, record)
            except KeyError as e:
                logger.error(f"Failed to find expected key in rules for field. The faulty entry is: {field_spec}. Error: {e}")
                raise
        logger.debug(f"  Generated record: {record}")
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
        elif method == "truncated_normal":
            return self._generate_truncated_normal(field_spec, params, record)
        elif method == "uniform_date_range":
            return self._generate_uniform_date(field_spec, params)
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
        
        return str(current_id)

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

    def _generate_truncated_normal(self, field_spec: Dict[str, Any], params: Dict[str, Any], record: Dict[str, Any]) -> float:
        """
        Generates a value from a truncated normal distribution.
        """
        mu = params['mu']
        sigma = params['sigma']
        min_val = params['min_value']
        max_val = params['max_value']
        
        dependencies = field_spec.get('dependencies', [])
        for dep in dependencies:
            if dep['rule'] == 'adjust_value_by_currency':
                currency = record.get(dep['field'])
                if currency in ['USD', 'EUR']:
                    mu *= dep['factor']
            # Other rules can be added here
        
        while True:
            val = np.random.normal(mu, sigma)
            if min_val <= val <= max_val:
                return val
    
    def _generate_uniform_date(self, field_spec: Dict[str, Any], params: Dict[str, Any]) -> str:
        """
        Generates a date string from a uniform date range.
        """
        if params.get('unique', False):
            field_name = field_spec['name']
            if self.data_pools.get(field_name):
                return self.data_pools[field_name].pop(0).strftime("%Y%m%d")
            else:
                raise ValueError("Unique date pool is empty.")
        else:
            start_date = datetime.datetime.strptime(params['start_date'], "%Y-%m-%d").date()
            end_date = datetime.datetime.strptime(params['end_date'], "%Y-%m-%d").date()
            num_days = (end_date - start_date).days
            random_days = random.randrange(num_days + 1)
            generated_date = start_date + datetime.timedelta(days=random_days)
            return generated_date.strftime("%Y%m%d")

    def _format_record(self, record: Dict[str, Any]) -> str:
        """
        Formats a dictionary record into a single fixed-length string.
        """
        formatted_fields = []
        for field_spec in self.generation_order:
            field_name = field_spec['name']
            value = record[field_name]
            
            length = field_spec['generation']['parameters'].get('length')
            
            original_spec = field_spec['original_spec'].upper()
            if 'V' in original_spec:
                v_match = re.search(r'V9+(\(\d+\))?', original_spec)
                decimal_places = int(v_match.group(1).strip('()')) if v_match and v_match.group(1) else len(v_match.group(0).replace('V', '')) if v_match else 0
                
                integer_value = int(round(value * (10 ** decimal_places)))
                formatted_value = str(integer_value).zfill(length)
                formatted_fields.append(formatted_value)
            else:
                formatted_fields.append(str(value).zfill(length))
        
        return "".join(formatted_fields)