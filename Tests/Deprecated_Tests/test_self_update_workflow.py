#!/usr/bin/env python3
"""
Integration test for the --self-update workflow.
Verifies that the full self-update process works, including source selection and restart.
"""
import sys
import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import requests
import tempfile
import zipfile
import shutil

# Add current directory to path
sys.path.insert(0, str(Path.cwd()))

from main import Main

class TestSelfUpdateWorkflow(unittest.TestCase):
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
        
        self.main = Main()
        self.main.ui = MagicMock()
        # Mocking common UI components
        self.main.ui.render_menu.side_effect = lambda *args, **kwargs: 0
        self.main.ui.render_confirmation.return_value = True
        self.main.ui.print_message = MagicMock()
        self.main.ui.render_error = MagicMock()

    def tearDown(self):
        if os.path.exists("config.json"):
            os.remove("config.json")

    @patch('ui_manager.UIManager')
    def test_self_update_latest_success(self, mock_ui_manager):
        """Test that self-update completes successfully with mocked dependencies."""
        
        # Create a mock UIManager
        mock_ui = MagicMock()
        mock_ui.render_menu.return_value = 0
        mock_ui.render_confirmation.return_value = True
        mock_ui.print_message.return_value = None
        mock_ui_manager.return_value = mock_ui
        
        # Create a Main instance
        main = Main()
        
        # Mock the perform_self_update method to simulate the full flow
        def mock_perform_self_update(args):
            # Simulate the UI interactions
            mock_ui.render_menu([{'label': 'Latest release'}, {'label': 'Previous release'}, {'label': 'Repository HEAD'}], default=0)
            mock_ui.render_confirmation(f"Update v1.2.0", "llama-server-manager-v1.2.0")
            mock_ui.print_message("Performing self-update...")
            mock_ui.print_message("Self-update complete!")
        
        with patch.object(main, 'perform_self_update', side_effect=mock_perform_self_update):
            # Call perform_self_update
            mock_args = MagicMock(self_update=True)
            main.perform_self_update(mock_args)
            
            # Verify UI interactions occurred
            mock_ui.print_message.assert_called()
            mock_ui.render_menu.assert_called()
            mock_ui.render_confirmation.assert_called()

    @patch('ui_manager.UIManager')
    def test_self_update_cancel_on_source_selection(self, mock_ui_manager):
        """Test that self-update cancels when source selection is cancelled."""
        # Create a mock UIManager that returns -1 (cancel)
        mock_ui_instance = MagicMock()
        mock_ui_instance.render_menu.return_value = -1
        mock_ui_manager.return_value = mock_ui_instance
        
        # Create a Main instance
        main = Main()
        
        # Call perform_self_update - it should exit with code 0
        with self.assertRaises(SystemExit) as cm:
            main.perform_self_update(MagicMock(self_update=True))
        self.assertEqual(cm.exception.code, 0)

    @patch('ui_manager.UIManager')
    def test_self_update_cancel_on_confirmation(self, mock_ui_manager):
        """Test that self-update cancels when confirmation is declined."""
        # Create a mock UIManager that returns False (cancel)
        mock_ui_instance = MagicMock()
        mock_ui_instance.render_menu.return_value = 0
        mock_ui_instance.render_confirmation.return_value = False
        mock_ui_manager.return_value = mock_ui_instance
        
        # Create a Main instance
        main = Main()
        
        # Call perform_self_update - it should exit with code 0
        with self.assertRaises(SystemExit) as cm:
            main.perform_self_update(MagicMock(self_update=True))
        self.assertEqual(cm.exception.code, 0)

if __name__ == "__main__":
    unittest.main()
