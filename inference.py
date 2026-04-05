from dotenv import load_dotenv
load_dotenv()

import asyncio
import os
import textwrap
from typing import List, Optional
from openai import OpenAI
from env import SentinelEnv
from models import Action

# 1. Environment Configuration (Mandatory for the Grader)
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY") or os.getenv("OPENAI_API_KEY")
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.groq.com/openai/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")
TASK_NAME = os.getenv("SENTINEL_TASK", "audit_hard")
BENCHMARK = "sentinel-db-v1"

# 2. Hyperparameters
MAX_STEPS = 10
TEMPERATURE = 0.1  # Low temperature for precise SQL generation
MAX_TOKENS = 150

# 3. Mandatory Logging Functions
def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    # Ensure action string has no newlines to keep log on one line
    action_clean = action.replace("\n", " ").strip()
    print(f"[STEP] step={step} action={action_clean} reward={reward:.2f} done={done_val} error={error_val}", flush=True)

def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.2f} rewards={rewards_str}", flush=True)

# 4. LLM Interaction Logic
def get_model_query(client: OpenAI, observation: str) -> str:
    system_prompt = textwrap.dedent("""
    [STRICT ROLE]
    You are a Database Auditor. You ONLY output one raw SQL statement.
    You will be given an observation. If 'current_checksum' is not perfect or duplicates exist, you MUST continue fixing.

    [DATABASE SCHEMA]
    - Table: 'accounts'
    - Columns: id (INT), name (TEXT), balance (REAL), status (TEXT)

    [MISSION PRIORITY]
    1. Fix Negatives: UPDATE accounts SET balance = 0 WHERE balance < 0;
    2. Fix Duplicates: DELETE FROM accounts WHERE rowid NOT IN (SELECT MIN(rowid) FROM accounts GROUP BY id);
    3. Fix Status: UPDATE accounts SET status = 'ACTIVE' WHERE status != 'ACTIVE';

    [TERMINATION RULE]
    - If and ONLY if there are 0 negative balances, 0 duplicates, and all statuses are 'ACTIVE', output: SELECT 1;
    - Never repeat 'SELECT 1;' if the reward you receive is less than 1.0.
    """).strip()

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Database State: {observation}"},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )
        return (completion.choices[0].message.content or "SELECT 1;").strip()
    except Exception as exc:
        return f"-- Error: {str(exc)}"

# 5. Main Execution Loop
async def main() -> None:
    # Initialize OpenAI Client (Pointed to Groq or Meta Endpoint)
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    
    # Initialize Environment
    env = SentinelEnv(task_id=TASK_NAME)
    
    history_rewards: List[float] = []
    steps_taken = 0
    success = False
    final_score = 0.0

    log_start(task=TASK_NAME, env=BENCHMARK, model=MODEL_NAME)

    try:
        # Reset Environment to get initial observation
        obs = env.reset()
        
        for step in range(1, MAX_STEPS + 1):
            # Get Action from LLM
            sql_query = get_model_query(client, str(obs))
            
            # Execute Action in Environment
            obs, reward, done, info = env.step(Action(query=sql_query))
            
            # Tracking
            history_rewards.append(reward)
            steps_taken = step
            error = info.get("error")

            # Mandatory STEP Log
            log_step(step=step, action=sql_query, reward=reward, done=done, error=error)

            if done:
                break

        # Final Evaluation
        final_score = history_rewards[-1] if history_rewards else 0.0
        success = final_score >= 0.95  # Success if integrity is restored

    except Exception as global_exc:
        print(f"[DEBUG] Execution Error: {global_exc}")
    finally:
        # Cleanup
        env.close()
        # Mandatory END Log
        log_end(success=success, steps=steps_taken, score=final_score, rewards=history_rewards)

if __name__ == "__main__":
    asyncio.run(main())