# /cibus2/src/main.py

import argparse
import logging
from pathlib import Path
from datetime import datetime

# Local imports
from .db_manager import create_db_and_table, insert_run_record
from .config_manager import load_config
from .profiler import run_profiling
from .generator import DataGenerator

# Set up basic logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_project_directories():
    """Ensures that the required project directories exist."""
    config = load_config()
    output_folder = Path(config['output_folder'])
    db_path = Path(config['database_path']).parent

    try:
        output_folder.mkdir(parents=True, exist_ok=True)
        db_path.mkdir(parents=True, exist_ok=True)
        logger.info("Project directories created or verified.")
    except Exception as e:
        logger.error(f"Failed to create project directories: {e}")
        raise

def run_profiler_mode(args):
    """
    Runs the utility in profiling mode.
    """
    layout_file_path = Path(args.layout)
    handoff_file_path = Path(args.handoff)
    layout_filename = layout_file_path.name
    handoff_filename = handoff_file_path.name
    
    config = load_config()
    output_folder = Path(config['output_folder'])
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json_filename = f"profile_output_{timestamp_str}.json"
    output_json_path = output_folder / output_json_filename

    try:
        run_profiling(layout_file_path, handoff_file_path, output_json_path)
        insert_run_record(layout_filename, handoff_filename, output_json_filename)
        logger.info("Profiling mode completed successfully.")
    except Exception as e:
        logger.error(f"Profiling failed: {e}")

def run_generator_mode(args):
    """
    Runs the utility in generation mode.
    """
    rules_file_path = Path(args.rules)
    num_records = args.num_records
    
    config = load_config()
    output_folder = Path(config['output_folder'])
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"generated_data_{timestamp_str}.txt"
    output_file_path = output_folder / output_filename
    
    try:
        generator = DataGenerator(rules_file_path)
        records = generator.generate_records(num_records)

        with open(output_file_path, 'w') as f:
            for record in records:
                f.write(record + '\n')
        
        logger.info(f"Generation mode completed successfully. Output saved to {output_file_path}")
    except Exception as e:
        logger.error(f"Data generation failed: {e}")

def main():
    """
    Main function to handle CLI arguments and orchestrate the utility.
    """
    parser = argparse.ArgumentParser(
        description="Cibus2 Data Utility - Profile or Generate data."
    )
    subparsers = parser.add_subparsers(dest='command', help='sub-command help')

    # Profiling Subparser
    profiler_parser = subparsers.add_parser('profile', help='Profile an existing flat file.')
    profiler_parser.add_argument(
        '--layout', type=str, required=True, help="Path to the COBOL layout Excel file."
    )
    profiler_parser.add_argument(
        '--handoff', type=str, required=True, help="Path to the sample fixed-length flat file."
    )

    # Generation Subparser
    generator_parser = subparsers.add_parser('generate', help='Generate a new synthetic data file.')
    generator_parser.add_argument(
        '--rules', type=str, required=True, help="Path to the JSON rules file."
    )
    generator_parser.add_argument(
        '--num_records', type=int, default=1000, help="Number of records to generate."
    )

    args = parser.parse_args()

    try:
        setup_project_directories()
        create_db_and_table()

        if args.command == 'profile':
            run_profiler_mode(args)
        elif args.command == 'generate':
            run_generator_mode(args)
        else:
            parser.print_help()
    except Exception as e:
        logger.critical(f"A fatal error occurred during execution: {e}")

if __name__ == "__main__":
    main()