import sys
import json
from pathlib import Path


DEFAULT_CONFIG = {
    "options": {},
    "llama-server": {"options": {}},
    "logging": {
        "enabled": True,
        "level": "INFO",
        "file": None
    }
}

def load_config() -> dict:
    """
    Load configuration from config.json or return DEFAULT_CONFIG.
    """
    config_path = Path.cwd() / "config.json"
    if not config_path.exists():
        with open(config_path, "w") as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            print("Warning: Could not parse config.json, using default configuration.", file=sys.stderr)
    return DEFAULT_CONFIG
