# Llama Server Manager — Project Plan
**Version:** 1.6

## Section 1: Current State Assessment

### 1.1 Compliance Checklist
| Requirement | Status | Notes |
| --- | --- | --- |
| **Core CLI functionality** | ✅ Implemented | `main.py` handles all primary operations. |
| **Self-update mechanism** | ✅ Implemented | Supports latest, previous, and HEAD sources. |
| **Install/Update llama.cpp** | ✅ Implemented | Uses `llama_updater.py` for full workflow. |
| **Stop-server functionality** | ✅ Implemented | Handled in `runner.py` with PID management. |
| **Configuration Management** | ✅ Implemented | `wrapper_config.py` manages `config.json`. |
| **ncurses-based UI** | ✅ Implemented | `ui_manager.py` handles all interactive elements. |
| **WSL Detection** | ✅ Implemented | Warning issued on native Windows. |
| **Cross-Platform Support** | ✅ Implemented | Supported on Linux, macOS, and WSL. |

### 1.2 Implementation Verification Table
| Component | File(s) | Status | Verification Method |
| --- | --- | --- | --- |
| Entry Point | `main.py` | ✅ Complete | Verified via CLI execution |
| Llama.cpp Updater | `llama_updater.py` | ✅ Complete | Verified via `--install-llama` |
| Runner | `runner.py` | ✅ Complete | Verified via `--stop-server` |
| UI Manager | `ui_manager.py` | ✅ Complete | Verified via Unit Tests |
| Configuration | `wrapper_config.py` | ✅ Complete | Verified via config.json persistence |

## Section 2: Core Engineering Decisions & Consistency
- **Path Handling:** Strictly uses `pathlib.Path` for all filesystem operations.
- **UI Framework:** Exclusively uses standard library `curses` for a consistent, no-dependency terminal UI.
- **Process Management:** Uses `subprocess` for `llama-server` execution with PID tracking in `llama-server.pid`.
- **Logging:** Unified logging via `wrapper_config.py` with support for both wrapper and server logs.
- **Naming Convention:** Adheres to `llama-server-manager` naming for the main script and `llama_updater.py` etc. for modules.

## Section 3: Testing & Verification Status
### 3.1 Unit Tests
- `Tests/test_ui_manager_comprehensive.py` ✅ Passed
- `Tests/test_wsl_detection.py` ✅ Passed
- `Tests/test_timeout_pytest.py` ✅ Passed
- `Tests/test_ui_manager_api.py` ✅ Passed
- `Tests/test_confirmation_fallback.py` ✅ Passed

### 3.2 Integration Tests
- `--install-llama` full workflow: 🟡 Pending (Manual Verification)
- `--self-update` full workflow: 🟡 Pending (Manual Verification)

### 3.3 Manual Verification
- Checksum verification for downloads: 🟡 Pending
- Graceful shutdown (SIGTERM) verification: 🟡 Pending

## Section 4: Architectural Specifications
### 4.1 Exit Codes
- `0`: Success (standard completion)
- `1`: General error (e.g., file not found, user input error)
- `2`: Fatal error (e.g., self-update failure, download failure)

### 4.2 Security
- No secret keys or hardcoded credentials.
- No local storage of sensitive user data.
- Checksum verification for all binary downloads to prevent tampering.

### 4.3 Dependencies
- `requests`: For GitHub API and file downloads.
- `pathlib`: For cross-platform pathing.
- `subprocess`: For process management.
- `curses`: For Terminal UI.

### 4.4 Non-Functional Requirements
- **Responsiveness:** Progress bars for all long-running tasks (downloads, extractions).
- **Persistence:** `config.json` persists last-used selections.
- **Reliability:** Clean-up of temporary files and archive deletion on failure.
- **Portability:** Works across Linux, macOS, and WSL.
