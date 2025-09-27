# This is a one-off script to test the main.py functionality
import os
import sys
import shutil
import sqlite3
from pathlib import Path

# Set up the environment to import from src
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import main
from src.db_manager import get_db_path

# Define dummy file paths
DUMMY_LAYOUT = 'dummy_layout.xlsx'
DUMMY_HANDOFF = 'dummy_handoff.txt'

# Clean up any previous test runs
def cleanup():
    if Path('db').exists():
        shutil.rmtree('db')
    if Path('data').exists():
        shutil.rmtree('data')

def verify_db_record():
    """Connects to the DB and verifies the record count."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM runs")
    count = cursor.fetchone()[0]
    conn.close()
    return count == 1

# Main test execution
print("Starting isolated test for main.py...")
cleanup()

# Simulate the main() function call with dummy arguments
main.main(args=type('args', (object,), {'layout': DUMMY_LAYOUT, 'handoff': DUMMY_HANDOFF})())

# Verification steps
# 1. Verify directories were created
print("Verifying directories...")
assert Path('db').is_dir(), "db directory was not created."
assert Path('data').is_dir(), "data directory was not created."
assert Path('data/synthetic_data').is_dir(), "data/synthetic_data directory was not created."
print("✅ Directories verified.")

# 2. Verify database file was created
print("Verifying database file...")
assert Path(get_db_path()).is_file(), "Database file was not created."
print("✅ Database file verified.")

# 3. Verify a record was inserted
print("Verifying database record...")
assert verify_db_record(), "No record was inserted into the database."
print("✅ Database record verified.")

print("\nIsolated test completed successfully. main.py is working as expected.")

# Final cleanup (optional)
# cleanup()