import sqlite3
import random
import os
from faker import Faker

DB_FILE = "template.db"
fake = Faker()

def create_expanded_db():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

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

    for i in range(100, 1050):
        accounts.append((
            i,
            fake.name(),
            round(random.uniform(100.0, 5000.0), 2),
            "ACTIVE"
        ))

    for _ in range(50):
        bug_type = random.choice(['negative', 'duplicate', 'invalid_status'])

        if bug_type == 'negative':
            accounts.append((len(accounts)+200, fake.name(), -random.uniform(50, 500), "ACTIVE"))

        elif bug_type == 'duplicate':
            existing_id = random.randint(100, 200)
            accounts.append((existing_id, f"ERR_{fake.name()}", random.uniform(10, 1000), "ACTIVE"))

        elif bug_type == 'invalid_status':
            accounts.append((len(accounts)+200, fake.name(), random.uniform(10, 1000), "CORRUPT_LOGIC"))

    random.shuffle(accounts)

    cursor.executemany("INSERT OR REPLACE INTO accounts VALUES (?, ?, ?, ?)", accounts)

    conn.commit()

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
    try:
        create_expanded_db()
    except ImportError:
        print("❌ Error: 'faker' library not found. Run 'pip install faker' first.")