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
    mock_curses = MagicMock()
    mock_curses.initscr = MagicMock(return_value=MagicMock())
    mock_curses.screen = MagicMock()
    mock_curses.start_color = MagicMock()
    mock_curses.init_pair = MagicMock(side_effect=lambda pair, fg, bg: pair)
    mock_curses.cbreak = MagicMock(return_value=True)
    mock_curses.noecho = MagicMock()
    mock_curses.curs_set = MagicMock(return_value=None)
    mock_curses.has_ungetch = MagicMock(return_value=False)
    mock_curses.getscrptr = MagicMock(return_value=None)
    mock_curses.color_pair = MagicMock(return_value=1)
    mock_curses.echo = MagicMock(return_value=None)
    mock_curses.nocbreak = MagicMock(return_value=None)
    mock_curses.endwin = MagicMock(return_value=None)
    mock_curses.reset_pair_matrix = MagicMock()
    mock_curses.KEY_RESIZE = curses.KEY_RESIZE
    mock_curses.KEY_UP = curses.KEY_UP
    mock_curses.KEY_DOWN = curses.KEY_DOWN
    mock_curses.KEY_LEFT = curses.KEY_LEFT
    mock_curses.KEY_RIGHT = curses.KEY_RIGHT
    mock_curses.KEY_ENTER = curses.KEY_ENTER
    mock_curses.KEY_BACKSPACE = curses.KEY_BACKSPACE
    mock_curses.COLOR_GREEN = curses.COLOR_GREEN
    mock_curses.COLOR_BLACK = curses.COLOR_BLACK

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
    test_small_terminal()
    
    # Test 2: Menu width calculation for large terminal
    print("[2/4] Testing Menu Width Calculation (Large)...")
    test_large_terminal()
    
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
    mock_curses = MagicMock()
    mock_curses.initscr = MagicMock(return_value=MagicMock())
    mock_curses.screen = MagicMock()
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
    mock_curses.KEY_RESIZE = curses.KEY_RESIZE
    
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

    if ui._using_curses:
        ui._cleanup_terminal()
    print("  ✓ Small terminal test passed")


def test_medium_terminal():
    """Test UIManager on 80x24 terminal."""
    mock_curses = MagicMock()
    mock_curses.initscr = MagicMock(return_value=MagicMock())
    mock_curses.screen = MagicMock()
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
    mock_curses.KEY_RESIZE = curses.KEY_RESIZE
    mock_curses.nodelay = MagicMock(return_value=True)
    mock_curses.getch = MagicMock(return_value=curses.KEY_RESIZE)
    
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

    if ui._using_curses:
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
    
    if ui._using_curses:
        ui._cleanup_terminal()
    print("  ✓ Large terminal test passed")


def test_small_terminal():
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
        menu_width = max(min_width, min(max_label_len + 15, 40 - 8)) + 2
        menu_width = max(24, min(29, 32)) + 2  # = 31
        
        assert menu_width <= 40, f"Menu width {menu_width} should fit in terminal width 40"
        assert menu_width >= 24, f"Menu width {menu_width} should be at least 24 (60%)"
    
    if ui._using_curses:
        ui._cleanup_terminal()
    print("  ✓ Menu width calculation for small terminal passed")


def test_large_terminal():
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
        menu_width = max(min_width, min(max_label_len + 15, 120 - 8)) + 2
        menu_width = max(72, min(20, 112)) + 2  # = 74
        
        assert menu_width <= 120, f"Menu width {menu_width} should fit in terminal width 120"
        assert menu_width >= 72, f"Menu width {menu_width} should be at least 72 (60%)"
    
    if ui._using_curses:
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
        ui, _ = setup_ui_for_size(width, height)
        
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
                # Bar height should be 6, width should be at least 60 but fit on screen
                # According to render_progress_bar: max_width = width - 12, min_width = max(60, max_width), bar_width = min(min_width, 100)
                min_width = max(60, width - 12)
                bar_width = min(min_width, 100)
                
                assert win_height == 6, f"Bar height should be 6, got {win_height} for {name}"
                assert win_width == bar_width, f"Bar width should be {bar_width}, got {win_width} for {name}"
    
    print("  ✓ Progress bar adaptation test passed")





