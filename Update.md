# Update.md — Code Updates Required (Gap Assessment v1.5)

**Version:** 1.5  
**Date:** April 2026  
**Author:** zero4281

---

## Summary

This document outlines code updates required to align the codebase with Requirements.md v1.5. The gap assessment identified **two implemented but non-required features** that should be removed to reduce code complexity and maintenance burden.

---

## Gap Assessment Findings

### ❌ Implemented but Non-Required: Features to Remove

#### 1. `print_simple_menu` Method in `ui_manager.py`

**Location:** `ui_manager.py:1470-1617` (147 lines)

**Description:** This method provides simple menu rendering without window borders, using direct screen positioning. It duplicates functionality already available through `render_menu`.

**Why remove:**
- Not referenced anywhere in the codebase
- Duplicates core menu functionality with less robust error handling
- Violates single responsibility principle
- Requirements.md §8.3 specifies numbered menus should be rendered inside bordered `curses` windows (which `render_menu` does)
- Adds unnecessary code complexity

**Recommended action:** Remove the entire `print_simple_menu` method (147 lines) from `ui_manager.py`.

---

## ✅ Fully Implemented and Compliant Features

All features specified in Requirements.md v1.5 are fully implemented and compliant:

| Section | Feature | Status | Notes |
|---------|---------|--------|-------|
| §2 | Project Structure | ✅ Complete | All files present and organized |
| §3 | Configuration File | ✅ Complete | Auto-generation, options/logging working |
| §4 | Start Script | ✅ Complete | Bash script with venv check functional |
| §5 | Main Entry Point | ✅ Complete | All CLI flags, self-update with source selection |
| §5.1.1 | WSL Detection | ✅ Complete | main.py:89 detects Windows/WSL |
| §6 | llama_updater.py | ✅ Complete | GitHub API, platform detection, download/extraction |
| §7 | Run Script | ✅ Complete | Process execution, PID management, graceful shutdown |
| §7.4 | Daemon Mode | ✅ Complete | runner.py:131 runs llama-server as daemon |
| §8 | CLI User Interface Module | ✅ Complete | UIManager with menus, prompts, progress bars |
| §9 | Non-Functional Requirements | ✅ Complete | Cross-platform, error handling, PEP 8 |

---

## Testing Status

All unit tests for `ui_manager.py` pass (33+ tests covering):
- Menu navigation and selection
- Confirmation prompts
- Progress bars and spinners
- Terminal size adaptation
- Timeout handling
- Edge cases and error scenarios

---

## Next Steps

1. **Remove `print_simple_menu` method** from `ui_manager.py` (147 lines)
2. **Run linting and type checking** to verify no issues introduced
3. **Update Plan.md** to reflect:
   - Correct compliance status against Requirements.md v1.5
   - Accurate implementation verification
   - Completed features (WSL detection, config auto-gen, daemon mode)

---

**End of Update.md**
