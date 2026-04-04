import os
import json
import time
from dotenv import load_dotenv
from openai import OpenAI
from models import Observation, Action
from env import SentinelEnv

# 1. Mandatory Environment Configuration
load_dotenv()
API_BASE_URL = os.getenv("API_BASE_URL")
MODEL_NAME = os.getenv("MODEL_NAME")
HF_TOKEN = os.getenv("HF_TOKEN")

client = OpenAI(
    base_url=API_BASE_URL,
    api_key=HF_TOKEN
)

# Mandatory Task IDs from openenv.yaml
TASKS = ["audit_easy", "audit_medium", "audit_hard"]

def run_inference():
    # MANDATORY LOGGING: START
    print("[START]")
    
    env = SentinelEnv()

    for task_id in TASKS:
        try:
            # 2. Reset with specific task_id
            obs = env.reset(task_id=task_id)
            
            system_prompt = f"""
            You are the Sentinel-DB Auditor. Currently performing task: {task_id}.
            Table: 'accounts'. Columns: 'id', 'name', 'balance', 'status'.
            Goal: Fix negative balances and reconcile duplicate IDs.
            Respond ONLY in JSON format: {{"action_type": "query", "sql_command": "..."}}
            """

            done = False
            step_count = 0
            max_steps = 10 # 10 steps per task is plenty for Groq speed

            while not done and step_count < max_steps:
                step_count += 1
                
                prompt = (
                    f"Task: {task_id}\n"
                    f"Step: {step_count}\n"
                    f"Row Count: {obs.row_count}\n"
                    f"Checksum: {obs.current_checksum}\n"
                    f"Sample Data: {obs.result_set}\n"
                    f"Error: {obs.error_message}"
                )

                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"}
                )

                raw_content = response.choices[0].message.content
                action = Action.model_validate_json(raw_content)

                # Execute environment step
                obs, reward, done, info = env.step(action)

                # MANDATORY LOGGING: STEP
                # The task_id is included to show the grader which task is scoring
                print(f"[STEP] {task_id}_{step_count}: Action={action.action_type}, Reward={reward:.2f}, Done={done}")
                
                time.sleep(0.5)

        except Exception as e:
            print(f"Inference Error on {task_id}: {str(e)}")

    # MANDATORY LOGGING: END
    print("[END]")

if __name__ == "__main__":
    run_inference()