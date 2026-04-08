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

# --- 2. THE BRAIN ---
async def run_autonomous_agent(env_instance):
    """Hardened background loop that won't crash the server"""
    print("--- Sentinel Agent: Background Task Started ---", flush=True)
    if not API_KEY:
        print("[WARNING] No API Key found. Agent idling, but server stays UP.", flush=True)
        return

    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    try:
        # Initial reset
        obs = env_instance.reset(task_id=TASK_NAME)
        for step in range(1, 11):
            # Agent logic
            system_prompt = "You are a Database Auditor. Output ONE raw SQL statement to fix issues."
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": f"State: {obs}"}],
                temperature=0.1, max_tokens=150
            )
            query = (completion.choices[0].message.content or "SELECT 1;").strip()
            
            # Step the environment
            obs, reward, done, info = env_instance.step(Action(query=query))
            print(f"[AGENT] Step {step} | Reward: {reward:.2f}", flush=True)
            
            if done: break
            await asyncio.sleep(2) # Don't spam the API
    except Exception as e:
        print(f"[AGENT ERROR] Handled gracefully: {e}", flush=True)

# --- 3. LIFESPAN (The fix for the Deprecation Warning) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic: Launch background agent
    agent_task = asyncio.create_task(run_autonomous_agent(env))
    yield
    # Shutdown logic
    agent_task.cancel()

app = FastAPI(lifespan=lifespan)
env = SentinelEnv(task_id=TASK_NAME)

# --- 4. ENDPOINTS ---

@app.post("/reset")
async def reset_endpoint(task: dict = None):
    t_id = task.get("task_id", TASK_NAME) if task else TASK_NAME
    return {"observation": env.reset(task_id=t_id)}

@app.post("/step")
async def step_endpoint(action: Action):
    observation, reward, done, info = env.step(action)
    return {"observation": observation, "reward": reward, "done": done, "info": info}

@app.get("/grade/{task_id}")
def grade_endpoint(task_id: str):
    reward = env._calculate_reward()
    score = max(0.01, min(0.99, reward))
    return {"score": score, "reward": score}

@app.get("/")
def health():
    return {"status": "running", "agent": "active"}

# --- 5. COMPLIANCE ENTRY POINT ---
def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
