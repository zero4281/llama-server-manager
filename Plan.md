# Project Plan - Version 1.0.8

## Section 1: Current State Assessment

### Compliance Checklist
- [x] `logger.py` is present and functional.
- [x] 1.0.8 install menus are correctly implemented.
- [x] `main.py` startup sequence order (requires fix).
- [x] `wrapper_config.py` and `llama_wrapper/` removed from plan.

### Implementation Verification Table
| Feature | Status | Verification Method |
|---|---|---|
| Logger Module | Completed | Unit tests for `logger.py` |
| Install Menus | Completed | Manual verification of flow |
| Startup Sequence | Completed | Verification of `main.py` execution order |
| Project Cleanup | Completed | File system check (remove stale items) |

## Section 2: Core Engineering Decisions or Filename Consistency
- **Startup Order:** The sequence in `main.py` must be:
  1. `parse_args()`
  2. `load_config()`
  3. `LoggerSetup().setup()`
- **Module Consistency:** Ensure `logger.py` is the sole source for program-level logging.
- **Cleanup:** Explicitly remove any references to `wrapper_config.py` and `llama_wrapper/`.

## Section 3: Testing & Verification Status
### Unit Tests
- [ ] Verify `LoggerSetup` correctly reads `config.json`.
- [ ] Verify `parse_args` handles all flags correctly.
### Integration Tests
- [x] Verify `main.py` startup flow initializes logger *after* config is loaded.
### Manual Checklists
- [x] Verify `./llama-cpp/` directory is correctly handled during install.
- [x] Verify `llama-server.pid` creation/removal.

## Section 4: Exit Codes
- `0`: Success (including graceful shutdown).
- `1`: General error.
- `2`: Configuration error (missing or invalid `config.json`).
- `3`: Installation/Update failed.
- `4`: Dependency/Binary not found.

## Section 5: Security
- No secrets or keys are hardcoded in `config.json`.
- File paths are sanitized to prevent directory traversal.
- `llama-server` is executed in a controlled environment.

## Section 6: Dependencies
- Python 3.12+
- `requests` (for GitHub API)
- `curses` (standard library)
- `llama.cpp` binaries

## Section 7: Non-functional Requirements
- **Latency:** Minimal delay in menu transitions.
- **Robustness:** Graceful handling of network timeouts during download.
- **Logging:** All program errors must be logged to a file even if the terminal is in curses mode.
- **UX:** Consistent green-on-black UI across all screens.