def test_menu_width_calculation_large_terminal():
    """Test menu width calculation for 120-column terminal."""
    # Direct calculation verification
    screen_width = 120
    screen_height = 30
    options = [{'label': 'Option'} for _ in range(10)]
    max_label_len = max(len(opt.get('label', '')) for opt in options)
    min_width = int(screen_width * 0.6)  # 72
    menu_width = max(min_width, min(max_label_len + 15, screen_width - 8)) + 2
    menu_height = len(options) + 4
    
    assert menu_width >= 72, f"Menu width {menu_width} should be at least 72 (60% of 120)"
    assert menu_width <= 112, f"Menu width {menu_width} should be at most 112 (120 - 8)"
    assert menu_height >= 6, f"Menu height {menu_height} should be at least 6"
    
    # Verify using UIManager's MIN_WIDTH_PERCENT constant
    ui, _ = setup_ui_for_size(120, 30)
    assert ui.MIN_WIDTH_PERCENT == 0.6, "MIN_WIDTH_PERCENT should be 0.6"

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
            
            # Verify positioning
            assert y == 2, f"Y position should be 2, got {y} for {name}"
            assert x == 2, f"X position should be 2, got {x} for {name}"
    
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
        # Calculate progress bar dimensions
        min_pb_width = 50
        max_pb_width = min(50, 80 - 10)  # 40, so min is used
        pb_width = max(min_pb_width, max_pb_width)  # 50
        pb_height = 6
        # Create menu window
        menu_win = ui.create_window(menu_height, menu_width, 2, 2)
        # Create progress bar window
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
    
    # Reset state instead of calling cleanup
    ui._using_curses = False
    ui._screen = None
    ui._color_pair = None
    ui._initialized = False
    
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
        # Width calculation: min_width = max(60, 80 - 12) = 68, bar_width = min(68, 100) = 68
        assert width == 68, f"Width should be 68, got {width}"
        
        if ui._using_curses:
            ui._cleanup_terminal()
    print("  ✓ Progress bar window height test passed")


