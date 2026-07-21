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
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path.cwd()))

from wrapper_config import load_config, get_logger
from ui_manager import UIManager
from runner import Runner
from llama_updater import LlamaUpdater


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
        import platform
        if platform.system() == 'Windows':
            print("Warning: Running on native Windows. Not all functionality may work as intended.\nFor full support, please run inside Windows Subsystem for Linux (WSL).", file=sys.stderr)
        
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
            import requests
            import zipfile
            import tempfile
            from ui_manager import UIManager
            
            self.ui = UIManager("Self-Update")
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
            confirm = ui.render_confirmation(f"Selected: {selected_tag if selected_tag != 'HEAD' else selected_name}", f"({selected_name})")
            
            if not confirm:
                ui.render_error("Update cancelled.")
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
            
            try:
                # Extract to a temp directory
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
                        moved_files = []
                        try:
                            backup_dir = project_root / ".backup"
                            backup_dir.mkdir(parents=True, exist_ok=True)
                            backups = []
                            
                            for file_path in top_level_dir.rglob("*"):
                                if file_path.is_file():
                                    rel_path = file_path.relative_to(top_level_dir)
                                    if rel_path.name.endswith('.md') or 'tests' in rel_path.parts:
                                        continue
                                    
                                    target = project_root / rel_path
                                    if target.exists():
                                        backup_path = backup_dir / rel_path
                                        backup_path.parent.mkdir(parents=True, exist_ok=True)
                                        shutil.move(str(target), str(backup_path))
                                        backups.append((backup_path, target))
                                        shutil.move(str(file_path), str(target))
                                    else:
                                        target.parent.mkdir(parents=True, exist_ok=True)
                                        shutil.move(str(file_path), str(target))
                                    
                                    self.ui.print_message(f"Updated: {rel_path}")
                            
                            if backup_dir.exists():
                                shutil.rmtree(backup_dir)
                            self.ui.render_success("Self-update complete!")
                        except Exception as e:
                            for backup_path, original_target_path in reversed(backups):
                                shutil.move(str(backup_path), str(original_target_path))
                            self.ui.render_error(f"Error during file move: {e}")
                            raise e
                        finally:
                            if top_level_dir.exists():
                                shutil.rmtree(top_level_dir)
                                self.ui.print_message(f"Removed: {top_level_dir.name}")


                        
            finally:
                # Clean up temporary zip file
                if zip_file_path.exists():
                    zip_file_path.unlink()
            
            # Restart with same arguments
            ui.print_message(f"Restarting with original arguments: {args}")
            
            new_args = ["main.py"] + sys.argv[1:]
            
            # Clear any cached modules to force reimport
            modules_to_clear = [
                'main', 'runner', 'llama_updater', 'logging'
            ]
            for module in modules_to_clear:
                if module in sys.modules:
                    del sys.modules[module]
            
            # Execute restart using subprocess
            import subprocess
            
            # Execute and replace current process
            subprocess.Popen([sys.executable, "main.py"] + sys.argv[1:], 
                             stdout=subprocess.PIPE, 
                             stderr=subprocess.PIPE, 
                             text=True)
            sys.exit(0)
            
        except Exception as e:
            ui.render_error(f"Self-update failed: {e}")
            sys.exit(2)

    def run(self) -> None:
        """Main execution flow."""
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

        runner = Runner(self.args, self.config, self.ui)
        
        # Handle special operations
        if self.args.self_update:
            self.ui.print_message("\n[Self-Update Mode]\n")
            self.perform_self_update(self.args)
            return
        
        if self.args.install_llama:
            self.ui.print_message("\n[Install llama.cpp]\n")
            try:
                 LlamaUpdater(ui_manager=self.ui).install()
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
                # Re-raise if it's a known updater error
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
        
        if self.args.stop_server:
            self.ui.print_message("\n[Stop Server Mode]\n")
            exit_code = runner.stop_server()
            sys.exit(exit_code)
        
        # Default: Run llama-server
        self.ui.print_message("\n[Run llama-server]\n")
        
        # Check if llama-cpp is installed
        llama_cpp_path = Path.cwd() / "llama-cpp" / "llama-server"
        if not llama_cpp_path.exists():
            self.ui.render_error("Error: llama-cpp is not installed. Please run with --install-llama first.")
            self.ui.print_message("\nUsage: ./llama-server-manager --install-llama")
            sys.exit(1)
        
        runner.run()



if __name__ == "__main__":
    app = Main()
    app.run()