# Cibus2: A Synthetic Data Generation Utility

Cibus2 is a Python-based utility designed to generate highly realistic, synthetic data that accurately mirrors the complex patterns and distributions found in an existing dataset.

The core strength of this project is its **unique, human-in-the-loop, and iterative approach**, which combines the power of automated data profiling with the analytical capabilities of a Large Language Model (LLM) to produce a robust and scalable data generator.

## Our Project Methodology

We developed Cibus2 through a four-phase protocol:

1.  **Phase 1: Automated Profiling**: A Python utility profiles a real, fixed-length handoff flat file and its corresponding COBOL layout. It calculates key statistics, identifies categorical values, and generates a structured JSON profile.
2.  **Phase 2: LLM-Guided Inference**: The JSON profile is provided to an LLM, which acts as a data analyst. It infers complex inter-field relationships, conditional business rules, and generation strategies, and then outputs these as a machine-readable JSON blueprint.
3.  **Phase 3: Rules-Based Generation**: A custom Python generator consumes the LLM's JSON blueprint and produces a large volume of synthetic data that adheres to all the specified rules and patterns.
4.  **Phase 4: Validation and Refinement**: The synthetic data is profiled again, and both the original and generated profiles are fed back to the LLM. This iterative feedback loop allows for the fine-tuning of generation rules to achieve the highest possible data fidelity.

## Key Features & Enhancements

  * **Modular and Scalable Architecture**: The project is built with separate, testable components for profiling, validation, and generation, making it easy to maintain and extend.
  * **Robust COBOL Data Type Handling**: The utility can parse and correctly interpret complex mainframe data types like `S9(n)`, `V99(m)`, `X(n)`, and `COMP` formats for accurate length calculation and decimal point handling.
  * **Self-Correcting JSON Validation**: A dedicated `RulesValidator` component intelligently sanitizes LLM output. It automatically infers missing parameters (e.g., `length` from `original_spec`) and corrects logical flaws, ensuring the generator always receives clean, valid instructions.
  * **Complex Relationship Modeling**: The generator can replicate intricate relationships, including one-to-many primary/foreign key links and conditional dependencies between fields.

## Project Structure

```
/cibus2
├── config.json               # Global configuration settings
├── requirements.txt          # Project dependencies
├── /data
│   └── /synthetic_data/      # Output folder for generated data and profiles
├── /src
│   ├── main.py               # The main command-line interface
│   ├── generator.py          # The core data generation logic
│   ├── profiler.py           # The data profiling engine
│   ├── rules_validator.py    # The component for sanitizing LLM rules
│   └── ...                   # Other modules
└── /tests
    ├── ...                   # Isolated test scripts for each module
```

## Installation and Usage

### 1\. Installation

Install the required Python packages using `pip`.

```bash
pip install -r requirements.txt
```

### 2\. Profiling a Dataset (Phase 1)

To profile an existing fixed-length file, run the `profile` subcommand.

```bash
python -m src.main profile --layout [path_to_layout.xlsx] --handoff [path_to_data.txt]
```

This command will generate a `profile_output_YYYYMMDD_HHMMSS.json` file in the `data/synthetic_data/` directory.

### 2\. LLM-Guided Rule Generation (Phase 2)
Manually provide the JSON profile from Phase 1 to an LLM. Instruct it to act as a data analyst and generate a new, machine-readable JSON rules file that contains all the necessary generation logic and dependencies.

