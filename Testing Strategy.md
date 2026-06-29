# UIManager Testing Strategy

## Overview

This document is the authoritative reference for writing, running, and maintaining tests for `ui_manager.py`. All tests live in the `Tests/` directory. The test suite uses **mocked curses** throughout — no real TTY is required, so tests run cleanly in any environment including CI/CD pipelines.

**Run all tests:**
```bash
python3 -m pytest Tests/ -v
```

**Run a specific file:**
```bash
python3 -m pytest Tests/test_ui_manager_pytest.py -v
```

**Run via the unified entry point:**
```bash
python3 Tests/__init__.py
```

---

## Test Files

The suite consists of exactly these five files plus `conftest.py` (shared fixtures) and `__init__.py` (entry point):

| File | Runner | Tests | Coverage area |
|---|---|---|---|
| `test_ui_manager_api.py` | unittest / standalone | 5 | Class structure, method signatures, color pair setup |
| `test_ui_manager_comprehensive.py` | standalone (`run_tests()`) | 8 | Init/lifecycle, menu navigation, confirmation, progress bar, styling, edge cases |
| `test_ui_manager_pytest.py` | pytest | 46 | Init fallback, arrow nav, number selection, cancel keys, confirmation inputs, progress bar, full workflow, page jump, wrapping, highlighted=None |
| `test_timeout_pytest.py` | pytest | 10 | Timeout returns -1, timeout after navigation, multiple timeouts, timeout with various highlighted states, cancel after timeout, default option, empty options, default=False timeout, _screen=None fallback |
| `test_ui_manager_terminal_sizes.py` | standalone (`run_tests()`) | 9 | 40×20 / 80×24 / 120×30 terminals, menu width calculation, progress bar adaptation, spinner/determinate bars |

**Do not add new test files.** New tests belong in the existing file that matches their coverage area (see Maintenance Rules).

---

## ⚠️ Critical Mocking Rule

**Any test that calls `render_menu` or `render_confirmation` MUST patch `ui_manager.curses.newwin`.**

Both methods call `curses.newwin()` internally to create their own window. If you mock `mock_win.getch` on a separate object without intercepting `newwin`, your mock is never called — a real (unmocked) window is created instead, and the test either hangs or produces unexpected results.

### ❌ Wrong — `mock_win.getch` is never reached

```python
mock_win = MagicMock()
mock_win.getch.side_effect = [curses.KEY_ENTER]
result = ui.render_menu(options)  # curses.newwin() runs unmocked internally
```

### ✅ Correct — intercept `newwin` so the internal window IS your mock

```python
def test_enter_selects_first_option(ui, mock_win):
    mock_win.getch.side_effect = [curses.KEY_ENTER]
    with patch('ui_manager.curses.newwin', return_value=mock_win):
        result = ui.render_menu([{'label': 'Option A'}, {'label': 'Option B'}])
    assert result == 0
```

### ❌ Wrong — patching the wrong path

```python
# This patches the curses module globally, not inside ui_manager
with patch('curses.newwin', return_value=mock_win):
    ...
```

The patch path must be `'ui_manager.curses.newwin'`, not `'curses.newwin'`.

### When you do NOT need to patch `newwin`

- Testing `UIManager.__init__` or `_cleanup_terminal` without driving render methods
- Testing `print_header`, `print_message`, `render_success`, `render_error` in fallback mode
- Testing pure logic that does not involve UI rendering

In those cases, only patch the curses module itself:

```python
with patch('ui_manager.curses', mock_curses):
    # your test here
```

---

## Standard Setup Patterns

### Creating a UIManager instance (used in tests for UIManager)

```python
import curses
from unittest.mock import MagicMock, patch
from ui_manager import UIManager

def create_ui(title="Test"):
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
        ui = UIManager(title)
        ui._using_curses = True  # Force enabled for testing
    return ui
```

#### Driving `render_menu` — complete working pattern

```python
def test_enter_selects_first_option():
    ui = create_ui()
    options = [{'label': 'Option A'}, {'label': 'Option B'}]

    mock_win = MagicMock()
    mock_win.getyx.return_value = (0, 0)
    mock_win.getch.side_effect = [curses.KEY_ENTER]

    with patch.object(ui, '_screen') as mock_screen, \
         patch.object(ui, 'refresh'), \
         patch('ui_manager.curses.newwin', return_value=mock_win):

        mock_screen.getmaxyx.return_value = (24, 80)
        result = ui.render_menu(options, default=0, highlighted=0)

    assert result == 0
```

#### Driving `render_confirmation` — complete working pattern

