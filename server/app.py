import sys
import os

# Adds the root directory to the path so it can find inference.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from inference import app, main

if __name__ == "__main__":
    main()