import sys
import os
import uvicorn
from openenv.core.env_server import create_fastapi_app

# This allows the server to find your env.py and models.py in the root folder
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from env import SentinelEnv
from models import Action, Observation

# The SDK handles all Phase 1 endpoints (/reset, /step, /state) automatically
app = create_fastapi_app(SentinelEnv, Action, Observation)

def main():
    uvicorn.run(
        "server.app:app", 
        host="0.0.0.0", 
        port=int(os.getenv("PORT", "7860")), 
        reload=False
    )

if __name__ == "__main__":
    main()