```python
def test_n_cancels_confirmation():
    ui = create_ui()

    mock_win = MagicMock()
    mock_win.getyx.return_value = (0, 0)
    mock_win.getch.side_effect = [ord('n')]

    with patch.object(ui, '_screen') as mock_screen, \
         patch.object(ui, 'refresh'), \
         patch('ui_manager.curses.newwin', return_value=mock_win):

        mock_screen.getmaxyx.return_value = (24, 80)
        result = ui.render_confirmation("Proceed with installation? [Y/n]:", default=True)

    assert result is False
```

---

## Key Code Reference

### Terminal key codes used in tests

| Key | Constant / Value | Used for |
|---|---|---|
| `curses.KEY_UP` | Up arrow | Menu navigation — move highlight up, wraps |
| `curses.KEY_DOWN` | Down arrow | Menu navigation — move highlight down, wraps |
| `curses.KEY_PPAGE` | Page Up | Jump to top of menu |
| `curses.KEY_NPAGE` | Page Down | Jump to bottom of menu |
| `curses.KEY_ENTER` | Enter (numpad) | Confirm selection |
| `10` | Enter (main keyboard, ASCII LF) | Confirm selection |
| `13` | Carriage return | Confirm selection |
| `curses.KEY_RESIZE` | Terminal resize | Cancel / return -1 |
| `curses.KEY_BACKSPACE` | Backspace | Cancel / return -1 |
| `27` | Escape (ASCII) | Cancel / return -1 |
| `127` | DEL (ASCII) | Cancel / return -1 |
| `8` | Backspace alternative | Cancel / return -1 |
| `ord('q')` / `113` | q | Cancel / return -1 |
| `ord('0')` – `ord('9')` | 48–57 | Select option by number (zero-indexed) |
| `ord('y')` / `ord('Y')` | 121 / 89 | Confirm in confirmation dialog |
| `ord('n')` / `ord('N')` | 110 / 78 | Cancel in confirmation dialog |
| `None` / `-1` | Timeout value | `getch` timeout — treated as cancel |

### Method signatures

```python
UIManager(title: str)

render_menu(options: list[dict], default: int, highlighted: int) -> int
# Returns: selected index (0-based), or -1 on cancel/timeout

render_confirmation(message: str, default: bool = True) -> bool
# Returns: True to confirm, False to cancel

render_progress_bar(filename: str, current: int, total: int, percent: float | None = None)
# total=0 triggers spinner mode for unknown-size downloads

render_success(message: str)
render_error(message: str)
print_header(title: str)
print_message(message: str)
```

### Color pair setup (verified in `test_ui_manager_api.py`)

`UIManager.__init__` must call `curses.init_pair` exactly twice:

| Call | Pair | Foreground | Background | Purpose |
|---|---|---|---|---|
| 1st | `1` | `COLOR_GREEN` | `COLOR_BLACK` | Normal text |
| 2nd | `2` | `COLOR_WHITE` | `COLOR_BLACK` | Secondary text |

Highlighted menu items use `curses.A_REVERSE`. The `_color_pair` attribute must include `curses.A_BOLD`.

---

## Behavior Specifications

These are the behaviors the tests verify. If you change `ui_manager.py`, the tests must still pass.

### `render_menu`

- Returns the 0-based index of the selected option when the user presses Enter
- `KEY_UP` and `KEY_DOWN` cycle through options with wrapping (top wraps to bottom and vice versa)
- `KEY_PPAGE` jumps UP by page size (half the menu or screen height, whichever is smaller, minimum 1) with wrapping
- `KEY_NPAGE` jumps DOWN by page size (half the menu or screen height, whichever is smaller, minimum 1) with wrapping
- Page size calculation: `max(1, min(len(options) // 2, (menu_height - 2) // 2))`
- Typing a digit selects that option directly by number (0-indexed); an out-of-range digit is ignored
- Any cancel key (`q`, Escape/27, `KEY_RESIZE`, `KEY_BACKSPACE`, 127, 8) returns `-1`
- A `getch` timeout (returns `None` or `-1`) returns `-1`
- An empty `options` list returns `-1` immediately without entering the input loop
- The `default` parameter indicates which option to pre-highlight; `highlighted` is the initial cursor position

### `render_confirmation`

- Enter (10, 13, or `KEY_ENTER`) confirms — returns `True`
- `y` or `Y` confirms — returns `True`
- `n` or `N` cancels — returns `False`
- Escape / `KEY_RESIZE` cancels — returns `False`
- A `getch` timeout returns the `default` parameter value
- When `_screen` is `None`, returns a safe default without crashing

