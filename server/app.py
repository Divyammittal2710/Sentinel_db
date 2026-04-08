import sys
import os
import uvicorn
from openenv.core.env_server import create_fastapi_app

<<<<<<< HEAD
# Ensure root is in sys.path
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_path not in sys.path:
    sys.path.insert(0, root_path)
=======
# Put root in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
>>>>>>> 2da2d79add4e0c58f565339351f2fd6e49ac4235

from env import SentinelEnv
from models import Action, Observation

<<<<<<< HEAD
app = create_fastapi_app(SentinelEnv, Action, Observation)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
=======
# The SDK expects the class, and the Pydantic models for Action and Observation
app = create_fastapi_app(SentinelEnv, Action, Observation)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860) 
>>>>>>> 2da2d79add4e0c58f565339351f2fd6e49ac4235
