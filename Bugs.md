# Bugs.md

## Current Bug Reports

### 🔴 HIGH: get_checksum_assets() returns no values, skipping checksum verification
**Status:** 🟢 **RESOLVED**  
**Priority:** **P1** - Major feature broken; security verification skipped

**Description:**  
When running `--install-llama`, the `get_checksum_assets()` method in `llama_updater.py` returns an empty list, causing checksum verification to be skipped entirely. The message "No checksum file available for this release, skipping verification" appears, and the post-install sanity check fails with "Warning: llama-server --version returned exit code 127" and "Warning: Could not verify llama-server version: 'NoneType' object is not subscriptable".

**Reproduction Steps:**
1. Run: `UI_MANAGER_DEBUG=1 PYTHONWARNINGS=ignore python3 main.py --install-llama <<< $'1\n8\n3\ny\n'`
2. **Expected:** Checksum files should be properly retrieved and verified from the release assets
3. **Actual:** Checksum verification is skipped, and sanity check fails with cryptic error messages

**Key Symptoms:**
- Checksum verification is skipped for releases that have checksum files available
- "No checksum file available for this release, skipping verification" message appears
- Sanity check fails with exit code 127 (llama-server not found)
- Error message "'NoneType' object is not subscriptable" appears during version verification
- The issue affects release b9010 and may affect other releases with checksum files

**Affected Components:**
- `llama_updater.py:get_checksum_assets` (line 361-377) - returns empty list for releases with checksum files
- `llama_updater.py:install_release` (line 661-793) - checksum verification logic not triggered
- `llama_updater.py:verify_installation` (line 610-645) - sanity check fails due to missing llama-server
- `llama_updater.py:LlamaUpdater:install` (line 807-895) - full installation flow affected
- `main.py:Main:run` (line 233-309) - entry point that delegates to LlamaUpdater

**Dependencies:**
- Requirements.md Section 6.5 (checksum verification: "After the download completes, check whether the release provides a checksum file... If one is present, download it and verify the archive before proceeding")
- Requirements.md Section 6.5 (fallback: "If no checksum asset is available for the release, skip verification and proceed directly to extraction")
- Requirements.md Section 9.3 (error handling: "All external calls must be wrapped in try/except blocks. Errors must be logged and result in a non-zero exit code")

**Root Cause Analysis:**
The `get_checksum_assets()` function filters release assets by checking if the asset name (lowercase) ends with `.sha256sum.txt` or `.sha256sum`, or contains 'sha256' or 'checksum'. The function returns an empty list for releases that have checksum files, indicating either:
1. The asset naming convention in the release differs from what the function expects
2. The `release.get('assets', [])` returns an empty list or None
3. The asset names in the release don't match the expected patterns (case-sensitivity, spacing, or different naming scheme)

**Workaround:**
None available. Manual verification of downloaded archives is not possible within the automated installation flow.

**Test Coverage:**
- No existing tests for `get_checksum_assets()` function
- No tests for checksum verification flow in `install_release`
- No tests for post-install sanity check in `verify_installation`
- Testing Strategy.md requires tests to verify checksum file detection and verification
- Missing: Test that `get_checksum_assets()` correctly identifies checksum assets from GitHub release data

**Related Bugs:**
- 🔴 HIGH: Fallback logic in render_menu not being triggered (P1) - similar degradation in error handling
- P1: Missing confirmation prompt after archive selection (P1) - related to installation flow errors

**Impact:**
Checksum verification is a critical security feature that ensures the integrity and authenticity of downloaded llama.cpp releases. Without working checksum verification:
- Users cannot verify that the downloaded archive has not been tampered with
- The installation flow may proceed with corrupted or malicious archives
- The post-install sanity check fails, leaving users with a non-functional installation
- The reliability and security of the installation process is compromised
- Affected releases (b9010 and potentially others) cannot be verified for integrity

---

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
| **P1 (High)** | get_checksum_assets() returns no values, skipping checksum verification | 🟠 Open |
| **P2 (Medium)** | Confirmation prompt in llama_updater.py doesn't match Requirements.md border styling specification | 🟢 Resolved |
| **P2 (Medium)** | Confirmation prompt in llama_updater.py uses render_confirmation() but Requirements.md Section 6.3.3 specifies a different layout | 🟢 Resolved |
| **P3 (Low)** | Title and footer bars in menu windows disappear or draw incorrectly | 🟢 Resolved |
| **P3 (Low)** | Menus not displayed in correctly bordered windows | 🟢 Resolved |
| **P2 (High)** | ui_manager.py:render_confirmation() has multiple redundant fallback sections | 🟢 Resolved |
| **P3 (Medium)** | Program drops out of curses and displays print on line 1312 | 🟢 Resolved |
| **P3 (Low)** | Logger debug message never prints | 🟢 Resolved |

---

## Summary

**Last Updated:** May 2, 2026  
**Overall Status:** All bugs resolved.

* **Resolved:** Fallback logic in render_menu not being triggered (P1)
* **Resolved:** Arrow key crashes (P0), missing confirmation prompt (P1), title/footer bar disappearance, logger debug messages, redundant fallback sections, curses environment drops, menu border issues, confirmation prompt layout (P2), confirmation prompt missing after archive selection (P1).
* **Resolved:** get_checksum_assets() returns no values, skipping checksum verification (P1)