    def perform_self_update(self, args: argparse.Namespace) -> None:
        """
        Perform self-update from GitHub.
        """
        zip_file_path = None
        try:
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
                                    shutil.move(str(file_path), str(target))
                                else:
                                    target.parent.mkdir(parents=True, exist_ok=True)
                                    shutil.move(str(file_path), str(target))
                                
                                self.ui.print_message(f"Updated: {rel_path}")
                        
                        if backup_dir.exists():
                            shutil.rmtree(backup_dir)
                        self.ui.render_success("Self-update complete!")
                    else:
                        self.ui.render_error("Could not find top-level directory in extraction.")
            except Exception as e:
                logger.error(f"Extraction error: {e}")
                raise
            finally:
                if zip_file_path and zip_file_path.exists():
                    zip_file_path.unlink()
            
            # Restart with same arguments
            self.ui.print_message(f"Restarting with original arguments: {args}")
            
            new_args = ["main.py"] + sys.argv[1:]
            
            # Clear any cached modules to force reimport
            modules_to_clear = ['main', 'runner', 'llama_updater', 'logging']
            for module in modules_to_clear:
                if module in sys.modules:
                    del sys.modules[module]
            
            # Execute restart using subprocess
            subprocess.Popen([sys.executable, "main.py"] + sys.argv[1:],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True)
            sys.exit(0)
            
        except Exception as e:
            self.ui.render_error(f"Self-update failed: {e}")
            sys.exit(2)
