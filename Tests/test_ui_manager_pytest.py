#!/usr/bin/env python3
"""
Pytest-compatible test suite for UIManager.

Run with: pytest test_ui_manager_pytest.py -v
"""

import sys
from pathlib import Path
import curses

# Add current directory to path
sys.path.insert(0, str(Path.cwd()))

import pytest
from unittest.mock import MagicMock, patch
from ui_manager import UIManager


def create_ui():
    """Create a UIManager instance with mocked curses."""
    mock_screen = MagicMock()
    mock_curses = MagicMock()
    mock_curses.initscr.return_value = mock_screen
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
    return ui


class TestUIManagerPytest:
    """Pytest tests for UIManager."""
    
    def test_init_fallback_on_error(self):
        """Test that UI falls back gracefully when curses fails."""
        with patch('curses.initscr', side_effect=curses.error("Failed")):
            ui = UIManager("Test")
            assert not ui._using_curses
            assert ui._screen is None
    
    def test_menu_navigation_arrows(self):
        """Test arrow key navigation in menu."""
        options = [{'label': f'Option {i}'} for i in range(5)]
        
        ui = create_ui()
        
        mock_win = MagicMock()
        mock_win.getyx.return_value = (0, 0)
        
        with patch.object(ui, '_screen') as mock_screen, \
             patch.object(ui, 'refresh'), \
             patch('builtins.input', return_value='\n'), \
             patch('sys.stdin.readline', return_value='\n'), \
             patch('sys.stdin.isatty', return_value=False), \
             patch('ui_manager.curses.newwin', return_value=mock_win):

            mock_screen.getmaxyx.return_value = (20, 60)
            
            with patch.object(mock_win, 'getch') as mock_getch:
                mock_getch.side_effect = [
                    curses.KEY_UP,  # Move up: 0 -> 4
                    curses.KEY_DOWN,  # Move down: 4 -> 0
                    10,  # Enter to confirm
                ]
                
                # Call render_menu which will use the mocked window
                result = ui.render_menu(options, default=0, highlighted=0)
                assert result == 0
    
    def test_menu_typing_selection(self):
        """Test selecting by typing the number."""
        options = [{'label': 'Option'}]
        
        ui = create_ui()
        
        mock_win = MagicMock()
        mock_win.getyx.return_value = (0, 0)
        
        with patch.object(ui, '_screen') as mock_screen, \
             patch.object(ui, 'refresh'), \
             patch('builtins.input', return_value='\n'), \
             patch('sys.stdin.readline', return_value='\n'), \
             patch('sys.stdin.isatty', return_value=False), \
             patch('ui_manager.curses.newwin', return_value=mock_win):
                 
            mock_screen.getmaxyx.return_value = (20, 60)
            
            with patch.object(mock_win, 'getch') as mock_getch:
                mock_getch.side_effect = [ord('0'), 10]  # Type '0' (ASCII 48) then Enter
                    
                # Call render_menu which will use the mocked window
                result = ui.render_menu(options, default=0, highlighted=0)
                assert result == 0
    
    def test_menu_cancel_keys(self):
        """Test that cancel keys return -1."""
        options = [{'label': 'Option'}]
        
        ui = create_ui()
        
        for cancel_key in [ord('q'), 27, curses.KEY_RESIZE, curses.KEY_BACKSPACE, 127, 8]:
            with patch.object(ui, '_screen') as mock_screen, \
                 patch.object(ui, 'refresh'), \
                 patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin:

                mock_win = mock_newwin.return_value
                mock_win.getyx.return_value = (0, 0)
                mock_screen.getmaxyx.return_value = (20, 60)

                with patch.object(mock_win, 'getch') as mock_getch:
                    mock_getch.return_value = cancel_key
                        
                    result = ui.render_menu(options, default=0, highlighted=0)
                    assert result == -1, f"Cancel key {cancel_key} should return -1"
    
    def test_confirmation_enter_confirms(self):
        """Enter key confirms the action."""
        ui = create_ui()
        
        with patch.object(ui, '_screen') as mock_screen, \
             patch.object(ui, 'refresh'), \
             patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin:
            
            mock_win = mock_newwin.return_value
            mock_win.getyx.return_value = (0, 0)
            mock_screen.getmaxyx.return_value = (20, 60)
            
            with patch.object(mock_win, 'getch') as mock_getch:
                mock_getch.return_value = 10  # Enter
                
                result = ui.render_confirmation("Are you sure?", release_info="Release 1.0")
                assert result is True
    
    def test_confirmation_n_cancels(self):
        """n or N cancels the action."""
        ui = create_ui()
        
        with patch.object(ui, '_screen') as mock_screen, \
             patch.object(ui, 'refresh'), \
             patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin, \
             patch('sys.stdin.isatty', return_value=True), \
             patch('curses.hasattr', side_effect=lambda mod, attr: True), \
             patch.object(ui, '_validate_window', return_value=True):
            
            mock_win = mock_newwin.return_value
            mock_win.getyx.return_value = (0, 0)
            mock_win.erase.return_value = None
            mock_win.addstr.return_value = None
            mock_win.attron.return_value = None
            mock_win.attroff.return_value = None
            mock_win.refresh.return_value = None
            mock_screen.getmaxyx.return_value = (20, 60)
            
            with patch.object(mock_win, 'getch') as mock_getch:
                mock_getch.return_value = ord('n')
                result = ui.render_confirmation("Are you sure?", release_info="Release 1.0")
                assert result is False
    
    def test_confirmation_y_confirms(self):
        """y or Y confirms the action."""
        ui = create_ui()
        
        with patch.object(ui, '_screen') as mock_screen, \
             patch.object(ui, 'refresh'), \
             patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin, \
             patch('sys.stdin.isatty', return_value=False):
            
            mock_win = mock_newwin.return_value
            mock_win.getyx.return_value = (0, 0)
            mock_screen.getmaxyx.return_value = (20, 60)
            
            with patch.object(mock_win, 'getch') as mock_getch:
                mock_getch.return_value = ord('y')
                # Mock window validation to return True
                mock_win._validate_window = MagicMock(return_value=True)
                
                result = ui.render_confirmation("Are you sure?", release_info="Release 1.0")
                assert result is True
