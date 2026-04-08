import sys
import os
import uvicorn
from openenv.core.env_server import create_fastapi_app

# Ensure root is in sys.path
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from env import SentinelEnv
from models import Action, Observation

app = create_fastapi_app(SentinelEnv, Action, Observation)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)