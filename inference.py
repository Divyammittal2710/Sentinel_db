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

# Use the environment variable or default to audit_easy
TASK_NAME = os.getenv("SENTINEL_TASK", "audit_easy")
BENCHMARK = "sentinel-db-v1"
MAX_STEPS = 10
TEMPERATURE = 0.1
MAX_TOKENS = 150

# --- 2. INITIALIZATION ---
app = FastAPI()
# Initialize the global environment
env = SentinelEnv(task_id=TASK_NAME)
client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

# --- 3. LOGGING FUNCTIONS ---
def log_start(task: str, env_name: str, model: str):
    print(f"[START] task={task} env={env_name} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]):
    error_val = error if error else "null"
    action_clean = action.replace("\n", " ").strip()
    print(f"[STEP] step={step} action={action_clean} reward={reward:.2f} done={str(done).lower()} error={error_val}", flush=True)

def log_end(success: bool, steps: int, score: float, rewards: List[float]):
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.2f} rewards={rewards_str}", flush=True)

# --- 4. AGENT LOGIC (The "Brain") ---
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

async def run_autonomous_agent():
    """The background task that performs the audit autonomously"""
    history_rewards = []
    steps_taken = 0
    success = False
    final_score = 0.0

    log_start(task=TASK_NAME, env_name=BENCHMARK, model=MODEL_NAME)
    try:
        # Initial reset for the autonomous run
        obs = env.reset(task_id=TASK_NAME)
        for step in range(1, MAX_STEPS + 1):
            sql_query = get_model_query(str(obs))
            obs, reward, done, info = env.step(Action(query=sql_query))
            
            history_rewards.append(reward)
            steps_taken = step
            log_step(step=step, action=sql_query, reward=reward, done=done, error=info.get("error"))
            
            if done:
                break
        
        final_score = history_rewards[-1] if history_rewards else 0.0
        success = final_score >= 0.95
    except Exception as e:
        print(f"[AGENT ERROR] {e}", flush=True)
    finally:
        log_end(success=success, steps=steps_taken, score=final_score, rewards=history_rewards)

# --- 5. COMPLIANCE ENDPOINTS (Phase 1 Fix) ---

@app.on_event("startup")
async def startup_event():
    """Starts the autonomous agent in the background when the Space starts"""
    print("--- SERVER STARTING: Launching Autonomous Agent ---", flush=True)
    asyncio.create_task(run_autonomous_agent())

@app.post("/reset")
async def reset_endpoint():
    """Mandatory for Phase 1 Handshake"""
    print(f"--- RESET CALLED by Validator ---", flush=True)
    observation = env.reset(task_id=TASK_NAME)
    return {"observation": observation}

@app.post("/step")
async def step_endpoint(action: Action):
    """Mandatory for Phase 1 Handshake"""
    observation, reward, done, info = env.step(action)
    return {
        "observation": observation,
        "reward": reward,
        "done": done,
        "info": info
    }

@app.get("/grade/{task_id}")
def grade_endpoint(task_id: str):
    """The Score Endpoint requested by the Meta Devs"""
    try:
        # Calculate current reward without resetting the DB
        reward = env._calculate_reward()
        score = max(0.01, min(0.99, reward))
        return {"score": score, "reward": score}
    except Exception as e:
        return {"score": 0.01, "reward": 0.01}

@app.get("/state")
def state_endpoint():
    return {"state": env.state()}

@app.get("/")
def health_check():
    return {"status": "running", "task": TASK_NAME}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)