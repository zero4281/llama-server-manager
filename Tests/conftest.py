import curses
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_curses():
    """A fully mocked curses module — safe to use without a TTY."""
    m = MagicMock()
    
    # Copy only the essential constant attributes
    for attr in ['KEY_UP', 'KEY_DOWN', 'KEY_ENTER', 'KEY_RESIZE', 'KEY_BACKSPACE', 'KEY_PPAGE', 'KEY_NPAGE', 'A_REVERSE', 'COLOR_GREEN', 'COLOR_WHITE', 'COLOR_BLACK']:
        if hasattr(curses, attr):
            setattr(m, attr, getattr(curses, attr))
    
    # Set up screen and other callables
    m.screen = MagicMock()
    m.initscr.return_value = m.screen
    m.start_color = MagicMock()
    m.init_pair = MagicMock(return_value=None)
    m.cbreak = MagicMock(return_value=True)
    m.noecho = MagicMock()
    m.curs_set = MagicMock(return_value=None)
    m.color_pair = MagicMock(return_value=curses.COLOR_GREEN)  # Return a valid color value
    # Use the real curses.error class
    m.error = curses.error
    
    # Mock screen methods
    m.screen.getmaxyx.return_value = (24, 80)
    m.screen.getyx.return_value = (0, 0)
    m.screen.getch.return_value = -1
    m.screen.addstr.return_value = None
    m.screen.refresh.return_value = None
    m.screen.move.return_value = None
    m.screen.keypad.return_value = None
    m.screen.timeout.return_value = None
    m.screen.erase.return_value = None
    m.screen.scrollok.return_value = None
    m.screen.addch.return_value = None
    m.screen.inch.return_value = (0, 0)
    m.screen.getbkgd.return_value = 0
    m.screen.border.return_value = None
    m.screen.initscr.return_value = m.screen
    
    return m


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



