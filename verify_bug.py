from llama_updater import install_release
import json

with open("mock_release.json", "r") as f:
    release = json.load(f)

# We want to see if 'cpu' is added to the backend options for ubuntu x64
# The install_release function is interactive.
# We can mock the UI to see the options.
from unittest.mock import MagicMock, patch

class MockUI:
    def __init__(self, title):
        self.title = title
        self.render_menu = MagicMock(return_value=0) # Simulate pressing Enter on first option
        self.render_confirmation = MagicMock(return_value=True)
        self.render_progress_bar = MagicMock()
        self.render_success = MagicMock()
        self.render_error = MagicMock()
        self.print_message = MagicMock()
        self.print_header = MagicMock()
        self.print_message = MagicMock()

with patch('llama_updater.UIManager', return_value=MockUI("Test")):
    # This will still try to do things like detect_platform
    # But we want to see the backend_options
    # Let's look at the code in llama_updater.py
    pass
