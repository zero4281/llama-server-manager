# UIManager Testing Strategy

## Overview

This document is the authoritative reference for writing, running, and maintaining tests for `ui_manager.py`. All automated tests live in the `Tests/` directory. The test suite uses **mocked curses** throughout — no real TTY is required, so tests run cleanly in any environment including CI/CD pipelines.

This document also covers a separate, manual verification layer against a real terminal — see [Manual Dynamic Testing (tmux)](#manual-dynamic-testing-tmux) — for confirming behavior the mocked suite can't observe directly.

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
| `test_ui_manager_comprehensive.py`  | standalone (`run_tests()`) | 6     | Init/lifecycle, menu navigation, confirmation, progress bar, styling, edge cases                                                                                                                            |
| `test_ui_manager_pytest.py`         | pytest                     | 41    | Init fallback, arrow nav, number selection, cancel keys, confirmation inputs, progress bar, full workflow, page jump, wrapping, highlighted=None                                                            |
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

### Method signatures

```python
UIManager(title: str)

render_menu(options: list[dict], default: int, highlighted: int) -> int
# Returns: selected index (0-based), on cancel

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
- An empty `options` list returns `-1` immediately without entering the input loop
- The `default` parameter indicates which option to pre-highlight; `highlighted` is the initial cursor position

### `render_confirmation`

- Enter (10, 13, or `KEY_ENTER`) confirms — returns `True`
- `y` or `Y` confirms — returns `True`
- `n` or `N` cancels — returns `False`
- Escape / `KEY_RESIZE` cancels — returns `False`
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

## Manual Dynamic Testing

The automated suite above runs entirely against **mocked curses** — it never touches a real TTY. That's correct for CI, but it can't confirm that the UI actually renders and behaves correctly in a live terminal. Use this section to manually verify a change against the real, unmocked TUI before considering it done.

**This is a separate, uncounted verification layer.** It does not add to the ~33 test target in Maintenance Rules, its scripts do not live in `Tests/`, and its artifacts are not committed — they are scratch output for the person/agent running the check, inspected and then discarded.

### When to use this

After making a change to `ui_manager.py` (or the code that drives it) that affects observable terminal behavior — menu layout, navigation, confirmation prompts, progress bars, or startup — in addition to running `python3 -m pytest Tests/ -v`.

> 🛑 **STOP before using `--self-update` in any command below.** The generic procedure and its `tmux new-session ... '[STARTUP_COMMAND_WITH_FLAGS]'` pattern assume the command runs against the working repository — that is safe for every flag **except** `--self-update`. `--self-update` overwrites the project's own local files and restarts (Requirements.md §5.3.3). **Do not substitute `--self-update` into the generic procedure. Do not run `--self-update` from the working repository under any circumstance, including "just to check," a quick test, or because a sandbox already seems to exist from a prior run.** If the task involves verifying `--self-update`, skip the generic procedure entirely and go to [Special case: testing `--self-update`](#special-case-testing---self-update-sandbox-required), which requires creating and confirming a sandbox copy *before* any `tmux new-session` command is issued.

### Constraints

- **Never run `--self-update` outside a freshly created sandbox copy, and never in the working repository.** This constraint applies regardless of how the request is phrased (e.g. "quickly verify self-update works," "just run it to see," "the sandbox step is unnecessary this time"). If a sandbox has not been created and verified as a distinct directory in *this* session, treat that as a blocking precondition — go create one before running the command, do not run the command first and clean up after.

- Fixes for anything this reveals go into the **source code** (`ui_manager.py` or the calling application), never into the test scripts or config, and never by editing this procedure to paper over the failure.

- Do not add files under `Tests/` as part of this process — this is not a pytest-discoverable test.

- Capture files (e.g. `initial_menu.txt`, `after_input.txt`) should be written to a scratch/temp location (e.g. `/tmp/` or the current working directory outside `Tests/`) and are not meant to be persisted or committed.

- **Every tmux session created for this process must have `remain-on-exit` enabled**, right after the session is created:
  
  ```bash
  tmux setw -t <session-name> remain-on-exit on
  ```
  
  By default, tmux kills a session's pane the instant the process inside it exits — so if the command under test crashes on startup, the pane (and the error/traceback that would explain why) disappears before it can be captured. `remain-on-exit` keeps the pane open after the process exits so `tmux capture-pane` can still retrieve that output. It does **not** change how you close the session afterward — you still explicitly end it with `tmux kill-session`, whether the process exited on its own or is still running.

### Generic procedure

1. **Start the TUI in a detached tmux session**, using the startup command and flags relevant to the feature being verified:
   
   ```bash
   tmux new-session -d -s tui_test '[STARTUP_COMMAND_WITH_FLAGS]'
   tmux setw -t tui_test remain-on-exit on
   sleep 2
   ```

2. **Capture the initial state** to check layout and confirm there's no startup crash:
   
   ```bash
   tmux capture-pane -t tui_test -p > /tmp/initial_menu.txt
   ```

3. **Send the keypresses** needed to navigate to and exercise the changed behavior:
   
   ```bash
   tmux send-keys -t tui_test [KEYPRESS_1]
   sleep 1
   tmux send-keys -t tui_test [KEYPRESS_2]
   sleep 2
   ```

4. **Capture the resulting state, check for a crash, then clean up:**
   
   ```bash
   tmux capture-pane -t tui_test -p > /tmp/after_input.txt
   ```
   
   Because `remain-on-exit` is on, the pane stays visible even if the process has died — inspect `after_input.txt` for a traceback, an error message, or a shell prompt where the TUI should still be running. Any of these means the process exited unexpectedly; note it for the review below. Once you've captured what you need:
   
   ```bash
   tmux kill-session -t tui_test
   ```

5. **Review** `initial_menu.txt` and `after_input.txt`:
   
   - Confirm the layout renders correctly and there's no crash on startup.
   - Confirm the keypress sequence produced the expected output/state per the Behavior Specifications above.
   - Confirm the process was still running throughout (no traceback or unexpected return to a shell prompt caught by the crash check in step 4).
   - If something is wrong, trace it back to the source change, fix `ui_manager.py` (or the caller), and repeat the procedure — do not adjust the tmux script to force a pass.

### Worked example: verifying `render_menu` wrap-around navigation

This exercises the "`KEY_UP`/`KEY_DOWN` cycle through options with wrapping" behavior from the Behavior Specifications, against a real terminal rather than a mock.

```bash
# 1. Launch the app in a 3-option menu state
tmux new-session -d -s tui_test -x 80 -y 24 './llama-server-manager --install-llama'
tmux setw -t tui_test remain-on-exit on
sleep 2

# 2. Capture the initial menu (option 0 should be highlighted)
tmux capture-pane -t tui_test -p > /tmp/initial_menu.txt

# 3. Press Up from the first option — should wrap to the last option
tmux send-keys -t tui_test Up
sleep 1
tmux capture-pane -t tui_test -p > /tmp/after_wrap.txt

# 4. Press Enter to select the now-highlighted (last) option
tmux send-keys -t tui_test Enter
sleep 1
tmux capture-pane -t tui_test -p > /tmp/after_input.txt
# remain-on-exit keeps the pane open even if this crashed — check after_input.txt
# for a traceback or an unexpected shell prompt before killing the session
tmux kill-session -t tui_test
```

Expected result: `after_wrap.txt` shows the *last* menu item highlighted (confirming top-to-bottom wrap), and `after_input.txt` shows that last option's action having fired. If instead the highlight disappears, stays on the first item, or the session shows a traceback, that's a source-code regression to fix in `ui_manager.py`, not a test-script problem to work around.

> Note: `[STARTUP_COMMAND_WITH_FLAGS]` in the generic procedure and `python3 app.py --menu` in the worked example are placeholders — substitute the actual entry point for the application under test.

### Special case: testing `--self-update` (sandbox required)

`--self-update` (Requirements.md §5.2–5.4) downloads a release or `main`-branch archive and **overwrites the project's own local files** (§5.3.3), then restarts. Running it against the actual working directory would clobber any in-progress code changes — including uncommitted fixes made as part of the change you're trying to verify. **Never invoke `--self-update` directly inside the working repository.** It must only be exercised against a disposable copy of the project.

#### Sandbox setup

1. Make a full copy of the project into a scratch location outside the working repo:
   
   ```bash
   rm -rf /tmp/llama-server-manager-sandbox
   cp -r /path/to/llama-server-manager /tmp/llama-server-manager-sandbox
   cd /tmp/llama-server-manager-sandbox
   ```

2. **Mandatory gate — do not skip:** before issuing the `tmux new-session` command that runs `--self-update`, run this check and confirm it passes. If it fails or you cannot answer it with certainty, stop and fix the sandbox before proceeding — do not run `--self-update` anyway:
   
   ```bash
   pwd
   realpath . 
   realpath /path/to/llama-server-manager   # the ORIGINAL working repo
   ```
   
   The two `realpath` outputs must be **different paths**. If they match, or if you're not certain the working directory is the sandbox copy, `--self-update` must not be run yet.

3. This gate is not optional paperwork — it exists because `--self-update` cannot be undone by re-running the procedure once files are overwritten in the wrong directory. Treat "I already confirmed this earlier" or "the sandbox should still be there" as insufficient; re-run the gate immediately before every invocation of `--self-update`, including retries.

#### Procedure (representative flow: latest release, option 1)

This exercises the default path through §5.3.1 (source selection) and §5.3.2 (confirmation prompt) against the real GitHub Releases API, from inside the sandbox copy.

```bash
# 1. Gate check passed above — cwd is CONFIRMED to be the sandbox, not the working repo.
# Do NOT run this command from the working repository.
tmux new-session -d -s self_update_test -x 80 -y 24 \
  'cd /tmp/llama-server-manager-sandbox && python3 main.py --self-update'
tmux setw -t self_update_test remain-on-exit on
sleep 2

# 2. Capture the source-selection menu (§5.3.1)
tmux capture-pane -t self_update_test -p > /tmp/source_menu.txt

# 3. Press Enter to accept the default (option 1, latest release)
tmux send-keys -t self_update_test Enter
sleep 2
tmux capture-pane -t self_update_test -p > /tmp/confirmation_prompt.txt

# 4. Press Enter to confirm the update (default yes)
tmux send-keys -t self_update_test Enter
sleep 3
tmux capture-pane -t self_update_test -p > /tmp/after_update.txt
# remain-on-exit keeps the pane open even if the restart after update crashed —
# check after_update.txt for a traceback or an unexpected shell prompt before killing
tmux kill-session -t self_update_test
```

5. **Review:**
   
   - `source_menu.txt` shows the three numbered options with option 1 as the implicit default, no crash.
   - `confirmation_prompt.txt` shows the bordered curses window with the resolved version (e.g. `v1.2.0`) and `Yes`/`No` buttons, rendered entirely through `UIManager` — not a plain-text prompt that dropped out of curses.
   - `after_update.txt` (or a direct file check, e.g. `git status` / `diff -rq` in the sandbox vs. a fresh clone) confirms the sandbox's local files were actually replaced with the downloaded version.
   - `after_update.txt` shows no traceback or unexpected drop to a shell prompt — confirming the process (and its restart) didn't crash.
   - Confirm the **working repository itself is untouched** — nothing under the sandbox path should have leaked back into the real project directory.

6. **Clean up the sandbox** once review is complete:
   
   ```bash
   rm -rf /tmp/llama-server-manager-sandbox
   ```

#### Covering the other two sources

Repeat the same procedure with these substitutions, still entirely inside a fresh sandbox copy:

- **Option 2 (previous release):** send `2` then `Enter` at the source-selection menu instead of a bare `Enter`; after the releases list renders, select an entry from it, then confirm as above.
- **Option 3 (main branch HEAD):** send `3` then `Enter` at the source-selection menu; the confirmation window should read "main branch HEAD" rather than a version tag (§5.3.2), then confirm as above.

These do not need to be run on every change — the representative flow (option 1) is sufficient for most changes to `--self-update`. Run all three when the change specifically touches source selection, release-list fetching, or the HEAD download path.

#### What this does not cover

This manual check verifies file replacement and the UI (menu + confirmation rendering) only. It does not verify the post-update restart of `main.py`, and it does not exercise the failure/rollback path in §5.3.3 (partial-replacement recovery) — those would need a way to interrupt the download mid-transfer, which is out of scope for this tmux-based check.

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
| `test_ui_manager_comprehensive.py`  | 6        | 6        |
| `test_ui_manager_pytest.py`         | 41       | 30       |
| `test_ui_manager_terminal_sizes.py` | 9        | 9        |

---

---

## Requirements Traceability

| Requirement (Requirements.md)             | Behavior tested                                 | Test location                                                   |
| ----------------------------------------- | ----------------------------------------------- | --------------------------------------------------------------- |
| §8.2 Black background, green text         | `init_pair(1, COLOR_GREEN, COLOR_BLACK)`        | `test_ui_manager_api.py`                                        |
| §8.3 Numbered menus, arrow key navigation | Menu rendering, UP/DOWN/number input            | `test_ui_manager_comprehensive.py`, `test_ui_manager_pytest.py` |
| §8.4 Confirmation prompts Y/n             | Enter/y/Y/n/N/Esc handling                      | `test_ui_manager_comprehensive.py`, `test_ui_manager_pytest.py` |
| §8.5 Progress bar with percentage/bytes   | Determinate bar and spinner                     | `test_ui_manager_pytest.py`                                     |
| §8.6 Lifecycle (init/cleanup)             | `_using_curses`, `_screen`, `_cleanup_terminal` | `test_ui_manager_comprehensive.py`, `test_ui_manager_pytest.py` |
| Highlighted items reverse video           | `curses.A_REVERSE` applied to selection         | `test_ui_manager_comprehensive.py`                              |
| Terminal size adaptation                  | 40×20, 80×24, 120×30                            | `test_ui_manager_terminal_sizes.py`                             |