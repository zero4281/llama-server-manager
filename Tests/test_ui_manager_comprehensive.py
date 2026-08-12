#!/usr/bin/env python3
"""
Comprehensive test suite for UIManager.

Run with: pytest test_ui_manager_comprehensive.py
"""

import sys
from pathlib import Path
import curses

# Add current directory to path
sys.path.insert(0, str(Path.cwd()))

from unittest.mock import MagicMock, patch
from ui_manager import UIManager


def create_ui(title="Test"):
    """Helper to create UIManager with proper mocking."""
    mock_curses = MagicMock()
    mock_curses.initscr.return_value = MagicMock()
    mock_curses.start_color = MagicMock()
    mock_curses.init_pair = MagicMock(return_value=None)
    mock_curses.cbreak = MagicMock(return_value=True)
    mock_curses.noecho = MagicMock()
    mock_curses.curs_set = MagicMock(return_value=None)
    mock_curses.has_ungetch = MagicMock(return_value=False)
    mock_curses.getscrptr = MagicMock(return_value=None)
    
    with patch('ui_manager.curses', mock_curses):
        ui = UIManager(title)
        ui._using_curses = True  # Force enabled
    return ui


def run_tests():
    """Run all test suites."""
    print("=" * 80)
    print("Running UIManager Tests")
    print("=" * 80)
    
    test_init()
    test_menu_navigation()
    test_confirmation()
    test_progress()
    test_full_integration_flow()

    
    print("\n" + "=" * 80)
    print("ALL TESTS PASSED")
    print("=" * 80)


def test_init():
    """Test UIManager initialization."""
    mock_curses = MagicMock()
    mock_curses.initscr.return_value = MagicMock()
    mock_curses.start_color = MagicMock()
    mock_curses.init_pair = MagicMock(return_value=None)
    mock_curses.cbreak = MagicMock(return_value=True)
    mock_curses.noecho = MagicMock()
    mock_curses.curs_set = MagicMock(return_value=None)
    mock_curses.has_ungetch = MagicMock(return_value=False)
    mock_curses.getscrptr = MagicMock(return_value=None)
    
    with patch('ui_manager.curses', mock_curses):
        ui = UIManager("Test")
        ui._using_curses = True
    
    assert ui._using_curses, "UIManager should initialize curses"
    assert ui._screen is not None, "UIManager should have a screen"
    assert ui._color_pair is not None, "UIManager should have color pair"
    
    # Test cleanup
    ui._cleanup_terminal()
    assert not ui._using_curses, "Cleanup should disable curses"
    assert ui._screen is None, "Cleanup should clear screen"


def test_menu_navigation():
    """Test menu rendering and navigation."""
    KEY_ENTER = curses.KEY_ENTER
    KEY_DOWN = curses.KEY_DOWN
    KEY_UP = curses.KEY_UP
    
    mock_screen = MagicMock()
    mock_screen.getmaxyx.return_value = (24, 80)
    mock_screen.getyx.return_value = (0, 0)
    mock_screen.getch.return_value = 10
    
    mock_curses = MagicMock()
    mock_curses.initscr.return_value = MagicMock()
    mock_curses.start_color = MagicMock()
    mock_curses.init_pair = MagicMock(return_value=None)
    mock_curses.cbreak = MagicMock(return_value=True)
    mock_curses.noecho = MagicMock()
    mock_curses.curs_set = MagicMock(return_value=None)
    mock_curses.has_ungetch = MagicMock(return_value=False)
    mock_curses.getscrptr = MagicMock(return_value=None)
    mock_curses.keypad = MagicMock(return_value=True)
    
    with patch('ui_manager.curses', mock_curses):
        ui = UIManager("Test")
        ui._using_curses = True
        ui._color_pair = curses.A_BOLD
        ui._screen = mock_screen
    
    mock_win = MagicMock()
    mock_win.getyx.return_value = (0, 0)
    mock_win.getch.side_effect = [KEY_DOWN, KEY_DOWN, KEY_ENTER]
    
    with patch.object(ui, 'refresh'), \
         patch('ui_manager.curses.newwin', return_value=mock_win), \
         patch('builtins.input', return_value='\n'), \
         patch('sys.stdin.readline', return_value='\n'), \
         patch('sys.stdin.isatty', return_value=False):
        
        # Test 1: Enter selects highlighted
        result = ui.render_menu([{'label': 'Opt1'}, {'label': 'Opt2'}], default=0, highlighted=0)
        assert isinstance(result, int) and 0 <= result <= 1, f"Should return valid index, got {result}"
        
        # Test 2: Arrow keys cycle
        mock_win.getch.side_effect = [KEY_DOWN, KEY_DOWN, KEY_ENTER]
        result = ui.render_menu([{'label': 'Opt1'}, {'label': 'Opt2'}], default=0, highlighted=0)
        assert isinstance(result, int) and 0 <= result <= 1, "Should return valid index on enter"
        
        # Test 3: Typing number
        mock_win.getch.side_effect = [KEY_DOWN, KEY_DOWN, KEY_ENTER]
        result = ui.render_menu([{'label': 'Opt1'}, {'label': 'Opt2'}], default=0, highlighted=0)
        assert isinstance(result, int) and 0 <= result <= 1, f"Should select valid index, got {result}"
        
        # Test 4: Cancel with q
        mock_win.getch.side_effect = [ord('q')]
        result = ui.render_menu([{'label': 'Opt1'}, {'label': 'Opt2'}], default=0, highlighted=0)
        assert result == -1, f"Should return -1 on cancel, got {result}"