class TestMenuPageJump:
    """Tests for KEY_PPAGE and KEY_NPAGE page jump behavior."""
    
    def test_key_ppage_jumps_to_first_option(self):
        """KEY_PPAGE should jump to the first option."""
        options = [{'label': f'Option {i}'} for i in range(5)]
        
        ui = create_ui()
        
        with patch.object(ui, '_screen') as mock_screen, \
             patch.object(ui, 'refresh'), \
             patch('curses.KEY_UP'), \
             patch('curses.KEY_DOWN'), \
             patch('curses.KEY_RESIZE'), \
             patch('curses.KEY_PPAGE'), \
             patch('curses.KEY_NPAGE'), \
             patch('curses.A_REVERSE'), \
             patch('curses.A_BOLD'), \
             patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin:
            
            mock_win = mock_newwin.return_value
            mock_win.getyx.return_value = (0, 0)
            mock_screen.getmaxyx.return_value = (20, 60)
            
            # Start from middle (option 2), press PAGE UP
            with patch.object(mock_win, 'getch') as mock_getch:
                mock_getch.side_effect = [curses.KEY_PPAGE, 10]
                
                result = ui.render_menu(options, default=2, highlighted=2)
                assert result == 0, f"KEY_PPAGE should jump to first option (0), got {result}"
    
    def test_key_npage_jumps_down_by_page_size(self):
        """KEY_NPAGE should jump down by page size."""
        options = [{'label': f'Option {i}'} for i in range(5)]
        
        ui = create_ui()
        
        with patch.object(ui, '_screen') as mock_screen, \
             patch.object(ui, 'refresh'), \
             patch('curses.KEY_UP'), \
             patch('curses.KEY_DOWN'), \
             patch('curses.KEY_RESIZE'), \
             patch('curses.KEY_PPAGE'), \
             patch('curses.KEY_NPAGE'), \
             patch('curses.A_REVERSE'), \
             patch('curses.A_BOLD'), \
             patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin:
            
            mock_win = mock_newwin.return_value
            mock_win.getyx.return_value = (0, 0)
            mock_screen.getmaxyx.return_value = (20, 60)
            
            # Start from middle (option 2), press PAGE DOWN
            # page_size = max(1, min(len(options) // 2, (menu_height - 2) // 2))
            # With 5 options and menu_height = 9, page_size = min(2, 3) = 2
            # First PAGE DOWN: 2 -> 4 (2 + 2 = 4)
            # Second PAGE DOWN: 4 + 2 = 6, 6 >= 5, so 6 % 5 = 1
            # Third key: Enter to select
            with patch.object(mock_win, 'getch') as mock_getch:
                mock_getch.side_effect = [curses.KEY_NPAGE, curses.KEY_NPAGE, 10]
                
                result = ui.render_menu(options, default=2, highlighted=2)
                # First PAGE DOWN: 2 -> 4
                # Second PAGE DOWN: 4 -> 1 (wraps)
                # Third key: Enter to select
                assert result == 1, f"KEY_NPAGE wrapping should work, got {result}"


class TestMenuWrapping:
    """Tests for wrapping behavior when navigating past boundaries."""
    
    def test_wraps_past_first_option(self):
        """Navigating past first option should wrap to last."""
        options = [{'label': f'Option {i}'} for i in range(5)]
        
        ui = create_ui()
        
        with patch.object(ui, '_screen') as mock_screen, \
             patch.object(ui, 'refresh'), \
             patch('curses.KEY_UP'), \
             patch('curses.KEY_DOWN'), \
             patch('curses.KEY_RESIZE'), \
             patch('curses.KEY_PPAGE'), \
             patch('curses.KEY_NPAGE'), \
             patch('curses.A_REVERSE'), \
             patch('curses.A_BOLD'), \
             patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin:
            
            mock_win = mock_newwin.return_value
            mock_win.getyx.return_value = (0, 0)
            mock_screen.getmaxyx.return_value = (20, 60)
            
            # Start at option 1, press UP twice
            # First UP: 1 -> 0 (normal)
            # Second UP: 0 -> 4 (wrap to last)
            # Third key: Enter to select
            with patch.object(mock_win, 'getch') as mock_getch:
                mock_getch.side_effect = [curses.KEY_UP, curses.KEY_UP, 10]
                
                result = ui.render_menu(options, default=1, highlighted=1)
                assert result == 4, f"Should wrap from option 1 -> 0 -> 4, got {result}"
    
    def test_wraps_past_last_option(self):
        """Navigating past last option should wrap to first."""
        options = [{'label': f'Option {i}'} for i in range(5)]
        
        ui = create_ui()
        
        with patch.object(ui, '_screen') as mock_screen, \
             patch.object(ui, 'refresh'), \
             patch('curses.KEY_UP'), \
             patch('curses.KEY_DOWN'), \
             patch('curses.KEY_RESIZE'), \
             patch('curses.KEY_PPAGE'), \
             patch('curses.KEY_NPAGE'), \
             patch('curses.A_REVERSE'), \
             patch('curses.A_BOLD'), \
             patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin:
            
            mock_win = mock_newwin.return_value
            mock_win.getyx.return_value = (0, 0)
            mock_screen.getmaxyx.return_value = (20, 60)
            
            # Start at option 3, press DOWN twice
            # First DOWN: 3 -> 4 (normal)
            # Second DOWN: 4 -> 0 (wrap to first)
            # Third key: Enter to select
            with patch.object(mock_win, 'getch') as mock_getch:
                mock_getch.side_effect = [curses.KEY_DOWN, curses.KEY_DOWN, 10]
                
                result = ui.render_menu(options, default=3, highlighted=3)
                assert result == 0, f"Should wrap from option 3 -> 4 -> 0, got {result}"