### `render_progress_bar`

- When `total > 0`, renders a filled bar with bytes transferred and percentage
- When `total == 0`, renders a spinner animation for downloads of unknown size
- Window height is always 6 rows
- Window width scales with terminal width but stays ≤ `terminal_width - 10`

### Initialization and lifecycle

- `UIManager.__init__` sets `_using_curses = True`, `_screen` to a valid screen object, and `_color_pair` to a non-None value on success
- If `curses.initscr()` raises `curses.error`, the instance falls back gracefully: `_using_curses = False`, `_screen = None`
- `_cleanup_terminal()` sets `_using_curses = False` and `_screen = None`

### Terminal size adaptation

All render methods read `_screen.getmaxyx()` before creating windows. Tests verify correct behavior at:

- Small: 40 columns × 20 rows
- Medium: 80 columns × 24 rows (standard)
- Large: 120 columns × 30 rows

Menu width is calculated as `max(terminal_width * 0.6, label_length + 15)`, capped at `terminal_width - 8`.

---

## Test Author Checklist

Before committing a test that calls `render_menu` or `render_confirmation`:

- [ ] Imported `patch` from `unittest.mock`
- [ ] Imported `curses` for key code constants
- [ ] Created `mock_win` with `MagicMock()`
- [ ] Set `mock_win.getyx.return_value = (0, 0)`
- [ ] Configured `mock_win.getch.side_effect` (or `.return_value`) with the expected input sequence
- [ ] Used `patch('ui_manager.curses.newwin', return_value=mock_win)` — NOT `'curses.newwin'`
- [ ] The `patch` context wraps the render call, not just setup code before it
- [ ] Added the test to the correct existing file (see Maintenance Rules)

---

## Maintenance Rules

1. **One file per coverage area.** New behavior in `render_menu`? Add the test to `test_ui_manager_pytest.py` or `test_ui_manager_comprehensive.py`. New terminal size edge case? Add to `test_ui_manager_terminal_sizes.py`. Do not create new test files.
2. **Fixtures belong in `conftest.py`.** If you are copying mock setup code into a test, extract it into a fixture instead.
3. **Always mock `newwin`.** Every test driving `render_menu` or `render_confirmation` must patch `'ui_manager.curses.newwin'`.
4. **No source inspection tests.** Do not write tests that call `inspect.getsource()` or inspect the implementation text.
5. **Integration tests cover cross-method flows only.** A sequence like menu → selection → confirmation → progress bar belongs in the integration section of `test_ui_manager_comprehensive.py`. Unit behavior belongs in the dedicated files.
6. **Mark known-failing tests.** Use `@pytest.mark.xfail` with a reason string rather than commenting out or deleting tests that are temporarily broken.
7. **Target test counts.** The suite currently sits at approximately 33 tests. When expanding coverage (see below), aim for these targets per file:

| File | Current | Target |
|---|---|---|
| `test_ui_manager_api.py` | 5 | 5 |
| `test_ui_manager_comprehensive.py` | 8 suites | 6 suites |
| `test_ui_manager_pytest.py` | 46 | 30 |
| `test_ui_manager_terminal_sizes.py` | 9 | 6 |

---

---

## Requirements Traceability

| Requirement (Requirements.md) | Behavior tested | Test location |
|---|---|---|
| §8.2 Black background, green text | `init_pair(1, COLOR_GREEN, COLOR_BLACK)` | `test_ui_manager_api.py` |
| §8.3 Numbered menus, arrow key navigation | Menu rendering, UP/DOWN/number input | `test_ui_manager_comprehensive.py`, `test_ui_manager_pytest.py` |
| §8.4 Confirmation prompts Y/n | Enter/y/Y/n/N/Esc handling | `test_ui_manager_comprehensive.py`, `test_ui_manager_pytest.py` |
| §8.5 Progress bar with percentage/bytes | Determinate bar and spinner | `test_ui_manager_pytest.py` |
| §8.6 Lifecycle (init/cleanup) | `_using_curses`, `_screen`, `_cleanup_terminal` | `test_ui_manager_comprehensive.py`, `test_ui_manager_pytest.py` |
| §8.7 Timeout handling | `getch` returns `None`/`-1` → cancel | `test_timeout_pytest.py` |
| Highlighted items reverse video | `curses.A_REVERSE` applied to selection | `test_ui_manager_comprehensive.py` |
| Terminal size adaptation | 40×20, 80×24, 120×30 | `test_ui_manager_terminal_sizes.py` |