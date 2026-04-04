# import sqlite3
# import os

# def create_ground_truth():
#     db_file = "template.db"
    
#     # Remove existing template if it exists to start fresh
#     if os.path.exists(db_file):
#         os.remove(db_file)
#         print(f"Existing {db_file} removed.")

#     # Connect to SQLite
#     conn = sqlite3.connect(db_file)
#     cursor = conn.cursor()

#     # --- Schema Design ---
#     print("Creating tables...")
    
#     # Main Accounts Table
#     cursor.execute("""
#         CREATE TABLE accounts (
#             id INTEGER, 
#             name TEXT NOT NULL,
#             balance REAL,
#             status TEXT
#         );
#     """)

#     # Audit Log Table (To track agent actions later)
#     cursor.execute("""
#         CREATE TABLE audit_log (
#             log_id INTEGER PRIMARY KEY AUTOINCREMENT,
#             account_id INTEGER,
#             action TEXT,
#             timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
#         );
#     """)

#     # --- Injecting the "Bugs" ---
#     print("Injecting bugs into data...")

#     # 1. Healthy Data (The Baseline)
#     cursor.execute("INSERT INTO accounts VALUES (100, 'Alice Smith', 1250.50, 'ACTIVE')")
    
#     # 2. Duplicate Entry (Bug: Two rows with ID 101)
#     cursor.execute("INSERT INTO accounts VALUES (101, 'Bob Jones', 400.00, 'ACTIVE')")
#     cursor.execute("INSERT INTO accounts VALUES (101, 'Bob Jones', 400.00, 'ACTIVE')")

#     # 3. Negative Balance (Bug: Financial impossibility for this schema)
#     cursor.execute("INSERT INTO accounts VALUES (102, 'Charlie Brown', -500.0, 'ACTIVE')")

#     # 4. Inconsistency (Bug: Active status but zero balance/inactive state logic)
#     cursor.execute("INSERT INTO accounts VALUES (103, 'Diana Prince', 0.0, 'ACTIVE')")

#     # Commit and Close
#     conn.commit()
#     conn.close()
#     print(f"Successfully created {db_file} with injected errors.")

# if __name__ == "__main__":
#     create_ground_truth()

import sqlite3
import random
import os
from faker import Faker

# Use the same filename your env.py expects
DB_FILE = "template.db"
fake = Faker()

def create_expanded_db():
    # 1. Clean up old files to prevent 'Ghost Data'
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 2. Create Schema (Matching your teammate's latest Grid View)
    # columns: id, name, balance, status
    cursor.execute("""
        CREATE TABLE accounts (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            balance REAL NOT NULL,
            status TEXT NOT NULL
        )
    """)

    print(f"🚀 Generating 1,000 rows of FinTech data in {DB_FILE}...")

    accounts = []
    # Generate 950 Clean Records first
    for i in range(100, 1050):
        accounts.append((
            i, 
            fake.name(), 
            round(random.uniform(100.0, 5000.0), 2), 
            "ACTIVE"
        ))

    # 3. Inject 50 "Corrupt" Rows (5% Error Rate)
    # We use these to test the AI's Audit capabilities
    for _ in range(50):
        bug_type = random.choice(['negative', 'duplicate', 'invalid_status'])
        
        if bug_type == 'negative':
            # Negative balance bug
            accounts.append((len(accounts)+200, fake.name(), -random.uniform(50, 500), "ACTIVE"))
        
        elif bug_type == 'duplicate':
            # Duplicate ID bug: Pick an existing ID from the first 100 rows
            existing_id = random.randint(100, 200)
            accounts.append((existing_id, f"ERR_{fake.name()}", random.uniform(10, 1000), "ACTIVE"))
            
        elif bug_type == 'invalid_status':
            # Logic bug: Valid balance but status is 'CORRUPT' or 'NULL'
            accounts.append((len(accounts)+200, fake.name(), random.uniform(10, 1000), "CORRUPT_LOGIC"))

    # 4. Shuffle so bugs aren't all at the bottom
    random.shuffle(accounts)

    # 5. Insert into Database
    # We use 'INSERT OR REPLACE' so duplicates don't crash the script, 
    # but remain in the DB for the AI to find.
    cursor.executemany("INSERT OR REPLACE INTO accounts VALUES (?, ?, ?, ?)", accounts)

    conn.commit()
    
    # 6. Final Verification
    cursor.execute("SELECT COUNT(*) FROM accounts")
    row_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(balance) FROM accounts")
    total_checksum = cursor.fetchone()[0] or 0.0

    print("-" * 30)
    print(f"✅ Success! {DB_FILE} is ready.")
    print(f"📊 Total Rows: {row_count}")
    print(f"💰 Initial Checksum: {round(total_checksum, 2)}")
    print("-" * 30)
    
    conn.close()

if __name__ == "__main__":
    # Check if faker is installed
    try:
        create_expanded_db()
    except ImportError:
        print("❌ Error: 'faker' library not found. Run 'pip install faker' first.")
