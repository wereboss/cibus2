# /cibus2/src/db_manager.py

import sqlite3
import logging

logger = logging.getLogger(__name__)

def get_db_path():
    """Helper function to get the database path from the placeholder config."""
    # We'll use a hardcoded path for this isolated test.
    return "db/cibus_runs.db"

def create_db_and_table():
    """Creates the SQLite database and the `runs` table."""
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
    """Inserts a new record into the `runs` table and returns the row ID."""
    db_path = get_db_path()
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Use a simplified timestamp for the placeholder
        timestamp = '2025-09-27 16:44:29'
        
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
        return None