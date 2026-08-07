### Current Bug Reports

**Title:** `--install-llama` fails to restart `llama-server` and throws `NameError`
**Status:** ✅ **COMPLETED**
**Severity/Priority:** **High**
**Dependencies:** `llama_updater.py`
**Description:**
When running `./llama-server-manager --install-llama`, the application fails to restart `llama-server` if it is already running. It also fails to persist the configuration even if it isn't running, throwing a `NameError: name 'config' is not defined` (or `NameError: name 'args' is not defined`) at the end of the installation process.

This occurs because the `install_release` function in `llama_updater.py` attempts to use `args` and `config` variables which are neither passed as arguments nor loaded within its scope. The `config` variable is only loaded in the `_install_release_core` helper function, and `args` is completely missing from the `install_release` signature.

**Verified Reproduction Workflow:**
1. Start `llama-server` (e.g. using `runner.py` or manually) so that `llama-server.pid` exists.
2. Run `./llama-server-manager --install-llama`.
3. Select default options (Enter 4 times) to proceed with the default release, platform, and backend.
4. Observe the error `NameError: name 'args' is not defined` (if `llama-server` was running) or `NameError: name 'config' is not defined` (if it was not) at the end of the installation process.

**Resolution:** Fixed `NameError` by passing `args` and `config` to `install_release` in `llama_updater.py`. Improved configuration persistence and handled `llama-server` restart logic.

**Affected Components:**
- `llama_updater.py` (`install_release` function)

**Title:** `--install-llama` fails with "No compatible assets found" for release `b10297`
**Status:** ✅ **COMPLETED**
**Severity/Priority:** **High**
**Dependencies:** `llama_updater.py`
**Description:**
When running `./llama-server-manager --install-llama` and manually entering release tag `b10297`, the application exits with the message: "No compatible assets found for this release."

The issue stems from how `llama_updater.py` parses assets for a release. It appears that the naming pattern regex or the filtering logic is failing to correctly identify and exclude incompatible assets (like `llama-b10297-xcframework.zip`) while still finding valid assets for the target platform. This results in an empty list of available platforms, triggering the error message.

**Verified Reproduction Workflow:**
1. Run `./llama-server-manager --install-llama`.
2. Select option `0` ("Enter a tag manually").
3. Enter `b10297` when prompted for the release tag.
4. Observe the error: "No compatible assets found for this release."

**Test Suitability:**
A new automated test case should be added to `Tests/test_ui_manager_pytest.py` to verify that `llama_updater.py` correctly filters assets and identifies compatible platforms, ensuring that non-binary assets (e.g., XCFrameworks) are excluded from the selection menus.

**Resolution:** Updated the `new_pattern` regex in `llama_updater.py` to include an optional backend segment, ensuring that releases with backends are correctly parsed and included in the platform selection menu.


**Title:** `--install-llama` crashes with `Error: 'backend'` after selecting Operating System & Architecture
**Status:** ✅ **COMPLETED**
**Severity/Priority:** **High**
**Dependencies:** `llama_updater.py`, `ui_manager.py`
**Description:**
When running `./llama-server-manager --install-llama`, the application exits after the "Select Operating System & Architecture" (second) menu with the message: "Error: 'backend'". The application should proceed to the "Select Compute Backend" menu but fails to resolve the backend segment for the selected OS/Architecture.

**Verified Reproduction Workflow:**
1. Run `./llama-server-manager --install-llama`.
2. Press Enter to select the default release.
3. Press Enter to select the default Operating System & Architecture (e.g., Ubuntu x64).
4. Observe the error message `Error: 'backend'` and the application exit.

**Resolution:** Updated `llama_updater.py` to ensure the `backend` key is always included in the parsed asset dictionary, even when the release name uses the old naming format or does not specify a backend. This prevents the `KeyError` that occurred during the selection flow.

**Test Suitability:**
A new automated test case should be added to `Tests/test_ui_manager_pytest.py` to verify that `llama_updater.py` correctly identifies and parses the backend segment from the release assets, ensuring it doesn't fail when a valid backend is present for the selected OS/Architecture.

### Project Roadmap
- [x] Fix `--install-llama` fails to restart `llama-server` and throws `NameError` (High)
- [x] Fix `--install-llama` fails with "No compatible assets found" for release `b10297` (High)
- [x] Fix `--install-llama` crashes with `Error: 'backend'` after selecting Operating System & Architecture (High)
