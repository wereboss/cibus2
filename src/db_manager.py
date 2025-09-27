# /cibus2/src/db_manager.py

import sqlite3
import logging
from datetime import datetime
from pathlib import Path

# Local imports
from .config_manager import load_config

# Set up logging for this module
logger = logging.getLogger(__name__)

def get_db_path():
    """
    Loads the database path from the configuration file.

    Returns:
        Path: The absolute path to the SQLite database file.
    """
    try:
        config = load_config()
        db_path_str = config['database_path']
        return Path(db_path_str).resolve()
    except Exception as e:
        logger.error(f"Failed to load database path from config: {e}")
        raise

def create_db_and_table():
    """
    Creates the SQLite database file and the 'runs' table if they don't exist.
    """
    db_path = get_db_path()
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY,
                layout_filename TEXT NOT NULL,
                handoff_filename TEXT NOT NULL,
                output_json_filename TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()
        logger.info("Database and 'runs' table created successfully.")
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        raise

def insert_run_record(layout_filename, handoff_filename, output_json_filename):
    """
    Inserts a new record into the 'runs' table with a real-time timestamp.

    Returns:
        int: The row ID of the newly inserted record.
    """
    db_path = get_db_path()
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Use a real timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute('''
            INSERT INTO runs (layout_filename, handoff_filename, output_json_filename, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (layout_filename, handoff_filename, output_json_filename, timestamp))
        
        conn.commit()
        row_id = cursor.lastrowid
        conn.close()
        logger.info(f"Record inserted successfully with ID: {row_id}")
        return row_id
    except sqlite3.Error as e:
        logger.error(f"Failed to insert record: {e}")
        raise

def list_run_records():
    """
    Retrieves and prints all records from the 'runs' table.
    """
    db_path = get_db_path()
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM runs ORDER BY timestamp DESC")
        records = cursor.fetchall()
        conn.close()

        if not records:
            print("No run records found.")
            return

        print("\n--- Cibus2 Run Records ---")
        for record in records:
            print(f"ID: {record[0]} | Layout: {record[1]} | Handoff: {record[2]} | JSON: {record[3]} | Time: {record[4]}")
        print("--------------------------")
        
    except sqlite3.Error as e:
        logger.error(f"Error listing records: {e}")
        raise