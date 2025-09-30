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

### 3\. Generating Synthetic Data (Phase 3)

To generate a new dataset from a set of rules, run the `generate` subcommand with a JSON rules file.

```bash
python -m src.main generate --rules [path_to_rules.json] --num_records 10000
```

This will create a `generated_data_YYYYMMDD_HHMMSS.txt` file containing 10,000 synthetic records.