import json
from llama_updater import install_release
from unittest.mock import MagicMock, patch
import sys

# Mocking the UIManager to see what's happening
class MockUI:
    def __init__(self, title):
        self.title = title
        self.render_menu = MagicMock(return_value=0) # Press Enter on first option
        self.render_confirmation = MagicMock(return_value=True)
        self.render_progress_bar = MagicMock()
        self.render_success = MagicMock()
        self.render_error = MagicMock()
        self.print_message = MagicMock()
        self.print_header = MagicMock()
        self._using_curses = True
        self._screen = MagicMock()

def test_backend_fix():
    with open("mock_release.json", "r") as f:
        release = json.load(f)

    with patch('llama_updater.UIManager', return_value=MockUI("Test")):
        try:
            install_release(release, "b10154")
            print("Success: install_release completed without errors.")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_backend_fix()
