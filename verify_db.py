import sqlite3
import os

db_file = "template.db"

# 1. Check if the file actually exists in this folder
if not os.path.exists(db_file):
    print(f"❌ ERROR: {db_file} not found in this directory!")
    print(f"Current Directory: {os.getcwd()}")
else:
    print(f"✅ Found {db_file}. Connecting...")
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # 2. Check what tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"📊 Tables found in DB: {tables}")

        # 3. Try to fetch data
        print("--- Fetching Account Data ---")
        cursor.execute("SELECT * FROM accounts")
        rows = cursor.fetchall()

        if not rows:
            print("⚠️ The 'accounts' table is EMPTY.")
        else:
            print(f"Found {len(rows)} rows:")
            print(f"{'ID':<5} | {'Name':<15} | {'Balance':<10} | {'Status'}")
            print("-" * 50)
            for row in rows:
                print(f"{row[0]:<5} | {row[1]:<15} | {row[2]:<10} | {row[3]}")

        conn.close()
        print("--- Verification Complete ---")

    except Exception as e:
        print(f"❌ DATABASE ERROR: {e}")