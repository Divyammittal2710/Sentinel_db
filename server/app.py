import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from inference import app, main as root_main
def main():
    """Explicit main function required by the validator"""
    root_main()

if __name__ == "__main__":
    main()