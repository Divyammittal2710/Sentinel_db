import sqlite3
import threading
import time
import os
from models import Observation, Action

class SentinelEnv:
    def __init__(self, task_id: str = "audit_easy"):
        self.db_path = "active.db"
        self.template_path = "template.db"
        self.task_id = task_id
        self.stop_monkey = threading.Event()
        self.max_steps = 20
        self.current_step = 0

    def reset(self, task_id: str = "audit_easy") -> Observation:
        """Mandatory OpenEnv Reset: Prepares the task and resets the DB."""
        self.task_id = task_id
        self.current_step = 0

        # 1. Stop any existing chaos monkey threads
        self.stop_monkey.set()
        time.sleep(0.1)

        # 2. Reset the Active DB from the Template
        if not os.path.exists(self.template_path):
            print("[DEBUG] template.db not found. Generating on the fly for validator...")
            os.system("python setup_db.py")
            time.sleep(1)
            
        with open(self.template_path, 'rb') as f_src, open(self.db_path, 'wb') as f_dst:
            f_dst.write(f_src.read())

        # 3. Trigger Chaos Monkey based on task difficulty
        if task_id == "audit_hard":
            self.stop_monkey.clear()
            threading.Thread(target=self._run_chaos_monkey, daemon=True).start()
        elif task_id == "audit_medium":
            self.stop_monkey.clear()
            threading.Thread(target=self._run_chaos_monkey_medium, daemon=True).start()

        return self.state()

    def state(self) -> Observation:
        """Mandatory OpenEnv Method: Returns current state without a turn."""
        return self._get_current_observation()

    def _run_chaos_monkey(self):
        """Background thread that corrupts data during Task 3."""
        while not self.stop_monkey.is_set():
            try:
                conn = sqlite3.connect(self.db_path)
                conn.execute(
                    "UPDATE accounts SET balance = balance - 5.0 "
                    "WHERE id = (SELECT id FROM accounts ORDER BY RANDOM() LIMIT 1)"
                )
                conn.commit()
                conn.close()
            except:
                pass
            time.sleep(2)

    def _run_chaos_monkey_medium(self):
        """Slower chaos: drains money every 8s AND occasionally injects a duplicate row."""
        import random
        tick = 0
        while not self.stop_monkey.is_set():
            try:
                conn = sqlite3.connect(self.db_path)

                # Every tick: subtract a small amount from a random account
                conn.execute(
                    "UPDATE accounts SET balance = balance - 5.0 "
                    "WHERE id = (SELECT id FROM accounts ORDER BY RANDOM() LIMIT 1)"
                )

                # Every 3 ticks (~24s): inject a duplicate row
                if tick % 3 == 0:
                    conn.execute(
                        "INSERT INTO accounts SELECT id, name || '_DUP', balance, status "
                        "FROM accounts ORDER BY RANDOM() LIMIT 1"
                    )

                conn.commit()
                conn.close()
            except:
                pass
            tick += 1
            time.sleep(8)

    def _get_current_observation(self) -> Observation:
        """Improved: Now identifies BOTH negatives and duplicates for the Agent."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT SUM(balance) as checksum, COUNT(*) as rows FROM accounts")
            result = cursor.fetchone()
            checksum = result['checksum'] if result['checksum'] else 0.0
            row_count = result['rows']

            cursor.execute("SELECT * FROM accounts WHERE balance < 0 LIMIT 3")
            neg_samples = [dict(row) for row in cursor.fetchall()]

            cursor.execute("SELECT id, COUNT(*) as count FROM accounts GROUP BY id HAVING count > 1 LIMIT 3")
            dup_samples = [dict(row) for row in cursor.fetchall()]

            report = {
                "negative_balance_samples": neg_samples,
                "duplicate_id_samples": dup_samples,
                "current_reward": self._calculate_reward()
            }

            return Observation(
                current_checksum=float(checksum),
                row_count=int(row_count),
                result_set=[report],
                success=True
            )
        except Exception as e:
            return Observation(current_checksum=0.0, row_count=0, result_set=[], success=False, error_message=str(e))
        finally:
            conn.close()

    def _calculate_reward(self) -> float:
        """The Programmatic Grader: Normalizes integrity to 0.0 - 1.0 range."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM accounts WHERE balance < 0")
        neg_balances = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM (SELECT id FROM accounts GROUP BY id HAVING COUNT(*) > 1)")
        duplicates = cursor.fetchone()[0]
        conn.close()

        total_issues = neg_balances + duplicates
        score = max(0.0, 1.0 - (total_issues / 50.0))
        return float(score)

    def step(self, action: Action):
        """Improved: Uses executescript to allow multiple fixes in one turn."""
        self.current_step += 1
        error_msg = None

        if action.query:
            try:
                conn = sqlite3.connect(self.db_path)
                conn.executescript(action.query)
                conn.close()
            except Exception as e:
                error_msg = str(e)

        obs = self.state()
        reward = self._calculate_reward()
        done = (reward >= 1.0) or (self.current_step >= self.max_steps)

        if done:
            self.stop_monkey.set()

        return obs, reward, done, {"error": error_msg}

    def close(self):
        """Ensures the thread is killed when the environment is closed."""
        self.stop_monkey.set()