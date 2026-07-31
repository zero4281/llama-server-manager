## Current Bug Reports

### Self-update loops indefinitely because it restarts with the `--self-update` flag

**Status:** ✅ **COMPLETED**
**Severity:** **High**
**Description:**
When running `./llama-server-manager --self-update`, the program performs the update and then uses `os.execv` to restart itself with the exact same arguments. Because the `--self-update` flag is preserved in the argument list, the new process immediately re-enters the `perform_self_update` method, creating an infinite loop where the program repeatedly displays the update menu and "Success" screen without ever finishing.

**Reproduction Steps:**
1. Run `./llama-server-manager --self-update`.
2. Select the default option (Latest release) and press Enter.
3. Confirm the installation prompt by pressing Enter.
4. Observe that the program immediately restarts and displays the "Self-Update" source selection menu again.
5. Repeat step 4 to confirm the infinite loop.

**Affected Components:**
- `main.py` (`perform_self_update` method)

**Dependencies:**
- None

**Verified Reproduction Workflow:**
Verified via manual dynamic testing in a sandbox environment. The `os.execv` call at `main.py:214` passes `sys.argv[1:]` directly, which includes the `--self-update` flag. This causes the child process to re-execute the self-update logic instead of restarting the manager in its normal operational mode.

**Resolution Summary:**
Modified `main.py` to filter out the `--self-update` flag from the arguments list before calling `os.execv` during self-updates.


### Bug Report
**Title:** Self-update fails to download and replace project files
**Status:** ✅ **COMPLETED**
**Severity/Priority:** High
**Dependencies:** None
**Verified Reproduction Workflow:**
1. Run `./llama-server-manager --self-update`.
2. Select the default option (Latest release) and press Enter.
3. Confirm the installation prompt by pressing Enter.
4. Observe that the program completes the UI flow but the local files (specifically `main.py`) are not updated to the version containing the removal of the `--self-update` flag.

**Resolution Summary:**
Fixed the issue by ensuring the downloaded release correctly overwrites local files and the `--self-update` flag is filtered out before restarting.

---

---

### Bug Report
**Title:** Self-update loses executable permission on llama-server-manager
**Status:** ✅ **COMPLETED**
**Severity/Priority:** Medium
**Dependencies:** `main.py` (Self-update logic), `llama_updater.py` (File movement)

**Verified Reproduction Workflow:**
1. Run `./llama-server-manager --self-update`.
2. Select the default option (Latest release) and press Enter.
3. Confirm the installation prompt by pressing Enter.
4. Observe that the program completes the UI flow but the `llama-server-manager` binary loses its executable bit (e.g., `-rwxrwxr-x` becomes `-rw-rw-r--`).

**Resolution Summary:**
Added `ensure_executable` call in `main.py` during the update process to explicitly set the executable bit on the `llama-server-manager` binary. Verified with manual dynamic testing in a sandbox and full regression tests.


### Bug Report
**Title:** Terminal left in broken state (no echo, weird wrapping) after `--self-update`
**Status:** ✅ **COMPLETED**
**Severity/Priority:** High
**Dependencies:** `main.py` (Self-update restart logic), `ui_manager.py` (Curses lifecycle)

**Description:**
When running `./llama-server-manager --self-update` and selecting the default update source, the program successfully completes the update and restart sequence. However, the terminal is left in a "funky state" where characters are invisible (echo is off) and line wrapping is disrupted. This indicates that the `curses` environment is not being properly torn down before the process terminates or restarts.

**Verified Reproduction Workflow:**
1. Run `./llama-server-manager --self-update`.
2. Select the default option (Latest release) by pressing Enter.
3. Confirm the installation prompt by pressing Enter.
4. Observe that the program completes the update and restarts.
5. Note that the terminal remains in a broken state (no echo, cursor hidden/misplaced) after the process has finished or restarted.

**Affected Components:**
- `main.py`
- `ui_manager.py`
**Resolution Summary:**
Ensured that `curses.endwin()` is called in `ui_manager.py` during the self-update sequence to restore the terminal state properly before the process restarts.

### 📋 Project Roadmap / Status Summary

| Section | Status |
| **Bug Reports** | 2 open |
| **Install Workflow (§7.3)** | All bugs resolved. |

**Current Priorities:**

1. **P1** — Fix self-update infinite loop by filtering `--self-update` flag from arguments.

---