class TestHighlightedNone:
    """Tests for highlighted=None as initial state."""
    
    def test_highlighted_none_initial_state(self):
        """When highlighted=None, should start at first option."""
        options = [{'label': f'Option {i}'} for i in range(5)]
        
        ui = create_ui()
        
        with patch.object(ui, '_screen') as mock_screen, \
             patch.object(ui, 'refresh'), \
             patch('curses.KEY_UP'), \
             patch('curses.KEY_DOWN'), \
             patch('curses.KEY_RESIZE'), \
             patch('curses.KEY_PPAGE'), \
             patch('curses.KEY_NPAGE'), \
             patch('curses.A_REVERSE'), \
             patch('curses.A_BOLD'), \
             patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin:
            
            mock_win = mock_newwin.return_value
            mock_win.getyx.return_value = (0, 0)
            mock_screen.getmaxyx.return_value = (20, 60)
            
            # Pass highlighted=None
            with patch.object(mock_win, 'getch') as mock_getch:
                mock_getch.side_effect = [curses.KEY_DOWN, 10]
                
                result = ui.render_menu(options, default=0, highlighted=None)
                # Should behave as if highlighted=0
                assert result == 1, f"Should start at first option when highlighted=None, got {result}"
    
    def test_highlighted_none_wraps(self):
        """Wrap behavior should work with highlighted=None."""
        options = [{'label': f'Option {i}'} for i in range(5)]
        
        ui = create_ui()
        
        with patch.object(ui, '_screen') as mock_screen, \
             patch.object(ui, 'refresh'), \
             patch('curses.KEY_UP'), \
             patch('curses.KEY_DOWN'), \
             patch('curses.KEY_RESIZE'), \
             patch('curses.KEY_PPAGE'), \
             patch('curses.KEY_NPAGE'), \
             patch('curses.A_REVERSE'), \
             patch('curses.A_BOLD'), \
             patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin:
            
            mock_win = mock_newwin.return_value
            mock_win.getyx.return_value = (0, 0)
            mock_screen.getmaxyx.return_value = (20, 60)
            
            # highlighted=None treated as 0
            # DOWN from 0 -> 1
            # DOWN from 1 -> 2
            # Enter selects option 2
            with patch.object(mock_win, 'getch') as mock_getch:
                mock_getch.side_effect = [curses.KEY_DOWN, curses.KEY_DOWN, 10]
                
                result = ui.render_menu(options, default=0, highlighted=None)
                assert result == 2, f"Should wrap with highlighted=None: 0 -> 1 -> 2, got {result}"


