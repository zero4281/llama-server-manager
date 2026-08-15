#!/usr/bin/env python3
"""
uimanager.py — ncurses CLI user interface module.
This module provides ncurses-based UI rendering for menus, prompts,
progress bars, and other interactive elements with black background
and green text styling.
Key Code Reference
==================
All UIManager methods use standard curses key codes. Below is a quick reference:
### Navigation & Control Keys
| Key Code | Constant | Description | Used For |
|----------|----------|-------------|----------|
| `curses.KEY_UP` | KEY_UP | Move cursor up | Menu navigation, highlight selection |
| `curses.KEY_DOWN` | KEY_DOWN | Move cursor down | Menu navigation, highlight selection |
| `curses.KEY_LEFT` | KEY_LEFT | Move cursor left | Not used in menus |
| `curses.KEY_RIGHT` | KEY_RIGHT | Move cursor right | Not used in menus |
| `curses.KEY_PPAGE` | KEY_PPAGE | Page up | Jump to top of menu |
| `curses.KEY_NPAGE` | KEY_NPAGE | Page down | Jump to bottom of menu |
| `curses.KEY_ENTER` | KEY_ENTER | Enter key | Confirm selection, confirm actions |
| `curses.KEY_RESIZE` | KEY_RESIZE | Terminal resize | Cancel operation |
| `curses.KEY_BACKSPACE` | KEY_BACKSPACE | Backspace | Cancel operation |
### Cancel Keys (Escape, DEL, Backspace)
| Key Code | ASCII | Description |
|----------|-------|-------------|
| `curses.KEY_RESIZE` | 27 (Escape) | Cancel operation |
| `curses.KEY_BACKSPACE` | 127 (DEL) | Cancel operation |
| ASCII 27 | - | Escape key |
| ASCII 127 | - | DEL key |
| ASCII 8 | - | Backspace (alternative) |
| `ord('q')` | 113 | Cancel operation |
### Input Characters
| Character | ASCII | Description | Used For |
|-----------|-------|-------------|----------|
| `'0'` - `'9'` | 48-57 | Select option by number | Menu selection |
| `'y'` / `'Y'` | 121 | Confirm action | Confirmation dialogs |
| `'n'` / `'N'` | 110 | Cancel action | Confirmation dialogs |
### Other Control Keys
| Key Code | ASCII | Description | Used For |
|----------|-------|-------------|----------|
| ASCII 10 | - | LF/Enter | Confirm selection |
| ASCII 13 | - | CR/Enter | Confirm selection |
Main Methods:
- `render_menu(options, default, highlighted)`: Returns selected index or -1 (cancel)
- `render_confirmation(message, default)`: Returns True (confirm) or False (cancel)
- `render_progress_bar(filename, current, total)`: Waits for any key
- `render_success(message)`: Waits for any key
- `render_error(message)`: Waits for any key
- `print_simple_menu(options, default, highlighted)`: Returns selected index or None (cancel)
- `get_input(prompt)`: Returns input string
- `get_numbered_input(options, default)`: Returns selected index or None (cancel)
Usage Examples:
- Menu: Use arrow keys to navigate, type number to select, Enter to confirm, q/Esc to cancel
- Confirmation: Enter/Y to confirm, n/Esc to cancel
- Progress bars: Press any key to continue
"""

import logging
import curses
import sys
import time
from config import load_config


import os
from pathlib import Path
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

# Logging configuration
UI_MANAGER_DEBUG = os.environ.get("UI_MANAGER_DEBUG", "0").lower() in ("1", "true")
UI_MANAGER_LOG_LEVEL = logging.DEBUG if UI_MANAGER_DEBUG else logging.INFO


def _configure_logging():
    """Configure logging for UIManager."""
    if not logger.handlers:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(UI_MANAGER_LOG_LEVEL)


# Configure logging at module load time
_configure_logging()


def enable_debug_mode():
    """Enable debug logging for UIManager."""
    global UI_MANAGER_DEBUG, UI_MANAGER_LOG_LEVEL
    UI_MANAGER_DEBUG = True
    UI_MANAGER_LOG_LEVEL = logging.DEBUG
    logger.setLevel(logging.DEBUG)
    # Re-add handler with debug level
    if logger.handlers:
        handler = logger.handlers[0]
        handler.setLevel(logging.DEBUG)
    else:
        _configure_logging()


class UIManagerError(Exception):
    """Base exception for UIManager errors."""
    pass


