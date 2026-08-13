# Plan: Llama Server Manager

**Version 1.1.4**

Revision Jump Context: 1.1.3 → 1.1.4 (one revision). Intermediate versions processed: none (no intermediate revisions were jumped).

## 1.1.3 Changes

- §7.3.0 asset-filename matching rule clarified: exclusion from selection menus now requires **both** correct segment shape AND a literal `bin` value in the Type position (not segment shape alone). Worked examples added (`llama-b10297-xcframework.zip`, `cudart-llama-bin-win-cuda-12.4-x64.zip`).

## 1.1.4 Changes

- New §10.6.1 (curses-init fallback): `UIManager` now catches `curses.initscr()` failures at construction and enters a "headless" state instead of raising.
- New §10.8 (`print_message`): standalone messages (success/warning/error, not bordered menus) must use `print_message` with plain text rendering. In headless state, `print_message` writes directly to `sys.stdout`/`sys.stderr` (never `print()` builtin).
- Updated §5.2.1: `--version` must instantiate `UIManager` and call `print_message(level="info")` with the `__version__` constant. `--version` does not require `config.json` to be loaded, the logger to be configured, or `./llama-cpp` to exist; it is handled **immediately after argument parsing**.
- Updated §5.1: `main.py` itself must not call `print()` or write to stdout/stderr directly; `print_message`'s internal fallback is the sanctioned path.

---

# Section 1: Current State Assessment

## Verification Table

| File               | Finding                                                                                                                                         | Status               |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------- | -------------------- |
| `main.py`          | `__version__` is 1.1.3, should be 1.1.4                                                                                                        | **Violation**        |
| `main.py`          | `--version` uses `UIManager` and `print_message(level="info")` — correct approach, but ordering is wrong                                      | **Violation (ordering)** |
| `main.py`          | `--version` exits with status code 0 after printing                                                                                             | Correct              |
| `main.py`          | `--version` output format matches spec (`llama-server-manager version X.Y.Z`)                                                                   | Correct              |
| `main.py`          | `--version` is checked **after** `LoggerSetup` and `load_config()` are called, violating §5.2.1                                                 | **Violation**        |
| `main.py`          | `--self-update` instantiates `UIManager` inside `perform_self_update`, after `LoggerSetup` and `load_config()`                                  | **Violation**        |
| `ui_manager.py`    | `print_message` calls `print(text)` in headless fallback, violating §10.8                                                                       | **Violation**        |
| `llama_updater.py` | `--update-llama` fast path: `verify_installation` is called **before** download/extraction in the update method                                   | **Violation**        |
| `llama_updater.py` | `--update-llama` fast path: `is_verified` is set to `True` before installation occurs, should reflect actual sanity check result              | **Violation**        |
| `llama_updater.py` | `--update-llama` fast path: `sys.exit(1)` used in except block — works but inconsistent with other error handling patterns                      | Minor concern        |
| `llama_updater.py` | `runner.py` `_merge_args` is a no-op — correct per §5.2/§9.2                                                                                  | Correct              |
| `llama_updater.py` | `_install_release_core` checks `is_fast_path` from a fresh `load_config()` call inside the function, not from the caller's config              | Minor concern        |

## Structural/Functional Drift Breakdown

- Version string is inconsistent with Requirements.md target version 1.1.4.
- `--version` and `--self-update` ordering violates §5.4 startup sequence — `LoggerSetup` and `load_config()` are called before these special flags are checked.
- `print_message` headless fallback uses `print()` builtin instead of `sys.stdout`/`sys.stderr` write — violates §10.8.
- `--update-llama` fast path: `verify_installation` is called before download/extraction; `is_verified` parameter is `True` before installation occurs — should reflect actual sanity check result after extraction.
- `--update-llama` fast path config save: `is_fast_path` variable in `_install_release_core` is computed from a fresh `load_config()` call inside the function, not from the caller's config dict — could produce incorrect results if the caller's config has been modified.

# Section 2: Core Engineering Decisions or Filename Consistency