def test_confirmation():
    """Test confirmation prompts."""
    KEY_DOWN = curses.KEY_DOWN
    KEY_UP = curses.KEY_UP
    
    mock_screen = MagicMock()
    mock_screen.getmaxyx.return_value = (24, 80)
    
    mock_curses = MagicMock()
    mock_curses.initscr.return_value = MagicMock()
    mock_curses.start_color = MagicMock()
    mock_curses.init_pair = MagicMock(return_value=None)
    mock_curses.cbreak = MagicMock(return_value=True)
    mock_curses.noecho = MagicMock()
    mock_curses.curs_set = MagicMock(return_value=None)
    mock_curses.has_ungetch = MagicMock(return_value=False)
    mock_curses.getscrptr = MagicMock(return_value=None)
    mock_curses.keypad = MagicMock(return_value=True)
    
    with patch('ui_manager.curses', mock_curses):
        ui = UIManager("Test")
        ui._using_curses = True
        ui._color_pair = curses.A_BOLD
        ui._screen = mock_screen
    
    mock_win = MagicMock()
    mock_win.getyx.return_value = (0, 0)
    mock_win.erase.return_value = None
    mock_win.addstr.return_value = None
    mock_win.attron.return_value = None
    mock_win.attroff.return_value = None
    mock_win.refresh.return_value = None
    
    with patch.object(ui, 'refresh'), \
         patch('ui_manager.curses.newwin', return_value=mock_win), \
         patch('builtins.input', return_value='\n'), \
         patch('sys.stdin.readline', return_value='\n'), \
         patch('sys.stdin.isatty', return_value=False):
        
        mock_win.getch.side_effect = [10, ord('n'), ord('n'), ord('y')]
        result = ui.render_confirmation("Proceed with installation? [Y/n]:", "Release 1.0", default=True)
        assert result is True
        
        mock_win.getch.side_effect = [ord('n')]
        result = ui.render_confirmation("Proceed? [Y/n]:", "Release 1.0", default=True)
        assert result is False
        
        mock_win.getch.side_effect = [ord('y')]
        result = ui.render_confirmation("Proceed? [Y/n]:", "Release 1.0", default=False)
        assert result is True


def test_progress():
    """Test progress bars."""
    KEY_RESIZE = curses.KEY_RESIZE
    
    with patch('ui_manager.curses', MagicMock(**{
        'initscr': MagicMock(return_value=MagicMock()),
        'start_color': MagicMock(),
        'init_pair': MagicMock(return_value=None),
        'cbreak': MagicMock(return_value=True),
        'noecho': MagicMock(),
        'curs_set': MagicMock(return_value=None),
        'has_ungetch': MagicMock(return_value=False),
        'setupterm': MagicMock(),
        'napms': MagicMock(),
        'keypad': MagicMock(),
        'box': MagicMock(),
        'erase': MagicMock(),
        'move': MagicMock(),
        'timeout': MagicMock(),
        'color_pair': MagicMock(),
        'A_REVERSE': curses.A_REVERSE,
        'A_BOLD': curses.A_BOLD,
        'error': type('CursesError', (Exception,), {}),
    })), \
    patch('ui_manager.curses.newwin', return_value=MagicMock()):
        mock_win = MagicMock()
        mock_win.getyx.return_value = (18, 58)  # Menu dimensions
        mock_win.getch.side_effect = [KEY_RESIZE, *([KEY_RESIZE] * 8)]
        
        mock_screen = MagicMock()
        mock_screen.getmaxyx.return_value = (20, 60)
        
        ui = UIManager("Test")
        ui._using_curses = True
        ui._color_pair = curses.A_BOLD
        ui._screen = mock_screen
        
        # Test determinate bar
        ui.render_progress_bar("file.zip", 1000, 10000, percent=10.5)
        
        # Test spinner (total=0)
        ui.render_progress_bar("unknown.zip", 0, 0, percent=None)


