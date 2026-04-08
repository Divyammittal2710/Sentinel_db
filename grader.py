import sqlite3
import os
import glob

def grade(state=None, **kwargs) -> float:
    try:
        # 1. Find all .db files (ignoring the template)
        db_files = [f for f in glob.glob("*.db") if "template" not in f.lower()]

        if not db_files:
            return 0.0

        # 2. Grab the most recently modified active DB
        db_files.sort(key=os.path.getmtime, reverse=True)
        active_db = db_files[0]

        conn = sqlite3.connect(active_db)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM accounts WHERE balance < 0")
        negatives = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(id) - COUNT(DISTINCT id) FROM accounts")
        duplicates = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM accounts WHERE status != 'ACTIVE'")
        corrupts = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM accounts")
        total = cursor.fetchone()[0]

        conn.close()

        if total == 0:
            return 0.0

        # Partial credit: penalize proportionally per issue, not binary
        total_issues = negatives + duplicates + corrupts
        score = max(0.0, 1.0 - (total_issues / max(total, 1)))
        return round(min(score, 1.0), 4)

    except Exception:
        return 0.0

if _name_ == "_main_":
    score = grade()
    print(score)