prompt used:
```
I need you to act as a data analyst. Your task is to examine the provided JSON data profile (refer profile_output_first.json) of a fixed-length flat file and generate a set of detailed, actionable data generation rules. The goal is to create synthetic data that mimics the original dataset's complex patterns and inter-attribute relationships, not just random values.

Your assessment should be a clear. Be as specific as possible, referencing column names, data types, and values from the JSON.

Here are the specific insights I need you to infer and document:

1. Primary and Foreign Key Relationships: Identify primary key (unique_percentage = 100%) and foreign key (unique_percentage < 100% and a likely link to a primary key) fields.

2. Parent-Child Relationships: Based on naming conventions, description and sample values, identify which fields are likely dependent on others. For example, sub-product-type-code is probably dependent on sub-product-type-code.

3. Data Distributions: For each numeric field, specify a generation strategy based on the provided min, max, mean, and std_dev metrics (e.g., normal, uniform).

4. Categorical Values: For categorical fields, document the exact list of enum_values and their frequencies to be used for generation.

5. Conditional Logic & Dependencies: Infer specific business rules based on the inferred relationships between fields. For example, "if product-type is 'Credit-Card', then currency-code must be 'USD' or 'EUR'."

6. Formatting Rules: Note any specific formatting, such as zero-padding or fixed lengths.

Aligned to the goal, generate the output in a JSON format below, which would be necessarily detailed and still leverageable by a synthesis utility. Generate only the JSON output and dont include any additional text.

JSON output schema:

{
  "global_config": {
    "default_row_count": "<integer>",
    "scaling_factor": "<float>",
    "random_seed": "<integer>"
  },
  "fields": [
    {
      "name": "<string>",
      "description": "<string>",
      "original_spec": "<string>",
      "generation_order": "<integer>",
      "generation": {
        "method": "sequential_unique_id",
        "parameters": {
          "prefix": "<string>",
          "start_value": "<integer>",
          "length": "<integer>",
          "unique": true
        }
      },
      "dependencies": []
    },
    {
      "name": "<string>",
      "description": "<string>",
      "original_spec": "<string>",
      "generation_order": "<integer>",
      "generation": {
        "method": "foreign_key_pool",
        "parameters": {
          "pool_size_ratio": "<float>",
          "prefix": "<string>",
          "length": "<integer>",
          "distribution": "<string>",
          "distribution_params": {
            "lambda": "<float>"
          }
        }
      },
      "dependencies": []
    },
    {
      "name": "<string>",
      "description": "<string>",
      "original_spec": "<string>",
      "generation_order": "<integer>",
      "generation": {
        "method": "conditional_categorical",
        "parameters": {
          "parent_field": "<string>",
          "mappings": {
            "value1": {
              "values": ["<string>"],
              "weights": ["<float>"]
            }
          }
        }
      },
      "dependencies": [
        {
          "field": "<string>",
          "rule": "<string>"
        }
      ]
    },
    {
      "name": "<string>",
      "description": "<string>",
      "original_spec": "<string>",
      "generation_order": "<integer>",
      "generation": {
        "method": "truncated_normal",
        "parameters": {
          "mu": "<float>",
          "sigma": "<float>",
          "min_value": "<float>",
          "max_value": "<float>",
          "decimal_places": "<integer>"
        }
      },
      "dependencies": []
    },
    {
      "name": "<string>",
      "description": "<string>",
      "original_spec": "<string>",
      "generation_order": "<integer>",
      "generation": {
        "method": "uniform_date_range",
        "parameters": {
          "start_date": "<string>",
          "end_date": "<string>",
          "length": "<integer>",
          "unique": "<boolean>"
        }
      },
      "dependencies": []
    }
  ]
}
```

### 3\. Generating Synthetic Data (Phase 3)

To generate a new dataset from a set of rules, run the `generate` subcommand with a JSON rules file.

```bash
python -m src.main generate --rules [path_to_rules.json] --num_records 10000
```

This will create a `generated_data_YYYYMMDD_HHMMSS.txt` file containing 10,000 synthetic records.

### 4\. Evaulating the generated data (phase 4)

Generate the data profile of the newly generated synthetic data and utilize LLM to compare against the original profile and suggest corrections

```bash
python -m src.main profile --layout [path_to_layout.xlsx] --handoff [path_to_synthetic_data.txt]
```

Prompt used for :
```
I have two JSON data profiles. The first is 'Original_Profile' from a small sample dataset. The second is 'Generated_Profile' from a large synthetic dataset created based on rules inferred from the first.

Your task is to act as a data analyst and provide a comprehensive, side-by-side analysis. Highlight key similarities and, more importantly, any significant discrepancies or mismatches.

For your analysis, focus on:
1. Statistical metrics (min, max, mean, std_dev) for each field.
2. Uniqueness and distribution of categorical fields (unique_count and enum_values).
3. Consistency in inferred relationships and patterns.

structure your response such that, for every column, include the below sub-bullets
- "original" - which mentions the column's nature and distribution in the original profile
- "generated" - which mentions the same column's nature and distribution in the generated data profile
- "observations" - mention your observations on how the column rendering behaved after synthetic data generation
- "Fix suggestions" - give a clear succinct instruction on how this specific column synthetic data can be fixed

at the end include a "key takeaways" section, which succinctly summarises the key observations & fixes in a prioritised order. 

Do not provide any new technical rules or code yet. Your output should be a clear, written analysis.
```