"""
Sentinel DB — FastAPI HTTP Server
===================================
Exposes the OpenEnv-compliant API:
  POST /reset   → reset the environment for a task
  POST /step    → execute one agent action
  GET  /state   → return current environment state
  GET  /        → health check
"""

import sys
import os

# Make root-level modules importable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from env import SentinelEnv
from models import Action, Observation

app = FastAPI(title="Sentinel DB", version="1.0.0")
env = SentinelEnv()


class ResetRequest(BaseModel):
    task_id: Optional[str] = "audit_easy"


# ── ENDPOINTS ─────────────────────────────────────────────────────────────────

@app.get("/", summary="Health check")
async def health():
    return {"status": "running", "env": "sentinel_db"}


@app.post("/reset", response_model=Observation)
async def reset_endpoint(request: ResetRequest = None):
    task_id = (request.task_id if request else None) or "audit_easy"
    obs = env.reset(task_id=task_id)
    return obs


@app.post("/step")
async def step_endpoint(action: Action):
    try:
        observation, reward, done, info = env.step(action)
        return {
            "observation": observation.dict(),
            "reward": reward,
            "done": done,
            "info": info,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/state", response_model=Observation)
async def state_endpoint():
    return env.state()


# ── ENTRY POINT ───────────────────────────────────────────────────────────────

def main():
    import uvicorn
    port = int(os.getenv("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    main()