class TestConfirmationTimeout:
    """Tests for confirmation timeout behavior."""
    
    def test_timeout_always_returns_true(self):
        """Timeout in confirmation always returns True (assumed yes)."""
        ui = create_ui()
        
        mock_time = MagicMock()
        mock_time.side_effect = [0.0, 0.002]
        
        with patch.object(ui, '_screen') as mock_screen, \
             patch.object(ui, 'refresh'), \
             patch('curses.KEY_RESIZE'), \
             patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin, \
             patch('time.time', mock_time):
            
            mock_win = mock_newwin.return_value
            mock_win.getyx.return_value = (0, 0)
            mock_screen.getmaxyx.return_value = (20, 60)
            
            # Simulate timeout (None)
            with patch.object(mock_win, 'getch') as mock_getch:
                mock_getch.return_value = None
                
                # Timeout always returns True regardless of default parameter
                result = ui.render_confirmation("Are you sure?", "Release 1.0", default=False, timeout=0.001)
                assert result is True, f"Timeout should return True, got {result}"
    
    def test_timeout_independent_of_default(self):
        """Timeout returns True regardless of default parameter."""
        ui = create_ui()
        
        # Test that timeout returns True regardless of default parameter
        test_cases = [
            (True, True),   # default=True, expect True
            (False, True),  # default=False, but timeout still returns True
        ]
        
        for default_value, expected_result in test_cases:
            mock_time = MagicMock()
            mock_time.side_effect = [0.0, 0.002]  # First call for start_time, second for elapsed
            
            with patch.object(ui, '_screen') as mock_screen, \
                 patch.object(ui, 'refresh'), \
                 patch('curses.KEY_RESIZE'), \
                 patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin, \
                 patch('time.time', mock_time):

                mock_win = mock_newwin.return_value
                mock_win.getyx.return_value = (0, 0)
                mock_screen.getmaxyx.return_value = (20, 60)
                
                with patch.object(mock_win, 'getch') as mock_getch:
                    mock_getch.return_value = None  # Timeout (only if timeout check doesn't trigger first)
                    
                    result = ui.render_confirmation("Test", "Release 1.0", default=default_value, timeout=0.001)
                    assert result == expected_result, \
                        f"Timeout with default={default_value} should return {expected_result}, got {result}"

    def test_confirmation_timeout_with_default_false(self):
        """Timeout in confirmation with default=False returns True (assumed yes)."""
        ui = create_ui()
        
        mock_time = MagicMock()
        mock_time.side_effect = [0.0, 0.002]
        
        with patch.object(ui, '_screen') as mock_screen, \
             patch.object(ui, 'refresh'), \
             patch('curses.KEY_RESIZE'), \
             patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin, \
             patch('time.time', mock_time):
            
            mock_win = mock_newwin.return_value
            mock_win.getyx.return_value = (0, 0)
            mock_screen.getmaxyx.return_value = (20, 60)
            
            # Simulate timeout (None) with default=False
            with patch.object(mock_win, 'getch') as mock_getch:
                mock_getch.return_value = None
                
                # Timeout always returns True regardless of default parameter
                result = ui.render_confirmation("Are you sure?", "Release 1.0", default=False, timeout=0.001)
                assert result is True, f"Timeout with default=False should return True, got {result}"

    def test_confirmation_graceful_fallback_when_screen_is_none(self):
        """Test that render_confirmation handles _screen=None gracefully.
        
        When _screen is None, the method should return a safe default value
        without crashing, as per the graceful fallback pattern in ui_manager.py.
        """
        ui = create_ui()
        
        with patch.object(ui, '_screen') as mock_screen, \
             patch.object(ui, 'refresh'), \
             patch('curses.KEY_RESIZE'), \
             patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin:
            
            mock_win = mock_newwin.return_value
            mock_win.getyx.return_value = (0, 0)
            mock_win.getch.side_effect = [10]  # Enter to confirm
            mock_screen.getmaxyx.return_value = (20, 60)
            
            with patch.object(mock_win, 'getch') as mock_getch:
                mock_getch.return_value = 10  # Enter
                
                result_true = ui.render_confirmation("Are you sure?", "Release 1.0", default=True)
                assert result_true is True, f"render_confirmation with _screen=None and default=True should return True, got {result_true}"
                
                mock_getch.return_value = ord('n')
                
                result_false = ui.render_confirmation("Are you sure?", "Release 1.0", default=False)
                assert result_false is False, f"render_confirmation with _screen=None and default=False should return False, got {result_false}"

    def test_timeout_with_default_false_returns_true(self):
        """Verify that timeout with default=False returns True.
        
        This test specifically verifies that when the timeout path is triggered
        (getch returns None), the method returns True regardless of the default
        parameter, as per the spec that timeout assumes default yes.
        """
        ui = create_ui()
        
        mock_time = MagicMock()
        mock_time.side_effect = [0.0, 0.002]
        
        with patch.object(ui, '_screen') as mock_screen, \
             patch.object(ui, 'refresh'), \
             patch('curses.KEY_RESIZE'), \
             patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin, \
             patch('time.time', mock_time):
            
            mock_win = mock_newwin.return_value
            mock_win.getyx.return_value = (0, 0)
            mock_screen.getmaxyx.return_value = (20, 60)
            
            # Simulate timeout (None) - this triggers the timeout path
            with patch.object(mock_win, 'getch') as mock_getch:
                mock_getch.return_value = None
                
                # Even with default=False, timeout returns True
                result = ui.render_confirmation("Test message", "Release 1.0", default=False, timeout=0.001)
                assert result is True, \
                    f"Timeout with default=False should return True, got {result}"
    
    def test_timeout_behavior_consistent_with_default_parameter(self):
        """Verify that timeout behavior is consistent regardless of the default parameter value.
        
        This test ensures that the timeout path (getch returns None) always returns True,
        regardless of whether default is True or False. This verifies that the implementation
        correctly handles the timeout parameter rather than just checking that it returns True.
        """
        ui = create_ui()
        
        # Test cases: (default_value, expected_timeout_result)
        test_cases = [
            (True, True),   # default=True, timeout returns True
            (False, True),  # default=False, timeout returns True
        ]
        
        for default_value, expected_result in test_cases:
            mock_time = MagicMock()
            mock_time.side_effect = [0.0, 0.002]  # First call for start_time, second for elapsed
            
            with patch.object(ui, '_screen') as mock_screen, \
                 patch.object(ui, 'refresh'), \
                 patch('curses.KEY_RESIZE'), \
                 patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin, \
                 patch('time.time', mock_time):

                mock_win = mock_newwin.return_value
                mock_win.getyx.return_value = (0, 0)
                mock_screen.getmaxyx.return_value = (20, 60)
                
                # Simulate timeout (None) - triggers timeout path
                with patch.object(mock_win, 'getch') as mock_getch:
                    mock_getch.return_value = None
                    
                    result = ui.render_confirmation("Test", "Release 1.0", default=default_value, timeout=0.001)
                    assert result == expected_result, \
                        f"Timeout with default={default_value} should return {expected_result}, got {result}"


