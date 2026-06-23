#!/usr/bin/env python3
"""
Simple test suite for UIManager API verification.

This tests the UIManager class structure and basic functionality
without requiring complex mocking of curses.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import curses

sys.path.insert(0, str(Path.cwd()))
from ui_manager import UIManager, UIManagerError


def test_ui_manager_structure():
    """Test UIManager class structure and initialization."""
    print("[1/5] Testing UIManager structure...")
    
    # Test 1: Class exists and has expected methods
    assert hasattr(UIManager, 'render_menu'), "UIManager should have render_menu method"
    assert hasattr(UIManager, 'render_confirmation'), "UIManager should have render_confirmation method"
    assert hasattr(UIManager, 'render_progress_bar'), "UIManager should have render_progress_bar method"
    assert hasattr(UIManager, 'render_success'), "UIManager should have render_success method"
    assert hasattr(UIManager, 'render_error'), "UIManager should have render_error method"
    assert hasattr(UIManager, 'print_message'), "UIManager should have print_message method"
    
    # Test 2: UIManagerError exists
    assert issubclass(UIManagerError, Exception), "UIManagerError should be an Exception subclass"
    
    # Test 3: UIManager can be instantiated (with curses mocked)
    with patch('ui_manager.curses') as mock_curses:
        # Set up mocks
        mock_curses.initscr.return_value = MagicMock()
        mock_curses.start_color = MagicMock()
        mock_curses.init_pair = MagicMock(return_value=None)
        mock_curses.cbreak = MagicMock(return_value=True)
        mock_curses.noecho = MagicMock()
        mock_curses.curs_set = MagicMock(return_value=None)
        mock_curses.has_ungetch = MagicMock(return_value=False)
        
        ui = UIManager("Test")
        assert hasattr(ui, '_using_curses'), "UIManager should have _using_curses attribute"
        assert hasattr(ui, '_screen'), "UIManager should have _screen attribute"
        assert hasattr(ui, '_color_pair'), "UIManager should have _color_pair attribute"
    
    print("  PASSED")


def test_color_pair_setup():
    """Test that color pairs are set up correctly."""
    print("[2/5] Testing color pair setup...")
    
    # Test 1: Normal curses initialization path (stdin is TTY)
    with patch('ui_manager.sys.stdin.isatty', return_value=True):
        with patch('ui_manager.curses') as mock_curses:
            # Set up the mock to return actual curses constants
            mock_curses.initscr.return_value = MagicMock()
            mock_curses.start_color = MagicMock()
            mock_curses.cbreak = MagicMock(return_value=True)
            mock_curses.noecho = MagicMock()
            mock_curses.curs_set = MagicMock(return_value=None)
            mock_curses.has_ungetch = MagicMock(return_value=False)
            
            # Make init_pair track calls and return actual constants
            call_count = [0]
            def mock_init_pair(pair_num, color1, color2):
                call_count[0] += 1
                return None
            
            # Set up the mock to have attributes that return actual constants
            mock_curses.COLOR_GREEN = curses.COLOR_GREEN
            mock_curses.COLOR_BLACK = curses.COLOR_BLACK
            mock_curses.COLOR_WHITE = curses.COLOR_WHITE
            
            mock_curses.init_pair.side_effect = mock_init_pair
            
            ui = UIManager("Test")
            
            # Verify curses.init_pair was called
            calls = mock_curses.init_pair.call_args_list
            assert len(calls) == 2, f"Expected 2 init_pair calls, got {len(calls)}"
            
            # First call: color pair 1 (green on black)
            first_call = calls[0][0]
            assert first_call[0] == 1, "First call should use color pair 1"
            assert first_call[1] == curses.COLOR_GREEN, "First call should use COLOR_GREEN"
            assert first_call[2] == curses.COLOR_BLACK, "First call should use COLOR_BLACK"
            
            # Second call: color pair 2 (white on black)
            second_call = calls[1][0]
            assert second_call[0] == 2, "Second call should use color pair 2"
            assert second_call[1] == curses.COLOR_WHITE, "Second call should use COLOR_WHITE"
            assert second_call[2] == curses.COLOR_BLACK, "Second call should use COLOR_BLACK"
    
    # Test 2: Fallback path (stdin is not a TTY)
    with patch('ui_manager.sys.stdin.isatty', return_value=False):
        with patch('ui_manager.curses') as mock_curses:
            ui = UIManager("Test")
            
            # Verify no curses initialization occurred
            assert mock_curses.initscr.call_count == 0, "initscr should not be called in fallback path"
            assert mock_curses.init_pair.call_count == 0, "init_pair should not be called in fallback path"
            
            # Verify _color_pair is None
            assert ui._color_pair is None, "_color_pair should be None in fallback path"
            assert ui._using_curses == False, "_using_curses should be False in fallback path"
            
            # Verify screen is the dummy object
            assert ui._screen is not None, "_screen should be set to dummy object in fallback path"
    
    print("  PASSED")


def test_menu_rendering_api():
    """Test menu rendering API."""
    print("[3/5] Testing menu rendering API...")
    
    with patch('ui_manager.curses') as mock_curses:
        mock_curses.initscr.return_value = MagicMock()
        mock_curses.start_color = MagicMock()
        mock_curses.init_pair = MagicMock(return_value=None)
        mock_curses.cbreak = MagicMock(return_value=True)
        mock_curses.noecho = MagicMock()
        mock_curses.curs_set = MagicMock(return_value=None)
        mock_curses.has_ungetch = MagicMock(return_value=False)
        
        ui = UIManager("Test Menu")
        
        # Test that render_menu accepts expected arguments
        options = [{'label': f'Option {i}'} for i in range(3)]
        
        # Verify method signature
        import inspect
        sig = inspect.signature(ui.render_menu)
        params = list(sig.parameters.keys())
        assert 'options' in params, "render_menu should accept 'options' parameter"
        assert 'default' in params, "render_menu should accept 'default' parameter"
        assert 'highlighted' in params, "render_menu should accept 'highlighted' parameter"
    
    print("  PASSED")


def test_confirmation_api():
    """Test confirmation prompt API."""
    print("[4/5] Testing confirmation API...")
    
    with patch('ui_manager.curses') as mock_curses:
        mock_curses.initscr.return_value = MagicMock()
        mock_curses.start_color = MagicMock()
        mock_curses.init_pair = MagicMock(return_value=None)
        mock_curses.cbreak = MagicMock(return_value=True)
        mock_curses.noecho = MagicMock()
        mock_curses.curs_set = MagicMock(return_value=None)
        mock_curses.has_ungetch = MagicMock(return_value=False)
        
        ui = UIManager("Test")
        
        # Verify method signature
        import inspect
        sig = inspect.signature(ui.render_confirmation)
        params = list(sig.parameters.keys())
        assert 'message' in params, "render_confirmation should accept 'message' parameter"
        assert 'default' in params, "render_confirmation should accept 'default' parameter"
    
    print("  PASSED")


def test_progress_bar_api():
    """Test progress bar API."""
    print("[5/5] Testing progress bar API...")
    
    with patch('ui_manager.curses') as mock_curses:
        mock_curses.initscr.return_value = MagicMock()
        mock_curses.start_color = MagicMock()
        mock_curses.init_pair = MagicMock(return_value=None)
        mock_curses.cbreak = MagicMock(return_value=True)
        mock_curses.noecho = MagicMock()
        mock_curses.curs_set = MagicMock(return_value=None)
        mock_curses.has_ungetch = MagicMock(return_value=False)
        
        ui = UIManager("Test")
        
        # Verify method signature
        import inspect
        sig = inspect.signature(ui.render_progress_bar)
        params = list(sig.parameters.keys())
        assert 'filename' in params, "render_progress_bar should accept 'filename' parameter"
        assert 'current' in params, "render_progress_bar should accept 'current' parameter"
        assert 'total' in params, "render_progress_bar should accept 'total' parameter"
        assert 'percent' in params, "render_progress_bar should accept 'percent' parameter"
    
    print("  PASSED")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("Running UIManager API Tests")
    print("=" * 60)
    
    try:
        test_ui_manager_structure()
        test_color_pair_setup()
        test_menu_rendering_api()
        test_confirmation_api()
        test_progress_bar_api()
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED")
        print("=" * 60)
        return True
    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
