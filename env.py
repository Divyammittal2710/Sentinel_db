import sqlite3
import threading
import time
import os
import shutil
from models import Observation, Action

class SentinelEnv:
    def __init__(self, task_id: str = "audit_easy"):
        self.db_path = "active.db"
        self.template_path = "template.db"
        self.task_id = task_id
        self.stop_monkey = threading.Event()
        self.lock = threading.Lock() # Prevents collisions
        self.max_steps = 20
        self.current_step = 0

    def reset(self, task_id: str = "audit_easy") -> Observation:
        self.task_id = task_id
        self.current_step = 0
        self.stop_monkey.set() # Stop any running monkey
        
        with self.lock:
            time.sleep(0.2)
            if os.path.exists(self.template_path):
                shutil.copyfile(self.template_path, self.db_path)
        
        if self.task_id in ["audit_medium", "audit_hard"]:
            self.stop_monkey.clear()
            target = self._run_chaos_monkey if self.task_id == "audit_hard" else self._run_chaos_monkey_medium
            threading.Thread(target=target, daemon=True).start()

        return self.state()

    def state(self) -> Observation:
        with self.lock:
            conn = sqlite3.connect(self.db_path, timeout=30)
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT SUM(balance), COUNT(*) FROM accounts")
                res = cursor.fetchone()
                return Observation(
                    current_checksum=float(res[0] or 0.0),
                    row_count=int(res[1] or 0),
                    success=True
                )
            except Exception as e:
                return Observation(success=False, error_message=str(e), current_checksum=0.0, row_count=0)
            finally:
                conn.close()

    def step(self, action: Action):
        self.current_step += 1
        error = None
        with self.lock:
            if action.query:
                try:
                    conn = sqlite3.connect(self.db_path, timeout=30)
                    conn.executescript(action.query)
                    conn.close()
                except Exception as e:
                    error = str(e)
        
        reward = self._calculate_reward()
        done = (reward >= 1.0) or (self.current_step >= self.max_steps)
        if done: self.stop_monkey.set()
        return self.state(), reward, done, {"error": error}

    def _calculate_reward(self) -> float:
        with self.lock:
            conn = sqlite3.connect(self.db_path, timeout=30)
            try:
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM accounts WHERE balance < 0")
                n = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM (SELECT id FROM accounts GROUP BY id HAVING COUNT(*) > 1)")
                d = c.fetchone()[0]
                return float(max(0.0, 1.0 - ((n + d) / 1000.0)))
            except:
                return 0.0
            finally:
                conn.close()

    def _run_chaos_monkey(self):
        while not self.stop_monkey.is_set():
            with self.lock:
                try:
                    conn = sqlite3.connect(self.db_path, timeout=5)
                    conn.execute("UPDATE accounts SET balance = balance - 5 WHERE id = (SELECT id FROM accounts ORDER BY RANDOM() LIMIT 1)")
                    conn.commit()
                    conn.close()
                except: pass
            time.sleep(2)

    def _run_chaos_monkey_medium(self):
        while not self.stop_monkey.is_set():
            with self.lock:
                try:
                    conn = sqlite3.connect(self.db_path, timeout=5)
                    conn.execute("INSERT INTO accounts SELECT id, name, balance, status FROM accounts ORDER BY RANDOM() LIMIT 1")
                    conn.commit()
                    conn.close()
                except: pass
            time.sleep(8)