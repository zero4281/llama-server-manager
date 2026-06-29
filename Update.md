# Update.md

## Required Updates

### 1. UI Integration (Main Task)
- Migrate all interactive output from `print()` to `UIManager` across all modules.
- Ensure that once `UIManager` is initialized, no direct `print()` calls are used for user-facing information.

#### `main.py`
- Replace `print()` calls for operation headers (Self-Update, Install, Update, Stop, Run) with `ui.print_message()`.
- Replace error messages for missing installations and parameter errors with `ui.render_error()`.
- Ensure `UIManager` is initialized before these messages are shown.

#### `llama_updater.py`
- Replace `print()` calls for checksum verification status, progress updates, and installation status with `ui.print_message()` or `ui.render_error()`.
- Ensure `ui_manager` is passed to `install_release` and other relevant functions to maintain the curses session.
- Migrate all "cancelled" messages to `ui.render_error()`.

#### `runner.py`
- Replace `print()` calls for start/stop status messages with `ui.print_message()`.
- Replace "No running llama-server found" and "Process did not exit cleanly" with `ui.render_error()`.
- Integrate `ui_manager` into the `Runner` class to handle these messages.

### 2. Configuration & State
- Verify `config.json` auto-generation logic in `wrapper_config.py` works correctly on first run.
- Ensure all platform-specific detection is correctly utilized in the `llama_updater.py` release selection flow.

### 3. Refinement
- Ensure all required modules are correctly imported and available in the `llama_wrapper` namespace.
- Verify that the `llama_updater` sanity check output is rendered through `UIManager`.