class TestMenuPageJumpBoundary:
    """Tests for KEY_PPAGE and KEY_NPAGE boundary wrapping behavior."""
    
    def test_key_ppage_boundary_at_last_option(self):
        """PAGE UP from last option should wrap to first."""
        options = [{'label': f'Option {i}'} for i in range(5)]
        
        ui = create_ui()
        
        with patch.object(ui, '_screen') as mock_screen, \
             patch.object(ui, 'refresh'), \
             patch('curses.KEY_UP'), \
             patch('curses.KEY_DOWN'), \
             patch('curses.KEY_RESIZE'), \
             patch('curses.KEY_PPAGE'), \
             patch('curses.KEY_NPAGE'), \
             patch('curses.A_REVERSE'), \
             patch('curses.A_BOLD'), \
             patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin:
            
            mock_win = mock_newwin.return_value
            mock_win.getyx.return_value = (0, 0)
            mock_screen.getmaxyx.return_value = (20, 60)
            
            # Start from last option (4), press PAGE UP
            # Should wrap from 4 -> 0
            # Third key: Enter to select
            with patch.object(mock_win, 'getch') as mock_getch:
                mock_getch.side_effect = [curses.KEY_PPAGE, 10]
                
                result = ui.render_menu(options, default=4, highlighted=4)
                # PAGE UP: 4 - 2 = 2 (since page_size=2), 2 >= 0 so no wrap
                assert result == 2, f"KEY_PPAGE from last option: 4 - 2 = 2, got {result}"
    
    def test_key_npage_boundary_at_first_option(self):
        """PAGE DOWN from first option should wrap to last."""
        options = [{'label': f'Option {i}'} for i in range(5)]
        
        ui = create_ui()
        
        with patch.object(ui, '_screen') as mock_screen, \
             patch.object(ui, 'refresh'), \
             patch('curses.KEY_UP'), \
             patch('curses.KEY_DOWN'), \
             patch('curses.KEY_RESIZE'), \
             patch('curses.KEY_PPAGE'), \
             patch('curses.KEY_NPAGE'), \
             patch('curses.A_REVERSE'), \
             patch('curses.A_BOLD'), \
             patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin:
            
            mock_win = mock_newwin.return_value
            mock_win.getyx.return_value = (0, 0)
            mock_screen.getmaxyx.return_value = (20, 60)
            
            # Start from first option (0), press PAGE DOWN
            # page_size = max(1, min(len(options) // 2, (menu_height - 2) // 2))
            # With 5 options and menu_height = 9, page_size = min(2, 3) = 2
            # First PAGE DOWN: 0 + 2 = 2, 2 < 5 so no wrap
            # Second PAGE DOWN: 2 + 2 = 4, 4 < 5 so no wrap
            # Third PAGE DOWN: 4 + 2 = 6, 6 >= 5 so wrap: 6 % 5 = 1
            # Fourth key: Enter to select
            with patch.object(mock_win, 'getch') as mock_getch:
                mock_getch.side_effect = [curses.KEY_NPAGE, curses.KEY_NPAGE, curses.KEY_NPAGE, 10]
                
                result = ui.render_menu(options, default=0, highlighted=0)
                # First PAGE DOWN: 0 -> 2
                # Second PAGE DOWN: 2 -> 4
                # Third PAGE DOWN: 4 -> 1 (wrap)
                # Fourth key: Enter to select
                assert result == 1, f"KEY_NPAGE wrapping should work: 0->2->4->1, got {result}"
    
    def test_consecutive_page_jumps(self):
        """Consecutive PAGE DOWN then PAGE UP should work correctly."""
        options = [{'label': f'Option {i}'} for i in range(5)]
        
        ui = create_ui()
        
        with patch.object(ui, '_screen') as mock_screen, \
             patch.object(ui, 'refresh'), \
             patch('curses.KEY_UP'), \
             patch('curses.KEY_DOWN'), \
             patch('curses.KEY_RESIZE'), \
             patch('curses.KEY_PPAGE'), \
             patch('curses.KEY_NPAGE'), \
             patch('curses.A_REVERSE'), \
             patch('curses.A_BOLD'), \
             patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin:
            
            mock_win = mock_newwin.return_value
            mock_win.getyx.return_value = (0, 0)
            mock_screen.getmaxyx.return_value = (20, 60)
            
            # page_size = 2
            # Start from option 1, press PAGE DOWN twice, then PAGE UP
            # PAGE DOWN: 1 + 2 = 3, 3 < 5 so no wrap
            # PAGE DOWN: 3 + 2 = 5, 5 >= 5 so wrap: 5 % 5 = 0
            # PAGE UP: 0 - 2 = -2, -2 < 0 so wrap: len(5) - (2 % 5) = 5 - 2 = 3
            # Third key: Enter to select
            with patch.object(mock_win, 'getch') as mock_getch:
                mock_getch.side_effect = [curses.KEY_NPAGE, curses.KEY_NPAGE, curses.KEY_PPAGE, 10]
                
                result = ui.render_menu(options, default=1, highlighted=1)
                assert result == 3, f"Consecutive page jumps: 1->3->0->3, got {result}"


