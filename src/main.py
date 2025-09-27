# /cibus2/src/main.py

import argparse
import logging
from pathlib import Path
from datetime import datetime

# Local imports
from .db_manager import create_db_and_table, insert_run_record
from .config_manager import load_config

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
        logger.info(f"Project directories created or verified.")
    except Exception as e:
        logger.error(f"Failed to create project directories: {e}")
        raise

def main(args=None):
    """
    Main function to handle CLI arguments and orchestrate the profiling process.
    Accepts optional args for testing.
    """
    if args is None:
        parser = argparse.ArgumentParser(
            description="Cibus2 Data Profiling Utility - Phase 1."
        )
        parser.add_argument(
            '--layout',
            type=str,
            required=True,
            help="Path to the COBOL layout Excel file."
        )
        parser.add_argument(
            '--handoff',
            type=str,
            required=True,
            help="Path to the sample fixed-length flat file."
        )
        args = parser.parse_args()

    # Get filenames for logging
    layout_filename = Path(args.layout).name
    handoff_filename = Path(args.handoff).name
    
    # Generate a unique output JSON filename
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json_filename = f"profile_output_{timestamp_str}.json"

    # Set up directories and database
    try:
        setup_project_directories()
        create_db_and_table()
    except Exception as e:
        logger.critical(f"Setup failed. Exiting.")
        return

    # Record the run in the database
    run_id = insert_run_record(
        layout_filename, 
        handoff_filename, 
        output_json_filename
    )

    logger.info(f"Run recorded with ID: {run_id}")
    logger.info(f"Processing '{layout_filename}' and '{handoff_filename}'...")

    # TODO: Add call to profiler.py once implemented
    # from .profiler import run_profiling
    # run_profiling(args.layout, args.handoff, output_json_filename)

if __name__ == "__main__":
    main()