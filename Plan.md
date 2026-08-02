# Plan: Llama Server Manager

**Version:** 1.1.2

## Section 1: Current State Assessment

### Requirement Verification Status

| Requirement | Status | Notes |
|---|---|---|
| Req 3 (Configuration) | Fully Met | |
| Req 4 (Start Script) | Fully Met | |
| Req 5 (Main Entry Point) | Partially Met | Missing `__version__` constant and `--version` flag. |
| Req 6 (Configuration Module) | Fully Met | |
| Req 7 (Logging Module) | Fully Met | |
| Req 8 (Update/Download Module) | Partially Met | Restart behavior (§8.5.1) is unmet. |
| Req 9 (Run Script) | Fully Met | |
| Req 10 (CLI UI Module) | Fully Met | |
| Req 11 (Non-Functional) | Fully Met | |

### Structural & Functional Drift
- **Version Mismatch:** `Plan.md` was at v1.1.0 while `Requirements.md` is at v1.1.2.
- **Incorrect Status:** Requirement 8 was incorrectly marked as "Fully Met" in previous documentation.
- **Requirement 5 Specifics:** Specific items for Requirement 5 (Main Entry Point) need to be addressed (missing `__version__` constant and `--version` flag).

## Section 2: Core Engineering Decisions or Filename Consistency
- **Configuration Ownership:** `config.py` is the single source of truth for reading, writing, and default-generation of `config.json`. No other module may access `config.json` directly.
- **Logging Isolation:** `logger.py` configures the root logger; all other modules obtain independent loggers via `logging.getLogger(__name__)`.
- **UI Consistency:** `UIManager` is the sole entry point for all interactive output (menus, prompts, progress bars, and messages) within the curses environment.

## Section 3: Testing & Verification Status
- **Unit Tests:**
  - [ ] Test `config.py`'s `load_config()` with missing/malformed files.
  - [ ] Test `logger.py`'s root logger configuration.
- **Integration Tests:**
  - [ ] Verify `main.py`'s startup sequence correctly handles `--version`.
  - [ ] Verify `LlamaUpdater`'s fast path and fallback logic.
- **Manual Checklists:**
  - [ ] Verify `llama-server-manager --version` output.
  - [ ] Verify `llama-server` restart behavior on install/update.

## Section 4: Exit Codes
- `0`: Success (Normal exit, version display, update completion).
- `1`: General Error (Config parsing error, network failure, file I/O error).
- `2`: Dependency Missing (e.g. `llama-cpp` not found).
- `3`: User Cancellation (Exiting via `n`/`Esc` in menus/confirmation).

## Section 5: Security
- No sensitive credentials (passwords, API keys) are stored in `config.json`.
- Local file permissions are respected; `config.json` is created in the project directory.
- The program does not execute arbitrary shell commands except for the managed `llama-server` process.

## Section 6: Dependencies
- Python 3.12+
- `requests` (for GitHub API calls)
- Standard `curses` library (for CLI UI)
- Standard `logging` library (for program logs)

## Section 7: Non-Functional Requirements
- **Cross-platform:** Linux, macOS, Windows (WSL).
- **Reliability:** Proper cleanup of PID files and temporary download archives.
- **User Experience:** Interactive workflow must remain consistent within the `curses` environment.
- **Transparency:** Progress bars and status messages must be clear and real-time.
