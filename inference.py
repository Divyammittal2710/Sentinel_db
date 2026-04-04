import os
import json
from dotenv import load_dotenv
from groq import Groq
from models import Observation, Action

# 1. Load the API Key from your .env file
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("❌ GROQ_API_KEY not found in .env file!")

# 2. Initialize the Groq Client
client = Groq(api_key=api_key)

class SentinelAgent:
    def __init__(self, model_name="llama-3.3-70b-versatile"):
        self.model_name = model_name
        # The System Prompt defines the AI's "personality" and rules
        self.system_prompt = """
        You are the Sentinel-DB Autonomous Auditor. Your goal is to maintain financial integrity.
        
        RULES:
        1. You only output valid SQL commands for SQLite.
        2. You must fix: Negative balances, Duplicate IDs, and Invalid Statuses.
        3. Table name is 'accounts'. Columns are: 'id', 'name', 'balance', 'status'.
        4. For 'Audit' tasks, start by querying the database to find anomalies.
        5. Respond ONLY with a JSON object matching this structure:
           {"action_type": "query", "sql_command": "SELECT * FROM accounts WHERE balance < 0;"}
        """

    def get_action(self, observation: Observation) -> Action:
        """Processes the current database state and returns the next SQL action."""
        
        # We pass the 'Eyes' of the agent (Checksum, Rows, and previous Results)
        prompt = f"""
        --- CURRENT DATABASE STATE ---
        Total Rows: {observation.row_count}
        Current Checksum: {observation.current_checksum}
        Previous Query Results: {observation.result_set}
        Last Error: {observation.error_message}

        --- TASK ---
        Identify any anomalies (negative balances or duplicates) and fix them. 
        What is your next SQL move?
        """

        try:
            # Call Groq API with JSON Mode enabled
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                model=self.model_name,
                response_format={"type": "json_object"}
            )

            # 3. Parse the response
            raw_response = chat_completion.choices[0].message.content
            
            # This validates the LLM response against your Pydantic Action model
            return Action.model_validate_json(raw_response)

        except Exception as e:
            print(f"⚠️ Agent Brain Error: {e}")
            # Fallback action if the LLM fails to respond correctly
            return Action(action_type="query", sql_command="SELECT * FROM accounts LIMIT 5;")