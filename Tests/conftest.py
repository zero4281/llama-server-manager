import sys
import curses
import pytest
from unittest.mock import MagicMock, patch

# Create a global mock for the curses module
mock_curses = MagicMock()

# Copy only the essential constant attributes
for attr in ['KEY_UP', 'KEY_DOWN', 'KEY_ENTER', 'KEY_RESIZE', 'KEY_BACKSPACE', 'KEY_PPAGE', 'KEY_NPAGE', 'A_REVERSE', 'COLOR_GREEN', 'COLOR_WHITE', 'COLOR_BLACK']:
    if hasattr(curses, attr):
        setattr(mock_curses, attr, getattr(curses, attr))

# Set up screen and other callables
mock_curses.screen = MagicMock()
mock_curses.initscr.return_value = mock_curses.screen
mock_curses.start_color = MagicMock()
mock_curses.init_pair = MagicMock(side_effect=lambda pair, fg, bg: pair)
mock_curses.cbreak = MagicMock(return_value=True)
mock_curses.noecho = MagicMock()
mock_curses.curs_set = MagicMock(return_value=None)
mock_curses.echo = MagicMock(return_value=None)
mock_curses.color_pair = MagicMock(return_value=curses.COLOR_GREEN)
mock_curses.refresh = MagicMock(return_value=None)
mock_curses.has_ungetch = MagicMock(return_value=False)
mock_curses.getscrptr = MagicMock(return_value=None)
mock_curses.nodelay = MagicMock(return_value=None)
mock_curses.keypad = MagicMock(return_value=None)
mock_curses.timeout = MagicMock(return_value=None)
mock_curses.error = curses.error

# Set sys.modules["curses"] to our mock before any other module can import the real one
sys.modules["curses"] = mock_curses

# Mock screen methods
mock_curses.screen.getmaxyx.return_value = (24, 80)
mock_curses.screen.getyx.return_value = (0, 0)
mock_curses.screen.getch.return_value = -1
mock_curses.screen.addstr.return_value = None
mock_curses.screen.refresh.return_value = None
mock_curses.screen.move.return_value = None
mock_curses.screen.keypad.return_value = None
mock_curses.screen.timeout.return_value = None
mock_curses.screen.erase.return_value = None
mock_curses.screen.scrollok.return_value = None
mock_curses.screen.addch.return_value = None
mock_curses.screen.inch.return_value = (0, 0)
mock_curses.screen.getbkgd.return_value = 0
mock_curses.screen.border.return_value = None
mock_curses.screen.initscr.return_value = mock_curses.screen

@pytest.fixture(scope="session", autouse=True)
def global_mock_curses():
    pass

@pytest.fixture
def mock_curses():
    """Return the global mock_curses object."""
    return mock_curses

@pytest.fixture
def mock_win():
    """A mock curses window with sensible defaults."""
    win = MagicMock()
    win.getmaxyx.return_value = (24, 80)
    win.getyx.return_value = (0, 0)
    win.addstr.return_value = None
    win.refresh.return_value = None
    win.move.return_value = None
    win.keypad.return_value = None
    win.timeout.return_value = None
    win.getch.return_value = -1
    win.erase.return_value = None
    win.scrollok.return_value = None
    win.addch.return_value = None
    win.inch.return_value = (0, 0)
    win.getbkgd.return_value = 0
    win.border.return_value = None
    win.box.return_value = None
    win.addch.return_value = None
    win.getwin.return_value = None
    win.getstr.return_value = None
    win.getnstr.return_value = None
    win.getmaxy.return_value = 24
    win.getmaxx.return_value = 80
    win.getyx.return_value = (0, 0)
    win.getpattr.return_value = 0
    return win

@pytest.fixture
def ui(mock_curses):
    """A UIManager instance with curses fully mocked, _using_curses=True."""
    from ui_manager import UIManager
    # No need to patch ui_manager.curses since it's already globally mocked
    instance = UIManager("Test")
    instance._using_curses = True
    instance._color_pair = mock_curses.color_pair(1) | mock_curses.A_REVERSE
    instance._screen = mock_curses.screen
    return instance