class UIManager:
    """
    ncurses-based UI manager for rendering menus, prompts, and progress bars.
    
    Features:
    - Black background with green text (curses.COLOR_GREEN)
    - Numbered menu rendering with arrow key navigation
    - Confirmation prompts with Y/n handling
    - Progress bars with percentage and byte counts
    - Spinner animation for indeterminate progress
    - Proper initialization and cleanup
    - Fallback to console output if curses fails
    """

    # Constants
    WIDTH = 60
    TIMEOUT = 100
    MIN_WIDTH_PERCENT = 0.6
    MIN_HEIGHT_PERCENT = 0.5
    
    def __init__(self, title: Optional[str] = None):
        """
        Initialize the UI manager.
        
        Args:
            title: Optional title for windows
        """
        self._screen = None
        self._title = title or "Llama Server Wrapper"
        self._color_pair = None
        self._using_curses = False
        self._initialized = False
        self._progress_bar_win = None  # Store progress bar window reference
        
        try:
            # Initialize curses
            self._screen = curses.initscr()
            
            # Use alternate screen buffer for full-screen UI
            curses.start_color()
            curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
            self._color_pair = curses.color_pair(1) | curses.A_BOLD
            
            curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Reverse video
            
            # Set terminal mode for interactive curses
            try:
                curses.cbreak()
            except:
                pass
            
            curses.noecho()
            curses.curs_set(0)  # Hide cursor
            self._screen.timeout(100)  # 100ms timeout for key refresh
            
            self._using_curses = True
            self._initialized = True
            
        except (OSError, IOError, curses.error) as e:
            try:
                logger.error(f"Curses initialization failed: {e}")
                self._restore_terminal_state()
                print(f"Curses initialization failed: {e}", file=sys.stderr)
                self._using_curses = False
                self._screen = None
                self._color_pair = None
                self._initialized = False
            except Exception as restore_error:
                try:
                    logger.error(f"Error restoring terminal state: {restore_error}")
                except:
                    pass
        except AttributeError as e:
            # Handle partial initialization failures where curses attributes are missing
            try:
                logger.error(f"AttributeError during curses initialization: {e}")
                self._restore_terminal_state()
                print(f"AttributeError during initialization: {e}", file=sys.stderr)
                self._using_curses = False
                self._screen = None
                self._color_pair = None
                self._initialized = False
            except Exception as restore_error:
                try:
                    logger.error(f"Error restoring terminal state: {restore_error}")
                except:
                    pass

    def _restore_terminal_state(self):
        """Restore terminal to original state."""
        try:
            # Validate window if available before attempting operations
            if self._screen:
                if not self._validate_window(self._screen):
                    logger.warning("Screen window invalid, falling back to console")
                    self._using_curses = False
                    self._screen = None
                    self._color_pair = None
                    self._initialized = False
                    return
            
            # Reset terminal mode
            try:
                curses.echo()
                curses.nocbreak()
                curses.keypad(False)
            except (AttributeError, OSError) as e:
                logger.warning(f"Failed to reset terminal modes: {e}")
            
            # Reset terminal mode
            try:
                curses.echo()
                curses.nocbreak()
                curses.keypad(False)
            except (AttributeError, OSError) as e:
                logger.warning(f"Failed to reset terminal modes: {e}")
            
            try:
                curses.curs_set(1)  # Show cursor
            except (AttributeError, OSError) as e:
                logger.warning(f"Failed to set cursor: {e}")
            
            # Reset colors
            try:
                if hasattr(curses, 'reset_pair_matrix'):
                    curses.reset_pair_matrix()
            except (AttributeError, OSError) as e:
                logger.warning(f"Failed to reset color pairs: {e}")
            
            try:
                curses.endwin()
            except (AttributeError, OSError) as e:
                logger.warning(f"Failed to endwin: {e}")
        except (OSError, EOFError, TypeError) as e:
            logger.error(f"Error restoring terminal state: {e}")
        finally:
            self._screen = None
            self._color_pair = None
            self._using_curses = False
            self._initialized = False
            # Try to reset stty if available
            try:
                import subprocess
                subprocess.run(["stty", "sane"], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            except:
                pass
    
    def _cleanup_terminal(self):
        """Clean up curses and restore terminal."""
        # Clean up progress bar window first
        try:
            if self._progress_bar_win is not None:
                self._progress_bar_win = None
        except:
            pass
        
        if self._using_curses and self._screen:
            # Validate screen window before attempting cleanup
            if not self._validate_window(self._screen):
                logger.warning("Screen window invalid, forcing cleanup")
                self._screen = None
                self._color_pair = None
                self._using_curses = False
                self._initialized = False
            else:
                try:
                    self._restore_terminal_state()
                except (AttributeError, OSError) as e:
                    logger.warning(f"Failed to cleanup terminal: {e}")
                    # Force cleanup even if restoration fails
                    self._screen = None
                    self._color_pair = None
                    self._using_curses = False
                    self._initialized = False
        else:
            # Even if not initialized, ensure clean state
            self._screen = None
            self._color_pair = None
            self._using_curses = False
            self._initialized = False

    def __del__(self):
        """Cleanup curses resources."""
        try:
            self._cleanup_terminal()
        except:
            pass

    def refresh(self):
        """Refresh screen."""
        if self._using_curses and self._screen:
            try:
                self._screen.refresh()
            except OSError as e:
                logger.error(f"Screen refresh error: {e}")
                try:
                    self._cleanup_terminal()
                except:
                    pass
            except (OSError, EOFError, TypeError) as e:
                logger.error(f"Unexpected error during screen refresh: {e}")
                # Don't attempt cleanup during cancel sequences to avoid geth() exhaustion
                pass

    def clear(self):
        """Clear screen."""
        if self._using_curses and self._screen:
            try:
                self._screen.erase()
            except:
                pass

    def _get_white_attr(self):
        """Get the white attribute for use when curses is initialized."""
        if self._using_curses and self._color_pair is not None:
            try:
                return curses.color_pair(1) | curses.A_BOLD | curses.A_REVERSE
            except (OSError, AttributeError):
                # Fallback to just bold attribute if color_pair fails
                return curses.A_BOLD
        return None
    
    def _validate_window(self, win) -> bool:
        """
        Validate if a window is usable before operations.
        
        Args:
            win: Window to validate
            
        Returns:
            True if window is valid, False otherwise
        """
        if win is None:
            return False
        
        # Check if window has required methods
        required_methods = ['box', 'refresh', 'getch', 'addstr']
        for method in required_methods:
            if not hasattr(win, method) or not callable(getattr(win, method)):
                logger.warning(f"Window missing required method: {method}")
                return False
        
        # Try to refresh to verify window is valid
        try:
            win.refresh()
            return True
        except (OSError, AttributeError):
            logger.warning("Window refresh failed, likely invalid")
            return False

    def print_message(self, text: str, level: str = "info", y: int = 1, x: int = 1):
        """Print message at specific position with color and log it."""
        level_map = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
            "critical": logging.CRITICAL
        }
        log_level = level_map.get(level.lower(), logging.INFO)
        logger.log(log_level, text)

        if not self._using_curses:
            if level.lower() in ("warning", "error", "critical"):
                print(text, file=sys.stderr)
            else:
                print(text)
            return
            
        if not self._screen:
            return
            
        try:
            self._screen.attron(self._color_pair)
            self._screen.addstr(y, x, text)
            self._screen.attroff(self._color_pair)
            self._screen.refresh()
        except (OSError, EOFError, TypeError) as e:
            logger.error(f"Unexpected error during message rendering: {e}")
            print(text)

    def create_window(self, height: int, width: int, y: int, x: int, title: Optional[str] = None) -> Optional[curses.window]:
        """
        Create a bordered window with proper padding.
        
        Args:
            height, width: Window dimensions
            y, x: Position
            title: Optional title line
            
        Returns:
            curses.window object
        """
        if not self._using_curses:
            return None
            
        if not self._screen:
            return None
            
        try:
            win = curses.newwin(height, width, y, x)
            win.box()
            
            if title:
                # Title goes in row 0, border in row 1
                # Add internal padding: title at column 2, separator at column 2
                win.addstr(0, 2, title.center(width - 4))
                win.addstr(1, 2, "-" * (width - 6))
            
            return win
        except OSError as e:
            logger.error(f"Window creation error at ({y},{x}) {height}x{width}: {e}")
            return None
        except (OSError, EOFError, TypeError) as e:
            logger.error(f"Unexpected error during window creation: {e}")
            return None

    def _is_terminal_in_cbreak(self) -> bool:
        """
        Check if terminal is already in cbreak mode without causing ERR.
        
        Returns:
            True if terminal is in cbreak mode, False otherwise
        """
        # Use non-blocking read to check terminal state
        try:
            self._screen.nodelay(True)
            key = self._screen.getch()
            self._screen.nodelay(False)
            # KEY_RESIZE (27) indicates cbreak mode
            return key == curses.KEY_RESIZE or key == 27
        except (OSError, EOFError):
            return False
    
    def _safe_keypad(self, win, enable: bool) -> bool:
        """
        Safely enable/disable keypad mode with error handling.
        
        Args:
            win: Window to modify
            enable: True to enable keypad mode, False to disable
            
        Returns:
            True if operation succeeded, False otherwise
        """
        try:
            win.keypad(enable)
            return True
        except (AttributeError, OSError, IOError) as e:
            logger.warning(f"Keypad operation failed: {e}")
            # Try to recover by refreshing the window
            try:
                win.refresh()
                return True
            except:
                return False
    
    def _ensure_terminal_ready(self) -> bool:
        """
        Ensure terminal is in proper state for curses operations.
        
        Returns:
            True if terminal is ready, False if we should fallback to console
        """
        try:
            # Check if terminal is in cbreak mode
            in_cbreak = self._is_terminal_in_cbreak()
            
            if not in_cbreak:
                try:
                    curses.cbreak()
                except (OSError, IOError, AttributeError, curses.error):
                    # In mocked environments, cbreak may fail
                    # This is acceptable - we can still operate if we have a valid screen
                    pass
            
            # Enable keypad mode on the main screen for arrow keys, Page Up/Down, Escape
            if self._screen:
                try:
                     if hasattr(curses, 'keypad'):
                         self._screen.keypad(True)
                except (OSError, IOError, AttributeError):
                    # In mocked environments, keypad may fail
                    # This is acceptable - we can still operate if we have a valid screen
                    pass
            
            return True
        except (OSError, IOError, AttributeError):
            # If we can't even perform basic validation, fallback
            return False
    
    def render_menu(self, options: List[Dict[str, Any]], 
                    default: Optional[int] = None,
                    highlighted: Optional[int] = None,
                    title: Optional[str] = None) -> int:
        """
        Render a numbered menu with options.
        
        Args:
            options: List of dictionaries with 'label' and optional 'description'
            default: Index of default option (appends '(default)')
            highlighted: Index of currently highlighted option
            
        Returns:
            Selected option index, or -1 if cancelled
        
        Supported Key Codes:
            - Navigation: KEY_UP (259), KEY_DOWN (258), KEY_PPAGE (339), KEY_NPAGE (338)
            - Enter: KEY_ENTER (343, 10, 13)
            - Cancel: 27 (Escape), ord('q') (113), KEY_RESIZE (410), KEY_BACKSPACE (263, 127, 8)
            - Selection: '0'-'9' (ASCII 48-57)
        """
        start_time = time.time()
        logger.debug(f"render_menu: options_count={len(options)}, default={default}, highlighted={highlighted}")
        
        # Return -1 immediately for empty options list
        if len(options) == 0:
            return -1
        
        # Check for non-interactive mode or curses failure at the start
        if (not sys.stdin.isatty() and not self._using_curses) or not self._screen:
            logger.warning(f"render_menu: stdin is not a TTY and curses not initialized, returning -1")
            return -1
        
        # Ensure terminal is ready before rendering
        if self._using_curses and self._screen:
            if not self._ensure_terminal_ready():
                logger.warning("Terminal not ready, falling back to console")
                # Force console fallback
                self._using_curses = False
                self._screen = None
        
        # Console fallback
        if not self._using_curses or not self._screen:
            # Reset terminal
            try:
                self._cleanup_terminal()
            except:
                pass
            
            # Clear and display menu
            print("\033[2J\033[H", end="")
            for i, opt in enumerate(options):
                marker = " (default)" if default is not None and i == default else ""
                label = opt.get('label', '')
                desc = opt.get('description', '')
                full_label = f"  {i}. {label}{marker}"
                print(full_label)
                if desc:
                    print(f"     {desc}")
            
            # Prompt
            print(f"Choice [{highlighted if highlighted is not None else 0}]: ", end="", flush=True)
            try:
                if sys.stdin.isatty():
                    # Use non-blocking read for fallback
                    import os
                    choice_str = ""
                    try:
                        data = os.read(0, 1)
                        if data:
                            choice_str = data.decode('utf-8').strip()
                    except (OSError, EOFError):
                        try:
                            data = sys.stdin.read(1)
                            if data:
                                choice_str = data.strip()
                        except (OSError, EOFError):
                            pass
                else:
                    choice_str = ""
            except:
                choice_str = ""
            
            try:
                idx = int(choice_str)
                return idx if 0 <= idx < len(options) else -1
            except ValueError:
                return -1

        # Create menu window
        self._screen.erase()
        self._screen.refresh()  # Force full screen refresh to clear old content
        screen_height, screen_width = self._screen.getmaxyx()
        max_label_len = max(len(opt.get('label', '')) for opt in options) if options else 20
        min_width = int(screen_width * self.MIN_WIDTH_PERCENT)
        menu_width = max(min_width, min(max_label_len + 15, screen_width - 8)) + 2
        content_width = menu_width - 4
        
        total_options_height = 0
        option_heights = []
        for i, opt in enumerate(options):
            label = opt.get('label', '')
            desc = opt.get('description', '')
            marker = " (default)" if default is not None and i == default else ""
            full_label = f"  {i}. {label}{marker}"
            
            label_lines = (len(full_label) + content_width - 1) // content_width
            desc_lines = (len(desc) + content_width - 1) // content_width if desc else 0
            
            height = label_lines + desc_lines
            option_heights.append(height)
            total_options_height += (height + (1 if desc else 0))

        menu_height = total_options_height + 4
        
        # Calculate centered position
        y_center = max(2, (screen_height - menu_height) // 2)
        x_center = max(2, (screen_width - menu_width) // 2)
        
        y_offset = 2
        x_offset = 4
        highlighted_idx = highlighted if highlighted is not None else 0
        
        # Define redraw function
        def redraw(win, hi_idx):
            try:
                logger.debug(f"Redraw called: win={win}, hi_idx={hi_idx}, options_count={len(options)}")
                curses.curs_set(0) # It's possible that this is needed because the cursor is getting displayed as part of a captured error.
                
                # Validate window before operations
                if not self._validate_window(win):
                    logger.warning("Window validation failed in redraw")
                    try:
                        self._cleanup_terminal()
                    except:
                        pass
                    raise Exception("Window invalid")
                
                # Clear the window content (inside the border)
                win.erase()
                
                # Redraw the border with box() to ensure it's properly drawn
                win.box()
                
                box_width = menu_width - (x_offset * 2)
                
                white_attr = self._get_white_attr()
                if white_attr is not None:
                    win.attron(white_attr)
                    display_title = title if title is not None else self._title
                    win.addstr(0, x_offset, display_title.center(box_width))
                    win.attroff(white_attr)
                    win.addstr(1, 1, "-" * (menu_width - 2))
                current_y = 2
                for i, opt in enumerate(options):
                    label = opt.get('label', '')
                    desc = opt.get('description', '')
                    marker = " (default)" if default is not None and i == default else ""
                    full_label = f"  {i}. {label}{marker}"
                    
                    if i == hi_idx:
                        win.attron(self._color_pair | curses.A_BOLD | curses.A_REVERSE)
                        win.addstr(current_y, x_offset, full_label)
                        if desc:
                            win.addstr(current_y + (len(full_label) + content_width - 1) // content_width, x_offset, desc)
                        win.attroff(self._color_pair | curses.A_BOLD | curses.A_REVERSE)
                    else:
                        win.attron(self._color_pair)
                        win.addstr(current_y, x_offset, full_label)
                        if desc:
                            win.addstr(current_y + (len(full_label) + content_width - 1) // content_width, x_offset, desc)
                        win.attroff(self._color_pair)
                    
                    current_y += option_heights[i] + (1 if options[i].get('description') else 0)
                
                footer = "Use arrow keys to navigate, type number to select, Enter to confirm, q to cancel"
                truncated_footer = footer[:box_width] if len(footer) > box_width else footer
                centered_footer = truncated_footer.center(box_width)
                win.addstr(menu_height - 1, x_offset, centered_footer, curses.A_REVERSE)
                
                win.refresh()
                logger.debug(f"Redraw completed successfully")
            except OSError as e:
                logger.error(f"OSError during redraw: {e}")
                try:
                    # Try to recover
                    if hasattr(win, 'refresh'):
                        try:
                            win.refresh()
                        except:
                            pass
                    self._screen.refresh()
                except:
                    pass
                # Continue with redraw - don't raise
                return
            except (OSError, EOFError, TypeError) as e:
                logger.error(f"Unexpected error during redraw: {e}")
                # Don't raise - continue with current state
                return

        try:
            logger.debug(f"Creating menu window: size={menu_height}x{menu_width}, pos=({y_center},{x_center})")
            menu_win = self.create_window(menu_height, menu_width, y_center, x_center)
            logger.debug(f"Window created: {menu_win}")
            
            if menu_win is None:
                logger.error("Menu window creation failed")
                try:
                    self._cleanup_terminal()
                except:
                            pass
                            return -1
            
            # Safely enable keypad mode with error handling
            if self._safe_keypad(menu_win, True):
                logger.debug("Keypad mode enabled successfully")
            else:
                logger.warning("Keypad mode failed to enable, attempting recovery")
                # Try to recover by refreshing
                try:
                    menu_win.refresh()
                    logger.debug("Window recovered after refresh")
                except:
                    logger.error("Window recovery failed, cleaning up")
                    try:
                        self._cleanup_terminal()
                    except:
                        pass
                    return -1
            
            logger.debug(f"Redrawing menu with highlighted index: {highlighted_idx}")
            redraw(menu_win, highlighted_idx)
            logger.debug(f"Menu redraw completed")
            
            # Log menu state for debugging
            logger.debug(f"Menu initialized: options_count={len(options)}, default={default}, highlighted={highlighted_idx}")
        except (AttributeError, OSError) as e:
            logger.error(f"Menu window creation error: {e}")
            try:
                self._cleanup_terminal()
            except:
                pass
            return -1
        except (OSError, EOFError, TypeError) as e:
            logger.error(f"Unexpected error during menu rendering: {e}")
            try:
                self._cleanup_terminal()
            except:
                pass
            return -1
        
        # Validate curses and terminal before input loop
        if not self._validate_window(menu_win):
            logger.warning("Menu window validation failed before input loop, returning -1")
            try:
                self._cleanup_terminal()
            except:
                pass
            return -1
        
        # Validate screen window before proceeding
        if not self._validate_window(self._screen):
            logger.warning("Screen window invalid, returning -1")
            try:
                self._cleanup_terminal()
            except:
                pass
            return -1
        
        # Input loop
        try:
            logger.debug("Starting render_menu input loop")
            while True:
                # Check if window is still valid before getting key
                if not hasattr(menu_win, 'getch') or not callable(menu_win.getch):
                    logger.warning(f"Window getch method not available, cleaning up and returning")
                    try:
                        self._cleanup_terminal()
                    except:
                        pass
                    return -1
                
                try:
                    key = menu_win.getch()
                    logger.debug(f"DEBUG: getch() returned key={key}")
                except (AttributeError, OSError, EOFError, TypeError, StopIteration) as e:
                    logger.error(f"Menu getch() error: {e}")
                    # Mocked or exhausted getch side-effects raise StopIteration;
                    # treat as a clean cancel so callers/tests don't crash.
                    if isinstance(e, StopIteration):
                        logger.debug("getch raised StopIteration (mock exhausted or EOF), returning -1")
                        return -1
                    # Try to recover before giving up
                    try:
                        # Attempt to refresh and recover
                        menu_win.refresh()
                        logger.debug("Attempted getch recovery via refresh")
                        # Retry once
                        key = menu_win.getch()
                        if key is not None:
                            logger.debug(f"Recovery successful, got key={key}")
                            # Continue with the key
                            if key is None:
                                logger.debug("Recovery got None, cleaning up")
                                try:
                                    self._cleanup_terminal()
                                except Exception:
                                    pass
                                return -1
                        continue  # Exit the while loop iteration and go back to the start
                    except:
                        logger.error("Recovery failed")
                
                # Log the raw key value with additional details for debugging
                if key is not None:
                    if isinstance(key, int):
                        # Determine key type for better logging
                        key_type = "UNKNOWN"
                        key_name = ""
                        
                        # Check for known key codes first
                        if key in (curses.KEY_UP, 259):
                            key_type = "KEY_UP"
                            key_name = "UP"
                        elif key in (curses.KEY_DOWN, 258):
                            key_type = "KEY_DOWN"
                            key_name = "DOWN"
                        elif key in (curses.KEY_LEFT, 260):
                            key_type = "KEY_LEFT"
                            key_name = "LEFT"
                        elif key in (curses.KEY_RIGHT, 261):
                            key_type = "KEY_RIGHT"
                            key_name = "RIGHT"
                        elif key in (curses.KEY_ENTER, 343, 10, 13):
                            key_type = "KEY_ENTER"
                            key_name = "ENTER"
                        elif key in (27, curses.KEY_RESIZE, 410):
                            key_type = "CANCEL_KEY"
                            return -1
                        elif key in (curses.KEY_PPAGE, 339):
                            key_type = "KEY_PPAGE"
                            key_name = "PAGE_UP"
                        elif key in (curses.KEY_NPAGE, 338):
                            key_type = "KEY_NPAGE"
                            key_name = "PAGE_DOWN"
                        elif key in (curses.KEY_BACKSPACE, 263, 127, 8):
                            key_type = "BACKSPACE"
                            key_name = "BACKSPACE"
                        
                        # Check for numeric keys (0-9) - ASCII codes 48-57
                        elif key >= ord('0') and key <= ord('9'):
                            key_type = "NUMERIC"
                            key_name = f"DIGIT({chr(key)})"
                            selection = int(chr(key))
                            if 0 <= selection < len(options):
                                old_highlighted = highlighted_idx
                                highlighted_idx = selection
                                logger.debug(f"State change: highlighted_idx {old_highlighted} -> {highlighted_idx}")
                                try:
                                    redraw(menu_win, highlighted_idx)
                                except Exception as redraw_error:
                                    logger.error(f"Redraw failed after numeric key {key_name}: {redraw_error}")
                                continue
                        
                        # Check for character keys (printable ASCII)
                        elif 32 <= key < 127:
                            key_type = "CHAR"
                            key_name = f"'{chr(key)}'"
                        
                        # For unknown keys, use hex representation
                        else:
                            char_repr = chr(key) if 32 <= key < 127 else f'0x{key:02X}'
                            key_type = f"UNKNOWN({key})"
                            key_name = char_repr
                        
                        logger.debug(f"Input loop iteration: key={key}, type={type(key).__name__}, key_type={key_type}, key_name={key_name}, hex=0x{key:02X}")
                    else:
                        logger.debug(f"Input loop iteration: key={key}, type={type(key).__name__}")
                else:
                    logger.debug(f"Input loop iteration: key=None (EOF/timeout)")
                

                
                # Handle navigation and control keys
                if key == curses.KEY_UP:
                    # Move up one option
                    old_hi = highlighted_idx
                    if highlighted_idx > 0:
                        highlighted_idx -= 1
                    else:
                        highlighted_idx = len(options) - 1  # Wrap to last
                    logger.debug(f"Navigation: UP key, {old_hi} -> {highlighted_idx}")
                    try:
                        redraw(menu_win, highlighted_idx)
                    except Exception as redraw_error:
                        logger.error(f"Redraw failed after UP key: {redraw_error}")
                    continue
                
                if key == curses.KEY_PPAGE:
                    # Page up - move up half the visible menu
                    old_hi = highlighted_idx
                    # Calculate page size based on screen height and menu size
                    page_size = max(1, min(len(options) // 2, (menu_height - 2) // 2))
                    new_idx = highlighted_idx - page_size
                    if new_idx < 0:
                        # Wrap to end
                        highlighted_idx = (len(options) - 1) - ((abs(new_idx) - 1) % len(options))
                    else:
                        highlighted_idx = new_idx
                    logger.debug(f"Navigation: PAGE UP key, {old_hi} -> {highlighted_idx}")
                    try:
                        redraw(menu_win, highlighted_idx)
                    except Exception as redraw_error:
                        logger.error(f"Redraw failed after PAGE UP key: {redraw_error}")
                    continue
                
                if key == curses.KEY_DOWN:
                    # Move down one option
                    old_hi = highlighted_idx
                    if highlighted_idx < len(options) - 1:
                        highlighted_idx += 1
                    else:
                        highlighted_idx = 0  # Wrap to first
                    logger.debug(f"Navigation: DOWN key, {old_hi} -> {highlighted_idx}")
                    try:
                        redraw(menu_win, highlighted_idx)
                    except Exception as redraw_error:
                        logger.error(f"Redraw failed after DOWN key: {redraw_error}")
                    continue
                
                if key == curses.KEY_NPAGE:
                    # Page down - move down half the visible menu
                    old_hi = highlighted_idx
                    # Calculate page size based on screen height and menu size
                    page_size = max(1, min(len(options) // 2, (menu_height - 2) // 2))
                    new_idx = highlighted_idx + page_size
                    if new_idx < len(options):
                        highlighted_idx = new_idx
                    else:
                        # Wrap to beginning
                        highlighted_idx = new_idx % len(options)
                    logger.debug(f"Navigation: PAGE DOWN key, {old_hi} -> {highlighted_idx}")
                    try:
                        redraw(menu_win, highlighted_idx)
                    except Exception as redraw_error:
                        logger.error(f"Redraw failed after PAGE DOWN key: {redraw_error}")
                    continue
                
                if key in (curses.KEY_ENTER, 10, 13):
                    # Confirm selection (Enter key - various codes)
                    logger.debug(f"Confirmation requested: highlighted={highlighted_idx}, options={len(options)}")
                    selected_option = options[highlighted_idx] if 0 <= highlighted_idx < len(options) else None
                    logger.debug(f"Selected option: {selected_option}")
                    try:
                        self._screen.refresh()
                    except (OSError, EOFError):
                        pass
                    return highlighted_idx
                
                if key == 27 or key == ord('q') or key == curses.KEY_RESIZE:
                    # Cancel
                    logger.debug(f"Cancellation requested: key={key}, current_highlighted={highlighted_idx}")
                    return -1
                
                if key == curses.KEY_BACKSPACE or key == 127 or key == 8:
                    # Backspace - cancel
                    logger.debug(f"Backspace received: cancelling, current_highlighted={highlighted_idx}")
                    return -1

                # Timeout - redraw to refresh display
                try:
                    redraw(menu_win, highlighted_idx)
                except Exception as redraw_error:
                    logger.error(f"Redraw failed on timeout: {redraw_error}")

                # Small delay to prevent rapid redraws
                curses.napms(10) if hasattr(curses, 'napms') else None
                continue  # Go back to the start of the while loop
                
        except (OSError, EOFError, TypeError) as e:
            logger.error(f"Menu input loop error: {e}")
            # Clear screen and fall back to console
            logger.warning(f"Falling back to console mode due to error: {e}")
            try:
                self._cleanup_terminal()
            except:
                pass
            for i, opt in enumerate(options):
                marker = " (default)" if default is not None and i == default else ""
                print(f"  {i}. {opt}{marker}")
            try:
                # Use non-blocking read for fallback
                import os
                choice_str = ""
                try:
                    data = os.read(0, 1)
                    if data:
                        choice_str = data.decode('utf-8').strip()
                except (OSError, EOFError):
                    try:
                        data = sys.stdin.read(1)
                        if data:
                            choice_str = data.strip()
                    except (OSError, EOFError):
                        pass
                idx = int(choice_str)
                return idx if 0 <= idx < len(options) else -1
            except Exception as input_error:
                logger.error(f"Console fallback error: {input_error}")
                return -1
            try:
                self._cleanup_terminal()
            except:
                pass
            return -1
        except (OSError, EOFError, TypeError) as e:
            logger.error(f"Unexpected error during menu rendering: {e}")
            try:
                self._cleanup_terminal()
            except:
                pass
            return -1

    def _render_console_fallback(self, message: str, prompt: str = "", prompt_suffix: str = "") -> Optional[str]:
        """
        Unified console fallback renderer.
        
        Args:
            message: The main message to display
            prompt: Optional prompt text
            prompt_suffix: Optional suffix after prompt
            
        Returns:
            Depending on method context: bool for confirmation, str for input
        """
        try:
            self._cleanup_terminal()
            import subprocess
            subprocess.run(["stty", "sane"], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            subprocess.run(["stty", "-icanon", "echo", "cr"], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            
            print("\033[2J\033[1;1H\n", end="")
            sys.stdout.flush()
            
            if prompt:
                print(f"{message}")
                print(prompt + prompt_suffix, end="", flush=True)
            else:
                print(f"{message}")
            
            if sys.stdin.isatty():
                import select
                ready, _, _ = select.select([sys.stdin], [], [], 0.5)
                if ready:
                    response = sys.stdin.readline().strip().lower()
                else:
                    response = ""
            else:
                response = ""
            
            return response
        except Exception:
            print(f"{message}")
            if prompt:
                response = input(prompt).strip().lower()
            else:
                response = input().strip().lower()
            return response
    
    def _render_confirmation_fallback(self, message: str, default: bool = True) -> bool:
        """
        Fallback for confirmation prompts.
        """
        response = self._render_console_fallback(message, "Proceed? [Y/n]: ")
        return response in ('y', 'yes') or (response == '' and default)
    
    def render_confirmation(self, message: str, release_info: str, title: str = "Confirm Installation", default: bool = True) -> bool:
        """
        Render a confirmation prompt.
        
        Args:
            message: The message to display
            default: If True, Enter = yes, 'n' = no
            
        Returns:
            True if confirmed, False if cancelled
        """
        try:
            
            # Validate screen and window upfront
            if not self._screen:
                logger.debug(f"Screen not found for confirmation window")
                return self._render_confirmation_fallback(message+"\n"+release_info, default)
            
            height, width = self._screen.getmaxyx()
            
            # Clear screen
            self._screen.erase()
            self._screen.refresh()  # Force full screen refresh to clear old content
            
            # Create the window
            width_int = int(width)
            msg_width = int(min(width_int - 4, max(width_int * self.MIN_WIDTH_PERCENT, 60)))
            
            # Calculate centered position
            screen_height, screen_width = self._screen.getmaxyx()
            menu_height = 8
            
            # Calculate menu width: screen_width + padding, but ensure minimum percentage and fit on screen
            min_width = int(screen_width * self.MIN_WIDTH_PERCENT)
            menu_width = max(min_width, min(msg_width + 15, screen_width - 8)) + 2
            
            y_center = max(2, (screen_height - menu_height) // 2)
            x_center = max(2, (screen_width - menu_width) // 2)

            prompt_win = self.create_window(menu_height, menu_width, y_center, x_center)
            if prompt_win is None:
                logger.error("Confirmation window creation failed")
                return self._render_confirmation_fallback(message, default)
            
            # Safely enable keypad mode
            if self._safe_keypad(prompt_win, True):
                logger.debug("Keypad mode enabled for confirmation window")
            else:
                logger.warning("Keypad mode failed for confirmation window")
                
            white_attr = self._get_white_attr()
            
            # Define redraw function for Yes/No menu
            def redraw(hi_idx):
                try:
                    # Validate window before operations
                    if not self._validate_window(prompt_win):
                        logger.warning("Window validation failed in redraw")
                        try:
                            self._cleanup_terminal()
                        except:
                            pass
                        raise Exception("Window invalid")
                    
                    # Clear the window content (inside the border)
                    prompt_win.erase()
                    
                    # Redraw the border with box() to ensure it's properly drawn
                    prompt_win.box()
                    
                    box_width = menu_width - 6
                    
                    # Title - row 0, centered with padding
                    if white_attr is not None:
                         prompt_win.attron(white_attr)
                         prompt_win.addstr(0, 3, title.center(box_width))
                         prompt_win.attroff(white_attr)
                         prompt_win.addstr(1, 1, "-" * (menu_width - 2))
                    
                    # Message - row 2, centered with padding
                    truncated_msg = message[:box_width] if len(message) > box_width else message
                    centered_msg = truncated_msg.center(box_width)
                    prompt_win.addstr(2, 3, centered_msg)
                    
                    # Release INfo - row 3, centered with padding
                    try:
                        truncated_release_info = release_info[:box_width] if len(release_info) > box_width else release_info
                        centered_release_info = truncated_release_info.center(box_width)
                        prompt_win.addstr(3, 3, centered_release_info)
                    except OSError:
                        pass
                    
                    # Yes/No options - row 5, centered with padding
                    # Calculate positions for two buttons on one line
                    button_width = 10  # width of "  [ Yes ]"
                    button_spacing = 4  # space between buttons
                
                    # Center the pair of buttons
                    pair_width = button_width * 2 + button_spacing
                    button_start_x = 2 + (menu_width - pair_width) // 2
                    
                    # Render Yes button
                    yes_x = button_start_x
                    if hi_idx == 0:
                        prompt_win.attron(self._color_pair | curses.A_BOLD | curses.A_REVERSE)
                    prompt_win.addstr(5, yes_x, f"[ Yes ]")
                    prompt_win.attroff(self._color_pair | curses.A_BOLD | curses.A_REVERSE)
                    
                    # Render No button
                    no_x = yes_x + button_width + button_spacing
                    if hi_idx == 1:
                        prompt_win.attron(self._color_pair | curses.A_BOLD | curses.A_REVERSE)
                    prompt_win.addstr(5, no_x, f"[ No  ]")
                    prompt_win.attroff(self._color_pair | curses.A_BOLD | curses.A_REVERSE)
                    
                    # Footer - row 7, centered with padding
                    footer = "Use arrow keys to navigate, Enter to confirm, q/ESC to cancel"
                    truncated_footer = footer[:box_width + 4] if len(footer) > box_width + 4 else footer
                    centered_footer = truncated_footer.center(box_width)
                    prompt_win.addstr(7, 3, centered_footer, curses.A_REVERSE)
                    
                    prompt_win.refresh()
                except (OSError, EOFError, TypeError):
                    pass
                except Exception:
                    pass
            
            # Initial state
            highlighted_idx = 0
            redraw(highlighted_idx)
            
            # Input loop
            while True:
                
                try:
                    key = prompt_win.getch()
                except (OSError, EOFError) as e:
                    logger.error(f"Confirmation getch() error: {e}")
                    continue
                
                # Handle key input
                if key == curses.KEY_DOWN or key ==  curses.KEY_RIGHT:
                    # Move to No option
                    highlighted_idx = 1
                    redraw(highlighted_idx)
                    continue
                
                if key == curses.KEY_UP or key ==  curses.KEY_LEFT:
                    # Move to Yes option
                    highlighted_idx = 0
                    redraw(highlighted_idx)
                    continue
                
                if key in (curses.KEY_ENTER, 10, 13):
                    # Confirm selection (Yes if highlighted_idx == 0)
                    logger.debug(f"Confirmation: ENTER pressed, highlighted={highlighted_idx}, returning {highlighted_idx == 0}")
                    self._screen.erase()
                    self._screen.refresh()
                    return highlighted_idx == 0
                
                if key == 27 or key == curses.KEY_RESIZE or key == curses.KEY_BACKSPACE:
                    # Cancel
                    logger.debug("Confirmation: ESC/RESIZE/BACKSPACE pressed, canceling")
                    self._screen.erase()
                    return False
                
                if key in (ord('y'), ord('Y')):
                    # Confirm (Yes)
                    logger.debug("Confirmation: 'y' pressed, confirming")
                    self._screen.erase()
                    self._screen.refresh()
                    return True
                
                if key in (ord('n'), ord('N')):
                    # Cancel (No)
                    logger.debug("Confirmation: 'n' pressed, canceling")
                    self._screen.erase()
                    self._screen.refresh()
                    return False
                
                # Timeout - redraw to refresh display
                redraw(highlighted_idx)
        except (OSError, EOFError, TypeError) as e:
            logger.error(f"Unexpected error during confirmation: {e}")
            return self._render_confirmation_fallback(message, default)
        except Exception as e:
            logger.error(f"Unexpected error during confirmation: {e}")
            return self._render_confirmation_fallback(message, default)

    def render_progress_bar(self, filename: str, current: int, total: int, 
                          speed: Optional[float] = None,
                          percent: Optional[float] = None,
                          estimated_time: Optional[int] = None,
                          spinner: bool = False) -> None:
        """
        Render a curses-based progress bar for downloads using the same centered window style as render_menu() and render_confirmation().
        
        Args:
            filename: Name of file being downloaded
            current: Current bytes downloaded
            total: Total bytes (0 for unknown)
            percent: Optional pre-calculated percentage
            speed: Optional download speed (bytes/sec)
            estimated_time: Optional estimated time remaining (seconds)
            spinner: If True, show spinner animation for unknown total
        
        Supported Key Codes:
            - Console fallback: Enter (10, 13)
        """
        if not self._using_curses or not self._screen:
            # Use console fallback
            self._render_console_fallback(
                f"Downloading {Path(filename).name}... {current}/{total} ({percent or (current/total*100 if total else 0.0):.1f}%)"
            )
            return

        try:
            height, width = self._screen.getmaxyx()
            logger.debug(f"getmaxyx returned: height={height}, width={width}")
        except (OSError, EOFError, TypeError) as e:
            logger.error(f"getmaxyx error: {e}")
            # Fall back to console mode if we can't get terminal size
            self._render_console_fallback(
                f"Downloading {Path(filename).name}... {current}/{total} ({percent or (current/total*100 if total else 0.0):.1f}%)"
            )
            return
        
        # Handle edge cases where terminal size is 0 or invalid
        if height is None or width is None or height <= 0 or width <= 0:
            # Invalid terminal size, fall back to console
            self._render_console_fallback(
                f"Downloading {Path(filename).name}... {current}/{total} ({percent or (current/total*100 if total else 0.0):.1f}%)"
            )
            return
        
        # Auto-resize: window width adapts to terminal, minimum 60 chars
        # Ensure width is a valid number
        if width is not None and not isinstance(width, (int, float)):
            logger.warning(f"width is not a number: {type(width)}, falling back to console")
            self._render_console_fallback(
                f"Downloading {Path(filename).name}... {current}/{total} ({percent or (current/total*100 if total else 0.0):.1f}%)"
            )
            return
        
        # Auto-resize: window width adapts to terminal
        # Width is min(max(60, width - 12), 100) to ensure it fits on screen with minimum 60
        # Subtract 2 for padding, 2 for window border, and 8 for status line
        max_width = int(width) - 12
        win_width = min(100, max(60, max_width))  # Cap at 100, minimum 60, or terminal width - 12
        win_height = 6
        
        # Calculate centered position
        screen_height, screen_width = self._screen.getmaxyx()
        y_center = max(2, (screen_height - win_height) // 2)
        x_center = max(2, (screen_width - win_width) // 2)
        
        try:
            # Calculate progress percentage if not provided
            if percent is None and (total if total is not None else 0) > 0:
                percent = min(current / total * 100, 100.0)
            elif percent is None and total <= 0:
                percent = 0
            # If percent is provided, use it as-is
            
            # Calculate estimated time if not provided
            if estimated_time is None and speed is not None and (total if total is not None else 0) > current:
                remaining = total - current
                estimated_time = int(remaining / speed) if speed > 0 else 0
                # Cap at 9999 seconds to avoid excessive display
                estimated_time = min(estimated_time, 9999)
            
            # Format sizes in human-readable format
            def format_size(size):
                for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                    if size < 1024.0:
                        return f"{size:.1f} {unit}"
                    size /= 1024.0
                return f"{size:.1f} PB"
            
            # Title line with filename and estimated time
            if estimated_time is not None and estimated_time > 0:
                # Format time: seconds -> "Xs", minutes -> "Xm Ys", hours -> "Xh Ym Zs"
                if estimated_time < 60:
                    time_str = f"{estimated_time}s"
                elif estimated_time < 3600:
                    mins = estimated_time // 60
                    secs = estimated_time % 60
                    time_str = f"{mins}m {secs}s"
                else:
                    hours = estimated_time // 3600
                    mins = (estimated_time % 3600) // 60
                    secs = estimated_time % 60
                    time_str = f"{hours}h {mins}m {secs}s"
                
                title_text = f"Download: {Path(filename).name} (ETA: {time_str})"
                # Only truncate if win_width is valid and title_text is too long
                if win_width is not None and win_width > 4 and len(title_text) > win_width - 4:
                    title_text = title_text[:win_width - 8] + "..."
            else:
                title_text = f"Download: {Path(filename).name}"
            
            # Create the window using the same centered approach as render_menu and render_confirmation
            white_attr = self._get_white_attr()
            
            # Define redraw function
            def redraw():
                try:
                    # Validate window before operations
                    if not self._validate_window(bar_win):
                        logger.warning("Window validation failed in redraw")
                        try:
                            self._cleanup_terminal()
                        except:
                            pass
                        raise Exception("Window invalid")
                    
                    # Clear the window content (inside the border)
                    bar_win.erase()
                    
                    # Redraw the border with box() to ensure it's properly drawn
                    bar_win.box()
                    
                    # Calculate box width for centering
                    box_width = win_width - 6
                    
                    # Title row 0, centered with padding
                    if white_attr is not None:
                        bar_win.attron(white_attr)
                        bar_win.addstr(0, 3, "Download".center(box_width))
                        bar_win.attroff(white_attr)
                        bar_win.addstr(1, 1, "-" * (win_width - 2))
                    
                    # Progress information - row 2
                    if spinner:
                        # Indeterminate progress with spinner
                        spinner_chars = ["◐", "◓", "◑", "◒"]
                        spinner_idx = int(time.time() * 3) % 4
                        status = f"Downloading {Path(filename).name}... ({spinner_chars[spinner_idx]})"
                        # Only truncate if win_width is valid
                        if win_width is not None and win_width > 4 and len(status) > win_width - 4:
                            status = status[:win_width - 8] + "..."
                    else:
                        # Draw filled bar
                        if win_width is not None:
                            bar_width = win_width - 6
                            filled_width = int(bar_width * percent / 100)
                            filled_bar = "█" * filled_width
                            remaining_bar = "░" * (bar_width - filled_width)
                            logger.debug(f"render_progress_bar: filled_width={filled_width}, percent={percent}")
                            
                            # Status line: downloaded/total, percentage, speed, ETA
                            speed_str = f"({format_size(speed):>6}/s)" if speed else ""
                            eta_str = f" (ETA: {time_str})" if estimated_time > 0 else ""
                            status = f"{format_size(current):>8}/{format_size(total):>8} {percent:>6.1f}% {speed_str}{eta_str}"
                            
                            # Truncate status if too long
                            if win_width is not None and win_width > 4 and len(status) > win_width - 4:
                                status = status[:win_width - 8] + "..."
                    
                    # Render with color
                    bar_win.attron(self._color_pair)
                    bar_win.addstr(2, 3, status)
                    bar_win.addstr(3, 3, filled_bar + remaining_bar)
                    bar_win.attroff(self._color_pair)
                    
                    # Footer - row 4, centered with padding
                    footer = "Use arrow keys to navigate, Enter to confirm, q/ESC to cancel"
                    truncated_footer = footer[:box_width + 4] if len(footer) > box_width + 4 else footer
                    centered_footer = truncated_footer.center(box_width)
                    bar_win.addstr(5, 3, centered_footer, curses.A_REVERSE)
                    
                    bar_win.refresh()
                except OSError:
                    pass
            
            # Create new window centered
            if self._progress_bar_win is not None:
                bar_win = self._progress_bar_win
            else:
                bar_win = self.create_window(win_height, win_width, y_center, x_center)
            
            if bar_win is None:
                logger.error("Progress bar window creation failed")
                return
            
            # Safely enable keypad mode
            if self._safe_keypad(bar_win, True):
                logger.debug("Keypad mode enabled for progress bar")
            
            # Store the window reference
            self._progress_bar_win = bar_win
            
            # Initial redraw
            redraw()
            
            logger.debug(f"Progress bar updated: {Path(filename).name} ({percent or 0:.1f}%)")
            
        except OSError as e:
            logger.error(f"Progress bar window error: {e}")
            # Clean up the window on error
            try:
                if self._progress_bar_win is not None:
                    self._progress_bar_win = None
                self._cleanup_terminal()
            except:
                pass
        except (OSError, EOFError, TypeError) as e:
            logger.error(f"Unexpected error during progress bar: {e}")
            # Clean up the window on error
            try:
                if self._progress_bar_win is not None:
                    self._progress_bar_win = None
                self._cleanup_terminal()
            except:
                pass
            # Fall back to console mode
            self._render_console_fallback(
                f"Downloading {Path(filename).name}... {current}/{total} ({percent or (current/total*100 if total else 0.0):.1f}%)"
            )

    def render_success(self, message: str) -> None:
        """Render success message.
        
        Supported Key Codes:
            - Any key press (all valid curses key codes)
            - Console fallback: Enter (10, 13)
        """
        logger.debug(f"render_success called: {message[:60]}...")
        if not self._using_curses:
            self._render_console_fallback(
                f"\n{'='*60}\n{message.center(60)}\n{'='*60}"
            )
            return

        if not self._screen:
            print(message)
            return

        height, width = self._screen.getmaxyx()
        
        # Create window
        msg_height = 4
        y_offset = height - msg_height - 2
        x_offset = 2
        
        try:
            msg_win = self.create_window(msg_height, width - 4, y_offset, x_offset)
            if msg_win is None:
                logger.error("Success window creation failed")
                print(message)
                return
            
            # Safely enable keypad mode
            if self._safe_keypad(msg_win, True):
                logger.debug("Keypad mode enabled for success window")
            else:
                logger.warning("Keypad mode failed for success window")
            
            # Title
            msg_win.attron(curses.A_REVERSE | curses.A_BOLD)
            msg_win.addstr(0, 1, "Success".center(width - 4))
            msg_win.attroff(curses.A_REVERSE | curses.A_BOLD)
            
            # Message
            msg_win.attron(self._color_pair)
            msg_win.addstr(2, 2, message)
            msg_win.attroff(self._color_pair)
            
            msg_win.refresh()
            
            # Wait for key
            if self._validate_window(self._screen):
                self.refresh()
                try:
                    key = self._screen.getch()
                except (OSError, EOFError) as e:
                    logger.error(f"Success getch() error: {e}")
                    try:
                        self._cleanup_terminal()
                    except:
                        pass
                    # Fallback to console
                    print(f"\n{'='*60}\n{message.center(60)}\n{'='*60}")
                    input("Press Enter to continue...")
                msg_win.erase()
            else:
                logger.warning("Screen invalid in success window, using fallback")
                print(f"\n{'='*60}\n{message.center(60)}\n{'='*60}")
                input("Press Enter to continue...")
        except OSError as e:
            logger.error(f"Success window error: {e}")
            # If curses fails during input, clean up and return
            try:
                self._cleanup_terminal()
            except:
                pass
            # Fallback to console
            print(f"\n{'='*60}\n{message.center(60)}\n{'='*60}")
            input("Press Enter to continue...")
        except (OSError, EOFError, TypeError) as e:
            logger.error(f"Unexpected error during success display: {e}")
            try:
                self._cleanup_terminal()
            except:
                pass
            print(f"\n{'='*60}\n{message.center(60)}\n{'='*60}")
            input("Press Enter to continue...")

    def render_error(self, message: str) -> None:
        """Render error message.
        
        Supported Key Codes:
            - Any key press (all valid curses key codes)
            - Console fallback: Enter (10, 13)
        """
        logger.debug(f"render_error called: {message[:60]}...")
        if not self._using_curses:
            self._render_console_fallback(
                f"\n{'='*60}\nError: {message.center(60)}\n{'='*60}"
            )
            return

        if not self._screen:
            print(f"Error: {message}")
            return

        height, width = self._screen.getmaxyx()
        
        # Create window
        msg_height = 4
        y_offset = height - msg_height - 2
        x_offset = 2
        
        try:
            msg_win = self.create_window(msg_height, width - 4, y_offset, x_offset)
            if msg_win is None:
                logger.error("Error window creation failed")
                print(f"Error: {message}")
                return
            
            # Safely enable keypad mode
            if self._safe_keypad(msg_win, True):
                logger.debug("Keypad mode enabled for error window")
            else:
                logger.warning("Keypad mode failed for error window")
            
            # Title
            msg_win.attron(curses.A_REVERSE | curses.A_BOLD)
            msg_win.addstr(0, 1, "Error".center(width - 4))
            msg_win.attroff(curses.A_REVERSE | curses.A_BOLD)
            
            # Message
            msg_win.attron(self._color_pair)
            msg_win.addstr(2, 2, message)
            msg_win.attroff(self._color_pair)
            
            msg_win.refresh()
            
            # Wait for key
            if self._validate_window(self._screen):
                self.refresh()
                try:
                    key = self._screen.getch()
                except (OSError, EOFError) as e:
                    logger.error(f"Error getch() error: {e}")
                    try:
                        self._cleanup_terminal()
                    except:
                        pass
                    # Fallback to console
                    print(f"\n{'='*60}\nError: {message.center(60)}\n{'='*60}")
                    input("Press Enter to continue...")
                msg_win.erase()
            else:
                logger.warning("Screen invalid in error window, using fallback")
                print(f"\n{'='*60}\nError: {message.center(60)}\n{'='*60}")
                input("Press Enter to continue...")
        except OSError as e:
            logger.error(f"Error window error: {e}")
            # If curses fails during input, clean up and return
            try:
                self._cleanup_terminal()
            except:
                pass
            # Fallback to console
            print(f"\n{'='*60}\nError: {message.center(60)}\n{'='*60}")
            input("Press Enter to continue...")
        except (OSError, EOFError, TypeError) as e:
            logger.error(f"Unexpected error during error display: {e}")
            try:
                self._cleanup_terminal()
            except:
                pass
            print(f"\n{'='*60}\nError: {message.center(60)}\n{'='*60}")
            input("Press Enter to continue...")

    def get_input(self, prompt: str) -> str:
        """Get user input with confirmation styling.
        
        Supported Key Codes:
            - Console fallback: Enter (10, 13)
        """
        logger.debug(f"get_input called with prompt={prompt[:60]}...")
        if not self._using_curses:
            return self._render_console_fallback("")

        height, width = self._screen.getmaxyx()
        y, x = self._screen.getyx()
        
        # Print prompt
        self._screen.attron(self._color_pair)
        self._screen.addstr(y, x, prompt)
        self._screen.attroff(self._color_pair)
        self._screen.refresh()

        try:
            # Get input
            input_str = self._screen.getstr(x + len(prompt), y, width - len(prompt)).decode()
            return input_str.strip()
        except (OSError, EOFError, TypeError) as e:
            logger.error(f"get_input error: {e}")
            # If curses fails during input, clean up and return
            try:
                self._cleanup_terminal()
            except:
                pass
            # Fallback to console
            print(f"{prompt}")
            response = sys.stdin.readline().strip()
            return response
        except (OSError, EOFError, TypeError) as e:
            # Log but don't fail
            logger.warning(f"Unexpected error during get_input: {e}")
            # Fallback to console
            print(f"{prompt}")
            response = sys.stdin.readline().strip()
            return response

    def get_numbered_input(self, options: List[str], 
                          default: Optional[int] = None) -> Optional[int]:
        """Get numbered input from user.
        
        Supported Key Codes:
            - Enter: KEY_ENTER (343, 10, 13)
            - Cancel: 27 (Escape)
            - Selection: '0'-'9' (ASCII 48-57)
        """
        logger.debug(f"get_numbered_input called with options={len(options)}, default={default}")
        if not self._using_curses:
            prompt = f"Choice [{default if default is not None else 0}]: "
            return self._render_console_fallback(
                f"\n{'\n'.join([f'  {i}. {opt}' for i, opt in enumerate(options)])}",
                prompt
            )

        height, width = self._screen.getmaxyx()
        y, x = self._screen.getyx()
        
        # Print options
        for i, opt in enumerate(options):
            marker = " (default)" if default is not None and i == default else ""
            
            if i == default:
                self._screen.attron(curses.A_REVERSE | curses.A_BOLD)
                self._screen.addstr(y + i + 1, x, f"  {i}. {opt}{marker}")
                self._screen.attroff(curses.A_REVERSE | curses.A_BOLD)
            else:
                self._screen.attron(self._color_pair)
                self._screen.addstr(y + i + 1, x, f"  {i}. {opt}{marker}")
                self._screen.attroff(self._color_pair)

        self._screen.refresh()

        # Get input
        try:
            input_str = self._screen.getstr(x + len(f"\nChoice [{default if default is not None else 0}]: "), y + len(options) + 1, width).decode()
            idx = int(input_str) if input_str.isdigit() else None
            return idx if idx is not None and 0 <= idx < len(options) else None
        except (OSError, EOFError, TypeError) as e:
            logger.error(f"get_numbered_input error: {e}")
            try:
                self._cleanup_terminal()
            except:
                pass
            # Fallback to console
            for i, opt in enumerate(options):
                marker = " (default)" if default is not None and i == default else ""
                print(f"  {i}. {opt}{marker}")
            print(f"Choice [{default if default is not None else 0}]: ", end="", flush=True)
            choice = sys.stdin.readline().strip()
            try:
                idx = int(choice)
                return idx if 0 <= idx < len(options) else None
            except ValueError:
                return None
        except (OSError, EOFError, TypeError) as e:
            logger.error(f"Unexpected error during get_numbered_input: {e}")
            try:
                self._cleanup_terminal()
            except:
                pass
            for i, opt in enumerate(options):
                marker = " (default)" if default is not None and i == default else ""
                print(f"  {i}. {opt}{marker}")
            print(f"Choice [{default if default is not None else 0}]: ", end="", flush=True)
            choice = sys.stdin.readline().strip()
            try:
                idx = int(choice)
                return idx if 0 <= idx < len(options) else None
            except ValueError:
                 return None
