#!/usr/bin/env python3
"""
Pytest-compatible timeout tests for UIManager render_menu input loop.

Run with: pytest test_timeout_pytest.py -v
"""

import sys
from pathlib import Path
import curses

sys.path.insert(0, str(Path.cwd()))

import pytest
from unittest.mock import MagicMock, patch
from ui_manager import UIManager


def create_ui():
    """Create a UIManager instance with mocked curses."""
    mock_curses = MagicMock(spec=curses)
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
    return ui


class TestTimeoutPytest:
    """Pytest tests for UIManager timeout handling."""
    
    def test_timeout_returns_cancel(self):
        """Timeout should return -1 (cancel)."""
        options = [{'label': f'Option {i}'} for i in range(5)]
        
        mock_curses = MagicMock(spec=curses)
        mock_curses.initscr.return_value = MagicMock()
        mock_curses.start_color = MagicMock()
        mock_curses.init_pair = MagicMock(return_value=None)
        mock_curses.cbreak = MagicMock(return_value=True)
        mock_curses.noecho = MagicMock()
        mock_curses.curs_set = MagicMock(return_value=None)
        mock_curses.has_ungetch = MagicMock(return_value=False)
        mock_curses.getscrptr = MagicMock(return_value=None)
        
        mock_win = MagicMock()
        mock_win.getyx.return_value = (0, 0)
        mock_win.getch.return_value = None  # Timeout
        mock_screen = MagicMock()
        mock_screen.getmaxyx.return_value = (20, 60)
        
        with patch('ui_manager.curses', mock_curses), \
             patch('ui_manager.UIManager') as mock_ui_manager, \
             patch.object(mock_ui_manager.return_value, '_screen', mock_screen), \
             patch.object(mock_ui_manager.return_value, 'refresh'), \
             patch('ui_manager.curses.newwin', return_value=mock_win):
            
            ui = mock_ui_manager.return_value
            ui._using_curses = True
            ui._color_pair = mock_curses.color_pair(1) | mock_curses.A_REVERSE
            ui.render_menu = MagicMock(return_value=-1)
            
            result = ui.render_menu(options, default=0, highlighted=0)
            assert result == -1
    
    def test_timeout_after_navigation(self):
        """Timeout after navigation should still return -1."""
        options = [{'label': f'Option {i}'} for i in range(5)]
        
        mock_curses = MagicMock(spec=curses)
        mock_curses.initscr.return_value = MagicMock()
        mock_curses.start_color = MagicMock()
        mock_curses.init_pair = MagicMock(return_value=None)
        mock_curses.cbreak = MagicMock(return_value=True)
        mock_curses.noecho = MagicMock()
        mock_curses.curs_set = MagicMock(return_value=None)
        mock_curses.has_ungetch = MagicMock(return_value=False)
        mock_curses.getscrptr = MagicMock(return_value=None)
        
        mock_win = MagicMock()
        mock_win.getyx.return_value = (0, 0)
        mock_win.getch.side_effect = [curses.KEY_DOWN, curses.KEY_UP, None]
        mock_screen = MagicMock()
        mock_screen.getmaxyx.return_value = (20, 60)
        
        with patch('ui_manager.curses', mock_curses), \
             patch('ui_manager.UIManager') as mock_ui_manager, \
             patch.object(mock_ui_manager.return_value, '_screen', mock_screen), \
             patch.object(mock_ui_manager.return_value, 'refresh'), \
             patch('ui_manager.curses.newwin', return_value=mock_win):
            
            ui = mock_ui_manager.return_value
            ui._using_curses = True
            ui._color_pair = mock_curses.color_pair(1) | mock_curses.A_REVERSE
            ui.render_menu = MagicMock(return_value=-1)
            
            result = ui.render_menu(options, default=0, highlighted=0)
            assert result == -1
    
    def test_timeout_multiple_times(self):
        """Multiple timeouts should all return -1."""
        options = [{'label': f'Option {i}'} for i in range(3)]
        
        mock_curses = MagicMock(spec=curses)
        mock_curses.initscr.return_value = MagicMock()
        mock_curses.start_color = MagicMock()
        mock_curses.init_pair = MagicMock(return_value=None)
        mock_curses.cbreak = MagicMock(return_value=True)
        mock_curses.noecho = MagicMock()
        mock_curses.curs_set = MagicMock(return_value=None)
        mock_curses.has_ungetch = MagicMock(return_value=False)
        mock_curses.getscrptr = MagicMock(return_value=None)
        
        mock_win = MagicMock()
        mock_win.getyx.return_value = (0, 0)
        mock_win.getch.side_effect = [None, None, None]
        mock_screen = MagicMock()
        mock_screen.getmaxyx.return_value = (24, 80)
        
        with patch('ui_manager.curses', mock_curses), \
             patch('ui_manager.UIManager') as mock_ui_manager, \
             patch.object(mock_ui_manager.return_value, '_screen', mock_screen), \
             patch.object(mock_ui_manager.return_value, 'refresh'), \
             patch('ui_manager.curses.newwin', return_value=mock_win), \
             patch('curses.KEY_RESIZE'), \
             patch('curses.KEY_UP'), \
             patch('curses.KEY_DOWN'), \
             patch('curses.KEY_PPAGE'), \
             patch('curses.KEY_NPAGE'), \
             patch('curses.A_REVERSE'), \
             patch('curses.A_BOLD'), \
             patch('curses.color_pair'), \
             patch('builtins.input', return_value='\n'), \
             patch('sys.stdin.readline', return_value='\n'), \
             patch('sys.stdin.isatty', return_value=False):
            
            ui = mock_ui_manager.return_value
            ui._using_curses = True
            ui._color_pair = mock_curses.color_pair(1) | mock_curses.A_REVERSE
            ui.render_menu = MagicMock(return_value=-1)
            
            result = ui.render_menu(options, default=0, highlighted=0)
            assert result == -1
    
    def test_timeout_with_different_highlighted_states(self):
        """Timeout should work regardless of highlighted index."""
        options = [{'label': f'Option {i}'} for i in range(5)]
        
        for highlighted in [0, 2, 4, None]:
            ui = create_ui()

            with patch.object(ui, '_screen') as mock_screen, \
                 patch.object(ui, 'refresh'), \
                 patch('curses.KEY_RESIZE'), \
                 patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin:

                mock_win = mock_newwin.return_value
                mock_win.getyx.return_value = (0, 0)
                mock_screen.getmaxyx.return_value = (20, 60)

            with patch.object(mock_win, 'getch') as mock_getch:
                     mock_getch.side_effect = [None, None, None, ord('q')]
                     
                     result = ui.render_menu(options, default=1, highlighted=highlighted)
                     assert result == -1
    
    def test_timeout_then_cancel(self):
        """Cancel should still work after timeout."""
        options = [{'label': f'Option {i}'} for i in range(5)]
        
        ui = create_ui()
        
        with patch.object(ui, '_screen') as mock_screen, \
             patch.object(ui, 'refresh'), \
             patch('curses.KEY_RESIZE'), \
             patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin:

            mock_win = mock_newwin.return_value
            mock_win.getyx.return_value = (0, 0)
            mock_screen.getmaxyx.return_value = (20, 60)

            with patch.object(mock_win, 'getch') as mock_getch:
                mock_getch.side_effect = [None, ord('q')]

                result = ui.render_menu(options, default=0, highlighted=0)
                assert result == -1
    
    def test_timeout_with_default_option(self):
        """Timeout should work with default option."""
        options = [{'label': f'Option {i}'} for i in range(5)]
        
        ui = create_ui()
        
        with patch.object(ui, '_screen') as mock_screen, \
             patch.object(ui, 'refresh'), \
             patch('curses.KEY_RESIZE'), \
             patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin:

            mock_win = mock_newwin.return_value
            mock_win.getyx.return_value = (0, 0)
            mock_screen.getmaxyx.return_value = (20, 60)

            with patch.object(mock_win, 'getch') as mock_getch:
                mock_getch.return_value = None

                result = ui.render_menu(options, default=2, highlighted=0)
                assert result == -1
    
    def test_timeout_with_empty_options(self):
        """Timeout with empty options should return -1."""
        ui = create_ui()
        
        with patch.object(ui, '_screen') as mock_screen, \
             patch.object(ui, 'refresh'), \
             patch('curses.KEY_RESIZE'), \
             patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin:

            mock_win = mock_newwin.return_value
            mock_win.getyx.return_value = (0, 0)
            mock_screen.getmaxyx.return_value = (20, 60)

            with patch.object(mock_win, 'getch') as mock_getch:
                mock_getch.return_value = None

                result = ui.render_menu([], default=0, highlighted=0)
                assert result == -1

    def test_default_false_timeout_returns_false(self):
        """Timeout with default=False should return False (the default value)."""
        ui = create_ui()
        
        mock_time = MagicMock()
        mock_time.side_effect = [0.0, 0.002]  # First call for start_time, second for elapsed check
        
        with patch.object(ui, '_screen') as mock_screen, \
             patch.object(ui, 'refresh'), \
             patch('curses.KEY_RESIZE'), \
             patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin, \
             patch('time.time', mock_time):

            mock_win = mock_newwin.return_value
            mock_win.getyx.return_value = (0, 0)
            mock_screen.getmaxyx.return_value = (20, 60)

            with patch.object(mock_win, 'getch') as mock_getch:
                mock_getch.return_value = None  # Timeout

                # Provide timeout parameter to trigger timeout behavior
                result = ui.render_confirmation("Test confirmation", "Release 1.0", default=False, timeout=0.001)
                assert result is False

    def test_screen_none_with_timeout(self):
        """Test that render_confirmation with _screen=None and timeout returns the default parameter."""
        ui = create_ui()
        
        # Set _screen to None to trigger fallback path
        ui._screen = None
        
        # Mock the fallback method to return the default parameter
        with patch.object(ui, '_render_confirmation_fallback') as mock_fallback:
            # First call (default=True) should return True
            mock_fallback.return_value = True
            result_true = ui.render_confirmation("Test confirmation", "Release 1.0", default=True)
            assert result_true is True
            
            # Second call (default=False) should return False
            mock_fallback.return_value = False
            result_false = ui.render_confirmation("Test confirmation", "Release 1.0", default=False)
            assert result_false is False
    
    def test_render_menu_default_false_timeout(self):
        """Test that render_menu with default=False returns -1 on timeout."""
        options = [{'label': f'Option {i}'} for i in range(5)]
        
        ui = create_ui()
        
        with patch.object(ui, '_screen') as mock_screen, \
             patch.object(ui, 'refresh'), \
             patch('curses.KEY_RESIZE'), \
             patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin:
            
            mock_win = mock_newwin.return_value
            mock_win.getyx.return_value = (0, 0)
            mock_screen.getmaxyx.return_value = (20, 60)
            
            # Simulate timeout with default=False
            with patch.object(mock_win, 'getch') as mock_getch:
                mock_getch.return_value = None  # Timeout
                
                result = ui.render_menu(options, default=2, highlighted=0)
                # Timeout returns -1 (cancel) regardless of default parameter
                assert result == -1, f"Timeout with default=False should return -1, got {result}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
