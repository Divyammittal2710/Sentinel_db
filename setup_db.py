import sqlite3
import os

def create_ground_truth():
    db_file = "template.db"
    
    # Remove existing template if it exists to start fresh
    if os.path.exists(db_file):
        os.remove(db_file)
        print(f"Existing {db_file} removed.")

    # Connect to SQLite
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # --- Schema Design ---
    print("Creating tables...")
    
    # Main Accounts Table
    cursor.execute("""
        CREATE TABLE accounts (
            id INTEGER, 
            name TEXT NOT NULL,
            balance REAL,
            status TEXT
        );
    """)

    # Audit Log Table (To track agent actions later)
    cursor.execute("""
        CREATE TABLE audit_log (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER,
            action TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # --- Injecting the "Bugs" ---
    print("Injecting bugs into data...")

    # 1. Healthy Data (The Baseline)
    cursor.execute("INSERT INTO accounts VALUES (100, 'Alice Smith', 1250.50, 'ACTIVE')")
    
    # 2. Duplicate Entry (Bug: Two rows with ID 101)
    cursor.execute("INSERT INTO accounts VALUES (101, 'Bob Jones', 400.00, 'ACTIVE')")
    cursor.execute("INSERT INTO accounts VALUES (101, 'Bob Jones', 400.00, 'ACTIVE')")

    # 3. Negative Balance (Bug: Financial impossibility for this schema)
    cursor.execute("INSERT INTO accounts VALUES (102, 'Charlie Brown', -500.0, 'ACTIVE')")

    # 4. Inconsistency (Bug: Active status but zero balance/inactive state logic)
    cursor.execute("INSERT INTO accounts VALUES (103, 'Diana Prince', 0.0, 'ACTIVE')")

    # Commit and Close
    conn.commit()
    conn.close()
    print(f"Successfully created {db_file} with injected errors.")

if __name__ == "__main__":
    create_ground_truth()