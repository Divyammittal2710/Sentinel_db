import sys
import os
import uvicorn
from fastapi import FastAPI

# Ensure root is in path
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from env import SentinelEnv
from models import Action, Observation

app = FastAPI()
env = SentinelEnv()

@app.post("/reset")
async def reset(task: dict = None):
    task_id = "audit_easy"
    if task and "task_id" in task:
        task_id = task["task_id"]
    obs = env.reset(task_id=task_id)
    return {"observation": obs}

@app.post("/step")
async def step(action: Action):
    obs, reward, done, info = env.step(action)
    return {"observation": obs, "reward": reward, "done": done, "info": info}

@app.get("/grade/{task_id}")
async def grade(task_id: str):
    reward = env._calculate_reward()
    return {"score": reward, "reward": reward}

@app.get("/")
async def health():
    return {"status": "running"}

# --- THIS IS THE CRITICAL ADDITION FOR THE VALIDATOR ---
def main():
    """Platform entry point for multi-mode deployment"""
    uvicorn.run(app, host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()