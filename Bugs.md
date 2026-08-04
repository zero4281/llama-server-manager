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

### Project Roadmap
- [x] Fix `--install-llama` fails to restart `llama-server` and throws `NameError` (High)
