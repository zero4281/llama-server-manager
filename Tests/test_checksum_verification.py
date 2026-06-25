#!/usr/bin/env python3
"""
Test for checksum verification in llama_updater.py.
"""
import tempfile
import unittest
import os
import json
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from llama_updater import LlamaUpdater, LlamaUpdaterError

# Add current directory to path
import sys
sys.path.insert(0, str(Path.cwd()))

class TestChecksumVerification(unittest.TestCase):
    def setUp(self):
        self.updater = LlamaUpdater()
        # Create a dummy archive for testing
        self.archive_path = Path(tempfile.gettempdir()) / "dummy_archive.zip"
        with open(self.archive_path, "w") as f:
            f.write("dummy content")

    def tearDown(self):
        if self.archive_path.exists():
            self.archive_path.unlink()
        if (self.archive_path.with_suffix('.sha256sum.txt')).exists():
            self.archive_path.with_suffix('.sha256sum.txt').unlink()

    @patch('llama_updater.open')
    @patch('llama_updater.shutil.rmtree')
    @patch('llama_updater.shutil.move')
    @patch('llama_updater.subprocess.run')
    @patch('llama_updater.ensure_executable')
    @patch('llama_updater.datetime.datetime')
    @patch('llama_updater.hashlib.sha256')
    @patch('llama_updater.extract_archive')
    @patch('llama_updater.get_available_platforms')
    @patch('llama_updater.get_latest_release')
    @patch('llama_updater.get_release_by_tag')
    @patch('llama_updater.requests.get')
    def test_checksum_verification_success(self, mock_requests, mock_get_release_by_tag, mock_get_latest_release, mock_get_available_platforms, mock_extract_archive, mock_sha256, mock_datetime, mock_ensure_executable, mock_sub_run, mock_move, mock_rmtree, mock_open):
        # Mock datetime
        mock_datetime.utcfromtimestamp.return_value = None
        mock_datetime.now.return_value = None

        # Create mock release data
        mock_release_data = {
            "tag_name": "b9637",
            "name": "llama-server-v1.2.0",
            "published_at": "2026-06-01T12:00:00Z",
            "assets": [
                {
                    "name": "llama-b9637-bin-ubuntu-x64.tar.gz",
                    "browser_download_url": "http://example.com/llama-b9637-bin-ubuntu-x64.tar.gz",
                    "size": 1000000
                },
                {
                    "name": "sha256sum.txt",
                    "browser_download_url": "http://example.com/sha256sum.txt",
                    "size": 100
                }
            ]
        }

        # Set up get_latest_release to return the release data
        mock_get_latest_release.return_value = mock_release_data

        # Set up get_release_by_tag to return the release data when manual tag is entered
        mock_get_release_by_tag.return_value = mock_release_data

        # Mock UI manager
        mock_ui = MagicMock()
        mock_ui.render_menu.side_effect = lambda *args, **kwargs: 0
        mock_ui.render_confirmation.return_value = True
        mock_ui.print_message = MagicMock()
        mock_ui.render_error = MagicMock()
        mock_ui.get_input.return_value = "manual-tag"

        # Mock hashlib
        mock_sha256_instance = MagicMock()
        mock_sha256_instance.hexdigest.return_value = "expected_hash_value"
        mock_sha256.return_value = mock_sha256_instance

        # Mock get_available_platforms
        mock_get_available_platforms.return_value = [
            {
                "platform": "Linux",
                "arch": "x64",
                "variant": "vulkan",
                "assets": [{
                    "name": "llama-b9637-bin-ubuntu-x_64.tar.gz",
                    "browser_download_url": "http://example.com/llama-b9637-bin-ubuntu-x64.tar.gz",
                    "size": 1000000
                }]
            }
        ]
        
        # Mock get_checksum_assets to return the checksum asset
        mock_get_checksum_assets = MagicMock(return_value=[mock_release_data['assets'][1]])
    
        # Mock verify_checksum to return True (success)
        mock_verify_checksum = MagicMock(return_value=True)
    
        # Configure mock_open to return a mock file object
        mock_file = MagicMock()
        mock_file.__enter__ = MagicMock(return_value=mock_file)
        mock_file.__exit__ = MagicMock(return_value=None)
        mock_file.read.return_value = json.dumps({})
        mock_open.return_value = mock_file
        
        # Patch these functions during install
        with patch('llama_updater.get_checksum_assets', mock_get_checksum_assets):
            with patch('llama_updater.verify_checksum', mock_verify_checksum):
                # Run the installation
                self.updater.install(ui_manager=mock_ui)
        
        # Verify checksum was verified
        mock_verify_checksum.assert_called_once()
        mock_ui.print_message.assert_any_call("Checking checksum...")
        mock_ui.print_message.assert_any_call("Installation complete!")

    @patch('llama_updater.open')
    @patch('llama_updater.shutil.rmtree')
    @patch('llama_updater.shutil.move')
    @patch('llama_updater.subprocess.run')
    @patch('llama_updater.ensure_executable')
    @patch('llama_updater.datetime.datetime')
    @patch('llama_updater.hashlib.sha256')
    @patch('llama_updater.extract_archive')
    @patch('llama_updater.get_available_platforms')
    @patch('llama_updater.get_latest_release')
    @patch('llama_updater.get_release_by_tag')
    @patch('llama_updater.requests.get')
    def test_checksum_verification_failure(self, mock_requests, mock_get_release_by_tag, mock_get_latest_release, mock_get_available_platforms, mock_extract_archive, mock_sha256, mock_datetime, mock_ensure_executable, mock_sub_run, mock_move, mock_rmtree, mock_open):
        # Mock datetime
        mock_datetime.utcfromtimestamp.return_value = None
        mock_datetime.now.return_value = None

        # Mock release with checksum asset
        mock_release = {
            "tag_name": "b9637",
            "name": "llama-server-v1.2.0",
            "published_at": "2026-06-01T12:00:00Z",
            "assets": [
                {
                    "name": "llama-b9637-bin-ubuntu-x64.tar.gz",
                    "browser_download_url": "http://example.com/llama-b9637-bin-ubuntu-x64.tar.gz",
                    "size": 1000000
                },
                {
                    "name": "sha256sum.txt",
                    "browser_download_url": "http://example.com/sha256sum.txt",
                    "size": 100
                }
            ]
        }

        # Set up get_latest_release to return the release data
        mock_get_latest_release.return_value = mock_release

        # Set up get_release_by_tag to return the release data when manual tag is entered
        mock_get_release_by_tag.return_value = mock_release

        # Mock UI manager
        mock_ui = MagicMock()
        mock_ui.render_menu.side_effect = lambda *args, **kwargs: 0
        mock_ui.render_confirmation.return_value = True
        mock_ui.print_message = MagicMock()
        mock_ui.render_error = MagicMock()
        mock_ui.get_input.return_value = "manual-tag"

        # Mock hashlib
        mock_sha256_instance = MagicMock()
        mock_sha256_instance.hexdigest.return_value = "wrong_hash_value"
        mock_sha256.return_value = mock_sha256_instance

        # Mock get_available_platforms
        mock_get_available_platforms.return_value = [
            {
                "platform": "Linux",
                "arch": "x64",
                "variant": "vulkan",
                "assets": [{
                    "name": "llama-b9637-bin-ubuntu-x_64.tar.gz",
                    "browser_download_url": "http://example.com/llama-b9637-bin-ubuntu-x64.tar.gz",
                    "size": 1000000
                }]
            }
        ]
        
        # Mock get_checksum_assets to return the checksum asset
        mock_get_checksum_assets = MagicMock(return_value=[mock_release['assets'][1]])
    
        # Mock verify_checksum to return False (failure)
        mock_verify_checksum = MagicMock(return_value=False)
    
        # Configure mock_open to return a mock file object
        mock_file = MagicMock()
        mock_file.__enter__ = MagicMock(return_value=mock_file)
        mock_file.__exit__ = MagicMock(return_value=None)
        mock_file.read.return_value = json.dumps({})
        mock_open.return_value = mock_file
        
        # Patch these functions during install
        with patch('llama_updater.get_checksum_assets', mock_get_checksum_assets):
            with patch('llama_updater.verify_checksum', mock_verify_checksum):
                # Run the installation
                with self.assertRaises(LlamaUpdaterError) as cm:
                    self.updater.install(ui_manager=mock_ui)
        
        self.assertIn("Checksum verification failed", str(cm.exception))

if __name__ == "__main__":
    unittest.main()