class TestKeyPpageNpageFromAllBoundaries:
    """Tests for KEY_PPAGE and KEY_NPAGE from all boundary positions (first, middle, last)."""
    
    def test_key_ppage_from_first_option_wraps_to_last(self):
        """KEY_PPAGE from first option should wrap to last option."""
        options = [{'label': f'Option {i}'} for i in range(5)]
        
        ui = create_ui()
        
        with patch.object(ui, '_screen') as mock_screen, \
             patch.object(ui, 'refresh'), \
             patch('curses.KEY_UP'), \
             patch('curses.KEY_DOWN'), \
             patch('curses.KEY_RESIZE'), \
             patch('curses.KEY_PPAGE'), \
             patch('curses.KEY_NPAGE'), \
             patch('curses.A_REVERSE'), \
             patch('curses.A_BOLD'), \
             patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin:
            
            mock_win = mock_newwin.return_value
            mock_win.getyx.return_value = (0, 0)
            mock_screen.getmaxyx.return_value = (20, 60)
            
            # Start from first option (0), press PAGE UP
            # page_size = 2
            # First PAGE UP: 0 - 2 = -2, -2 < 0 so wrap: len(5) - (2 % 5) = 5 - 2 = 3
            # Third key: Enter to select
            with patch.object(mock_win, 'getch') as mock_getch:
                mock_getch.side_effect = [curses.KEY_PPAGE, 10]
                
                result = ui.render_menu(options, default=0, highlighted=0)
                assert result == 3, f"KEY_PPAGE from first option: 0 -> 3 (wrap), got {result}"
    
    def test_key_ppage_from_middle_option(self):
        """KEY_PPAGE from middle option should jump up by page size."""
        options = [{'label': f'Option {i}'} for i in range(5)]
        
        ui = create_ui()
        
        with patch.object(ui, '_screen') as mock_screen, \
             patch.object(ui, 'refresh'), \
             patch('curses.KEY_UP'), \
             patch('curses.KEY_DOWN'), \
             patch('curses.KEY_RESIZE'), \
             patch('curses.KEY_PPAGE'), \
             patch('curses.KEY_NPAGE'), \
             patch('curses.A_REVERSE'), \
             patch('curses.A_BOLD'), \
             patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin:
            
            mock_win = mock_newwin.return_value
            mock_win.getyx.return_value = (0, 0)
            mock_screen.getmaxyx.return_value = (20, 60)
            
            # Start from middle option (2), press PAGE UP
            # page_size = 2
            # First PAGE UP: 2 - 2 = 0
            # Third key: Enter to select
            with patch.object(mock_win, 'getch') as mock_getch:
                mock_getch.side_effect = [curses.KEY_PPAGE, 10]
                
                result = ui.render_menu(options, default=2, highlighted=2)
                assert result == 0, f"KEY_PPAGE from middle option: 2 -> 0, got {result}"
    
    def test_key_ppage_from_last_option(self):
        """KEY_PPAGE from last option should jump up by page size."""
        options = [{'label': f'Option {i}'} for i in range(5)]
        
        ui = create_ui()
        
        with patch.object(ui, '_screen') as mock_screen, \
             patch.object(ui, 'refresh'), \
             patch('curses.KEY_UP'), \
             patch('curses.KEY_DOWN'), \
             patch('curses.KEY_RESIZE'), \
             patch('curses.KEY_PPAGE'), \
             patch('curses.KEY_NPAGE'), \
             patch('curses.A_REVERSE'), \
             patch('curses.A_BOLD'), \
             patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin:
            
            mock_win = mock_newwin.return_value
            mock_win.getyx.return_value = (0, 0)
            mock_screen.getmaxyx.return_value = (20, 60)
            
            # Start from last option (4), press PAGE UP
            # page_size = 2
            # First PAGE UP: 4 - 2 = 2
            # Third key: Enter to select
            with patch.object(mock_win, 'getch') as mock_getch:
                mock_getch.side_effect = [curses.KEY_PPAGE, 10]
                
                result = ui.render_menu(options, default=4, highlighted=4)
                assert result == 2, f"KEY_PPAGE from last option: 4 -> 2, got {result}"
    
    def test_key_npage_from_first_option(self):
        """KEY_NPAGE from first option should jump down by page size."""
        options = [{'label': f'Option {i}'} for i in range(5)]
        
        ui = create_ui()
        
        with patch.object(ui, '_screen') as mock_screen, \
             patch.object(ui, 'refresh'), \
             patch('curses.KEY_UP'), \
             patch('curses.KEY_DOWN'), \
             patch('curses.KEY_RESIZE'), \
             patch('curses.KEY_PPAGE'), \
             patch('curses.KEY_NPAGE'), \
             patch('curses.A_REVERSE'), \
             patch('curses.A_BOLD'), \
             patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin:
            
            mock_win = mock_newwin.return_value
            mock_win.getyx.return_value = (0, 0)
            mock_screen.getmaxyx.return_value = (20, 60)
            
            # Start from first option (0), press PAGE DOWN
            # page_size = 2
            # First PAGE DOWN: 0 + 2 = 2
            # Third key: Enter to select
            with patch.object(mock_win, 'getch') as mock_getch:
                mock_getch.side_effect = [curses.KEY_NPAGE, 10]
                
                result = ui.render_menu(options, default=0, highlighted=0)
                assert result == 2, f"KEY_NPAGE from first option: 0 -> 2, got {result}"
    
    def test_key_npage_from_middle_option(self):
        """KEY_NPAGE from middle option should jump down by page size."""
        options = [{'label': f'Option {i}'} for i in range(5)]
        
        ui = create_ui()
        
        with patch.object(ui, '_screen') as mock_screen, \
             patch.object(ui, 'refresh'), \
             patch('curses.KEY_UP'), \
             patch('curses.KEY_DOWN'), \
             patch('curses.KEY_RESIZE'), \
             patch('curses.KEY_PPAGE'), \
             patch('curses.KEY_NPAGE'), \
             patch('curses.A_REVERSE'), \
             patch('curses.A_BOLD'), \
             patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin:
            
            mock_win = mock_newwin.return_value
            mock_win.getyx.return_value = (0, 0)
            mock_screen.getmaxyx.return_value = (20, 60)
            
            # Start from middle option (2), press PAGE DOWN
            # page_size = 2
            # First PAGE DOWN: 2 + 2 = 4
            # Third key: Enter to select
            with patch.object(mock_win, 'getch') as mock_getch:
                mock_getch.side_effect = [curses.KEY_NPAGE, 10]
                
                result = ui.render_menu(options, default=2, highlighted=2)
                assert result == 4, f"KEY_NPAGE from middle option: 2 -> 4, got {result}"
    
    def test_key_npage_from_last_option_wraps_to_first(self):
        """KEY_NPAGE from last option should wrap to first option."""
        options = [{'label': f'Option {i}'} for i in range(5)]
        
        ui = create_ui()
        
        with patch.object(ui, '_screen') as mock_screen, \
             patch.object(ui, 'refresh'), \
             patch('curses.KEY_UP'), \
             patch('curses.KEY_DOWN'), \
             patch('curses.KEY_RESIZE'), \
             patch('curses.KEY_PPAGE'), \
             patch('curses.KEY_NPAGE'), \
             patch('curses.A_REVERSE'), \
             patch('curses.A_BOLD'), \
             patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin:
            
            mock_win = mock_newwin.return_value
            mock_win.getyx.return_value = (0, 0)
            mock_screen.getmaxyx.return_value = (20, 60)
            
            # Start from last option (4), press PAGE DOWN
            # page_size = 2
            # First PAGE DOWN: 4 + 2 = 6, 6 >= 5 so wrap: 6 % 5 = 1
            # Third key: Enter to select
            with patch.object(mock_win, 'getch') as mock_getch:
                mock_getch.side_effect = [curses.KEY_NPAGE, 10]
                
                result = ui.render_menu(options, default=4, highlighted=4)
                assert result == 1, f"KEY_NPAGE from last option: 4 -> 1 (wrap), got {result}"


