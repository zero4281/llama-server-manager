# Plan: Llama Server Manager

**Version 1.1.3**

Revision Jump Context (If applicable): None (No intermediate revisions were jumped).

# Section 1: Current State Assessment

## Verification Table

| File               | Finding                                                                                                                                         | Status               |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------- | -------------------- |
| `main.py`          | `__version__` is 1.1.2                                                                                                                          | Outdated             |
| `main.py`          | `--version` uses stdout instead of `UIManager.print_message`                                                                                    | Incomplete           |
| `main.py`          | `llama-cpp` error message includes "Error: " prefix                                                                                             | Minor Drift          |
| `llama_updater.py` | `_install_release_core` saves `config.json` during fast-path                                                                                    | Violation of Req 8.7 |
| `runner.py`        | `_merge_args` is a no-op — Req 5.2/9.2 define no CLI pass-through mechanism for `llama-server`; launch arguments come solely from `config.json` | Correct as-is        |

## Structural/Functional Drift Breakdown

- Versioning information is inconsistent across components.
- UI message routing is partially implemented for new flags.
- Fast-path update logic violates configuration persistence requirements.

# Section 2: Core Engineering Decisions or Filename Consistency

- Align all versioning to 1.1.3.
- Ensure all UI outputs route through `UIManager`.
- Refactor `llama_updater.py` to prevent config writes during fast-path updates.
- No action needed on `runner.py`'s argument handling — `_merge_args` being a no-op with respect to CLI pass-through is correct; `llama-server` launch arguments are derived solely from `config.json` (Req 5.2, 9.2).

# Section 3: Testing & Verification Status

- Unit: Test `--version` flag output and `LlamaUpdater` matching logic.
- Integration: Verify startup sequence and config persistence.
- Manual: Verify UI styling and error messages.

# Section 4: Exit Codes

- Define standard exit codes for: checksum/download verification failure (Req 8.5), GitHub API unreachable or rate-limited (Req 8.6), and forced (`SIGKILL`) termination during shutdown (Req 9.5).

# Section 5: Security

- Ensure `llama-cpp` paths are sanitized.
- Validate asset matching logic.

# Section 6: Dependencies

- `llama-cpp`: resolved dynamically at runtime via GitHub release tags (e.g. `b8800`); not pinned to a fixed version in this document (Req 8.2, 8.3.1, 8.7).
- `requirements.txt` updates.

# Section 7: Non-Functional Requirements

- Startup time < 2s.
- Clear error messaging.
