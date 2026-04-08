import os
import sys
import asyncio
import textwrap
from typing import List, Optional
from fastapi import FastAPI, BackgroundTasks
from openai import OpenAI
from env import SentinelEnv
from models import Action
from dotenv import load_dotenv

load_dotenv()

# --- 1. CONFIGURATION ---
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY") or os.getenv("OPENAI_API_KEY")
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.groq.com/openai/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")

if len(sys.argv) > 1 and not sys.argv[1].startswith('-'):
    TASK_NAME = sys.argv[1]
else:
    TASK_NAME = os.getenv("SENTINEL_TASK", "audit_easy")

BENCHMARK = "sentinel-db-v1"
MAX_STEPS = 10
TEMPERATURE = 0.1
MAX_TOKENS = 150

# Initialize Global App and Env
app = FastAPI()
env = SentinelEnv(task_id=TASK_NAME)
client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

# --- 2. LOGGING ---
def log_start(task: str, env: str, model: str):
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]):
    error_val = error if error else "null"
    action_clean = action.replace("\n", " ").strip()
    print(f"[STEP] step={step} action={action_clean} reward={reward:.2f} done={str(done).lower()} error={error_val}", flush=True)

def log_end(success: bool, steps: int, score: float, rewards: List[float]):
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.2f} rewards={rewards_str}", flush=True)

# --- 3. AGENT LOGIC ---
def get_model_query(observation: str) -> str:
    system_prompt = textwrap.dedent("""
        [STRICT ROLE]
        You are a Database Auditor. You ONLY output one raw SQL statement.
        [REQUIRED ACTION SEQUENCE]
        1. FIX NEGATIVES: UPDATE accounts SET balance = 0 WHERE balance < 0;
        2. FIX DUPLICATES: DELETE FROM accounts WHERE rowid NOT IN (SELECT MIN(rowid) FROM accounts GROUP BY id);
        3. FIX STATUS: UPDATE accounts SET status = 'ACTIVE' WHERE status != 'ACTIVE';
        4. IF ALL ISSUES ARE FIXED: SELECT 1;
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

async def run_agent():
    """The background task that performs the 97-minute audit"""
    history_rewards = []
    steps_taken = 0
    success = False
    final_score = 0.0

    log_start(task=TASK_NAME, env=BENCHMARK, model=MODEL_NAME)
    try:
        obs = env.reset()
        for step in range(1, MAX_STEPS + 1):
            sql_query = get_model_query(str(obs))
            obs, reward, done, info = env.step(Action(query=sql_query))
            history_rewards.append(reward)
            steps_taken = step
            log_step(step=step, action=sql_query, reward=reward, done=done, error=info.get("error"))
            if done: break
        
        final_score = history_rewards[-1] if history_rewards else 0.0
        success = final_score >= 0.95
    finally:
        log_end(success=success, steps=steps_taken, score=final_score, rewards=history_rewards)

# --- 4. API ENDPOINTS ---

@app.on_event("startup")
async def startup_event():
    """Starts the agent as soon as the Space is live"""
    asyncio.create_task(run_agent())

@app.get("/")
def health_check():
    return {"status": "running", "task": TASK_NAME}

@app.get("/grade/{task_id}")
def grade_task(task_id: str):
    """
    THIS IS THE CRITICAL FIX. 
    Returns the reward of the current database state to the validator.
    """
    try:
        # Get reward from current state (DO NOT call reset())
        reward = env._calculate_reward()
        # Scale score between 0.01 and 0.99
        score = max(0.01, min(0.99, reward))
        return {"score": score, "reward": score}
    except Exception as e:
        print(f"Grader Error: {e}", flush=True)
        return {"score": 0.01, "reward": 0.01}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)