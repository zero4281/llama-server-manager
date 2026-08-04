import argparse
import json
from pathlib import Path
from runner import Runner
from ui_manager import UIManager

# Mock args
parser = argparse.ArgumentParser()
parser.add_argument("--host", default="0.0.0.0")
parser.add_argument("--port", default="11235")
parser.add_argument("--models-max", default="1")
parser.add_argument("--log-file", default="llama-server.log")
args = parser.parse_args([])

# Load config
with open("config.json", "r") as f:
    config = json.load(f)

# UI
ui = UIManager("Start Server")

# Runner
runner = Runner(args, config, ui)
runner.run()
