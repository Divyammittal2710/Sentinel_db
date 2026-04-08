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

# --- 2. THE AGENT (Hardened & Tagged) ---
async def run_autonomous_agent(env_instance):
    """Provides the [START]/[STEP]/[END] logs for the validator's parser."""
    print("--- Sentinel Agent: Booting Background Task ---", flush=True)
    if not API_KEY:
        print("[CRITICAL] API Key missing. Server idling for evaluation.", flush=True)
        return

    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    history_rewards = []
    
    try:
        # Strict [START] tag
        print(f"[START] task={TASK_NAME} model={MODEL_NAME}", flush=True)
        obs = env_instance.reset(task_id=TASK_NAME)
        
        for step in range(1, 11):
            # Precision Prompting to avoid "hallucinated" table names
            prompt = textwrap.dedent("""
                You are a Database Auditor. Output ONE raw SQL statement.
                Goal: Fix negative balances and remove duplicates in 'accounts'.
                Rule: No prose, no markdown, just SQL.
            """).strip()
            
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "system", "content": prompt}, {"role": "user", "content": f"State: {obs}"}],
                temperature=0.1, max_tokens=100
            )
            query = (completion.choices[0].message.content or "SELECT 1;").strip()
            # Clean Markdown if the LLM ignores the rule
            query = query.replace("```sql", "").replace("```", "").strip()
            
            # Step the environment
            obs, reward, done, info = env_instance.step(Action(query=query))
            history_rewards.append(reward)
            
            # Strict [STEP] tag
            print(f"[STEP] step={step} action={query[:60]} reward={reward:.2f} done={str(done).lower()}", flush=True)
            
            if done: break
            await asyncio.sleep(1)

        final_score = history_rewards[-1] if history_rewards else 0.0
        # Strict [END] tag
        print(f"[END] success={str(final_score >= 0.90).lower()} steps={len(history_rewards)} score={final_score:.2f}", flush=True)
        
    except Exception as e:
        print(f"[AGENT ERROR] {e}", flush=True)

# --- 3. LIFESPAN MANAGER ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the agent background task automatically
    task = asyncio.create_task(run_autonomous_agent(env))
    yield
    task.cancel()

app = FastAPI(lifespan=lifespan)
env = SentinelEnv(task_id=TASK_NAME)

# --- 4. ENDPOINTS ---
@app.post("/reset")
async def reset_endpoint(task: dict = None):
    return {"observation": env.reset(task_id=TASK_NAME)}

@app.post("/step")
async def step_endpoint(action: Action):
    observation, reward, done, info = env.step(action)
    return {"observation": observation, "reward": reward, "done": done, "info": info}

@app.get("/")
async def health():
    return {"status": "running"}

# --- 5. THE ENTRY POINT ---
def main():
    import uvicorn
    # Single point of truth for the server
    uvicorn.run(app, host="0.0.0.0", port=7860, log_level="info")

if __name__ == "__main__":
    main()