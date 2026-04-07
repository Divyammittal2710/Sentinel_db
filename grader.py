import sqlite3

def grade(state=None, **kwargs) -> float:
    """
    The Meta OpenEnv Validator calls this function at the end of the episode
    to independently verify the score. It must return a float between 0.0 and 1.0.
    """
    try:
        conn = sqlite3.connect("active.db")
        cursor = conn.cursor()
        
        # 1. Check for negative balances
        cursor.execute("SELECT COUNT(*) FROM accounts WHERE balance < 0")
        negatives = cursor.fetchone()[0]
        
        # 2. Check for duplicate IDs
        cursor.execute("SELECT COUNT(id) - COUNT(DISTINCT id) FROM accounts")
        duplicates = cursor.fetchone()[0]
        
        # 3. Check for corrupt statuses
        cursor.execute("SELECT COUNT(*) FROM accounts WHERE status != 'ACTIVE'")
        corrupts = cursor.fetchone()[0]
        
        conn.close()
        
        # If all issues are 0, the database is perfectly clean (Score = 1.0)
        if negatives == 0 and duplicates == 0 and corrupts == 0:
            return 1.0
        return 0.0
        
    except Exception as e:
        # If the database is missing or locked, return 0.0
        return 0.0