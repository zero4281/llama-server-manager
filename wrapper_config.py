"""
logging.py — Configurable logging utility for llama-server-manager.

This module provides logging functionality that respects the configuration
from config.json, supporting file output, stdout, and log level filtering.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional


class ConfigLogger:
    """Logger that respects config.json settings."""

    def __init__(self, config: dict, log_level: str = "INFO"):
        """
        Initialize logger with config.

        Args:
            config: Configuration dictionary from config.json
            log_level: Log level string (DEBUG, INFO, WARNING, ERROR)
        """
        self.logger = logging.getLogger("llama_wrapper")
        self.logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()

        # Configure console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)

        # Optional file handler if configured
        log_file = config.get("logging", {}).get("file")
        if log_file:
            file_handler = logging.FileHandler(log_file, mode="a")
            file_handler.setLevel(logging.DEBUG)
            file_format = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            file_handler.setFormatter(file_format)
            self.logger.addHandler(file_handler)

    def debug(self, message: str) -> None:
        """Log debug message if DEBUG level enabled."""
        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug(message)

    def info(self, message: str) -> None:
        """Log info message."""
        self.logger.info(message)

    def warning(self, message: str) -> None:
        """Log warning message."""
        self.logger.warning(message)

    def error(self, message: str) -> None:
        """Log error message."""
        self.logger.error(message)

    def critical(self, message: str) -> None:
        """Log critical message."""
        self.logger.critical(message)


# Default configuration
DEFAULT_CONFIG = {
    "options": {
        "logfile": "./llama-server-manager.log"
    },
    "llama-server": {
        "options": {
            "host": "0.0.0.0",
            "port": "11235",
            "models-max": "1",
            "log-file": "llama-server.log"
        }
    },
    "logging": {
        "enabled": True,
        "level": "INFO",
        "file": None
    }
}

def load_config(config_path: Optional[Path] = None) -> dict:
    """
    Load configuration from config.json, auto-generating if missing.

    Args:
        config_path: Path to config.json (defaults to current directory)

    Returns:
        Configuration dictionary
    """
    if config_path is None:
        config_path = Path.cwd() / "config.json"

    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Auto-generate default config
        default = DEFAULT_CONFIG.copy()
        default["logging"] = DEFAULT_CONFIG["logging"].copy()
        
        # Write default config
        with open(config_path, "w") as f:
            json.dump(default, f, indent=2)
        
        return default


def get_logger(config: dict, log_level: str = "INFO") -> ConfigLogger:
    """
    Get a ConfigLogger instance from config.

    Args:
        config: Configuration dictionary
        log_level: Log level string

    Returns:
        ConfigLogger instance
    """
    return ConfigLogger(config, log_level)
