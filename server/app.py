import sys
import os
import uvicorn
from openenv.core.env_server import create_fastapi_app

# Put root in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from env import SentinelEnv
from models import Action, Observation

# The SDK expects the class, and the Pydantic models for Action and Observation
app = create_fastapi_app(SentinelEnv, Action, Observation)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860) 