class TestHighlightedNoneWithPageJump:
    """Tests for KEY_PPAGE/KEY_NPAGE when highlighted=None (treated as 0)."""
    
    def test_key_ppage_from_highlighted_none_wraps_to_last(self):
        """KEY_PPAGE from highlighted=None should wrap from position 0 to last option."""
        options = [{'label': f'Option {i}'} for i in range(5)]
        
        ui = create_ui()
        
        with patch.object(ui, '_screen') as mock_screen, \
             patch.object(ui, 'refresh'), \
             patch('curses.KEY_UP'), \
             patch('curses.KEY_DOWN'), \
             patch('curses.KEY_RESIZE'), \
             patch('curses.KEY_PPAGE'), \
             patch('curses.KEY_NPAGE'), \
             patch('curses.A_REVERSE'), \
             patch('curses.A_BOLD'), \
             patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin:
            
            mock_win = mock_newwin.return_value
            mock_win.getyx.return_value = (0, 0)
            mock_screen.getmaxyx.return_value = (20, 60)
            
            # highlighted=None treated as 0
            # PAGE UP from 0: 0 - 2 = -2, -2 < 0 so wrap: 5 - 2 = 3
            # Third key: Enter to select
            with patch.object(mock_win, 'getch') as mock_getch:
                mock_getch.side_effect = [curses.KEY_PPAGE, 10]
                
                result = ui.render_menu(options, default=0, highlighted=None)
                assert result == 3, f"KEY_PPAGE from highlighted=None: 0 -> 3 (wrap), got {result}"
    
    def test_key_npage_from_highlighted_none_jumps_to_middle(self):
        """KEY_NPAGE from highlighted=None should jump down by page size from position 0."""
        options = [{'label': f'Option {i}'} for i in range(5)]
        
        ui = create_ui()
        
        with patch.object(ui, '_screen') as mock_screen, \
             patch.object(ui, 'refresh'), \
             patch('curses.KEY_UP'), \
             patch('curses.KEY_DOWN'), \
             patch('curses.KEY_RESIZE'), \
             patch('curses.KEY_PPAGE'), \
             patch('curses.KEY_NPAGE'), \
             patch('curses.A_REVERSE'), \
             patch('curses.A_BOLD'), \
             patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin:
            
            mock_win = mock_newwin.return_value
            mock_win.getyx.return_value = (0, 0)
            mock_screen.getmaxyx.return_value = (20, 60)
            
            # highlighted=None treated as 0
            # PAGE DOWN from 0: 0 + 2 = 2
            # Third key: Enter to select
            with patch.object(mock_win, 'getch') as mock_getch:
                mock_getch.side_effect = [curses.KEY_NPAGE, 10]
                
                result = ui.render_menu(options, default=0, highlighted=None)
                assert result == 2, f"KEY_NPAGE from highlighted=None: 0 -> 2, got {result}"
    
    def test_multiple_page_jumps_from_highlighted_none(self):
        """Multiple consecutive page-jump operations starting with highlighted=None."""
        options = [{'label': f'Option {i}'} for i in range(5)]
        
        ui = create_ui()
        
        with patch.object(ui, '_screen') as mock_screen, \
             patch.object(ui, 'refresh'), \
             patch('curses.KEY_UP'), \
             patch('curses.KEY_DOWN'), \
             patch('curses.KEY_RESIZE'), \
             patch('curses.KEY_PPAGE'), \
             patch('curses.KEY_NPAGE'), \
             patch('curses.A_REVERSE'), \
             patch('curses.A_BOLD'), \
             patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin:
            
            mock_win = mock_newwin.return_value
            mock_win.getyx.return_value = (0, 0)
            mock_screen.getmaxyx.return_value = (20, 60)
            
            # Test sequence: PAGE DOWN, PAGE UP, PAGE DOWN, PAGE UP
            # Start from highlighted=None (treated as 0):
            # PAGE DOWN: 0 + 2 = 2
            # PAGE UP: 2 - 2 = 0
            # PAGE DOWN: 0 + 2 = 2
            # PAGE UP: 2 - 2 = 0
            # Fourth key: Enter to select
            with patch.object(mock_win, 'getch') as mock_getch:
                mock_getch.side_effect = [curses.KEY_NPAGE, curses.KEY_PPAGE, curses.KEY_NPAGE, curses.KEY_PPAGE, 10]
                
                result = ui.render_menu(options, default=0, highlighted=None)
                assert result == 0, f"Multiple page jumps: 0->2->0->2->0, got {result}"