- **Version alignment:** Update `__version__` in `main.py` from `"1.1.3"` to `"1.1.4"` to match Requirements.md §1.1.4.
- **`--version` ordering:** Move `--version` check to immediately after argument parsing (step 2 in §5.4), before `LoggerSetup` and `load_config()`. The `--version` path must instantiate `UIManager` and call `print_message(level="info")` with the `__version__` constant, then exit with status code 0.
- **`--self-update` ordering:** Move `--self-update` check to after `--version` check but before `LoggerSetup` and `load_config()`. The `--self-update` path must instantiate `UIManager` immediately after argument parsing.
- **`print_message` headless fallback:** Replace `print(text)` in `ui_manager.py` with `sys.stdout.write(text + '\n')` or `sys.stderr.write(text + '\n')` depending on the message level — never use the `print()` builtin.
- **`--update-llama` fast path:** In `llama_updater.py`, defer `verify_installation` call to after download/extraction in `_install_release_core`. The `is_verified` parameter passed to `_restart_llama_server` must reflect the actual sanity check result from post-extraction verification, not a pre-installation boolean.
- **`--update-llama` fast path config:** Pass the caller's config dict to `_install_release_core` and compute `is_fast_path` from that dict, not from a fresh `load_config()` call inside the function.
- **No action needed on `runner.py`'s `_merge_args`** — it is correctly a no-op with respect to CLI pass-through; `llama-server` launch arguments are derived solely from `config.json` (Req 5.2, 9.2).

# Section 3: Testing & Verification Status

## Unit Test Checklist

- [ ] Test `--version` flag output format: `llama-server-manager version 1.1.4`
- [ ] Test `--version` exits with status code 0
- [ ] Test `--version` works without `config.json` loaded
- [ ] Test `--version` works without logger configured
- [ ] Test `--version` works without `./llama-cpp` directory
- [ ] Test `--version` works in headless state (no curses)
- [ ] Test `print_message` in headless state writes to `sys.stdout`/`sys.stderr` (never `print()`)
- [ ] Test `--self-update` ordering: `UIManager` instantiated before `LoggerSetup`
- [ ] Test `--update-llama` fast path: `verify_installation` called after download/extraction
- [ ] Test `--update-llama` fast path: `is_verified` reflects actual sanity check result
- [ ] Test `--update-llama` fast path: no config save during fast path update
- [ ] Test `LlamaUpdater` fast-path matching logic

## Integration Test Checklist

- [ ] Verify `--version` startup sequence: arg parsing → UIManager → print_message → exit(0)
- [ ] Verify `--version` does not trigger `LoggerSetup` or `load_config()`
- [ ] Verify `--self-update` startup sequence: arg parsing → UIManager → UI flow → exit
- [ ] Verify `--self-update` does not trigger `LoggerSetup` or `load_config()` before UIManager instantiation
- [ ] Verify `--update-llama` fast path: download → extract → verify_installation → restart (if verified)
- [ ] Verify `--update-llama` fast path config persistence: `options.llama-cpp` keys not re-saved
- [ ] Verify `--update-llama` fallback path (missing options): full interactive workflow

## Manual Check Checklist

- [ ] Run `python main.py --version` and verify output format and exit code
- [ ] Run `python main.py --version` in non-interactive environment (piped, no TTY)
- [ ] Run `python main.py --self-update` and verify `UIManager` is available for source selection
- [ ] Run `python main.py --update-llama` with both `os-architecture` and `backend` present (fast path)
- [ ] Run `python main.py --update-llama` with either key missing (fallback path)
- [ ] Verify no `print()` calls in `main.py` or `ui_manager.py` headless fallback

# Section 4: Exit Codes

- Define standard exit codes for: `--version` (0), checksum/download verification failure (non-zero), GitHub API unreachable or rate-limited (non-zero), and forced (`SIGKILL`) termination during shutdown (non-zero per §9.5).
- `--version` must exit with status code `0` after printing.
- `--self-update` must exit with status code `0` on success, non-zero on failure.
- `--update-llama` fast path must exit with non-zero status if no matching asset found after download/extraction.

# Section 5: Security

- Ensure `llama-cpp` paths are sanitized.
- Validate asset matching logic (already correct per §7.3.0).
- Verify checksum after download before extraction.
- Ensure `print_message` headless fallback never uses `print()` builtin — must use `sys.stdout`/`sys.stderr` write to avoid potential injection issues.

# Section 6: Dependencies

- `llama-cpp`: resolved dynamically at runtime via GitHub release tags (e.g. `b8800`); not pinned to a fixed version in this document (Req 8.2, 8.3.1, 8.7).
- `requirements.txt` updates (no changes required for 1.1.4).

# Section 7: Non-Functional Requirements

- Startup time < 2s.
- Clear error messaging.
- `--version` and `--self-update` must not block on `LoggerSetup` or `load_config()` — these are handled immediately after argument parsing.
- `print_message` in headless state must write directly to `sys.stdout`/`sys.stderr` without using `print()` builtin.
