"""
main.py — Main entry point for llama-server-manager.

This is the central CLI tool that orchestrates all operations:
- Self-update
- Installing/updating llama.cpp
- Stopping a running server
- Running llama-server with configured options
"""

import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path.cwd()))

from llama_wrapper.main import Main

if __name__ == "__main__":
    app = Main()
    app.run()