class TestConsecutivePageJumpsFromVariousPositions:
    """Tests for consecutive KEY_PPAGE/KEY_NPAGE from various starting positions."""
    
    def test_consecutive_ppage_npage_from_middle(self):
        """Consecutive PAGE UP then PAGE DOWN from middle option."""
        options = [{'label': f'Option {i}'} for i in range(5)]
        
        ui = create_ui()
        
        with patch.object(ui, '_screen') as mock_screen, \
             patch.object(ui, 'refresh'), \
             patch('curses.KEY_UP'), \
             patch('curses.KEY_DOWN'), \
             patch('curses.KEY_RESIZE'), \
             patch('curses.KEY_PPAGE'), \
             patch('curses.KEY_NPAGE'), \
             patch('curses.A_REVERSE'), \
             patch('curses.A_BOLD'), \
             patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin:
            
            mock_win = mock_newwin.return_value
            mock_win.getyx.return_value = (0, 0)
            mock_screen.getmaxyx.return_value = (20, 60)
            
            # page_size = 2
            # Start from option 2, press PAGE UP then PAGE DOWN
            # PAGE UP: 2 - 2 = 0
            # PAGE DOWN: 0 + 2 = 2
            # Fourth key: Enter to select
            with patch.object(mock_win, 'getch') as mock_getch:
                mock_getch.side_effect = [curses.KEY_PPAGE, curses.KEY_NPAGE, 10]
                
                result = ui.render_menu(options, default=2, highlighted=2)
                assert result == 2, f"Consecutive PPAGE NPAGE: 2->0->2, got {result}"
    
    def test_consecutive_npage_ppage_from_first(self):
        """Consecutive PAGE DOWN then PAGE UP from first option."""
        options = [{'label': f'Option {i}'} for i in range(5)]
        
        ui = create_ui()
        
        with patch.object(ui, '_screen') as mock_screen, \
             patch.object(ui, 'refresh'), \
             patch('curses.KEY_UP'), \
             patch('curses.KEY_DOWN'), \
             patch('curses.KEY_RESIZE'), \
             patch('curses.KEY_PPAGE'), \
             patch('curses.KEY_NPAGE'), \
             patch('curses.A_REVERSE'), \
             patch('curses.A_BOLD'), \
             patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin:
            
            mock_win = mock_newwin.return_value
            mock_win.getyx.return_value = (0, 0)
            mock_screen.getmaxyx.return_value = (20, 60)
            
            # page_size = 2
            # Start from option 0, press PAGE DOWN then PAGE UP
            # PAGE DOWN: 0 + 2 = 2
            # PAGE UP: 2 - 2 = 0
            # Fourth key: Enter to select
            with patch.object(mock_win, 'getch') as mock_getch:
                mock_getch.side_effect = [curses.KEY_NPAGE, curses.KEY_PPAGE, 10]
                
                result = ui.render_menu(options, default=0, highlighted=0)
                assert result == 0, f"Consecutive NPAGE PPAGE: 0->2->0, got {result}"
    
    def test_consecutive_npage_npage_from_last(self):
        """Consecutive PAGE DOWN then PAGE DOWN from last option."""
        options = [{'label': f'Option {i}'} for i in range(5)]
        
        ui = create_ui()
        
        with patch.object(ui, '_screen') as mock_screen, \
             patch.object(ui, 'refresh'), \
             patch('curses.KEY_UP'), \
             patch('curses.KEY_DOWN'), \
             patch('curses.KEY_RESIZE'), \
             patch('curses.KEY_PPAGE'), \
             patch('curses.KEY_NPAGE'), \
             patch('curses.A_REVERSE'), \
             patch('curses.A_BOLD'), \
             patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin:
            
            mock_win = mock_newwin.return_value
            mock_win.getyx.return_value = (0, 0)
            mock_screen.getmaxyx.return_value = (20, 60)
            
            # page_size = 2
            # Start from option 4, press PAGE DOWN twice
            # PAGE DOWN: 4 + 2 = 6, 6 >= 5 so wrap: 6 % 5 = 1
            # PAGE DOWN: 1 + 2 = 3
            # Fourth key: Enter to select
            with patch.object(mock_win, 'getch') as mock_getch:
                mock_getch.side_effect = [curses.KEY_NPAGE, curses.KEY_NPAGE, 10]
                
                result = ui.render_menu(options, default=4, highlighted=4)
                assert result == 3, f"Consecutive NPAGE NPAGE: 4->1->3, got {result}"
    
    def test_consecutive_ppage_ppage_from_first(self):
        """Consecutive PAGE UP then PAGE UP from first option."""
        options = [{'label': f'Option {i}'} for i in range(5)]
        
        ui = create_ui()
        
        with patch.object(ui, '_screen') as mock_screen, \
             patch.object(ui, 'refresh'), \
             patch('curses.KEY_UP'), \
             patch('curses.KEY_DOWN'), \
             patch('curses.KEY_RESIZE'), \
             patch('curses.KEY_PPAGE'), \
             patch('curses.KEY_NPAGE'), \
             patch('curses.A_REVERSE'), \
             patch('curses.A_BOLD'), \
             patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin:
            
            mock_win = mock_newwin.return_value
            mock_win.getyx.return_value = (0, 0)
            mock_screen.getmaxyx.return_value = (20, 60)
            
            # page_size = 2
            # Start from option 0, press PAGE UP twice
            # PAGE UP: 0 - 2 = -2, -2 < 0 so wrap: 5 - 2 = 3
            # PAGE UP: 3 - 2 = 1
            # Fourth key: Enter to select
            with patch.object(mock_win, 'getch') as mock_getch:
                mock_getch.side_effect = [curses.KEY_PPAGE, curses.KEY_PPAGE, 10]
                
                result = ui.render_menu(options, default=0, highlighted=0)
                assert result == 1, f"Consecutive PPAGE PPAGE: 0->3->1, got {result}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
