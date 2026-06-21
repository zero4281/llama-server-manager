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

    def __init__(self, args, config: dict, ui_manager: Optional["UIManager"] = None):
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
        self.ui_manager = ui_manager


    def _load_config_options(self) -> list:
        """
        Load configuration options from the llama-server section of the config.

        Returns:
            A list of command-line arguments for llama-server.
        """
        config_args = []
        options = self.config.get("llama-server", {}).get("options", {})

        for key, value in options.items():
            if value is None:
                if not key.startswith("-"):
                    config_args.append(f"--{key}")
                else:
                    config_args.append(key)
            elif isinstance(value, bool):
                if value:
                    if not key.startswith("-"):
                        config_args.append(f"--{key}")
                    else:
                        config_args.append(key)
            else:
                if not key.startswith("-"):
                    config_args.append(f"--{key}")
                config_args.append(str(value))

        return config_args
    def run(self) -> None:
        """Main run method - launches llama-server."""
        # Load configuration options
        config_args = self._load_config_options()
        
        # Merge args and config options
        llama_args = getattr(self.args, 'llama_args', [])
        merged_args = config_args + llama_args
        
        # Build command
        command = self._build_command(merged_args)
        
        self._run_background(command, merged_args)

    def _build_command(self, args: list) -> list:
        """
        Build the command line arguments for llama-server.

        Args:
            args: Merged command-line arguments.

        Returns:
            List of command-line arguments including the path to the executable.
        """
        return [str(self.llama_server_path)] + args




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

            if self.ui_manager is not None:
                self.ui_manager.print_message(f"llama-server started with PID {pid}")
                self.ui_manager.print_message(f"PID file: {self.pid_file}")
            else:
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


def stop_server(ui_manager: Optional["UIManager"] = None) -> int:
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
        ui_manager.print_message("No running llama-server found (no PID file).")
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
            ui_manager.print_message("Process died while waiting...")
            return 0
        raise

    # Process didn't exit after 60 seconds, force kill
    ui_manager.print_message("Process did not exit cleanly, forcing termination...")
    
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
        ui_manager.print_message("llama-server force-terminated")
        return 1
    else:
        ui_manager.print_message("llama-server stopped")
        return 0

