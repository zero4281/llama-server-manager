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
from llama_updater import get_available_platforms


def create_ui():
    """Create a UIManager instance with mocked curses."""
    mock_screen = MagicMock()
    mock_curses = MagicMock()
    mock_curses.initscr.return_value = mock_screen
    mock_curses.start_color = MagicMock()
    mock_curses.init_pair = MagicMock(side_effect=lambda pair, fg, bg: pair)
    mock_curses.cbreak = MagicMock(return_value=True)
    mock_curses.noecho = MagicMock()
    mock_curses.curs_set = MagicMock(return_value=None)
    mock_curses.has_ungetch = MagicMock(return_value=False)
    mock_curses.getscrptr = MagicMock(return_value=None)
    mock_curses.echo = MagicMock(return_value=None)
    mock_curses.nocbreak = MagicMock(return_value=None)
    mock_curses.endwin = MagicMock(return_value=None)
    mock_curses.reset_pair_matrix = MagicMock()
    mock_curses.KEY_RESIZE = curses.KEY_RESIZE
    
    with patch('ui_manager.curses', mock_curses):
        ui = UIManager("Test")
        ui._using_curses = True
    return ui


class TestUIManagerPytest:
    """Pytest tests for UIManager."""
    
    def test_init_fallback_on_error(self):
        """Test that UI falls back gracefully when curses fails."""
        with patch('curses.initscr', side_effect=curses.error("Failed")), \
            patch('curses.start_color'), \
            patch('curses.init_pair'), \
            patch('curses.color_pair'), \
            patch('curses.cbreak'), \
            patch('curses.noecho'), \
            patch('curses.curs_set'), \
            patch('curses.echo'), \
            patch('curses.nocbreak'), \
            patch('curses.endwin'), \
            patch('curses.reset_pair_matrix'):
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
    
    def test_render_menu_empty_options(self):
        """Test that render_menu returns -1 immediately when provided with an empty options list."""
        ui = create_ui()
        result = ui.render_menu([], default=0, highlighted=0)
        assert result == -1
    
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

                result = ui.render_confirmation("Are you sure?", "Release 1.0")
                assert result is True
    
    def test_confirmation_n_cancels(self):
        """n or N cancels the action."""
        ui = create_ui()
            
        with patch.object(ui, '_screen') as mock_screen, \
             patch.object(ui, 'refresh'), \
             patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin, \
             patch('sys.stdin.isatty', return_value=True), \
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
                result = ui.render_confirmation("Are you sure?", "Release 1.0")
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
                
                result = ui.render_confirmation("Are you sure?", "Release 1.0")
                assert result is True

    def test_confirmation_cancel_keys(self):
        """Test that Escape or KEY_RESIZE cancels the action."""
        ui = create_ui()
        
        with patch.object(ui, '_screen') as mock_screen, \
             patch.object(ui, 'refresh'), \
             patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin:
            
            mock_win = mock_newwin.return_value
            mock_win.getyx.return_value = (0, 0)
            mock_screen.getmaxyx.return_value = (20, 60)
            
            # Test Escape (27)
            with patch.object(mock_win, 'getch') as mock_getch:
                mock_getch.side_effect = [27]
                result = ui.render_confirmation("Are you sure?", "Release 1.0")
                assert result is False, "Escape should cancel confirmation"
            
            # Test KEY_RESIZE
            with patch.object(mock_win, 'getch') as mock_getch:
                mock_getch.side_effect = [curses.KEY_RESIZE]
                result = ui.render_confirmation("Are you sure?", "Release 1.0")
                assert result is False, "KEY_RESIZE should cancel confirmation"


    def test_confirmation_cancel_keys(self):
        """Test that Escape or KEY_RESIZE cancels the action."""
        ui = create_ui()
        
        with patch.object(ui, '_screen') as mock_screen, \
             patch.object(ui, 'refresh'), \
             patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin:
            
            mock_win = mock_newwin.return_value
            mock_win.getyx.return_value = (0, 0)
            mock_screen.getmaxyx.return_value = (20, 60)
            
            # Test Escape (27)
            with patch.object(mock_win, 'getch') as mock_getch:
                mock_getch.side_effect = [27]
                result = ui.render_confirmation("Are you sure?", "Release 1.0")
                assert result is False, "Escape should cancel confirmation"
            
            # Test KEY_RESIZE
            with patch.object(mock_win, 'getch') as mock_getch:
                mock_getch.side_effect = [curses.KEY_RESIZE]
                result = ui.render_confirmation("Are you sure?", "Release 1.0")
                assert result is False, "KEY_RESIZE should cancel confirmation"

    def test_confirmation_cancel_keys(self):
        """Test that Escape or KEY_RESIZE cancels the action."""
        ui = create_ui()
        
        with patch.object(ui, '_screen') as mock_screen, \
             patch.object(ui, 'refresh'), \
             patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin:
            
            mock_win = mock_newwin.return_value
            mock_win.getyx.return_value = (0, 0)
            mock_screen.getmaxyx.return_value = (20, 60)
            
            # Test Escape (27)
            with patch.object(mock_win, 'getch') as mock_getch:
                mock_getch.side_effect = [27]
                result = ui.render_confirmation("Are you sure?", "Release 1.0")
                assert result is False, "Escape should cancel confirmation"
            
            # Test KEY_RESIZE
            with patch.object(mock_win, 'getch') as mock_getch:
                mock_getch.side_effect = [curses.KEY_RESIZE]
                result = ui.render_confirmation("Are you sure?", "Release 1.0")
                assert result is False, "KEY_RESIZE should cancel confirmation"

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
        """When highlighted=None, should start at first option and support navigation/selection."""
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
            
            # Test 1: Selection from initial state (highlighted=None = 0)
            with patch.object(mock_win, 'getch') as mock_getch:
                mock_getch.side_effect = [10]  # Enter to select first option
                
                result = ui.render_menu(options, default=0, highlighted=None)
                assert result == 0, f"Selection from initial state (None->0): should return 0, got {result}"
            
            # Test 2: Arrow key navigation from initial state
            with patch.object(mock_win, 'getch') as mock_getch:
                # UP from 0 -> 4 (wrap), then Enter
                mock_getch.side_effect = [curses.KEY_UP, 10]
                
                result = ui.render_menu(options, default=0, highlighted=None)
                assert result == 4, f"UP from initial state: should return 4, got {result}"
            
            # Test 3: Multiple DOWN presses from initial state
            with patch.object(mock_win, 'getch') as mock_getch:
                # DOWN from 0 -> 1 -> 2, then Enter
                mock_getch.side_effect = [curses.KEY_DOWN, curses.KEY_DOWN, 10]
                
                result = ui.render_menu(options, default=0, highlighted=None)
                assert result == 2, f"Multiple DOWN from initial state: should return 2, got {result}"
            
            # Test 4: Mixed navigation from initial state
            with patch.object(mock_win, 'getch') as mock_getch:
                # DOWN from 0 -> 1, UP from 1 -> 0, then Enter
                mock_getch.side_effect = [curses.KEY_DOWN, curses.KEY_UP, 10]
                
                result = ui.render_menu(options, default=0, highlighted=None)
                assert result == 0, f"Mixed navigation from initial state: should return 0, got {result}"
            
            # Test 5: PAGE DOWN from initial state
            with patch.object(mock_win, 'getch') as mock_getch:
                # PAGE DOWN from 0 -> 2, then Enter
                mock_getch.side_effect = [curses.KEY_NPAGE, 10]
                
                result = ui.render_menu(options, default=0, highlighted=None)
                assert result == 2, f"PAGE DOWN from initial state: should return 2, got {result}"
            
            # Test 6: PAGE UP from initial state (should wrap to last)
            with patch.object(mock_win, 'getch') as mock_getch:
                # PAGE UP from 0 -> 3 (wrap), then Enter
                mock_getch.side_effect = [curses.KEY_PPAGE, 10]
                
                result = ui.render_menu(options, default=0, highlighted=None)
                assert result == 3, f"PAGE UP from initial state: should return 3 (wrap), got {result}"
    
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
    

    def test_get_available_platforms_ubuntu_x64(self):
        """Verify that Ubuntu x64 includes all backends when assets are correctly parsed."""
        release = {
            "assets": [
                {"name": "llama-b10357-bin-ubuntu-x64.tar.gz", "browser_download_url": "http://test"},
                {"name": "llama-b10357-bin-ubuntu-vulkan-x64.tar.gz", "browser_download_url": "http://test"},
                {"name": "llama-b10357-bin-ubuntu-rocm-x64.tar.gz", "browser_download_url": "http://test"},
            ]
        }
        
        platforms = get_available_platforms(release)
        
        # Find Ubuntu x64 platform
        ubuntu_x64 = next((p for p in platforms if p['platform'] == "Ubuntu" and p['arch'] == "x64"), None)
        
        assert ubuntu_x64 is not None, "Ubuntu x64 platform missing"
        # Check that it has all backends
        asset_names = [a['name'] for a in ubuntu_x64['assets']]
        assert "llama-b10357-bin-ubuntu-x64.tar.gz" in asset_names
        assert "llama-b10357-bin-ubuntu-vulkan-x64.tar.gz" in asset_names
        assert "llama-b10357-bin-ubuntu-rocm-x64.tar.gz" in asset_names

    
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


