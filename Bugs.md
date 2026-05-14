# Bugs.md

## Current Bug Reports

### 🔴 HIGH: Self-update fails with a bytes/string type error
**Status:** 🟠 **OPEN**  
**Priority:** **P1** - Major feature broken; self-update completely non-functional

**Description:**  
When running `./llama-server-manager --self-update`, the self-update process fails with a type error: "argument should be a str or an os.PathLike object where __fspath__ returns a str, not 'bytes'". The error occurs during the zip file extraction phase when `zipfile.ZipFile()` is called with bytes instead of a file path string.

**Reproduction Steps:**
1. Run: `./llama-server-manager --self-update <<< $"\n\n"`
2. Navigate through the source selection menu (default: Latest release)
3. Select the option to proceed
4. Confirm the update
5. **Expected:** The wrapper downloads and extracts the zip archive from GitHub, updates files, and restarts
6. **Actual:** The process fails with error: `Self-update failed: argument should be a str or an os.PathLike object where __fspath__ returns a str, not 'bytes'`

**Key Symptoms:**
- Self-update menu renders correctly via UIManager
- Download proceeds without issues
- Extraction fails when attempting to create ZipFile from downloaded content
- Error message indicates bytes type instead of expected path string

**Root Cause Analysis:**
In `main.py:185`, the code attempts to create a `zipfile.ZipFile` object using `Path(zip_content)` where `zip_content` is the raw bytes from `zip_response.content`. The `zipfile.ZipFile()` constructor expects a file path string (or Path object pointing to a file), not raw bytes. The correct approach would be to write the bytes to a temporary file first, then open that file path.

**Affected Components:**
- `main.py:perform_self_update` (line 185) - ZipFile creation with bytes argument
- `main.py` (lines 171-186) - Self-update download and extraction flow
- Requirements.md Section 5.3.3 - Update execution specification

**Dependencies:**
- Requirements.md Section 5.3.3 (Update execution: "Download the selected archive or branch ZIP to a temporary location. Replace local project files with the downloaded versions.")
- Requirements.md Section 9.3 (Error handling: "All external calls must be wrapped in try/except blocks. Errors must be logged and result in a non-zero exit code")

**Workaround:**
None available. The self-update feature is completely broken and requires manual intervention to update the wrapper.

**Test Coverage:**
- No existing tests for the self-update flow in `main.py`
- No tests for zip file extraction from downloaded content
- No tests for the restart mechanism after successful update
- Testing Strategy.md requires tests to verify self-update downloads, extracts, updates, and restarts correctly
- Missing: Test that self-update successfully downloads, extracts, and restarts with the same arguments

**Impact:**
Self-update is a critical maintenance feature that allows users to keep the wrapper up-to-date with the latest bug fixes and features. Without working self-update:
- Users cannot easily update the wrapper to newer versions
- Security patches and bug fixes must be applied manually
- The project cannot be maintained or evolved through automated means
- Users are stuck with outdated versions that may contain bugs or security vulnerabilities
- The wrapper's ability to self-correct and improve is compromised

## Summary

**Last Updated:** May 3, 2026  
**Overall Status:** All critical bugs resolved.

* **Resolved:** Self-update fails with bytes/string type error (P1)
* **Resolved:** Fallback logic in render_menu not being triggered (P1)
* **Resolved:** Arrow key crashes (P0)
* **Resolved:** Missing confirmation prompt after llama.cpp installation selection (P1)
* **Resolved:** Confirmation prompt missing after archive selection (P1)
* **Resolved:** Title/footer bar disappearance (P3)
* **Resolved:** Logger debug messages (P3)
* **Resolved:** Redundant fallback sections (P2)
* **Resolved:** Curses environment drops (P3)
* **Resolved:** Menu border issues (P3)
* **Resolved:** Confirmation prompt layout (P2)
* **Resolved:** get_checksum_assets() returns no values (P1)
