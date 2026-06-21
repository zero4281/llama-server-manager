# Update Summary
The project requires alignment to ensure all interactive output is rendered through the `UIManager` (curses), streamlining redundant argument parsing in `runner.py`, and replacing brittle path manipulation with standard root execution.

## Implemented but Non-Required: Features to Remove
- **File:** `runner.py` | **Range:** `_merge_args` method | **Rationale:** Redundant with `main.py` argument parsing.
- **File:** `main.py` | **Range:** Section headers (e.g., `[Self-Update Mode]`) | **Rationale:** Should be handled within `UIManager` flow to eliminate `print()` calls.

## Compliance Table
| Requirement | Status | File(s) | Notes |
| --- | --- | --- | --- |
| UI Compliance | Pending | `main.py` | Replace `print()` calls at lines 274, 279, 298, 317, 322. |
| WSL Detection | Compliant | `main.py` | WSL warning at line 256 is permitted. |
| Argument Handling | Partial | `runner.py`, `main.py` | Streamline `_merge_args` logic. |
| Path Handling | Pending | `main.py` | Replace `sys.path.insert` with root execution. |

## Next Steps
1. Move `UIManager` initialization earlier in `main.py`.
2. Replace `print()` calls in `main.py` with `ui.print_message()`.
3. Refactor `runner.py` to remove redundant `_merge_args` method.
4. Update project execution to ensure the project is executed from the root directory.