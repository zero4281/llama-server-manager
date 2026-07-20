# UIManager Testing Strategy

## Overview

This document is the authoritative reference for writing, running, and maintaining tests for `ui_manager.py`. All automated tests live in the `Tests/` directory. The test suite uses **mocked curses** throughout — no real TTY is required, so tests run cleanly in any environment including CI/CD pipelines.

This document also covers a separate, manual verification layer against a real terminal — see [Manual Dynamic Testing](#manual-dynamic-testing) — for confirming behavior the mocked suite can't observe directly.

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

| File                                | Runner                     | Tests | Coverage area                                                                                                                                                                                               |
| ----------------------------------- | -------------------------- | ----- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `test_ui_manager_api.py`            | unittest / standalone      | 5     | Class structure, method signatures, color pair setup                                                                                                                                                        |
| `test_ui_manager_comprehensive.py`  | standalone (`run_tests()`) | 8     | Init/lifecycle, menu navigation, confirmation, progress bar, styling, edge cases                                                                                                                            |
| `test_ui_manager_pytest.py`         | pytest                     | 46    | Init fallback, arrow nav, number selection, cancel keys, confirmation inputs, progress bar, full workflow, page jump, wrapping, highlighted=None                                                            |
| `test_timeout_pytest.py`            | pytest                     | 10    | Timeout returns -1, timeout after navigation, multiple timeouts, timeout with various highlighted states, cancel after timeout, default option, empty options, default=False timeout, _screen=None fallback |
| `test_ui_manager_terminal_sizes.py` | standalone (`run_tests()`) | 9     | 40×20 / 80×24 / 120×30 terminals, menu width calculation, progress bar adaptation, spinner/determinate bars                                                                                                 |

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

| Key                     | Constant / Value                | Used for                                     |
| ----------------------- | ------------------------------- | -------------------------------------------- |
| `curses.KEY_UP`         | Up arrow                        | Menu navigation — move highlight up, wraps   |
| `curses.KEY_DOWN`       | Down arrow                      | Menu navigation — move highlight down, wraps |
| `curses.KEY_PPAGE`      | Page Up                         | Jump to top of menu                          |
| `curses.KEY_NPAGE`      | Page Down                       | Jump to bottom of menu                       |
| `curses.KEY_ENTER`      | Enter (numpad)                  | Confirm selection                            |
| `10`                    | Enter (main keyboard, ASCII LF) | Confirm selection                            |
| `13`                    | Carriage return                 | Confirm selection                            |
| `curses.KEY_RESIZE`     | Terminal resize                 | Cancel / return -1                           |
| `curses.KEY_BACKSPACE`  | Backspace                       | Cancel / return -1                           |
| `27`                    | Escape (ASCII)                  | Cancel / return -1                           |
| `127`                   | DEL (ASCII)                     | Cancel / return -1                           |
| `8`                     | Backspace alternative           | Cancel / return -1                           |
| `ord('q')` / `113`      | q                               | Cancel / return -1                           |
| `ord('0')` – `ord('9')` | 48–57                           | Select option by number (zero-indexed)       |
| `ord('y')` / `ord('Y')` | 121 / 89                        | Confirm in confirmation dialog               |
| `ord('n')` / `ord('N')` | 110 / 78                        | Cancel in confirmation dialog                |
| `None` / `-1`           | Timeout value                   | `getch` timeout — treated as cancel          |

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

| Call | Pair | Foreground    | Background    | Purpose        |
| ---- | ---- | ------------- | ------------- | -------------- |
| 1st  | `1`  | `COLOR_GREEN` | `COLOR_BLACK` | Normal text    |
| 2nd  | `2`  | `COLOR_WHITE` | `COLOR_BLACK` | Secondary text |

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
- The option at index `default` is rendered with `(default)` appended to its label (Requirements.md §8.3)

### `render_confirmation`

- Enter (10, 13, or `KEY_ENTER`) confirms — returns `True`
- `y` or `Y` confirms — returns `True`
- `n` or `N` cancels — returns `False`
- Escape / `KEY_RESIZE` cancels — returns `False`
- A `getch` timeout returns the `default` parameter value
- When `_screen` is `None`, returns a safe default without crashing

### `render_progress_bar`

- Title line displays the `filename` argument (Requirements.md §8.5)
- When `total > 0`, renders a filled bar with bytes transferred and percentage
- Byte counts are shown human-readable, not as raw bytes (e.g. `12.4 MB / 98.0 MB`, not `13002343 / 102760448`) (Requirements.md §8.5)
- When `total == 0`, renders a spinner animation for downloads of unknown size
- Window height is always 6 rows
- Window width scales with terminal width but stays ≤ `terminal_width - 10`

### Initialization and lifecycle

- `UIManager.__init__` sets `_using_curses = True`, `_screen` to a valid screen object, and `_color_pair` to a non-None value on success
- If `curses.initscr()` raises `curses.error`, the instance falls back gracefully: `_using_curses = False`, `_screen = None`
- `_cleanup_terminal()` sets `_using_curses = False` and `_screen = None`
- The terminal is restored to its original state **on any unhandled exception**, not just on normal destruction — Requirements.md §8.6 requires the terminal is "never left in a broken state." Test this by raising inside a render call (e.g. patch a `curses` call to `side_effect=Exception(...)`) and asserting `_cleanup_terminal`-equivalent state is reached rather than the exception propagating with the terminal still in raw/curses mode

### Curses session integrity (Requirements.md §5.1, §8.4, §8.6)

- Requirements.md §5.1 requires that **no output reach stdout/stderr directly** once `UIManager` has initialized curses — every menu, prompt, confirmation, progress update, success message, and error message must render through `UIManager`. The only plain-text output permitted anywhere in the program is emitted *before* `UIManager` is constructed (the WSL warning in §5.1.1) or entirely outside the Python process (the Bash venv check in §4.2).
- Requirements.md §8.6 requires a **single** `UIManager` construction/destruction per run — the curses session must stay open continuously from the first menu to the final success/error message, and must not be torn down and re-entered mid-workflow.
- These are cross-cutting, whole-program invariants rather than something one `render_*` call can violate in isolation, so they are not covered by the mocked unit suite. Verify them via the "Curses session integrity" check in Manual Dynamic Testing below.

### Terminal size adaptation

All render methods read `_screen.getmaxyx()` before creating windows. Tests verify correct behavior at:

- Small: 40 columns × 20 rows
- Medium: 80 columns × 24 rows (standard)
- Large: 120 columns × 30 rows

Menu width is calculated as `max(terminal_width * 0.6, label_length + 15)`, capped at `terminal_width - 8`.

---

## Manual Dynamic Testing

The automated suite above runs entirely against **mocked curses** — it never touches a real TTY. That's correct for CI, but it can't confirm that the UI actually renders and behaves correctly in a live terminal. Use this section to manually verify a change against the real, unmocked TUI before considering it done.

**This is a separate, uncounted verification layer.** It does not add to the ~33 test target in Maintenance Rules, its scripts do not live in `Tests/`, and its artifacts are not committed — they are scratch output for the person/agent running the check, inspected and then discarded.

### When to use this

After making a change to `ui_manager.py` (or the code that drives it) that affects observable terminal behavior — menu layout, navigation, confirmation prompts, progress bars, or startup — in addition to running `python3 -m pytest Tests/ -v`.

### Constraints

- Fixes for anything this reveals go into the **source code** (`ui_manager.py` or the calling application), never into the test scripts or config, and never by editing this procedure to paper over the failure.
- Do not add files under `Tests/` as part of this process — this is not a pytest-discoverable test.
- Capture files (e.g. `initial_menu.txt`, `after_input.txt`) should be written to a scratch/temp location (e.g. `/tmp/` or the current working directory outside `Tests/`) and are not meant to be persisted or committed.

### Required input coverage by widget

Manual testing is not just "poke it once and see if it looks fine." Every screen touched by a change must have its **full input surface** exercised through tmux, not just the one input path the change happened to target. At minimum, run every applicable row below against the live TUI for any screen that touches `render_menu`, `render_confirmation`, or `render_progress_bar`. This mirrors the Behavior Specifications above — the point of manual testing is confirming those same specs hold true against a real terminal, not just against the mock.

**Any screen that calls `render_menu` — test ALL of these, not a subset:**

| Input | Key(s) to send via `tmux send-keys` | Must confirm |
|---|---|---|
| Enter (numpad) | `KP_Enter` or the literal key your terminal emulator maps to `KEY_ENTER` | Selects the currently highlighted option |
| Enter (main keyboard) | `Enter` (sends ASCII 10) | Selects the currently highlighted option |
| Number key selection | `0`, `1`, `2`, ... up to the option count | Jumps directly to and selects that option, zero-indexed |
| Out-of-range number key | A digit beyond the last option, e.g. `9` on a 3-item menu | Ignored — no crash, no selection change |
| Down arrow | `Down` | Moves highlight to next option |
| Up arrow | `Up` | Moves highlight to previous option |
| Down-arrow wrap | `Down` sent repeatedly past the last option | Highlight wraps to the first option |
| Up-arrow wrap | `Up` sent from the first option | Highlight wraps to the last option |
| Page down | `NPage` (or `KEY_NPAGE`) | Highlight jumps forward by page size, with wrap |
| Page up | `PPage` (or `KEY_PPAGE`) | Highlight jumps backward by page size, with wrap |
| Cancel — `q` | `q` | Menu exits, returns to caller with no selection |
| Cancel — Escape | `Escape` | Menu exits, returns to caller with no selection |
| Cancel — Backspace | `BSpace` | Menu exits, returns to caller with no selection |
| Resize | resize the tmux window/pane (`tmux resize-window` or send `KEY_RESIZE`) | Treated as cancel, no crash |
| Idle / timeout | send nothing and wait past the configured timeout | Treated as cancel per the `default`/timeout behavior |
| Default label (visual, not a keypress) | none — inspect the initial capture | The option passed as `default` shows `(default)` appended to its label (§8.3) |

**Any screen that calls `render_confirmation` — test ALL of these:**

| Input | Key(s) | Must confirm |
|---|---|---|
| Enter | `Enter` | Confirms (`True`) |
| `y` / `Y` | `y` then separately `Y` | Confirms (`True`) |
| `n` / `N` | `n` then separately `N` | Cancels (`False`) |
| Escape | `Escape` | Cancels (`False`) |
| Idle / timeout | send nothing and wait | Returns the `default` value passed to the call |

**Any screen that calls `render_progress_bar` — test:**

| Scenario | How to trigger | Must confirm |
|---|---|---|
| Determinate transfer | trigger a download/operation with a known total size | Filled bar advances, percentage and byte counts update, 6-row window |
| Spinner (unknown size) | trigger an operation where `total == 0` | Spinner animates instead of a filled bar |
| Narrow terminal | resize/launch at a small width (e.g. 40 cols) before triggering | Bar width scales down and stays ≤ `terminal_width - 10`, no wrapping/corruption |
| Title line (visual) | inspect the capture during a transfer | Title line shows the actual `filename` being downloaded (§8.5) |
| Byte formatting (visual) | inspect the capture during a determinate transfer | Byte counts render human-readable, e.g. `12.4 MB / 98.0 MB` — not raw byte integers (§8.5) |

If a change only touches one of these widgets, you still owe the **full row set for that widget** — e.g. a change that only affects `render_menu`'s page-jump logic still requires re-checking Enter, number keys, both arrow directions, wrap, and all cancel keys on that same menu, because a regression in shared navigation state is easy to introduce without touching the page-jump code itself.

### Curses session integrity (walk once per full manual pass, not per widget)

Requirements.md §5.1, §8.4, and §8.6 require the entire interactive workflow to stay inside **one continuous curses session** with zero direct stdout/stderr output once it starts. No single widget check above can catch a violation of this — it only shows up across a full, multi-screen run:

1. Launch the real entry point for a multi-step workflow (e.g. `--install-llama`, which chains menu → confirmation → progress bar → success message).
2. Capture the pane after every step, per the procedure below, from launch through the final success/error message.
3. Across every capture, confirm:
   - No plain, unbordered text ever appears outside a `UIManager`-rendered bordered window — a stray `print()`/`sys.stderr.write()` mid-workflow would show up as raw text breaking the curses layout, which is a §5.1 violation.
   - The screen never drops back to a plain shell prompt and re-enters curses between steps — that would mean the curses session was torn down and re-initialized mid-workflow instead of staying open for the entire run, a §8.6 violation.
   - The only plain-text output that's acceptable anywhere in the capture is the WSL warning (§5.1.1), and only if it appears *before* the first curses screen — never interleaved with or after it.

### Generic procedure

1. **Start the TUI in a detached tmux session**, using the startup command and flags relevant to the feature being verified:
   
   ```bash
   tmux new-session -d -s tui_test '[STARTUP_COMMAND_WITH_FLAGS]'
   sleep 2
   ```

2. **Capture the initial state** to check layout and confirm there's no startup crash:
   
   ```bash
   tmux capture-pane -t tui_test -p > /tmp/initial_menu.txt
   ```

3. **Send each keypress from the applicable "Required input coverage" table above**, one at a time, capturing state after each so a regression can be pinned to a specific input:
   
   ```bash
   tmux send-keys -t tui_test [KEYPRESS_1]
   sleep 1
   tmux capture-pane -t tui_test -p > /tmp/step_1.txt

   tmux send-keys -t tui_test [KEYPRESS_2]
   sleep 1
   tmux capture-pane -t tui_test -p > /tmp/step_2.txt
   ```
   
   Repeat for every row in the relevant table(s) — Enter, every cancel key, every arrow direction (including enough repeats to prove wraparound), number-key selection, and page up/down for menus; Enter/y/Y/n/N/Escape for confirmations; both bar modes and at least one narrow-terminal size for progress bars. Do not stop after the first successful input — a change can fix the input it targeted while silently breaking another one covered by the same screen.

4. **Capture the final state** and clean up:
   
   ```bash
   tmux capture-pane -t tui_test -p > /tmp/after_input.txt
   tmux kill-session -t tui_test
   ```

5. **Review every captured file**, not just the last one:
   
   - Confirm the layout renders correctly and there's no crash on startup.
   - Confirm each keypress in step 3 produced the expected output/state per the Behavior Specifications and the coverage tables above — check every step's capture, since an intermediate step can regress even if the final capture looks fine.
   - If something is wrong, trace it back to the source change, fix `ui_manager.py` (or the caller), and repeat the **entire** applicable coverage table — not just the one input that failed — before considering the change verified.

### Worked example: full input coverage for a `render_menu` change

This walks the full "Any screen that calls `render_menu`" table against a real terminal, for a 3-option menu (options 0, 1, 2), rather than exercising only the one input the change targeted.

```bash
# 0. Launch the app at the menu screen under test
tmux new-session -d -s tui_test -x 80 -y 24 './llama-server-manager --install-llama'
sleep 2

# 1. Capture the initial menu — option 0 should be highlighted, no crash
tmux capture-pane -t tui_test -p > /tmp/01_initial.txt

# 2. Down arrow — highlight should move 0 -> 1
tmux send-keys -t tui_test Down
sleep 1
tmux capture-pane -t tui_test -p > /tmp/02_down.txt

# 3. Down arrow again, then once more past the last option — should wrap 2 -> 0
tmux send-keys -t tui_test Down
sleep 1
tmux send-keys -t tui_test Down
sleep 1
tmux capture-pane -t tui_test -p > /tmp/03_down_wrap.txt

# 4. Up arrow from option 0 — should wrap up to the last option (2)
tmux send-keys -t tui_test Up
sleep 1
tmux capture-pane -t tui_test -p > /tmp/04_up_wrap.txt

# 5. Number-key selection — jump directly to option 1
tmux send-keys -t tui_test 1
sleep 1
tmux capture-pane -t tui_test -p > /tmp/05_number_select.txt

# 6. Out-of-range number key — should be ignored, no crash, selection unchanged
tmux send-keys -t tui_test 9
sleep 1
tmux capture-pane -t tui_test -p > /tmp/06_number_out_of_range.txt

# 7. Enter — confirms whichever option is currently highlighted
tmux send-keys -t tui_test Enter
sleep 1
tmux capture-pane -t tui_test -p > /tmp/07_enter_selects.txt
tmux kill-session -t tui_test

# 8. Re-launch fresh to test the cancel keys in isolation (each exits the menu,
#    so each needs its own session/relaunch rather than chaining after step 7)
for key in q Escape BSpace; do
  tmux new-session -d -s tui_test -x 80 -y 24 './llama-server-manager --install-llama'
  sleep 2
  tmux send-keys -t tui_test "$key"
  sleep 1
  tmux capture-pane -t tui_test -p > "/tmp/08_cancel_${key}.txt"
  tmux kill-session -t tui_test
done
```

Expected results, checked file by file: `02_down.txt` shows option 1 highlighted; `03_down_wrap.txt` shows option 0 highlighted (top wrap confirmed); `04_up_wrap.txt` shows option 2 highlighted (bottom wrap confirmed); `05_number_select.txt` shows option 1 selected directly; `06_number_out_of_range.txt` is unchanged from `05` with no traceback; `07_enter_selects.txt` shows the highlighted option's action firing; each `08_cancel_*.txt` shows the menu exiting cleanly with no selection made. Any deviation — wrong option highlighted, a crash, a cancel key that doesn't exit, a number key that does nothing — is a source-code regression to fix in `ui_manager.py`, not something to paper over in the tmux script.

> Note: `[STARTUP_COMMAND_WITH_FLAGS]` in the generic procedure and `./llama-server-manager --install-llama` in the worked example are placeholders — substitute the actual entry point for the application under test.

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

| File                                | Current  | Target   |
| ----------------------------------- | -------- | -------- |
| `test_ui_manager_api.py`            | 5        | 5        |
| `test_ui_manager_comprehensive.py`  | 8 suites | 6 suites |
| `test_ui_manager_pytest.py`         | 46       | 30       |
| `test_ui_manager_terminal_sizes.py` | 9        | 6        |

---

---

## Requirements Traceability

| Requirement (Requirements.md) | Behavior tested | Test location |
|---|---|---|
| §8.2 Black background, green text | `init_pair(1, COLOR_GREEN, COLOR_BLACK)` | `test_ui_manager_api.py` |
| §8.2 Highlighted items reverse video, same colour pair | `curses.A_REVERSE` applied to selection | `test_ui_manager_comprehensive.py` |
| §8.3 Numbered menus, arrow key + number-key navigation | Menu rendering, UP/DOWN/number input | `test_ui_manager_comprehensive.py`, `test_ui_manager_pytest.py` |
| §8.3 Enter confirms; `q`/`Esc` cancel | Enter selects; `q`/Escape return `-1` | `test_ui_manager_pytest.py`; Manual Dynamic Testing (`render_menu` table) |
| §8.3 Default option labeled `(default)` | Label text at the `default` index | Manual Dynamic Testing (`render_menu` table) — visual only, not asserted by the mocked unit suite |
| §8.4 Confirmation prompts Y/n | Enter/y/Y/n/N/Esc handling | `test_ui_manager_comprehensive.py`, `test_ui_manager_pytest.py` |
| §8.5 Progress bar with percentage/bytes | Determinate bar and spinner | `test_ui_manager_pytest.py` |
| §8.5 Human-readable byte counts, filename title line | Byte formatting, title-line content | Manual Dynamic Testing (`render_progress_bar` table) — visual only, not asserted by the mocked unit suite |
| §8.6 Lifecycle (init/cleanup) | `_using_curses`, `_screen`, `_cleanup_terminal` | `test_ui_manager_comprehensive.py`, `test_ui_manager_pytest.py` |
| §8.6 Terminal restored on unhandled exception | Cleanup reached when a render call raises | Not yet in `Test Files` — recommended addition to `test_ui_manager_comprehensive.py` edge cases |
| §5.1 / §8.4 / §8.6 Continuous curses session, no stdout/stderr leak | Full-workflow capture shows no plain text outside curses, session opened once | Manual Dynamic Testing → "Curses session integrity" — cross-cutting; not unit-testable against a single mocked call |
| Terminal size adaptation *(implementation detail — no corresponding requirement text in Requirements.md)* | 40×20, 80×24, 120×30 | `test_ui_manager_terminal_sizes.py` |
| Page Up/Down jump; extra cancel keys (`Backspace`, `127`, `8`, `KEY_RESIZE`); `getch` timeout → cancel/default *(implementation robustness beyond current Requirements.md — §8.3 only specifies `q`/`Esc` for cancel and does not mention paging or timeouts)* | Page jump, additional cancel keys, timeout handling | `test_ui_manager_pytest.py`, `test_timeout_pytest.py` |