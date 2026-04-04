# import sqlite3
# import shutil
# import os
# from models import Action, Observation, State

# class SentinelEnv:
#     def get_row_count(self):
#         conn = sqlite3.connect(self.active_path)
#         count = conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
#         conn.close()
#         return count
#     def __init__(self):
#         self.template_path = "template.db"
#         self.active_path = "active.db"
#         self.state = State()

#     def get_checksum(self):
#         """Calculates the total balance of all accounts to ensure data integrity."""
#         conn = sqlite3.connect(self.active_path)
#         cursor = conn.cursor()
#         cursor.execute("SELECT SUM(balance) FROM accounts")
#         total = cursor.fetchone()[0] or 0.0
#         conn.close()
#         return total

#     def reset(self) -> Observation:
#         """Starts a fresh session by copying the Ground Truth database."""
#         if os.path.exists(self.active_path):
#             os.remove(self.active_path)
        
#         shutil.copy(self.template_path, self.active_path)
        
#         # Reset internal state
#         self.state = State()
        
#         return Observation(
#             success=True,
#             result_set=[{"message": "Environment reset. Ready for tasks."}],
#             current_checksum=self.get_checksum(),
#             unprocessed_chaos_events=0
#         )

#     def step(self, action: Action) -> tuple[Observation, float, bool]:
#         """Executes the agent's SQL command and returns the outcome."""
#         self.state.step_count += 1
#         error = None
#         results = None
#         success = True

#         try:
#             conn = sqlite3.connect(self.active_path)
#             # Enable WAL mode for better concurrency
#             conn.execute("PRAGMA journal_mode=WAL;")
#             cursor = conn.cursor()

#             # Execute the command
#             cursor.execute(action.sql_command)
            
#             # If it's a SELECT, fetch data. If it's UPDATE/DELETE, commit it.
#             if action.action_type == "query":
#                 if action.sql_command.strip().upper().startswith("SELECT"):
#                     columns = [description[0] for description in cursor.description]
#                     results = [dict(zip(columns, row)) for row in cursor.fetchall()]
#             elif action.action_type == "commit":
#                 conn.commit()
#             elif action.action_type == "rollback":
#                 conn.rollback()

#             conn.close()
#         except Exception as e:
#             success = False
#             error = str(e)

#         # Calculate Reward (Basic logic: negative reward for errors)
#         reward = -0.1 if not success else 0.0
        
#         # Check if we hit the step limit
#         if self.state.step_count >= self.state.max_steps:
#             self.state.is_done = True

#         obs = Observation(
#             success=success,
#             result_set=results,
#             error_message=error,
#             current_checksum=self.get_checksum()
#         )
        
#         return obs, reward, self.state.is_done, {}

import sqlite3
import shutil
import os
from models import Action, Observation, State

class SentinelEnv:
    def __init__(self):
        self.template_path = "template.db"
        self.active_path = "active.db"
        self.state = State()

    def get_row_count(self):
        """Returns total records in accounts table."""
        try:
            conn = sqlite3.connect(self.active_path)
            count = conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
            conn.close()
            return count
        except:
            return 0

    def get_checksum(self):
        """Calculates total balance to ensure data integrity."""
        try:
            conn = sqlite3.connect(self.active_path)
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(balance) FROM accounts")
            total = cursor.fetchone()[0] or 0.0
            conn.close()
            return total
        except:
            return 0.0

    def reset(self) -> Observation:
        """Starts a fresh session by copying the Ground Truth database."""
        if os.path.exists(self.active_path):
            os.remove(self.active_path)
        
        shutil.copy(self.template_path, self.active_path)
        self.state = State()
        
        # We call the helpers directly inside the return
        return Observation(
            success=True,
            result_set=[{"message": "Environment reset. Ready for tasks."}],
            error_message=None,
            current_checksum=self.get_checksum(),
            unprocessed_chaos_events=0,
            row_count=self.get_row_count()
        )

    def step(self, action: Action) -> tuple[Observation, float, bool, dict]:
        """Executes the agent's SQL command and returns the outcome."""
        self.state.step_count += 1
        error = None
        results = None
        success = True

        try:
            conn = sqlite3.connect(self.active_path)
            conn.execute("PRAGMA journal_mode=WAL;")
            cursor = conn.cursor()

            cursor.execute(action.sql_command)

            command_upper = action.sql_command.strip().upper()
            
            if action.action_type == "query":
                if command_upper.startswith("SELECT"):
                    columns = [description[0] for description in cursor.description]
                    results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                # Automatically commit for UPDATE/INSERT/DELETE if type is query
                else:
                    conn.commit()
            elif action.action_type == "commit":
                conn.commit()
            elif action.action_type == "rollback":
                conn.rollback()

            conn.close()
        except Exception as e:
            success = False
            error = str(e)

        reward = -0.1 if not success else 0.0
        
        if self.state.step_count >= self.state.max_steps:
            self.state.is_done = True

        # Ensure all fields from models.py Observation are here
        obs = Observation(
            success=success,
            result_set=results,
            error_message=error,
            current_checksum=self.get_checksum(),
            unprocessed_chaos_events=0,
            row_count=self.get_row_count()
        )
        
        return obs, reward, self.state.is_done, {}