"""
main.py — Main entry point for llama-server-manager.

This is the central CLI tool that orchestrates all operations:
- Self-update
- Installing/updating llama.cpp
- Stopping a running server
- Running llama-server with configured options
"""

import argparse
import os
import shutil
import sys
import platform
import requests
import zipfile
import tempfile
from pathlib import Path

from wrapper_config import load_config, get_logger
from llama_updater import LlamaUpdater
from runner import stop_server, Runner
from ui_manager import UIManager



# Check if script is running from the project root
project_root = Path(__file__).parent.absolute()
if Path.cwd().resolve() != project_root:
    print(f"Warning: Script is not running from the project root ({project_root}). "
          "Please navigate to the project root before running the script.", file=sys.stderr)

class Main:
    """Main wrapper application."""

    def __init__(self):
        self.args = None
        self.config = None
        self.logger = None
        self.ui = UIManager("Llama Server Manager")

    def parse_args(self, args: list = None) -> argparse.Namespace:
        """
        Parse command-line arguments.

        Args:
            args: List of arguments (defaults to sys.argv[1:])

        Returns:
            Parsed arguments namespace
        """
        # WSL detection (per Requirements.md Section 5.1.1)
         
        parser = argparse.ArgumentParser(
            prog="llama-server-manager",
            description="Manager for llama.cpp server operations"
        )

        # Special operations
        parser.add_argument("--self-update", action="store_true",
            help="Pull latest code from GitHub and restart")
        parser.add_argument("--install-llama", action="store_true",
            help="Download and install latest llama.cpp release")
        parser.add_argument("--update-llama", action="store_true",
            help="Update existing llama.cpp to latest release")
        parser.add_argument("--stop-server", action="store_true",
            help="Gracefully stop a running llama-server")

        # Pass-through arguments for llama-server
        parser.add_argument("llama_args", nargs="*",
            help="Additional arguments passed to llama-server")

        return parser.parse_args(args)

    def load_config(self) -> dict:
        """
        Load or auto-generate configuration.

        Returns:
            Configuration dictionary
        """
        return load_config()

    def perform_self_update(self, args: argparse.Namespace) -> None:
        """
        Perform self-update from GitHub.

        Args:
            args: Parsed arguments
        """
        try:
            self.ui.print_message("Performing self-update...")

            # Source selection menu
            source_options = [
                {"label": "Latest release (recommended)", "description": "Most recent official release"},
                {"label": "Previous release", "description": "Select from available releases"},
                {"label": "Repository HEAD", "description": "Main branch latest commit"},
            ]

            default_source = 0
            selected_source = self.ui.render_menu(source_options, default=default_source)

            if selected_source == -1:
                self.ui.render_error("Update cancelled.")
                sys.exit(0)

            selected_zip_url = ""
            selected_tag = ""
            selected_name = ""

            if selected_source == 0:
                # Latest release
                url = "https://api.github.com/repos/zero4281/llama-server-manager/releases/latest"
                headers = {
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                }
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                release = response.json()
                selected_tag = release["tag_name"]
                selected_name = release["name"]
                selected_zip_url = release.get("zipball_url") or ""
            elif selected_source == 1:
                # Fetch previous releases
                url = "https://api.github.com/repos/zero4281/llama-server-manager/releases"
                headers = {
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                }
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                releases = response.json()

                # Show previous releases menu
                prev_releases = [
                    {"label": rel["tag_name"], "description": f"{rel['name']} ({rel['published_at']})"}
                    for rel in releases
                ]

                prev_choice = self.ui.render_menu(prev_releases)
                if prev_choice == -1:
                    self.ui.render_error("Update cancelled.")
                    sys.exit(0)

                selected_release = releases[prev_choice]
                selected_tag = selected_release["tag_name"]
                selected_name = selected_release["name"]
                selected_zip_url = selected_release.get("zipball_url") or ""
            else:
                # Repository HEAD
                selected_zip_url = "https://github.com/zero4281/llama-server-manager/archive/refs/heads/main.zip"
                selected_tag = "HEAD"
                selected_name = "main branch HEAD"
                selected_release = "HEAD"

            # Confirmation prompt
            confirm = self.ui.render_confirmation(
                self.ui,
                f"Update {selected_tag if selected_tag != 'HEAD' else selected_name}",
                selected_name
            )

            if not confirm:
                self.ui.render_error("Update cancelled.")
                sys.exit(0)

            # Download and extract directly to project root
            project_root = Path.cwd()

            # Download the zip file
            headers = {
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
            zip_response = requests.get(selected_zip_url, headers=headers, timeout=60)
            zip_response.raise_for_status()
            zip_content = zip_response.content

            # Write zip content to a temporary file and extract
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as zip_file:
                zip_file.write(zip_content)
                zip_file_path = Path(zip_file.name)

        
            with tempfile.TemporaryDirectory() as extract_temp:
                # Extract to a subdirectory
                extract_subdir = Path(extract_temp) / "extract"
                extract_subdir.mkdir()
                
                with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_subdir)
                
                # Find the top-level directory in the extracted files
                top_level_dir = None
                for item in extract_subdir.iterdir():
                    if item.is_dir() and not item.name.startswith(('.', '_')):
                        top_level_dir = item
                        break
                
                if top_level_dir:
                    # Move files from top-level directory to project root
                    for file_path in top_level_dir.rglob("*"):
                        if file_path.is_file():
                            rel_path = file_path.relative_to(top_level_dir)
                            target = project_root / rel_path
                            target.parent.mkdir(parents=True, exist_ok=True)
                            target.write_bytes(file_path.read_bytes())
                            # Clean up the old file
                            file_path.unlink()
                            self.ui.print_message(f"Updated: {rel_path}")
                    
                    # Remove the top-level directory from extract_subdir
                    shutil.rmtree(top_level_dir)
                    self.ui.print_message(f"Removed: {top_level_dir.name}")
                    
                    self.ui.render_success("Self-update complete!")
        except Exception as e:
            self.ui.render_error(f"Self-update failed: {e}")
            sys.exit(2)
        finally:
            # Clean up temporary zip file
            if zip_file_path.exists():
                zip_file_path.unlink()
            
            # Restart with same arguments
            self.ui.print_message(f"Restarting with original arguments: {args}")
            
            # Re-parse args to preserve llama_args
            new_args = [sys.argv[0]]
            for arg in sys.argv[1:]:
                if arg != "--self-update":
                    new_args.append(arg)
            
            # Execute and replace current process
            os.execvp(sys.executable, new_args)

    def run(self) -> None:
        """Main execution flow."""
        if platform.system() == 'Windows':
            print("Warning: Running on native Windows. Not all functionality may work as intended.\nFor full support, please run inside Windows Subsystem for Linux (WSL).", file=sys.stderr, end='')
            
        # Parse arguments
        self.args = self.parse_args()


        # Load config (auto-generate if missing)
        self.config = self.load_config()

        # Set up logging
        logging_config = self.config.get("logging", {})
        if logging_config.get("enabled", True):
            self.logger = get_logger(self.config, logging_config.get("level", "INFO"))
        else:
            self.logger = None


        # Handle special operations
        if self.args.self_update:
            self.ui.print_message("\n[Self-Update Mode]\n")
            self.perform_self_update(self.args)
            return

        if self.args.install_llama:
            self.ui.print_message("\n[Install llama.cpp]\n")
            try:
                LlamaUpdater().install()
            except SystemExit:
                raise
            except Exception as e:
                # Re-raise if it's a known updater error
                from llama_updater import (RateLimitError, GitHubAPIError, 
                                            DownloadError, ExtractionError, 
                                            PlatformNotFoundError, LlamaUpdaterError)
                if isinstance(e, (RateLimitError, GitHubAPIError, 
                                   DownloadError, ExtractionError, 
                                   PlatformNotFoundError, LlamaUpdaterError)):
                    raise
                print(f"Error: {e}")
                sys.exit(1)
            return

        if self.args.update_llama:
            self.ui.print_message("\n[Update llama.cpp]\n")
            try:
                LlamaUpdater().update()
            except SystemExit:
                raise
            except Exception as e:
                # Re-raise if it's a known updater error
                from llama_updater import (RateLimitError, GitHubAPIError, 
                                            DownloadError, ExtractionError, 
                                            PlatformNotFoundError, LlamaUpdaterError)
                if isinstance(e, (RateLimitError, GitHubAPIError, 
                                   DownloadError, ExtractionError, 
                                   PlatformNotFoundError, LlamaUpdaterError)):
                    raise
                print(f"Error: {e}")
                sys.exit(1)
            return

        if self.args.stop_server:
            self.ui.print_message("\n[Stop Server Mode]\n")
            exit_code = stop_server()
            sys.exit(exit_code)

        # Default: Run llama-server
        self.ui.print_message("\n[Run llama-server]\n")

        # Check if llama-cpp is installed
        llama_cpp_path = Path.cwd() / "llama-cpp" / "llama-server"
        if not llama_cpp_path.exists():
            self.ui.print_message("Error: llama-cpp is not installed. Please run with --install-llama first.")
            self.ui.print_message("\nUsage: ./llama-server-manager --install-llama")
            sys.exit(1)

        runner = Runner(self.args, self.config)
        runner.run()

if __name__ == "__main__":
    app = Main()
    app.run()
