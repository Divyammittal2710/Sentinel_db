import sqlite3
import threading
import time
import os
import sys
from models import Observation, Action

class SentinelEnv:
    def __init__(self, task_id: str = "audit_easy"):
        self.db_path = "active.db"
        self.template_path = "template.db"
        self.task_id = task_id
        self.stop_monkey = threading.Event()
        self.max_steps = 20
        self.current_step = 0

    def reset(self, task_id: str = None, **kwargs) -> Observation:
        """FIXED: Removed os.system to prevent 500 Errors"""
        if task_id:
            self.task_id = task_id
        self.current_step = 0
        self.stop_monkey.set()
        time.sleep(0.2) 

        # Copy fresh DB from template (already built by Dockerfile)
        if os.path.exists(self.template_path):
            with open(self.template_path, 'rb') as f_src, open(self.db_path, 'wb') as f_dst:
                f_dst.write(f_src.read())
        
        if self.task_id in ["audit_medium", "audit_hard"]:
            self.stop_monkey.clear()
            target = self._run_chaos_monkey if self.task_id == "audit_hard" else self._run_chaos_monkey_medium
            threading.Thread(target=target, daemon=True).start()

        return self.state()

    def state(self) -> Observation:
        return self._get_current_observation()

    def _get_current_observation(self) -> Observation:
        # Increased timeout to 20s to prevent 'Database Locked' crashes
        conn = sqlite3.connect(self.db_path, timeout=20)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(balance) as checksum, COUNT(*) as rows FROM accounts")
            result = cursor.fetchone()
            checksum = result['checksum'] if result['checksum'] else 0.0
            row_count = result['rows']

            return Observation(
                current_checksum=float(checksum),
                row_count=int(row_count),
                result_set=[], 
                success=True
            )
        except Exception as e:
            return Observation(current_checksum=0.0, row_count=0, success=False, error_message=str(e))
        finally:
            conn.close()

    def _calculate_reward(self) -> float:
        conn = sqlite3.connect(self.db_path, timeout=20)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM accounts WHERE balance < 0")
            neg = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM (SELECT id FROM accounts GROUP BY id HAVING COUNT(*) > 1)")
            dupes = cursor.fetchone()[0]
            return float(max(0.0, 1.0 - ((neg + dupes) / 1000.0)))
        except:
            return 0.0
        finally:
            conn.close()

    def step(self, action: Action):
        self.current_step += 1
        if action.query:
            try:
                conn = sqlite3.connect(self.db_path, timeout=20)
                conn.executescript(action.query)
                conn.close()
            except:
                pass 

        reward = self._calculate_reward()
        done = (reward >= 1.0) or (self.current_step >= self.max_steps)
        if done: self.stop_monkey.set()
        return self.state(), reward, done, {}

    def _run_chaos_monkey(self):
        while not self.stop_monkey.is_set():
            try:
                conn = sqlite3.connect(self.db_path, timeout=20)
                conn.execute("UPDATE accounts SET balance = balance - 5 WHERE id = (SELECT id FROM accounts ORDER BY RANDOM() LIMIT 1)")
                conn.commit()
                conn.close()
            except: pass
            time.sleep(2)

    def _run_chaos_monkey_medium(self):
        while not self.stop_monkey.is_set():
            try:
                conn = sqlite3.connect(self.db_path, timeout=20)
                conn.execute("INSERT INTO accounts SELECT id, name, balance, status FROM accounts ORDER BY RANDOM() LIMIT 1")
                conn.commit()
                conn.close()
            except: pass
            time.sleep(8)