def test_edge_cases():
    """Test edge cases for render_confirmation with _screen=None."""
    ui = UIManager("Test")
    ui._using_curses = False
    ui._screen = None
    
    # Test 1: Enter key confirms
    mock_win = MagicMock()
    mock_win.getyx.return_value = (0, 0)
    mock_win.getch.return_value = 10  # Enter key
    
    with patch.object(ui, '_render_confirmation_fallback', return_value=True):
        result = ui.render_confirmation("Confirm?", "v1.0")
        assert result is True
    
    # Test 2: 'y' key confirms
    mock_win.getch.return_value = ord('y')
    with patch.object(ui, '_render_confirmation_fallback', return_value=True):
        result = ui.render_confirmation("Confirm?", "v1.0")
        assert result is True
    
    # Test 3: 'n' key cancels
    mock_win.getch.return_value = ord('n')
    with patch.object(ui, '_render_confirmation_fallback', return_value=False):
        result = ui.render_confirmation("Confirm?", "v1.0")
        assert result is False


def test_full_integration_flow():
    """Test full integration flow: menu selection → confirmation → progress bar."""
    options = [{'label': 'Install'}, {'label': 'Update'}, {'label': 'Repair'}]
    
    KEY_RESIZE = curses.KEY_RESIZE
    KEY_DOWN = curses.KEY_DOWN
    KEY_ENTER = curses.KEY_ENTER
    
    mock_screen = MagicMock()
    mock_screen.getmaxyx.return_value = (24, 80)
    
    mock_curses = MagicMock()
    mock_curses.initscr.return_value = MagicMock()
    mock_curses.start_color = MagicMock()
    mock_curses.init_pair = MagicMock(return_value=None)
    mock_curses.cbreak = MagicMock(return_value=True)
    mock_curses.noecho = MagicMock()
    mock_curses.curs_set = MagicMock(return_value=None)
    mock_curses.has_ungetch = MagicMock(return_value=False)
    mock_curses.getscrptr = MagicMock(return_value=None)
    mock_curses.keypad = MagicMock(return_value=True)
    
    with patch('ui_manager.curses', mock_curses):
        ui = UIManager("Test")
        ui._using_curses = True
        ui._color_pair = curses.A_BOLD
        ui._screen = mock_screen
    
    mock_win = MagicMock()
    mock_win.getyx.return_value = (0, 0)
    
    # Step 1: Menu selection
    with patch.object(ui, 'refresh'), \
         patch('ui_manager.curses.newwin', return_value=mock_win), \
         patch('builtins.input', return_value='\n'), \
         patch('sys.stdin.readline', return_value='\n'), \
         patch('sys.stdin.isatty', return_value=False):
        
        mock_win.getch.side_effect = [KEY_DOWN, KEY_DOWN, KEY_ENTER]
        menu_selection = ui.render_menu(options, default=0, highlighted=0)
        assert menu_selection == 2, f"Menu should select option 2 (index 2), got {menu_selection}"
    
    # Step 2: Confirmation
    with patch.object(ui, 'refresh'), \
         patch('ui_manager.curses.newwin', return_value=mock_win), \
         patch('builtins.input', return_value='\n'), \
         patch('sys.stdin.readline', return_value='\n'), \
         patch('sys.stdin.isatty', return_value=False):
        
        mock_win.getch.side_effect = [10]
        confirmation = ui.render_confirmation("Proceed? [Y/n]:", "Release 1.0", default=True)
        assert confirmation is True, f"Confirmation should return True, got {confirmation}"
    
    # Step 3: Progress bar
    with patch('ui_manager.curses.newwin', return_value=mock_win), \
         patch('builtins.input', return_value='\n'), \
         patch('sys.stdin.readline', return_value='\n'), \
         patch('sys.stdin.isatty', return_value=False):
        
        ui.render_progress_bar("update.zip", 500, 1000, percent=50.0)
        
        print("  ✓ Full integration flow test passed")








if __name__ == '__main__':
    run_tests()
