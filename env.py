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
        self.lock = threading.Lock()
        self.max_steps = 10
        self.current_step = 0

    # ── PUBLIC API ─────────────────────────────────────────────────────────────

    def reset(self, task_id: str = "audit_easy") -> Observation:
        self.task_id = task_id
        self.current_step = 0
        # Stop any running chaos monkey
        self.stop_monkey.set()

        with self.lock:
            time.sleep(0.2)
            if os.path.exists(self.template_path):
                shutil.copyfile(self.template_path, self.db_path)
            else:
                raise FileNotFoundError(
                    "template.db not found — did you run setup_db.py?"
                )

        # Start chaos monkey for medium / hard tasks
        if self.task_id in ("audit_medium", "audit_hard"):
            self.stop_monkey.clear()
            target = (
                self._run_chaos_monkey_hard
                if self.task_id == "audit_hard"
                else self._run_chaos_monkey_medium
            )
            threading.Thread(target=target, daemon=True).start()

        return self.state()

    def state(self) -> Observation:
        """Return a rich observation so the LLM agent knows exactly what to fix."""
        with self.lock:
            conn = sqlite3.connect(self.db_path, timeout=30)
            try:
                c = conn.cursor()

                # Aggregate stats
                c.execute("SELECT SUM(balance), COUNT(*) FROM accounts")
                total_balance, row_count = c.fetchone()
                total_balance = float(total_balance or 0.0)
                row_count = int(row_count or 0)

                # Count issues
                c.execute("SELECT COUNT(*) FROM accounts WHERE balance < 0")
                neg_count = c.fetchone()[0]

                c.execute(
                    "SELECT COUNT(*) FROM "
                    "(SELECT id FROM accounts GROUP BY id HAVING COUNT(*) > 1)"
                )
                dup_count = c.fetchone()[0]

                c.execute(
                    "SELECT COUNT(*) FROM accounts WHERE status != 'ACTIVE'"
                )
                bad_status_count = c.fetchone()[0]

                # Sample rows for the LLM
                c.execute(
                    "SELECT id, name, balance, status FROM accounts "
                    "WHERE balance < 0 LIMIT 3"
                )
                neg_samples = [
                    {"id": r[0], "name": r[1], "balance": r[2], "status": r[3]}
                    for r in c.fetchall()
                ]

                c.execute(
                    "SELECT id, COUNT(*) as cnt FROM accounts "
                    "GROUP BY id HAVING cnt > 1 LIMIT 3"
                )
                dup_samples = [{"id": r[0], "duplicate_count": r[1]} for r in c.fetchall()]

                c.execute(
                    "SELECT id, status FROM accounts WHERE status != 'ACTIVE' LIMIT 3"
                )
                bad_status_samples = [{"id": r[0], "status": r[1]} for r in c.fetchall()]

                result_set = [
                    {
                        "negative_balance_count": neg_count,
                        "negative_balance_samples": neg_samples,
                        "duplicate_id_count": dup_count,
                        "duplicate_id_samples": dup_samples,
                        "invalid_status_count": bad_status_count,
                        "invalid_status_samples": bad_status_samples,
                        "current_reward": round(self._raw_reward(neg_count, dup_count, bad_status_count), 4),
                    }
                ]

                return Observation(
                    success=True,
                    result_set=result_set,
                    current_checksum=total_balance,
                    row_count=row_count,
                )
            except Exception as e:
                return Observation(
                    success=False,
                    error_message=str(e),
                    current_checksum=0.0,
                    row_count=0,
                )
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
        if done:
            self.stop_monkey.set()
        return self.state(), reward, done, {"error": error}

    # ── INTERNAL ───────────────────────────────────────────────────────────────

    @staticmethod
    def _raw_reward(neg: int, dup: int, bad: int) -> float:
        """
        Reward is 1.0 only when ALL issues are zero.
        Uses a denominator of 50 (matches setup_db's ~50 injected bugs),
        so 50 issues → reward=0.0, 0 issues → reward=1.0 with smooth in between.
        """
        total_issues = neg + dup + bad
        return float(max(0.0, min(1.0, 1.0 - (total_issues / 50.0))))

    def _calculate_reward(self) -> float:
        with self.lock:
            conn = sqlite3.connect(self.db_path, timeout=30)
            try:
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM accounts WHERE balance < 0")
                neg = c.fetchone()[0]
                c.execute(
                    "SELECT COUNT(*) FROM "
                    "(SELECT id FROM accounts GROUP BY id HAVING COUNT(*) > 1)"
                )
                dup = c.fetchone()[0]
                c.execute(
                    "SELECT COUNT(*) FROM accounts WHERE status != 'ACTIVE'"
                )
                bad = c.fetchone()[0]
                return self._raw_reward(neg, dup, bad)
            except Exception:
                return 0.0
            finally:
                conn.close()

    def _run_chaos_monkey_hard(self):
        """Subtracts $5 from a random account every 2 seconds."""
        while not self.stop_monkey.is_set():
            with self.lock:
                try:
                    conn = sqlite3.connect(self.db_path, timeout=5)
                    conn.execute(
                        "UPDATE accounts SET balance = balance - 5 "
                        "WHERE id = (SELECT id FROM accounts ORDER BY RANDOM() LIMIT 1)"
                    )
                    conn.commit()
                    conn.close()
                except Exception:
                    pass
            time.sleep(2)

    def _run_chaos_monkey_medium(self):
        """Inserts a duplicate row every 8 seconds."""
        while not self.stop_monkey.is_set():
            with self.lock:
                try:
                    conn = sqlite3.connect(self.db_path, timeout=5)
                    conn.execute(
                        "INSERT INTO accounts SELECT id, name, balance, status "
                        "FROM accounts ORDER BY RANDOM() LIMIT 1"
                    )
                    conn.commit()
                    conn.close()
                except Exception:
                    pass
            time.sleep(8)