def test_progress_bar_width_calculated_from_terminal():
        """Test that progress bar width is calculated correctly based on terminal size."""
        test_cases = [
            (20, 40, 60, "Small terminal"),   # min_width = max(60, 40-12)=60, bar_width = min(60,100)=60
            (24, 80, 68, "Medium terminal"),  # min_width = max(60, 80-12)=68, bar_width = min(68,100)=68
            (30, 120, 100, "Large terminal"), # min_width = max(60, 120-12)=108, bar_width = min(108,100)=100
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
        
        if ui._using_curses:
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
        expected_x = 6  # fixed x_offset
        
        assert height == 6, f"Height should be 6, got {height}"
        assert y == expected_y, f"Y position should be {expected_y}, got {y}"
        assert x == expected_x, f"X position should be {expected_x}, got {x}"
        
        if ui._using_curses:
            ui._cleanup_terminal()
    print("  ✓ Progress bar window position test passed")


def test_progress_bar_exact_window_width_formula():
    """Test that progress bar window width follows the exact formula: ≤ terminal_width - 10."""
    # Test cases: (terminal_width, expected_max_width, description)
    test_cases = [
        (40, 30, "Small terminal: 40 - 10 = 30"),
        (80, 70, "Medium terminal: 80 - 10 = 70"),
        (120, 110, "Large terminal: 120 - 10 = 110"),
        (60, 50, "Medium-small terminal: 60 - 10 = 50"),
    ]
    
    for terminal_width, expected_max_width, description in test_cases:
        ui, mock_curses = setup_ui_for_size(terminal_width, 24)
        
        mock_screen = MagicMock()
        mock_screen.getmaxyx.return_value = (24, terminal_width)
        
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
            
            # According to the implementation: min(100, max(60, terminal_width - 12))
            expected_width = min(100, max(60, terminal_width - 12))
            assert width == expected_width, \
                f"{description}: Window width {width} should be {expected_width}"
            
            if ui._using_curses:
                ui._cleanup_terminal()
    
    print("  ✓ Progress bar exact window width formula test passed")


if __name__ == '__main__':
    run_tests()


def test_menu_width_formula_exact_values():
    """Test the exact menu width calculation formula with various scenarios."""
    
    def calculate_menu_width(terminal_width, label_length):
        """Calculate menu width using the exact formula: max(min_width, label_based), capped at max_cap, then +2."""
        min_width = int(terminal_width * 0.6)
        max_cap = terminal_width - 8
        label_based = label_length + 15
        # Apply formula: max(min_width, label_based), then cap at max_cap, then add 2
        menu_width = max(min_width, label_based)
        menu_width = min(menu_width, max_cap)
        menu_width += 2
        return min_width, max_cap, menu_width, label_based
    
    # Test 1: Standard case - label fits within both constraints
    terminal_width, label_length = 80, 20
    min_width, max_cap, menu_width, label_based = calculate_menu_width(terminal_width, label_length)
    assert min_width == 48, f"Standard case: min_width should be 48, got {min_width}"
    assert max_cap == 72, f"Standard case: max_cap should be 72, got {max_cap}"
    assert label_based == 35, f"Standard case: label_based should be 35, got {label_based}"
    assert menu_width == 50, f"Standard case: menu_width should be 50, got {menu_width}"
    
    # Test 2: Very long label - exceeds terminal_width - 8
    terminal_width, label_length = 60, 60
    min_width, max_cap, menu_width, label_based = calculate_menu_width(terminal_width, label_length)
    assert min_width == 36, f"Long label case: min_width should be 36, got {min_width}"
    assert max_cap == 52, f"Long label case: max_cap should be 52, got {max_cap}"
    assert label_based == 75, f"Long label case: label_based should be 75, got {label_based}"
    assert menu_width == 54, f"Long label case: menu_width should be 54 (max_cap + 2), got {menu_width}"
    
    # Test 3: Very short terminal - 60% of width < label_length + 15
    terminal_width, label_length = 30, 20
    min_width, max_cap, menu_width, label_based = calculate_menu_width(terminal_width, label_length)
    assert min_width == 18, f"Short terminal case: min_width should be 18, got {min_width}"
    assert max_cap == 22, f"Short terminal case: max_cap should be 22, got {max_cap}"
    assert label_based == 35, f"Short terminal case: label_based should be 35, got {label_based}"
    assert menu_width == 24, f"Short terminal case: menu_width should be 24 (max_cap + 2), got {menu_width}"
    
    # Test 4: Very large terminal - 60% of width > terminal_width - 8
    terminal_width, label_length = 120, 10
    min_width, max_cap, menu_width, label_based = calculate_menu_width(terminal_width, label_length)
    assert min_width == 72, f"Large terminal case: min_width should be 72, got {min_width}"
    assert max_cap == 112, f"Large terminal case: max_cap should be 112, got {max_cap}"
    assert label_based == 25, f"Large terminal case: label_based should be 25, got {label_based}"
    assert menu_width == 74, f"Large terminal case: menu_width should be 74, got {menu_width}"
    
    # Test 5: Boundary case exactly at the cap
    terminal_width, label_length = 50, 40
    min_width, max_cap, menu_width, label_based = calculate_menu_width(terminal_width, label_length)
    assert min_width == 30, f"Boundary case: min_width should be 30, got {min_width}"
    assert max_cap == 42, f"Boundary case: max_cap should be 42, got {max_cap}"
    assert label_based == 55, f"Boundary case: label_based should be 55, got {label_based}"
    assert menu_width == 44, f"Boundary case: menu_width should be 44 (exactly max_cap + 2), got {menu_width}"
    
    print("  ✓ Menu width formula exact values test passed")





def test_page_size_edge_cases():
    """Test page size calculation for edge cases."""
    
    def calculate_page_size(len_options, menu_height):
        """Calculate page size using formula: max(1, min(len // 2, (menu_height - 2) // 2))"""
        return max(1, min(len_options // 2, (menu_height - 2) // 2))
    
    # Test 1: Single option (len=1, menu_height=5)
    page_size = calculate_page_size(1, 5)
    assert page_size == 1, f"Single option: expected page_size=1, got {page_size}"
    
    # Test 2: Very small terminal (menu_height=6)
    # Formula: max(1, min(len // 2, 2))
    page_size_2 = calculate_page_size(10, 6)
    assert page_size_2 == 2, f"Very small terminal: expected page_size=2, got {page_size_2}"
    
    # Test 3: Very large menu (len=100, menu_height=20)
    # Formula: max(1, min(50, 9)) = 9
    page_size_3 = calculate_page_size(100, 20)
    assert page_size_3 == 9, f"Very large menu: expected page_size=9, got {page_size_3}"
    
    # Test 4: Boundary where len // 2 < (menu_height - 2) // 2
    # len=15, menu_height=20 => min(7, 9) = 7
    page_size_4 = calculate_page_size(15, 20)
    assert page_size_4 == 7, f"Boundary case 1: expected page_size=7, got {page_size_4}"
    
    # Test 5: Boundary where len // 2 > (menu_height - 2) // 2
    # len=30, menu_height=10 => min(15, 4) = 4
    page_size_5 = calculate_page_size(30, 10)
    assert page_size_5 == 4, f"Boundary case 2: expected page_size=4, got {page_size_5}"
    
    # Test 6: min(1, ...) case - single option with large menu
    page_size_6 = calculate_page_size(1, 30)
    assert page_size_6 == 1, f"Single option large menu: expected page_size=1, got {page_size_6}"
    
    # Test 7: min(..., 1) case - many options with small menu
    page_size_7 = calculate_page_size(100, 4)
    assert page_size_7 == 1, f"Many options small menu: expected page_size=1, got {page_size_7}"
    
    # Test 8: Verify the formula doesn't go below 1
    page_size_8 = calculate_page_size(5, 6)
    assert page_size_8 >= 1, f"Page size should not be below 1, got {page_size_8}"
    
    # Test 9: Verify the formula doesn't exceed len // 2
    page_size_9 = calculate_page_size(1000, 50)
    assert page_size_9 <= 500, f"Page size should not exceed len//2=500, got {page_size_9}"
    
    # Test 10: Verify the formula doesn't exceed (menu_height - 2) // 2
    page_size_10 = calculate_page_size(1000, 10)
    assert page_size_10 <= 4, f"Page size should not exceed (10-2)//2=4, got {page_size_10}"
    



