# Bugs.md

## Current Bug Reports

### 🔴 CRITICAL: Fallback logic in render_menu not being triggered, causing premature exit
**Status:** 🟠 **RESOLVED**  
**Priority:** **P1** - Major feature broken; UI degrades to unusable state

**Description:**  
When running `UI_MANAGER_DEBUG=1 PYTHONWARNINGS=ignore python3 main.py --install-llama <<< $'1
8
3
y
'`, the curses menu flashes across the screen and then the program exits prematurely. The expected behavior is for the fallback logic in `ui_manager.py:UIManager:render_menu` to activate when curses fails, gracefully degrading to console mode. Instead, the fallback is not being triggered correctly, causing the program to crash before completion.

**Reproduction Steps:**
1. Run: `UI_MANAGER_DEBUG=1 PYTHONWARNINGS=ignore python3 main.py --install-llama <<< $'1
8
3
y
'`
2. **Expected:** The program should detect curses failure and use fallback logic in render_menu, degrading to console mode
3. **Actual:** Curses menu flashes and program exits prematurely

**Key Symptoms:**
- Curses menu renders briefly then crashes
- Fallback logic in render_menu is not being triggered
- Program exits before completing the installation flow
- Debug output shows the menu rendering but no fallback activation
- The issue is reproducible with `UI_MANAGER_DEBUG=1` but may also occur without it

**Affected Components:**
- `ui_manager.py:render_menu` (line 488-997) - fallback logic not activating
- `ui_manager.py:render_confirmation` (line 1052-1209) - likely affected by same issue
- `llama_updater.py:install_release` (line 613-748) - uses both render_menu and render_confirmation
- `llama_updater.py:LlamaUpdater:install` (line 758-841) - orchestrates the full installation flow
- `main.py:Main:run` (line 233-309) - entry point that delegates to LlamaUpdater

**Dependencies:**
- Requirements.md Section 8.3 (Numbered menus, arrow key navigation, and fallback to console if curses fails)
- Requirements.md Section 8.4 (Confirmation prompts must never drop out of curses environment; if they fail, fallback must activate)
- Requirements.md Section 8.6 (Lifecycle management and graceful degradation)

**Root Cause Analysis:**
The fallback logic in `render_menu` has multiple conditions that must all evaluate to false for fallback to activate:
- Line 518: `(not sys.stdin.isatty() and not self._using_curses) or not self._screen` - checks for non-interactive mode or curses failure
- Line 523-526: `self._ensure_terminal_ready()` - validates terminal state before rendering
- Line 610-624: Redraw function validation - checks if window is valid before operations
- Line 721-736: Input loop validation - validates screen and menu windows before proceeding

The issue appears to be that one or more of these validation checks are failing or returning unexpected values, preventing the fallback path from being taken. The debug flag `UI_MANAGER_DEBUG=1` may be interfering with these checks by changing logging behavior or terminal state.

**Workaround:**
None available. The fallback mechanism is designed to handle this scenario but is not functioning correctly.

**Test Coverage:**
According to Testing Strategy.md, tests for render_menu must:
- Patch `ui_manager.curses.newwin` to intercept window creation
- Simulate curses failure by returning invalid values from mocked methods
- Verify fallback activation when curses fails
- Currently no test exists that validates fallback activation when curses fails mid-operation

**Related Bugs:**
- CRITICAL: Confirmation prompt missing after archive selection (Status: Open) - similar degradation issue in render_confirmation
- P1: Missing confirmation prompt after llama.cpp installation selection (Status: Resolved) - related to confirmation flow

**Impact:**
The fallback mechanism is a critical safety feature that allows the application to continue functioning even when the primary UI library (curses) fails. Without working fallback, the application becomes unusable in any environment where curses might fail (e.g., certain terminal emulators, Docker containers, CI/CD pipelines, or systems with restricted terminal capabilities). This affects the reliability and robustness of the entire installation workflow.

---

### 🔴 CRITICAL: Confirmation prompt missing or not displaying correctly after archive selection
**Status:** 🟢 **RESOLVED**
**Priority:** **P1** - Major feature broken; user cannot confirm installation

**Description:**  
When running `./llama-server-wrapper --install-llama`, after selecting a release tag, platform, and zip file, the required confirmation prompt (as specified in Requirements.md Section 6.3.3) either never appears or fails to display properly. The user reports that after hitting enter on the archive selection, no confirmation prompt is shown, yet the file downloads automatically.

**Reproduction Steps:**
1. Run: `./llama-server-wrapper --install-llama`
2. Navigate through release tag selection menu and select an option
3. Navigate through platform selection menu and select an option
4. Navigate through zip file selection menu and select an option
5. Hit enter on the archive selection
6. **Expected:** A bordered curses window should appear with:
```bash
┌─────────────────────────────────────────────────────┐
│  Selected release: vX.Y.Z (filename.zip)            │
│  Proceed with installation?                         │
│                                                     │
│            ▶ [ Yes ]          [ No  ]               │
└─────────────────────────────────────────────────────┘
```
7. **Actual:** No confirmation prompt appears; installation proceeds automatically

**Key Symptoms:**
- Confirmation prompt appears to be missing after archive selection
- Prompt fails to display when it should appear
- Installation proceeds to download without user confirmation
- Archive selection archive selection works (file downloads when enter is pressed)

**Affected Components:**
- `llama_updater.py` (Section 6.3.3) - confirmation prompt rendering logic
- `ui_manager.py` (Section 8.4) - `render_confirmation` method
- `main.py` - entry point that delegates to `LlamaUpdater`

**Dependencies:**
- Requirements.md Section 6.3.3 (After a release tag and asset are selected, UIManager must render a bordered curses window displaying both selections and prompt for confirmation before downloading anything)
- Requirements.md Section 8.4 (UIManager confirmation prompts must never drop out of curses environment)

---

## Project Roadmap

| Priority | Task | Status |
| :--- | :--- | :--- |
| **P0 (Critical)** | Arrow keys cause crashes and invalid key handling in menu navigation | 🟢 Resolved |
| **P1 (High)** | Missing confirmation prompt after llama.cpp installation selection | 🟢 Resolved |
| **P1 (High)** | Confirmation prompt missing or not displaying correctly after archive selection | 🔴 Resolved |
| **P1 (High)** | Fallback logic in render_menu not being triggered, causing premature exit | 🟠 Open |
| **P2 (Medium)** | Confirmation prompt in llama_updater.py doesn't match Requirements.md border styling specification | 🟢 Resolved |
| **P2 (Medium)** | Confirmation prompt in llama_updater.py uses render_confirmation() but Requirements.md Section 6.3.3 specifies a different layout | 🟢 Resolved |
| **P3 (Low)** | Title and footer bars in menu windows disappear or draw incorrectly | 🟢 Resolved |
| **P3 (Low)** | Menus not displayed in correctly bordered windows | 🟢 Resolved |
| **P2 (High)** | ui_manager.py:render_confirmation() has multiple redundant fallback sections | 🟢 Resolved |
| **P3 (Medium)** | Program drops out of curses and displays print on line 1312 | 🟢 Resolved |
| **P3 (Low)** | Logger debug message never prints | 🟢 Resolved |

---

## Summary

**Last Updated:** April 26, 2026  
**Overall Status:** 0 open bug.

* **Resolved:** Fallback logic in render_menu not being triggered (P1)
* **Resolved:** Arrow key crashes (P0), missing confirmation prompt (P1), title/footer bar disappearance, logger debug messages, redundant fallback sections, curses environment drops, menu border issues, confirmation prompt layout (P2), confirmation prompt missing after archive selection (P1).
