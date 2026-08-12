"""
main.py — Main entry point for llama-server-manager.

This is the central CLI tool that orchestrates all operations:
- Self-update
- Installing/updating llama.cpp
- Stopping a running server
- Running llama-server with configured options
"""

__version__ = "1.1.3"

import logging
import argparse
import os
import shutil
import sys
import json
import platform
import requests
import zipfile
import tempfile
import subprocess
from pathlib import Path
from logger import LoggerSetup
from ui_manager import UIManager
from runner import Runner
from llama_updater import LlamaUpdater, ensure_executable
from config import load_config

# Add current directory to path for imports
sys.path.insert(0, str(Path.cwd()))

logger = logging.getLogger(__name__)

class Main:
    """Main wrapper application."""

    def __init__(self):
        self.args = None
        self.config = None
        self.ui = None

    def parse_args(self, args: list = None) -> argparse.Namespace:
        """
        Parse command-line arguments.
        """
        # WSL detection
        if platform.system() == 'Windows':
            print("Warning: Running on native Windows. Not all functionality may work as intended.\n"
                  "For full support, please run inside Windows Subsystem for Linux (WSL).", file=sys.stderr)

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

        # Version flag
        parser.add_argument("--version", action="store_true",
                            help="Print the version and exit")
        
        return parser.parse_args(args)

    def load_config(self) -> dict:
        """
        Load or auto-generate configuration.
        """
        return load_config()

    def perform_self_update(self, args: argparse.Namespace) -> None:
        """
        Perform self-update from GitHub.
        """
        zip_file_path = None
        try:
            self.ui = UIManager("Self-Update")
            self.ui.print_message("Performing self-update...")

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
                url = "https://api.github.com/repos/zero4281/llama-server-manager/releases"
                headers = {
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                }
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                releases = response.json()

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
                selected_zip_url = "https://github.com/zero4281/llama-server-manager/archive/refs/heads/main.zip"
                selected_tag = "HEAD"
                selected_name = "main branch HEAD"

            confirm = self.ui.render_confirmation(f"Selected: {selected_tag if selected_tag != 'HEAD' else selected_name}", f"({selected_name})")

            if not confirm:
                self.ui.render_error("Update cancelled.")
                sys.exit(0)

            headers = {
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
            zip_response = requests.get(selected_zip_url, headers=headers, timeout=60)
            zip_response.raise_for_status()
            zip_content = zip_response.content

            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as zip_file:
                zip_file.write(zip_content)
                zip_file_path = Path(zip_file.name)

            try:
                with tempfile.TemporaryDirectory() as extract_temp:
                    extract_subdir = Path(extract_temp) / "extract"
                    extract_subdir.mkdir()

                    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                        zip_ref.extractall(extract_subdir)

                    top_level_dir = None
                    for item in extract_subdir.iterdir():
                        if item.is_dir() and not item.name.startswith(('.', '_')):
                            top_level_dir = item
                            break

                    if top_level_dir:
                        backups = []
                        backup_dir = Path.cwd() / ".backup"
                        backup_dir.mkdir(parents=True, exist_ok=True)

                        for file_path in top_level_dir.rglob("*"):
                            if file_path.is_file():
                                rel_path = file_path.relative_to(top_level_dir)
                                if rel_path.name.endswith('.md') or 'tests' in rel_path.parts:
                                    continue

                                target = Path.cwd() / rel_path
                                if target.exists():
                                    backup_path = backup_dir / rel_path
                                    backup_path.parent.mkdir(parents=True, exist_ok=True)
                                    shutil.move(str(target), str(backup_path))
                                    backups.append((backup_path, target))
                                else:
                                    target.parent.mkdir(parents=True, exist_ok=True)

                                shutil.move(str(file_path), str(target))
                                if target.name == 'llama-server-manager':
                                    ensure_executable(target)

                                self.ui.print_message(f"Updated: {rel_path}")


                        if backup_dir.exists():
                            shutil.rmtree(backup_dir)
                        self.ui.render_success("Self-update complete!")
                        self.ui._cleanup_terminal()
                        sys.exit(0)
                    else:
                        self.ui.render_error("Could not find top-level directory in extraction.")
            except Exception as e:
                logger.error(f"Extraction error: {e}")
                raise
            finally:
                if zip_file_path and zip_file_path.exists():
                    zip_file_path.unlink()


        except Exception as e:
            self.ui.render_error(f"Self-update failed: {e}")
            sys.exit(2)

    def run(self) -> None:
        """Main execution flow."""
        # 1. Parse arguments
        self.args = self.parse_args()
        
        # 3. Call load_config() to obtain the configuration dict.
        self.config = self.load_config()
        
        # 4. Instantiate LoggerSetup using the loaded configuration.
        LoggerSetup(self.config).setup()
        
        # 2. If --version: instantiate UIManager, print version, exit
        if self.args.version:
            if self.ui is None:
                self.ui = UIManager("Llama Server Manager")
            self.ui.print_message(__version__, level="info")
            sys.exit(0)
        
        # Instantiate UI for the rest of the paths (after LoggerSetup)
        if not self.ui:
            self.ui = UIManager("Llama Server Manager")
            
        # 5. If --self-update: perform the self-update and exit.
        if self.args.self_update:
            self.ui.print_message("\n[Self-Update Mode]\n")
            self.perform_self_update(self.args)
            return

        
        # 6. If --install-llama or --update-llama: instantiate LlamaUpdater and call the appropriate method; exit on completion.
        if self.args.install_llama:
            self.ui.print_message("\n[Install llama.cpp]\n")
            try:
                LlamaUpdater(ui_manager=self.ui).install()
            except SystemExit:
                raise
            except Exception as e:
                from llama_updater import (RateLimitError, GitHubAPIError,
                                          DownloadError, ExtractionError,
                                          PlatformNotFoundError, LlamaUpdaterError)
                if isinstance(e, (RateLimitError, GitHubAPIError,
                                    DownloadError, ExtractionError,
                                    PlatformNotFoundError, LlamaUpdaterError)):
                    raise
                self.ui.render_error(f"Error: {e}")
                sys.exit(1)
            return
            
        if self.args.update_llama:
            self.ui.print_message("\n[Update llama.cpp]\n")
            try:
                LlamaUpdater(ui_manager=self.ui).update()
            except SystemExit:
                raise
            except Exception as e:
                from llama_updater import (RateLimitError, GitHubAPIError,
                                          DownloadError, ExtractionError,
                                          PlatformNotFoundError, LlamaUpdaterError)
                if isinstance(e, (RateLimitError, GitHubAPIError,
                                    DownloadError, ExtractionError,
                                    PlatformNotFoundError, LlamaUpdaterError)):
                    raise
                self.ui.render_error(f"Error: {e}")
                sys.exit(1)
            return
            
        # 7. Otherwise:
        if self.args.stop_server:
            self.ui.print_message("\n[Stop Server Mode]\n")
            runner = Runner(self.args, self.config, self.ui)
            exit_code = runner.stop_server()
            sys.exit(exit_code)
            
        self.ui.print_message("\n[Run llama-server]\n")
        llama_cpp_dir = Path.cwd() / "llama-cpp"
        if not llama_cpp_dir.exists():
            self.ui.print_message("llama-cpp not found. Please install it first:\n   ./llama-server-manager --install-llama")
            sys.exit(1)
            
        # Instantiate Runner and call runner.run()
        runner = Runner(self.args, self.config, self.ui)
        runner.run()


if __name__ == "__main__":
    app = Main()
    app.run()
