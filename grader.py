import sqlite3
import os
import glob

def grade(state=None, **kwargs) -> float:
    try:
        # 1. Find all .db files in the folder (ignoring the template)
        db_files = [f for f in glob.glob("*.db") if "template" not in f.lower()]
        
        if not db_files:
            return 0.0
            
        # 2. Sort by modification time to grab the exact DB the agent just finished using
        db_files.sort(key=os.path.getmtime, reverse=True)
        active_db = db_files[0]
        
        # 3. Connect and Grade
        conn = sqlite3.connect(active_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM accounts WHERE balance < 0")
        negatives = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(id) - COUNT(DISTINCT id) FROM accounts")
        duplicates = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM accounts WHERE status != 'ACTIVE'")
        corrupts = cursor.fetchone()[0]
        
        conn.close()
        
        if negatives == 0 and duplicates == 0 and corrupts == 0:
            return 1.0
        return 0.0
        
    except Exception:
        return 0.0

if __name__ == "__main__":
    print(grade())