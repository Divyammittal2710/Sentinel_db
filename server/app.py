import sys
import os
import asyncio
from fastapi import FastAPI
from pydantic import BaseModel

# Put root in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from env import SentinelEnv
from models import Action, Observation

app = FastAPI()
env = SentinelEnv()

@app.post("/reset")
async def reset(task: dict = None):
    # Flexible task handling to prevent Phase 1 errors
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