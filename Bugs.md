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
## Project Roadmap
- [ ] Fix `NameError` in `llama_updater.py` (High Priority)
