import os
import sys
import asyncio
import textwrap
from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import FastAPI
from openai import OpenAI
from env import SentinelEnv
from models import Action
from dotenv import load_dotenv

load_dotenv()

# --- 1. CONFIG ---
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY") or os.getenv("OPENAI_API_KEY")
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.groq.com/openai/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")
TASK_NAME = os.getenv("SENTINEL_TASK", "audit_easy")
BENCHMARK = "sentinel-db-v1"

# --- 2. LOGGING (The Validator's Requirements) ---
def log_start():
    print(f"[START] task={TASK_NAME} env={BENCHMARK} model={MODEL_NAME}", flush=True)

def log_step(step: int, query: str, reward: float, done: bool):
    q_clean = query.replace("\n", " ").strip()
    print(f"[STEP] step={step} action={q_clean} reward={reward:.2f} done={str(done).lower()}", flush=True)

def log_end(success: bool, steps: int, score: float, rewards: List[float]):
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.2f} rewards={rewards_str}", flush=True)
    # Redundant end tag for stricter parsers
    print(f"[END] task={TASK_NAME} score={score:.2f} steps={steps}", flush=True)

# --- 3. THE AGENT ---
async def run_autonomous_agent(env_instance):
    print("--- Background Agent: Starting Audit ---", flush=True)
    if not API_KEY:
        print("[ERROR] No API Key. Server staying up for validator.", flush=True)
        return

    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    history_rewards = []
    
    try:
        log_start()
        obs = env_instance.reset(task_id=TASK_NAME)
        
        for step in range(1, 11):
            # Brain logic
            prompt = "You are a Database Auditor. Output ONE raw SQL statement to fix negatives/duplicates."
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "system", "content": prompt}, {"role": "user", "content": f"State: {obs}"}],
                temperature=0.1, max_tokens=150
            )
            query = (completion.choices[0].message.content or "SELECT 1;").strip()
            
            # Action
            obs, reward, done, info = env_instance.step(Action(query=query))
            history_rewards.append(reward)
            
            # THE LOGGING THE VALIDATOR WANTS
            log_step(step, query, reward, done)
            
            if done: break
            await asyncio.sleep(1)

        final_score = history_rewards[-1] if history_rewards else 0.0
        log_end(success=(final_score >= 0.90), steps=len(history_rewards), score=final_score, rewards=history_rewards)
        
    except Exception as e:
        print(f"[AGENT ERROR] {e}", flush=True)

# --- 4. LIFESPAN & SERVER ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    agent_task = asyncio.create_task(run_autonomous_agent(env))
    yield
    agent_task.cancel()

app = FastAPI(lifespan=lifespan)
env = SentinelEnv(task_id=TASK_NAME)

@app.post("/reset")
async def reset_endpoint(task: dict = None):
    return {"observation": env.reset(task_id=TASK_NAME)}

@app.post("/step")
async def step_endpoint(action: Action):
    observation, reward, done, info = env.step(action)
    return {"observation": observation, "reward": reward, "done": done, "info": info}

@app.get("/grade/{task_id}")
def grade_endpoint(task_id: str):
    reward = env._calculate_reward()
    return {"score": reward, "reward": reward}

@app.get("/")
def health():
    return {"status": "running"}

def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()