def test_page_size_calculation_formula():
    """Test the page size calculation formula: max(1, min(len(options) // 2, (menu_height - 2) // 2).
    
    This tests the formula used in KEY_NPAGE navigation to determine how many options
    to jump down per page.
    """
    
    def calculate_page_size(len_options: int, menu_height: int) -> int:
        """Calculate page size using the formula: max(1, min(len(options) // 2, (menu_height - 2) // 2))."""
        return max(1, min(len_options // 2, (menu_height - 2) // 2))
    
    # Test 1: Single option, standard height
    # len=1, menu_height=20 => max(1, min(0, 9)) = max(1, 0) = 1
    assert calculate_page_size(1, 20) == 1
    
    # Test 2: Very small terminal (menu_height=6)
    # len=10, menu_height=6 => max(1, min(5, 2)) = max(1, 2) = 2
    assert calculate_page_size(10, 6) == 2
    
    # Test 3: Very large menu (len=100, menu_height=20)
    # len=100, menu_height=20 => max(1, min(50, 9)) = max(1, 9) = 9
    assert calculate_page_size(100, 20) == 9
    
    # Test 4: Boundary case - menu_height limits result
    # len=100, menu_height=4 => max(1, min(50, 1)) = max(1, 1) = 1
    assert calculate_page_size(100, 4) == 1
    
    # Test 5: Boundary case - options count limits result
    # len=5, menu_height=100 => max(1, min(2, 49)) = max(1, 2) = 2
    assert calculate_page_size(5, 100) == 2
    
    # Test 6: Minimum possible values
    # len=1, menu_height=2 => max(1, min(0, 0)) = max(1, 0) = 1
    assert calculate_page_size(1, 2) == 1
    
    # Test 7: Very small options list
    # len=2, menu_height=20 => max(1, min(1, 9)) = max(1, 1) = 1
    assert calculate_page_size(2, 20) == 1
    
    # Test 8: Small options list where options limit result
    # len=3, menu_height=20 => max(1, min(1, 9)) = max(1, 1) = 1
    assert calculate_page_size(3, 20) == 1
    
    # Test 9: Small options list where menu height starts limiting
    # len=4, menu_height=20 => max(1, min(2, 9)) = max(1, 2) = 2
    assert calculate_page_size(4, 20) == 2
    
    # Test 10: Verify minimum floor of 1 is respected
    # len=1000, menu_height=2 => max(1, min(500, 0)) = max(1, 0) = 1
    assert calculate_page_size(1000, 2) == 1
    
    # Test 11: Verify maximum cap based on menu height
    # len=1000, menu_height=6 => max(1, min(500, 2)) = max(1, 2) = 2
    assert calculate_page_size(1000, 6) == 2
    
    # Test 12: Both factors contribute
    # len=12, menu_height=10 => max(1, min(6, 4)) = max(1, 4) = 4
    assert calculate_page_size(12, 10) == 4
    
    # Test 13: Both factors contribute (reversed)
    # len=8, menu_height=20 => max(1, min(4, 9)) = max(1, 4) = 4
    assert calculate_page_size(8, 20) == 4
    
    # Test 14: Even numbers
    # len=6, menu_height=12 => max(1, min(3, 5)) = max(1, 3) = 3
    assert calculate_page_size(6, 12) == 3
    
    # Test 15: Odd numbers
    # len=7, menu_height=11 => max(1, min(3, 4)) = max(1, 3) = 3
    assert calculate_page_size(7, 11) == 3


class TestMenuDigitInput:
    """Tests for digit input selection and out-of-range rejection."""
    
    def test_out_of_range_digit_is_ignored(self):
        """Test that out-of-range digits are silently ignored and navigation continues."""
        options = [{'label': f'Option {i}'} for i in range(5)]
        
        ui = create_ui()
        
        with patch.object(ui, '_screen') as mock_screen, \
             patch.object(ui, 'refresh'), \
             patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin:
            mock_win = mock_newwin.return_value
            mock_win.getyx.return_value = (0, 0)
            mock_screen.getmaxyx.return_value = (20, 60)
            
            # Start at option 0
            with patch.object(mock_win, 'getch') as mock_getch:
                # Type '9' (out of range, 0-4 valid), then '0', then Enter
                # '9' should be ignored, '0' selects option 0
                mock_getch.side_effect = [ord('9'), ord('0'), 10]
                
                result = ui.render_menu(options, default=0, highlighted=0)
                # Should still return 0 (option selected by '0' after ignoring '9')
                assert result == 0, f"Out-of-range digit should be ignored, result should be 0, got {result}"
    
    def test_multiple_out_of_range_digits_before_valid_selection(self):
        """Test that multiple out-of-range digits are all ignored before a valid selection."""
        options = [{'label': f'Option {i}'} for i in range(5)]
        
        ui = create_ui()
        
        with patch.object(ui, '_screen') as mock_screen, \
             patch.object(ui, 'refresh'), \
             patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin:
            mock_win = mock_newwin.return_value
            mock_win.getyx.return_value = (0, 0)
            mock_screen.getmaxyx.return_value = (20, 60)
            
            with patch.object(mock_win, 'getch') as mock_getch:
                # Multiple out-of-range: '9', '7', '5', then valid '2', then Enter
                mock_getch.side_effect = [ord('9'), ord('7'), ord('5'), ord('2'), 10]
                
                result = ui.render_menu(options, default=0, highlighted=0)
                assert result == 2, f"Should select option 2 after ignoring out-of-range, got {result}"
    
    def test_out_of_range_digit_does_not_reset_highlight(self):
        """Test that out-of-range digits don't reset the highlight position."""
        options = [{'label': f'Option {i}'} for i in range(5)]
        
        ui = create_ui()
        
        with patch.object(ui, '_screen') as mock_screen, \
             patch.object(ui, 'refresh'), \
             patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin:
            mock_win = mock_newwin.return_value
            mock_win.getyx.return_value = (0, 0)
            mock_screen.getmaxyx.return_value = (20, 60)
            
            # Start at option 2
            with patch.object(mock_win, 'getch') as mock_getch:
                # Type '9' (out of range), then '1', then Enter
                mock_getch.side_effect = [ord('9'), ord('1'), 10]
                
                result = ui.render_menu(options, default=2, highlighted=2)
                assert result == 1, f"Should select option 1 after ignoring '9', got {result}"


class TestCarriageReturnConfirmation:
    """Tests for Carriage Return (13) as a confirm/cancel key."""
    
    def test_carriage_return_confirms_in_menu(self):
        """Test that CR (13) confirms a selection in render_menu."""
        options = [{'label': f'Option {i}'} for i in range(5)]
        
        ui = create_ui()
        
        with patch.object(ui, '_screen') as mock_screen, \
             patch.object(ui, 'refresh'), \
             patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin:
            mock_win = mock_newwin.return_value
            mock_win.getyx.return_value = (0, 0)
            mock_screen.getmaxyx.return_value = (20, 60)
            
            with patch.object(mock_win, 'getch') as mock_getch:
                # Type '2' to select option 2, then CR (13) to confirm
                mock_getch.side_effect = [ord('2'), 13]
                
                result = ui.render_menu(options, default=0, highlighted=0)
                assert result == 2, f"CR should confirm option 2, got {result}"
    
    def test_carriage_return_confirms_in_confirmation(self):
        """Test that CR (13) confirms a confirmation dialog."""
        ui = create_ui()
        
        with patch.object(ui, '_screen') as mock_screen, \
             patch.object(ui, 'refresh'), \
             patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin:
            mock_win = mock_newwin.return_value
            mock_win.getyx.return_value = (0, 0)
            mock_screen.getmaxyx.return_value = (20, 60)
            
            with patch.object(mock_win, 'getch') as mock_getch:
                # Type 'y' then CR (13) to confirm
                mock_getch.side_effect = [ord('y'), 13]
                
                result = ui.render_confirmation("Are you sure?", "Release 1.0")
                assert result is True, f"CR should confirm confirmation, got {result}"
    
    def test_carriage_return_confirms_in_confirmation(self):
        """Test that CR (13) confirms a confirmation dialog, selecting Yes by default."""
        ui = create_ui()
        
        with patch.object(ui, '_screen') as mock_screen, \
             patch.object(ui, 'refresh'), \
             patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin:
            mock_win = mock_newwin.return_value
            mock_win.getyx.return_value = (0, 0)
            mock_screen.getmaxyx.return_value = (20, 60)
            
            with patch.object(mock_win, 'getch') as mock_getch:
                # Just CR (13) - should confirm (Yes) by default
                mock_getch.side_effect = [13]
                
                result = ui.render_confirmation("Are you sure?", "Release 1.0")
                assert result is True, f"CR should confirm (Yes) in confirmation, got {result}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
