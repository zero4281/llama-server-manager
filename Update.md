# Update Assessment

## Summary
Target alignment: Version `1.1.3`. This update involves a multi-revision jump, skipping `1.1.1` deltas to reach `1.1.3`.

## Implemented but Non-Required: Features to Remove
- **`main.py`** (Lines 298-300): Remove the "Error: " prefix from the `llama-cpp` not-found message.
  - **Rationale**: Violation of Plan Sec 1.
- **`llama_updater.py`** (Line 1229): Prevent `config.json` modification during fast-path updates.
  - **Rationale**: Satisfy the "read-only" constraint for saved selections (§8.7).

## Compliance Table
| Component | Requirement / Plan | Current Status | Action |
| :--- | :--- | :--- | :--- |
| `main.py` | Versioning (§5.1) | Version is `1.1.2` | Update `__version__` to `1.1.3`. |
| `main.py` | `--version` Output (§5.2.1) | Prints to stdout | Redirect output to `ui.print_message` and ensure exit code `0`. |
| `llama_updater.py` | Fast-Path Save (§8.7) | `_install_release_core` saves `config.json` | Modify `_install_release_core` to skip `save_config` when called via the fast-path (line 1229). |
| `main.py` | Startup Sequence (§5.4) | Partially aligned | Ensure `LoggerSetup` is called strictly before `UIManager` or `LlamaUpdater`. |

## Next Steps
1. Update `__version__` in `main.py` to `1.1.3`.
2. Refactor `--version` output in `main.py` to use `ui.print_message`.
3. Modify `llama_updater.py` to skip `save_config` on fast-path.
4. Reorder startup sequence in `main.py`.
5. Remove "Error: " prefix from `llama-cpp` message in `main.py`.
