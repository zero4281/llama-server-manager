#!/usr/bin/env python3
"""
Integration test for the --install-llama workflow.
Verifies that the full installation process works, including configuration persistence.
"""
import sys
import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from llama_updater import LlamaUpdater

# Add current directory to path
sys.path.insert(0, str(Path.cwd()))

class TestInstallWorkflow(unittest.TestCase):
    def setUp(self):
        # Ensure config.json exists
        config_data = {
            "options": {},
            "llama-server": {"options": {}},
            "logging": {"enabled": True, "level": "INFO", "file": None},
            "install": {}
        }
        with open("config.json", "w") as f:
            json.dump(config_data, f, indent=2)
        
        self.updater = LlamaUpdater()

    def tearDown(self):
        if os.path.exists("config.json"):
            os.remove("config.json")

    @patch('requests.get')
    @patch('llama_updater.shutil.rmtree')
    @patch('llama_updater.shutil.move')
    @patch('llama_updater.subprocess.run')
    @patch('llama_updater.ensure_executable')
    @patch('llama_updater.datetime.datetime')
    @patch('llama_updater.hashlib.sha256')
    @patch('llama_updater.extract_archive')
    @patch('llama_updater.get_available_platforms')
    def test_install_workflow_success(self, mock_get_available_platforms, mock_extract_archive, mock_sha256, mock_datetime, mock_ensure_executable, mock_sub_run, mock_move, mock_rmtree, mock_requests):
        # Mock datetime for timestamps
        mock_datetime.utcfromtimestamp.return_value = None
        mock_datetime.now.return_value = None
    
        # Mock GitHub API for latest release
        mock_release = {
            "tag_name": "b9637",
            "name": "llama-server-v1.2.0",
            "published_at": "2026-06-01T12:00:00Z",
            "assets": [
                {
                    "name": "llama-b9637-bin-ubuntu-x64-vulkan.tar.gz",
                    "browser_download_url": "http://example.com/llama-b9637-bin-ubuntu-x64-vulkan.tar.gz",
                    "size": 1000000
                },
                {
                    "name": "llama-b9637-bin-macos-arm64.tar.gz",
                    "browser_download_url": "http://example.com/llama-b9637-bin-macos-arm64.tar.gz",
                    "size": 1000000
                }
            ]
        }
    
        mock_release_list = [mock_release]

    
        # Mock responses
        mock_response_latest = MagicMock()
        mock_response_latest.status_code = 200
        mock_response_latest.json.return_value = mock_release
        mock_response_latest.headers = {}
    
        mock_response_releases = MagicMock()
        mock_response_releases.status_code = 200
        mock_response_releases.json.return_value = mock_release_list
        mock_response_releases.headers = {}







    
        mock_response_download = MagicMock()
        mock_response_download.status_code = 200
        mock_response_download.headers = {'content-length': '1000000'}
    
        # Mock requests.get to return different responses based on URL
        def make_request(url, **kwargs):
            if "latest" in url:
                return mock_response_latest
            elif "tags" in url:
                # Single release for specific tag (must check before releases)
                mock_response_tag = MagicMock()
                mock_response_tag.status_code = 200
                mock_response_tag.json.return_value = mock_release
                mock_response_tag.headers = {}
                return mock_response_tag
            elif "releases" in url and "latest" not in url:
                return mock_response_releases  # List of releases
            else:
                return mock_response_download
    
        mock_requests.side_effect = make_request
    
    
        # Mock UI manager to just return first available option for everything
        mock_ui = MagicMock()
        mock_ui.render_menu.side_effect = lambda *args, **kwargs: 0
        mock_ui.render_confirmation.return_value = True
        mock_ui.get_input.return_value = "manual-tag"
        mock_ui.print_message = MagicMock()
        mock_ui.render_error = MagicMock()
    
        # Mock hashlib.sha256
        mock_sha256_instance = MagicMock()
        mock_sha256_instance.hexdigest.return_value = "expected_hash_value"
        mock_sha256.return_value = mock_sha256_instance
    
        # Mock get_available_platforms to return a fixed list
        mock_get_available_platforms.return_value = [
            {
                "platform": "Linux",
                "arch": "x64",
                "variant": "vulkan",
                "assets": [{
                    "name": "llama-b9637-bin-ubuntu-x64.tar.gz",
                    "browser_download_url": "http://example.com/llama-b9637-bin-ubuntu-x64.tar.gz",
                    "size": 1000000
                }]
            }
        ]
    
        # Run the installation
        self.updater.install(ui_manager=mock_ui)


        # Verify config.json update
        with open("config.json", "r") as f:
            config = json.load(f)
        
        self.assertEqual(config["install"]["release"], "b9637")
        self.assertEqual(config["install"]["platform"], "Linux")
        self.assertEqual(config["install"]["arch"], "x64")
        self.assertEqual(config["install"]["backend"], "vulkan")

if __name__ == "__main__":
    unittest.main()
