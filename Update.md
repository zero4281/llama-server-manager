# Update Assessment

## Summary
The codebase requires alignment with Requirements.md and Plan.md. Key focus areas include implementing versioning, adjusting the startup sequence in `main.py`, adding restart logic to `llama_updater.py`, and removing non-compliant CLI arguments and self-restart mechanisms.

## Implemented but Non-Required: Features to Remove
- **`main.py`**: Remove `llama_args` argument from `argparse`.
  - **Rationale**: Violation of Req 9.2. `Runner` must derive all `llama-server` launch arguments solely from `config.json`.
- **`main.py`**: Remove `os.execv` call at the end of `perform_self_update`.
  - **Rationale**: Violation of Req 5.3.3. `main.py` must exit with status code 0 after a successful update instead of relaunching itself.

## Compliance Table
| Requirement / Plan Section | Status | Notes |
| :--- | :--- | :--- |
| Requirements.md Core | Partially Met | Missing versioning and restart logic |
| Plan Section 1 | Partially Met | |
| Plan Section 2 | Partially Met | |
| Plan Section 4 | Partially Met | |
| Plan Section 5 | Partially Met | Needs startup sequence alignment |
| Plan Section 6 | Partially Met | |
| Plan Section 7 | Partially Met | |

## Next Steps
1. Add `__version__` constant to `main.py` (Section 5.1).
2. Implement `--version` flag in `main.py` using `UIManager.print_message` and exit code 0 (Section 5.2.1).
3. Align `main.py` startup sequence with Section 5.4.
4. Implement restart logic in `llama_updater.py` (Section 8.5.1) to check `llama-server.pid`, stop the process, and restart if sanity check passes.
5. Remove `llama_args` from `main.py` argparse (Req 9.2).
6. Remove `os.execv` from `main.py` `perform_self_update` (Req 5.3.3).
