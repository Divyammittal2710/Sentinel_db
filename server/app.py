import sys
import os
import uvicorn
from fastapi import FastAPI

# 1. Critical: This allows the server folder to see env.py and models.py in the root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now we can safely import your local modules
from env import SentinelEnv
from models import Action

# 2. Initialize FastAPI
app = FastAPI()

# 3. Environment Setup
TASK_ID = os.getenv("SENTINEL_TASK", "audit_hard")
env = SentinelEnv(task_id=TASK_ID)

@app.post("/reset")
async def reset():
    """Mandatory: Resets the environment and returns initial observation."""
    observation = env.reset()
    return {"observation": observation}

@app.post("/step")
async def step(action: Action):
    """Mandatory: Takes an action and returns the next state/reward."""
    observation, reward, done, info = env.step(action)
    return {
        "observation": observation,
        "reward": reward,
        "done": done,
        "info": info
    }

@app.get("/state")
async def state():
    """Optional but recommended for the OpenEnv validator."""
    return {"state": env.state()}

# 4. MANDATORY FOR VALIDATOR: The main entry point
def main():
    """This is what 'openenv validate' looks for in your pyproject.toml."""
    uvicorn.run(
        "app:app", 
        host="0.0.0.0", 
        port=7860, 
        reload=False
    )

if __name__ == "__main__":
    main()