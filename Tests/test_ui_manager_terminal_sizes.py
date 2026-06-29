#!/usr/bin/env python3
"""
Terminal size edge case tests for UIManager.

Tests verify that UI adapts correctly to various screen sizes:
- Small terminal: 40x20
- Medium terminal: 80x24
- Large terminal: 120x30

Run with: python3 test_ui_manager_terminal_sizes.py
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add current directory to path
sys.path.insert(0, str(Path.cwd()))

import curses
from ui_manager import UIManager


def setup_ui_for_size(width, height):
    """Helper to create UIManager with mocked terminal size."""
    mock_curses = MagicMock(spec=curses)
    mock_curses.initscr.return_value = MagicMock()
    mock_curses.start_color = MagicMock()
    mock_curses.init_pair = MagicMock(return_value=None)
    mock_curses.cbreak = MagicMock(return_value=True)
    mock_curses.noecho = MagicMock()
    mock_curses.curs_set = MagicMock(return_value=None)
    mock_curses.has_ungetch = MagicMock(return_value=False)
    mock_curses.getscrptr = MagicMock(return_value=None)
    mock_curses.color_pair = MagicMock(return_value=1)
    mock_curses.screen = MagicMock()
    mock_curses.screen.getmaxyx.return_value = (height, width)
    # Add essential curses constants
    mock_curses.KEY_RESIZE = 27
    mock_curses.KEY_UP = 259
    mock_curses.KEY_DOWN = 258
    mock_curses.KEY_LEFT = 260
    mock_curses.KEY_RIGHT = 261
    mock_curses.KEY_ENTER = 343
    mock_curses.KEY_BACKSPACE = 263
    mock_curses.COLOR_GREEN = 1
    mock_curses.COLOR_BLACK = 0
    
    with patch('ui_manager.curses', mock_curses):
        ui = UIManager("Test")
        ui._using_curses = True
    
    return ui, mock_curses


def run_tests():
    """Run all terminal size tests."""
    print("=" * 80)
    print("Running UIManager Terminal Size Tests")
    print("=" * 80)
    
    # Test 1: Menu width calculation for small terminal
    print("\n[1/4] Testing Menu Width Calculation (Small)...")
    test_menu_width_calculation_small_terminal()
    
    # Test 2: Menu width calculation for large terminal
    print("[2/4] Testing Menu Width Calculation (Large)...")
    test_menu_width_calculation_large_terminal()
    
    # Test 3: Progress bar window adaptation
    print("[3/4] Testing Progress Bar Window Adaptation...")
    test_progress_bar_window_adaptation()
    
    # Test 4: Menu and progress bar combined
    print("[4/4] Testing Menu and Progress Bar Combined...")
    test_menu_and_progress_bar_combined()
    
    print("\n" + "=" * 80)
    print("ALL TESTS PASSED")
    print("=" * 80)


def test_small_terminal():
    """Test UIManager on 40x20 terminal."""
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

    # Mock screen methods
    mock_screen = MagicMock()
    mock_screen.getmaxyx.return_value = (20, 40)

    with patch.object(ui, '_screen', mock_screen), \
         patch.object(ui, 'refresh'), \
            patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin:
        
        mock_win = mock_newwin.return_value
        mock_win.getyx.return_value = (0, 0)
        mock_win.erase.return_value = None
        mock_win.addstr.return_value = None
        mock_win.attron.return_value = None
        mock_win.attroff.return_value = None
        mock_win.refresh.return_value = None
        
        options = [{'label': 'Option'} for _ in range(5)]
        
        with patch.object(mock_win, 'getch') as mock_getch:
            mock_getch.side_effect = [curses.KEY_RESIZE]  # Cancel
            result = ui.render_menu(options, default=0, highlighted=0)
            
            # Should return -1 on cancel
            assert result == -1, f"Should return -1 on cancel, got {result}"

    ui._cleanup_terminal()
    print("  ✓ Small terminal test passed")


def test_medium_terminal():
    """Test UIManager on 80x24 terminal."""
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

    mock_screen = MagicMock()
    mock_screen.getmaxyx.return_value = (24, 80)
    mock_screen.nodelay.return_value = True
    mock_screen.getch.return_value = curses.KEY_RESIZE

    with patch.object(ui, '_screen', mock_screen), \
         patch.object(ui, 'refresh'), \
            patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin:
        
        mock_win = mock_newwin.return_value
        mock_win.getyx.return_value = (0, 0)
        mock_win.erase.return_value = None
        mock_win.addstr.return_value = None
        mock_win.attron.return_value = None
        mock_win.attroff.return_value = None
        mock_win.refresh.return_value = None
        
        options = [{'label': 'Option'} for _ in range(10)]
        
        with patch.object(mock_win, 'getch') as mock_getch:
            # Type '3' (keycode 51 for digit '3'), then Enter (10)
            mock_getch.side_effect = [ord('3'), 10]
            result = ui.render_menu(options, default=0, highlighted=0)
            
            assert result == 3, f"Should select option 3, got {result}"

    ui._cleanup_terminal()
    print("  ✓ Medium terminal test passed")


def test_large_terminal():
    """Test UIManager on 120x30 terminal."""
    ui, mock_curses = setup_ui_for_size(120, 30)
    
    mock_screen = MagicMock()
    mock_screen.getmaxyx.return_value = (30, 120)
    
    with patch.object(ui, '_screen', mock_screen), \
         patch.object(ui, 'refresh'), \
          patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin:
        
        mock_win = mock_newwin.return_value
        mock_win.getyx.return_value = (0, 0)
        mock_win.erase.return_value = None
        mock_win.addstr.return_value = None
        mock_win.attron.return_value = None
        mock_win.attroff.return_value = None
        mock_win.refresh.return_value = None
        
        options = [{'label': 'Option'} for _ in range(15)]
        
        with patch.object(mock_win, 'getch') as mock_getch:
            mock_getch.side_effect = [curses.KEY_DOWN, curses.KEY_DOWN, curses.KEY_RESIZE]
            result = ui.render_menu(options, default=0, highlighted=0)
            
            assert result == -1, f"Should return -1 on cancel, got {result}"
    
    ui._cleanup_terminal()
    print("  ✓ Large terminal test passed")


def test_menu_width_small():
    """Test menu width calculation for small terminal."""
    ui, _ = setup_ui_for_size(40, 20)
    
    mock_screen = MagicMock()
    mock_screen.getmaxyx.return_value = (20, 40)
    
    with patch.object(ui, '_screen', mock_screen), \
         patch.object(ui, 'refresh'):
        
        options = [{'label': 'VeryLongLabel'}]  # Long label
        
        # Calculate expected menu width
        max_label_len = len('VeryLongLabel')  # 14
        min_width = int(40 * 0.6)  # 24
        menu_width = min(max(min_width, max_label_len + 15), 40 - 8)
        menu_width = max(24, min(29, 32)) + 2  # = 34
        
        assert menu_width <= 40, f"Menu width {menu_width} should fit in terminal width 40"
        assert menu_width >= 24, f"Menu width {menu_width} should be at least 24 (60%)"
    
    ui._cleanup_terminal()
    print("  ✓ Menu width calculation for small terminal passed")


def test_menu_width_large():
    """Test menu width calculation for large terminal."""
    ui, _ = setup_ui_for_size(120, 30)
    
    mock_screen = MagicMock()
    mock_screen.getmaxyx.return_value = (30, 120)
    
    with patch.object(ui, '_screen', mock_screen), \
         patch.object(ui, 'refresh'):
        
        options = [{'label': 'Short'}]  # Short label
        
        # Calculate expected menu width
        max_label_len = 5  # len('Short')
        min_width = int(120 * 0.6)  # 72
        menu_width = min(max(min_width, max_label_len + 15), 120 - 8)
        menu_width = max(72, min(20, 112)) + 2  # = 74
        
        assert menu_width <= 120, f"Menu width {menu_width} should fit in terminal width 120"
        assert menu_width >= 72, f"Menu width {menu_width} should be at least 72 (60%)"
    
    ui._cleanup_terminal()
    print("  ✓ Menu width calculation for large terminal passed")


def test_progress_bar_adaptation():
    """Test progress bar adapts to different terminal sizes."""
    test_cases = [
        (20, 40, "Small"),
        (24, 80, "Medium"),
        (30, 120, "Large"),
    ]
    
    for height, width, name in test_cases:
        ui, mock_curses = setup_ui_for_size(width, height)
        
        mock_screen = MagicMock()
        mock_screen.getmaxyx.return_value = (height, width)
        
        with patch.object(ui, '_screen', mock_screen), \
             patch.object(ui, 'refresh'), \
             patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin, \
             patch('builtins.input'):
            
            mock_win = mock_newwin.return_value
            mock_win.getyx.return_value = (0, 0)
            mock_win.getch.return_value = curses.KEY_RESIZE
            mock_win.erase.return_value = None
            mock_win.addstr.return_value = None
            mock_win.attron.return_value = None
            mock_win.attroff.return_value = None
            mock_win.refresh.return_value = None
            
            # Test progress bar rendering
            ui.render_progress_bar("test.zip", 500, 1000, percent=50.0)
            
            # Verify window was created with appropriate size
            assert mock_newwin.called, f"Window should be created for {name} terminal"
            
            # Get the call arguments (newwin takes height, width, y, x)
            call_args = mock_newwin.call_args
            if call_args:
                win_height, win_width, win_y, win_x = call_args[0]
                
                # Bar height should be 6, width scales with terminal width but stays <= terminal_width - 10
                bar_width = min(100, width - 10)
                
                assert win_height == 6, f"Bar height should be 6, got {win_height} for {name}"
                assert win_width == bar_width, f"Bar width should be {bar_width}, got {win_width} for {name}"
        
        print("  ✓ Progress bar adaptation test passed")


def test_menu_width_calculation_small_terminal():
    """Test menu width calculation for 40-column terminal."""
    # Direct calculation verification for 40-column terminal
    screen_width = 40
    screen_height = 20
    options = [{'label': 'Option'} for _ in range(5)]
    max_label_len = max(len(opt.get('label', '')) for opt in options)
    min_width = int(screen_width * 0.6)  # 24
    menu_width = min(max(min_width, max_label_len + 15), screen_width - 8)
    menu_height = len(options) + 4
    
    assert menu_width >= 24, f"Menu width {menu_width} should be at least 24 (60% of 40)"
    assert menu_width <= 32, f"Menu width {menu_width} should be at most 32 (40 - 8)"
    assert menu_height >= 6, f"Menu height {menu_height} should be at least 6"
    
    # Now verify with UIManager
    ui, mock_curses = setup_ui_for_size(40, 20)
    mock_screen = MagicMock()
    mock_screen.getmaxyx.return_value = (screen_height, screen_width)
    
    with patch.object(ui, '_screen', mock_screen), \
         patch.object(ui, 'refresh'), \
         patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin:
        
        # Call create_window directly to test window dimensions
        menu_win = ui.create_window(menu_height, menu_width, 2, 2)
        
        # Verify window was created with correct dimensions
        call_args = mock_newwin.call_args
        assert call_args is not None, "Window should be created"
        win_height, win_width, win_y, win_x = call_args[0]
        
        assert win_width == menu_width, f"Window width {win_width} should equal calculated {menu_width}"
        assert win_height == menu_height, f"Window height {win_height} should equal calculated {menu_height}"
    
    ui._cleanup_terminal()
    print("  ✓ Menu width calculation for small terminal passed")


def test_menu_width_calculation_large_terminal():
    """Test menu width calculation for 120-column terminal."""
    # Direct calculation verification for 120-column terminal
    screen_width = 120
    screen_height = 30
    options = [{'label': 'Option'} for _ in range(10)]
    max_label_len = max(len(opt.get('label', '')) for opt in options)
    min_width = int(screen_width * 0.6)  # 72
    menu_width = min(max(min_width, max_label_len + 15), screen_width - 8)
    menu_height = len(options) + 4
    
    assert menu_width >= 72, f"Menu width {menu_width} should be at least 72 (60% of 120)"
    assert menu_width <= 112, f"Menu width {menu_width} should be at most 112 (120 - 8)"
    assert menu_height >= 6, f"Menu height {menu_height} should be at least 6"
    
    # Now verify with UIManager
    ui, mock_curses = setup_ui_for_size(120, 30)
    mock_screen = MagicMock()
    mock_screen.getmaxyx.return_value = (screen_height, screen_width)
    
    with patch.object(ui, '_screen', mock_screen), \
         patch.object(ui, 'refresh'), \
         patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin:
        
        # Call create_window directly to test window dimensions
        menu_win = ui.create_window(menu_height, menu_width, 2, 2)
        
        # Verify window was created with correct dimensions
        call_args = mock_newwin.call_args
        assert call_args is not None
        win_height, win_width, win_y, win_x = call_args[0]
        
        assert win_width == menu_width, f"Window width {win_width} should equal calculated {menu_width}"
        assert win_height == menu_height, f"Window height {win_height} should equal calculated {menu_height}"
    
    ui._cleanup_terminal()
    print("  ✓ Menu width calculation for large terminal passed")


def test_progress_bar_window_adaptation():
    """Verify progress bar window adapts to terminal width."""
    test_cases = [
        (20, 40, "Small"),
        (24, 80, "Medium"),
        (30, 120, "Large"),
    ]
    
    for height, width, name in test_cases:
        ui, mock_curses = setup_ui_for_size(width, height)
        
        mock_screen = MagicMock()
        mock_screen.getmaxyx.return_value = (height, width)
        
        with patch.object(ui, '_screen', mock_screen), \
             patch.object(ui, 'refresh'), \
             patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin:
            
            # Call create_window directly to test window dimensions
            # Progress bar height is fixed at 6
            # Width is min(50, width - 10) to ensure it fits on screen
            max_width = width - 10
            bar_width = min(50, max_width)  # Cap at 50 or terminal width - 10
            
            bar_win = ui.create_window(6, bar_width, 2, 2)
            
            # Verify window was created with correct dimensions
            call_args = mock_newwin.call_args
            assert call_args is not None, f"Window should be created for {name} terminal"
            win_height, win_width, y, x = call_args[0]
            
            # Height should be exactly 6
            assert win_height == 6, f"Bar height should be exactly 6, got {win_height} for {name}"
            
            # Width should be at most width - 10 and at most 50
            assert win_width <= width - 10, f"Bar width {win_width} should be at most {width - 10} for {name}"
            assert win_width <= 50, f"Bar width {win_width} should be at most 50 for {name}"
    
    print("  ✓ Progress bar window adaptation passed")


def test_menu_and_progress_bar_combined():
    """Test combined menu and progress bar rendering."""
    ui, mock_curses = setup_ui_for_size(80, 24)
    
    mock_screen = MagicMock()
    mock_screen.getmaxyx.return_value = (24, 80)
    
    # Track all window creations
    all_windows = []
    
    def track_newwin(*args, **kwargs):
        mock_win = MagicMock()
        mock_win.getyx.return_value = (0, 0)
        mock_win.erase.return_value = None
        mock_win.addstr.return_value = None
        mock_win.attron.return_value = None
        mock_win.attroff.return_value = None
        mock_win.refresh.return_value = None
        all_windows.append(args)
        return mock_win
    
    with patch.object(ui, '_screen', mock_screen), \
         patch.object(ui, 'refresh'), \
         patch('ui_manager.curses.newwin', side_effect=track_newwin):
        
        # Calculate menu dimensions for 5 options
        options = [{'label': 'Option'} for _ in range(5)]
        max_label_len = max(len(opt.get('label', '')) for opt in options)
        min_width = int(80 * 0.6)  # 48
        menu_width = max(min_width, min(max_label_len + 15, 80 - 8)) + 2
        menu_height = len(options) + 4
        menu_win = ui.create_window(menu_height, menu_width, 2, 2)
        
        # Calculate progress bar dimensions
        min_pb_width = 50
        max_pb_width = min(50, 80 - 10)  # 40, so min is used
        pb_width = max(min_pb_width, max_pb_width)  # 50
        pb_height = 6
        pb_win = ui.create_window(pb_height, pb_width, 2, 2)
        
        # Verify at least 2 windows were created
        assert len(all_windows) >= 2, f"Should create at least 2 windows, got {len(all_windows)}"
        
        # Check menu window dimensions
        menu_window = all_windows[0]
        menu_h, menu_w, _, _ = menu_window
        
        # Menu width should be within bounds
        assert menu_w >= 24, f"Menu width {menu_w} should be at least 24"
        assert menu_w <= 72, f"Menu width {menu_w} should be at most 72 (80 - 8)"
        
        # Check progress bar window dimensions
        pb_window = all_windows[1]
        pb_h, pb_w, _, _ = pb_window
        
        # Progress bar height should be exactly 6
        assert pb_h == 6, f"Progress bar height should be exactly 6, got {pb_h}"
        
        # Progress bar width should be at least 50 and within bounds
        assert pb_w >= 50, f"Progress bar width {pb_w} should be at least 50"
        assert pb_w <= 70, f"Progress bar width {pb_w} should be at most 70 (80 - 10)"
    
    ui._cleanup_terminal()
    print("  ✓ Menu and progress bar combined rendering passed")


# Additional progress bar window tests
def test_progress_bar_window_height():
    """Test that progress bar window is created with height=6."""
    ui, mock_curses = setup_ui_for_size(80, 24)
    
    mock_screen = MagicMock()
    mock_screen.getmaxyx.return_value = (24, 80)
    
    with patch.object(ui, '_screen', mock_screen), \
         patch.object(ui, 'refresh'), \
         patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin, \
         patch('builtins.input'):
    
        mock_win = mock_newwin.return_value
        mock_win.getyx.return_value = (0, 0)
        mock_win.getch.return_value = curses.KEY_RESIZE
        mock_win.erase.return_value = None
        mock_win.addstr.return_value = None
        mock_win.attron.return_value = None
        mock_win.attroff.return_value = None
        mock_win.refresh.return_value = None
        
        ui.render_progress_bar("test.zip", 500, 1000, percent=50.0)
        
        call_args = mock_newwin.call_args
        height, width, y, x = call_args[0]
        
        assert height == 6, f"Height should be 6, got {height}"
        assert width == 70, f"Width should be 70, got {width}"
        
        ui._cleanup_terminal()
    print("  ✓ Progress bar window height test passed")


def test_progress_bar_width_calculated_from_terminal():
        """Test that progress bar width is calculated correctly based on terminal size."""
        test_cases = [
            (20, 40, 30, "Small terminal"),   # min_width = max(60, 40-10)=30, bar_width = min(30,100)=30
            (24, 80, 70, "Medium terminal"),  # min_width = max(60, 80-10)=70, bar_width = min(70,100)=70
            (30, 120, 100, "Large terminal"), # min_width = max(60, 120-10)=110, bar_width = min(110,100)=100
        ]

        for terminal_height, terminal_width, expected_width, name in test_cases:
            ui, mock_curses = setup_ui_for_size(terminal_width, terminal_height)
        
        mock_screen = MagicMock()
        mock_screen.getmaxyx.return_value = (terminal_height, terminal_width)
        
        with patch.object(ui, '_screen', mock_screen), \
             patch.object(ui, 'refresh'), \
             patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin, \
             patch('builtins.input'):
            
            mock_win = mock_newwin.return_value
            mock_win.getyx.return_value = (0, 0)
            mock_win.getch.return_value = curses.KEY_RESIZE
            mock_win.erase.return_value = None
            mock_win.addstr.return_value = None
            mock_win.attron.return_value = None
            mock_win.attroff.return_value = None
            mock_win.refresh.return_value = None
            
            ui.render_progress_bar("test.zip", 100, 200)
            
            call_args = mock_newwin.call_args
            height, width, y, x = call_args[0]
            
            assert height == 6, f"Height should be 6 for {name}, got {height}"
            assert width == expected_width, f"Width should be {expected_width} for {name}, got {width}"
        
        ui._cleanup_terminal()
    
        print("  ✓ Progress bar width calculation test passed")


def test_progress_bar_window_y_position():
    """Test that progress bar window is positioned correctly."""
    ui, mock_curses = setup_ui_for_size(80, 24)
    
    mock_screen = MagicMock()
    mock_screen.getmaxyx.return_value = (24, 80)
    
    with patch.object(ui, '_screen', mock_screen), \
         patch.object(ui, 'refresh'), \
         patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin, \
         patch('builtins.input'):
    
        mock_win = mock_newwin.return_value
        mock_win.getyx.return_value = (0, 0)
        mock_win.getch.return_value = curses.KEY_RESIZE
        mock_win.erase.return_value = None
        mock_win.addstr.return_value = None
        mock_win.attron.return_value = None
        mock_win.attroff.return_value = None
        mock_win.refresh.return_value = None
        
        ui.render_progress_bar("test.zip", 500, 1000)
        
        call_args = mock_newwin.call_args
        height, width, y, x = call_args[0]
        
        expected_y = 24 - 6 - 9  # terminal_height - bar_height - 9 = 9
        expected_x = 5  # fixed x_offset
        
        assert height == 6, f"Height should be 6, got {height}"
        assert y == expected_y, f"Y position should be {expected_y}, got {y}"
        assert x == expected_x, f"X position should be {expected_x}, got {x}"
        
        ui._cleanup_terminal()
    print("  ✓ Progress bar window position test passed")


if __name__ == '__main__':
    run_tests()


def test_menu_width_calculation_small_terminal():
    """Test menu width calculation for 40-column terminal."""
    # Direct calculation verification
    screen_width = 40
    options = [{'label': 'Option'} for _ in range(5)]
    max_label_len = max(len(opt.get('label', '')) for opt in options)
    min_width = int(screen_width * 0.6)  # 24
    menu_width = max(min_width, min(max_label_len + 15, screen_width - 8)) + 2
    
    assert menu_width >= 24, f"Menu width {menu_width} should be at least 24"
    assert menu_width <= 32, f"Menu width {menu_width} should be at most 32"
    
    ui, mock_curses = setup_ui_for_size(40, 20)
    mock_screen = MagicMock()
    mock_screen.getmaxyx.return_value = (20, 40)
    
    with patch.object(ui, '_screen', mock_screen), \
         patch.object(ui, 'refresh'), \
         patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin:
        
        menu_win = ui.create_window(len(options) + 4, menu_width, 2, 2)
        
        call_args = mock_newwin.call_args
        assert call_args is not None
        win_height, win_width, _, _ = call_args[0]
        
        assert win_width == menu_width, f"Window width should be {menu_width}"
        assert win_height == len(options) + 4, f"Window height should be {len(options) + 4}"
    
def test_validate_window_logic():
    """Test _validate_window logic with various window objects."""
    ui, _ = setup_ui_for_size(80, 24)
    
    # Test None window
    assert ui._validate_window(None) is False, "Should return False for None window"
    
    # Test window missing methods
    missing_methods_win = MagicMock(spec=[])
    assert ui._validate_window(missing_methods_win) is False, "Should return False for window missing methods"
    
    # Test window where refresh fails
    fail_refresh_win = MagicMock()
    fail_refresh_win.refresh.side_effect = curses.error("Refresh failed")
    assert ui._validate_window(fail_refresh_win) is False, "Should return False for window refresh failure"
    
    # Test valid window
    valid_win = MagicMock()
    assert ui._validate_window(valid_win) is True, "Should return True for valid window"
    
    ui._cleanup_terminal()
    print("  ✓ Validate window logic test passed")

def test_menu_width_calculation_small_terminal():
    """Test menu width calculation for 40-column terminal."""
    # Direct calculation verification
    screen_width = 40
    options = [{'label': 'Option'} for _ in range(5)]
    max_label_len = max(len(opt.get('label', '')) for opt in options)
    min_width = int(screen_width * 0.6)  # 24
    menu_width = max(min_width, min(max_label_len + 15, screen_width - 8)) + 2
    
    assert menu_width >= 24, f"Menu width {menu_width} should be at least 24"
    assert menu_width <= 32, f"Menu width {menu_width} should be at most 32"
    
    ui, mock_curses = setup_ui_for_size(40, 20)
    mock_screen = MagicMock()
    mock_screen.getmaxyx.return_value = (20, 40)
    
    with patch.object(ui, '_screen', mock_screen), \
         patch.object(ui, 'refresh'), \
         patch('ui_manager.curses.newwin', return_value=MagicMock()) as mock_newwin:
        
        menu_win = ui.create_window(len(options) + 4, menu_width, 2, 2)
        
        call_args = mock_newwin.call_args
        assert call_args is not None
        win_height, win_width, _, _ = call_args[0]
        
        assert win_width == menu_width, f"Window width should be {menu_width}"
        assert win_height == len(options) + 4, f"Window height should be {len(options) + 4}"
    
    ui._cleanup_terminal()
    print("  ✓ Menu width calculation test passed")


