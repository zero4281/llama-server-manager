"""
runner.py — Process execution and management for llama-server.

This module handles launching llama-server, managing its lifecycle,
and implementing graceful shutdown with proper signal handling.
"""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional


# Paths
PID_FILE = Path.cwd() / "llama-server.pid"


class Runner:
    """Manages the execution of llama-server process."""

    def __init__(self, args, config: dict):
        """
        Initialize Runner.

        Args:
            args: Parsed command-line arguments
            config: Configuration from config.json
        """
        self.args = args
        self.config = config
        self.pid_file = PID_FILE
        self.llama_server_path = Path.cwd() / "llama-cpp" / "llama-server"
        self.force_killed = False

    def run(self) -> None:
        """Main run method - launches llama-server."""
        # Load configuration options
        config_args = self._load_config_options()
        
        # Merge args and config options
        merged_args = self._merge_args(config_args)
        
        # Build command
        command = self._build_command(merged_args)
        
        self._run_background(command, merged_args)

    def _load_config_options(self) -> list:
        """
        Load options from config.json\'s llama-server.options section.

        Returns:
            List of command-line arguments
        """
        options = self.config.get("llama-server", {}).get("options", {})
        args = []
        for key, value in options.items():
            if value is not None and value != "":
                args.extend([f"--{key}", f"{value}"])
            else:
                args.append(f"--{key}")
        return args

    def _merge_args(self, config_args: list) -> list:
        """
        Merge configuration args with CLI args.

        CLI args take precedence over config args. This is a simple
        concatenation since argparse already handles duplicate handling.

        Args:
            config_args: Arguments from config.json

        Returns:
            Merged list of arguments
        """
        # Get pass-through args from main
        llama_args = getattr(self.args, 'llama_args', [])
        return config_args + llama_args

    def _build_command(self, merged_args: list) -> list:
        """
        Build the command to run llama-server.

        Args:
            merged_args: Merged arguments from config and CLI

        Returns:
            List of command arguments
        """
        cmd = [str(self.llama_server_path)]
        
        # Add merged args
        cmd.extend(merged_args)
        
        return cmd

    def _run_background(self, command: list, merged_args: list) -> None:
        """
        Run llama-server in the background as a daemon.

        Args:
            command: Command to execute
            merged_args: Merged arguments (kept for consistency with signature)
        """
        try:
            # Start process (no output capturing - llama-server writes to its own log)
            process = subprocess.Popen(command)

            # Write PID to file
            pid = process.pid
            with open(self.pid_file, "w") as f:
                f.write(str(pid))

            print(f"llama-server started with PID {pid}")
            print(f"PID file: {self.pid_file}")

        except Exception as e:
            self._cleanup()
            raise e

    def _cleanup(self) -> None:
        """Clean up resources."""  
        if self.pid_file.exists():
            try:
                self.pid_file.unlink()
            except OSError:
                pass


def stop_server() -> int:
    """
    Stop a running llama-server process.

    Returns:
        0 if clean shutdown, non-zero if force-killed
    """
    try:
        # Read PID file
        with open(PID_FILE, "r") as f:
            pid = int(f.read().strip())
    except (FileNotFoundError, ValueError):
        print("No running llama-server found (no PID file).")
        return 1

    force_killed = False

    try:
        # Send SIGTERM first
        os.kill(pid, signal.SIGTERM)
        
        # Wait up to 60 seconds for process to exit
        for i in range(60):
            try:
                # Check if process exists (raises OSError if not)
                os.kill(pid, 0)
            except OSError:
                # Process has exited
                return 0
            time.sleep(1)
    except OSError as e:
        if e.errno == signal.SIGKILL:
            print("Process died while waiting...")
            return 0
        raise

    # Process didn't exit after 60 seconds, force kill
    print("Process did not exit cleanly, forcing termination...")
    
    if sys.platform == 'win32':
        import ctypes
        import ctypes.wintypes
        kernel32 = ctypes.windll.kernel32
        kernel32.TerminateProcess(ctypes.c_int(pid), 1)
    else:
        os.kill(pid, signal.SIGKILL)
    
    force_killed = True

    # Remove PID file
    if PID_FILE.exists():
        PID_FILE.unlink()

    if force_killed:
        print("llama-server force-terminated")
        return 1
    else:
        print("llama-server stopped")
        return 0

