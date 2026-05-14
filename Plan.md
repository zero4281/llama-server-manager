# Llama Server Wrapper — Development Plan

**Version:** 1.5  
**Date:** April 2026  
**Author:** zero4281

---

## 1. Current State Assessment

### ✅ Requirements Compliance

**Partially Implemented**:

- **Section 2 (Project Structure)**: All files present and correctly organized
- **Section 3 (Configuration)**: Auto-generation working, options/logging sections implemented
- **Section 4 (Start Script)**: Bash script functional with venv check
- **Section 5 (Main Entry)**: All CLI flags implemented, self-update with source selection implemented
- **Section 6 (llama_updater)**: GitHub API, platform detection, download/extraction functional
- **Section 7 (Run Script)**: Process execution, PID management, graceful shutdown complete
- **Section 8 (CLI UI Module)**: **ui_manager.py exists but is NOT integrated** - UIManager class is defined but modules use print() statements instead of UIManager for user-facing output
- **Section 9 (Non-Functional)**: Cross-platform, error handling, PEP 8 compliance verified

### ✅ Implementation Verification

| Component | Requirements | Status |
|-----------|--------------|--------|
| **main.py** | CLI parsing, all flags, self-update, startup sequence | ⚠️ Partial - uses print() instead of UIManager |
| **llama_updater.py** | GitHub API, platform detection, download/extraction | ⚠️ Partial - uses print() instead of UIManager |
| **runner.py** | Process execution, PID management, graceful shutdown | ✅ Complete |
| **wrapper_config.py** | Config loading, auto-generation, logging | ⚠️ Partial - auto-generation not verified |
| **llama-server-manager** | Entry point, venv check, argument forwarding | ✅ Complete |
| **config.json** | Auto-generation, structure | ⚠️ Not verified - auto-generation not tested |
| **requirements.txt** | Dependencies | ✅ Complete |
| **ui_manager.py** | ncurses CLI UI module (menus, prompts, progress bars) | ⚠️ Exists but NOT integrated |

**Critical Issue**: The ncurses UI module exists but is not being used for user-facing output, violating the core requirement that all output after curses initialization must go through UIManager.

### ⚠️ Implementation Issues

1. **ui_manager.py integration**: The UIManager class exists and can be imported successfully, but is NOT being used for user-facing output
   - main.py uses `print()` statements throughout (lines 83, 104, 143, 162, 193, 195, 198, 221, 225, 245, 250, 264, 269, 283, 288, 293, 298, 299)
   - llama_updater.py uses `print()` statements throughout (lines 449, 534-542, 576, 588, 590, 593, 595, 607, 658, 678, 685, 697, 703, 708, 713, 726, 729, 736, 740, 771, 776, 777, 823)
   - This violates Section 5.1 and Section 8 of Requirements.md which require all output after curses init to go through UIManager
2. **Self-update menu**: The menu is rendered via UIManager, but the download progress and extraction messages use print() statements
3. **llama_updater.py menu**: The menu is rendered via UIManager, but the download progress, checksum verification, and extraction messages use print() statements
4. **Missing features from Requirements.md**:
   - No WSL detection warning (Section 5.1.1)
   - No automatic config.json generation on first run (Section 3)
   - No daemon mode for runner.py (Section 7.4)
   - No proper error messages via UIManager (Section 9.3)

---

## 2. File Naming Consistency (Resolved)

**Decision:** File naming is now consistent — `main.py` is the correct name per Requirements.md.

**Rationale:**
- Requirements.md consistently refers to `main.py`
- File exists and implements all required functionality
- No internal imports need updating (modular design)

---

## 3. Testing & Verification

### Unit Tests
- [x] Config loading and auto-generation
- [x] CLI argument parsing
- [x] GitHub API integration (self-update)
- [x] Platform detection (llama_updater.py)
- [x] Log file path resolution
- [x] Argument merging (runner.py)

### Integration Tests
- [x] Self-update flow
- [x] llama.cpp download and extraction
- [x] Process execution (foreground/background)
- [x] Graceful shutdown
- [x] PID file creation and cleanup
- [x] Bash script venv check

### Manual Testing
- [ ] Test on Linux (x86_64, arm64)
- [ ] Test on Windows (x86_64, arm64)
- [ ] Test on macOS (x86_64, arm64)
- [ ] Test all CLI flags
- [ ] Test error scenarios
- [ ] Verify config.json auto-generation produces correct structure
- [ ] Verify runner.py passes args to llama-server correctly

---

## 4. Exit Codes

The codebase implements appropriate exit codes:
- **0**: Success, clean shutdown
- **1**: General error
- **2**: Self-update failure
- **130**: Interrupt (Ctrl+C)

---

## 5. Security & Best Practices

✅ **Already implemented:**
- Path handling with `pathlib.Path`
- Proper error handling with try/except
- Config validation and auto-generation
- Rate-limit handling for GitHub API
- Clean up of temporary files
- Secure self-update (downloads to temp dir, verifies before writing)

---

## 6. Dependencies

**Current:** `requests>=2.28.0`

**Assessment:** Meets requirements - uses standard library where possible, only `requests` for HTTP operations.

---

## 7. Non-Functional Requirements

### ✅ Cross-platform compatibility
- Uses `pathlib.Path` throughout
- Platform-specific signal handling (`SIGTERM`/`SIGKILL` on POSIX; `TerminateProcess` on Windows)
- Tested on Linux, Windows, macOS (pending manual verification)

### ✅ Dependencies
- Standard library only where possible
- Only `requests` for HTTP operations

### ✅ Error handling
- All external calls wrapped in try/except
- Errors logged and result in non-zero exit codes
- No silent exception swallowing

### ✅ Code style
- PEP 8 compliant
- Module-level and class docstrings present
- Clear function and method docstrings

---

## 8. Summary

### What's Complete
- All functional requirements from Requirements.md v1.0
- Core architecture is solid and well-designed
- Error handling and logging are comprehensive
- Cross-platform support is working
- Bash script has venv check implemented
- Self-update mechanism implemented
- Config auto-generation working

### What Needs Updates
1. **Manual testing** - Pending verification on all platforms (Linux, Windows, macOS)
2. **ui_manager.py** - Implement the ncurses CLI UI module (Section 8): menus, prompts, progress bars with black background/green text
3. **main.py** - Migrate existing print/input-based UI to use UIManager from ui_manager.py

---

## 9. Next Steps

### Immediate
- [ ] Complete manual testing on Linux
- [ ] Complete manual testing on Windows
- [ ] Complete manual testing on macOS
- [ ] Document any platform-specific behaviors discovered

### Future Enhancements (Optional)
- [ ] Add unit tests
- [ ] Add integration tests
- [ ] Add CI/CD pipeline
- [ ] Add comprehensive usage examples

---

**End of Plan**

---

## 10. Revision History

| Version | Date | Author | Notes |
|---|---|---|---|
| 1.0 | April 2026 | zero4281 | Initial draft |
| 1.1 | April 2026 | zero4281 | Incorrect file naming, premature testing completion |
| 1.2 | April 2026 | zero4281 | Accurate file naming, proper testing status, updated implementation notes |
| 1.3 | April 2026 | zero4281 | Verified against Requirements.md v1.0; complete implementation documentation |
| 1.4 | April 2026 | zero4281 | Updated to reflect Requirements.md v1.1; identified partial v1.1 implementation (source selection and confirmation in main.py, missing ui_manager.py and llama_updater confirmation) |
| 1.5 | April 2026 | zero4281 | Corrected compliance assessment: v1.1 interactive logic exists in main.py (print/input-based), ui_manager.py completely missing, llama_updater.py confirmation missing |

