# Bug Reports

## Current Bug Reports

### Bug Report
**Title:** `--update-llama` fails with `NameError` because `load_config` is not imported in `llama_updater.py`
**Status:** ✅ **COMPLETED**
**Severity/Priority:** **High**
**Dependencies:** None
**Description:**
When running `./llama-server-manager --update-llama`, the application crashes during the fast-path update logic. The `LlamaUpdater.update` method attempts to call `load_config()` to retrieve the configuration, but `load_config` is not imported into the `llama_updater` module, resulting in a `NameError`.

**Verified Reproduction Workflow:**
1. Run `./llama-server-manager --update-llama`.
2. Observe the application flashing an error message: `Error: name 'load_config' is not defined` and then immediately exiting.
3. This occurs because `llama_updater.py:1157` calls `load_config()` without it being imported in the module scope.

**Affected Components:**
- `llama_updater.py` (`LlamaUpdater.update` method)

**Resolution:** Added missing imports for load_config and save_config in llama_updater.py, and implemented the delete_existing_installation helper to resolve a secondary NameError found during verification.

### Bug Report
**Title:** `install_release` fails when `./llama-cpp` directory is not cleaned before extraction
**Status:** ✅ **COMPLETED**
**Severity/Priority:** High
**Dependencies:** `llama_updater.py` (`install_release` function)
**Description:** 
When running `./llama-server-manager --install-llama`, the installation fails if the `./llama-cpp` directory already exists and contains a subdirectory with the same name as the archive being extracted. This occurs because `install_release` does not call `delete_existing_installation()`, unlike the fast-path logic in `_install_release_core`.

**Resolution:** Added `delete_existing_installation()` to the `install_release` function in `llama_updater.py` to ensure the directory is cleared before extraction.

**Verified Reproduction Workflow:**
1. Ensure the `./llama-cpp` directory exists in the project root.
2. Create a subdirectory within `./llama-cpp` that matches the expected name of the release's extracted content (e.g., `mkdir ./llama-cpp/llama-b10235`).
3. Run `./llama-server-manager --install-llama`.
4. Observe the application exit with `shutil.Error: Destination path '...' already exists` during the extraction phase.

### Bug Report
**Title:** `--update-llama` fails to restart `llama-server` after successful update
**Status:** ✅ **COMPLETED**
**Severity/Priority:** High
**Dependencies:** `llama_updater.py`
**Description:**
When running `./llama-server-manager --update-llama`, the application successfully completes the update of the `llama-cpp` binaries but fails to restart the already-running `llama-server` instance. The `llama-server.pid` file remains unchanged, and the old process is either left running or is stopped without being replaced by a new instance. Analysis of `llama_updater.py` reveals that while a `_restart_llama_server` function is defined, it is never actually invoked by the `install_release` or `_install_release_core` workflows.

**Verified Reproduction Workflow:**
1. Start `llama-server` using the manager or manually, ensuring `llama-server.pid` is created and the process is running.
2. Run `./llama-server-manager --update-llama`.
3. Observe that after the update completes, the `llama-server` process is not restarted (the PID remains the same or no new process is spawned).

**Affected Components:**
- `llama_updater.py` (`install_release` and `_install_release_core` functions)

**Resolution:** Fixed the restart logic in `llama_updater.py` by ensuring `_restart_llama_server` is called when a `llama-server.pid` file exists. Also fixed indentation errors in `llama_updater.py` to resolve syntax issues. Verified the fix with both manual dynamic testing and automated regression tests.

## Project Roadmap
- [ ] Fix `NameError` in `llama_updater.py` (High Priority)
- [ ] Fix `install_release` failure when `./llama-cpp` is not cleaned (High Priority)
- [ ] Fix `llama-server` restart failure after `--update-llama` (High Priority)
