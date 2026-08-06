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


**Title:** `--install-llama` fails with "Platform selection cancelled" when no compatible assets are found for a release
**Status:** ✅ **COMPLETED**
**Severity/Priority:** **Medium**
**Dependencies:** `llama_updater.py`
**Description:**
When installing a release that contains no assets matching the expected naming pattern (e.g., a release containing only non-binary artifacts like XCFrameworks), the `available_platforms` list becomes empty. This causes `ui.render_menu` to return `-1` immediately, triggering the "Platform selection cancelled" error message.

The current exclusion logic in `llama_updater.py` correctly filters out non-binary assets like `llama-b10297-xcframework.zip` (wrong segment count) and `cudart-llama-bin-win-cuda-12.4-x64.zip` (incorrect project prefix). However, the application fails to handle the case where no valid assets remain for a selected release, providing a confusing cancellation message instead of informing the user that no compatible assets were found.

**Verified Reproduction Workflow:**
1. Run `./llama-server-manager --install-llama`.
2. Select a release (e.g., `b10297`) that contains no assets matching the `llama-{tag}-bin-{platform}-{arch}` pattern (e.g., a release containing only XCFrameworks).
3. Observe that the application exits immediately after the release selection with the message "Platform selection cancelled."

**Affected Components:**
- `llama_updater.py` (`install_release` function)

**Summary of Changes:**
Updated `llama_updater.py` to check if any valid platform options were generated; if none are available, it now correctly informs the user that no compatible assets were found for that release instead of returning a confusing "Platform selection cancelled" message.

### Project Roadmap
- [x] Fix `--install-llama` fails to restart `llama-server` and throws `NameError` (High)
- [x] Fix `--install-llama` fails with "Platform selection cancelled" when no compatible assets are found for a release (Medium)
