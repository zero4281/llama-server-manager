# Update.md — Gap Assessment

## Summary

This assessment aligns the codebase to the `1.1.4` specification. The revision delta processed was `1.1.3` → `1.1.4` (single revision, no intermediate jumps). Update.md was NOT stale — it did not contain the placeholder text "Update.md is stale — re-run /sdlc-update", so it was reviewed but replaced with fresh findings.

## Implemented but Non-Required — Features to Remove

No features to prune were identified. All existing features are required by the specification.

## Compliance Table

| # | Specification | File | Line(s) | Status |
|---|--------------|------|---------|--------|
| 1 | `__version__` must be `"1.1.4"` | `main.py` | 11 | NON-COMPLIANT — currently `"1.1.3"` |
| 2 | `--version` checked immediately after argument parsing | `main.py` | 231–234, 237 | NON-COMPLIANT — checked after `load_config()` and `LoggerSetup` |
| 3 | `--self-update` checked before `load_config()` and `LoggerSetup` | `main.py` | 248 | NON-COMPLIANT — checked after `load_config()` and `LoggerSetup` |
| 4 | `--version` output must include `llama-server-manager version` prefix (§5.2.1) | `main.py` | — | NON-COMPLIANT — passes `__version__` directly to `print_message`, missing prefix |
| 5 | `print_message` must never use `print()` builtin in headless fallback | `ui_manager.py` | 374 | NON-COMPLIANT — uses `print(text)` in headless fallback |
| 6 | `--update-llama` fast path: `verify_installation` after download/extraction; `is_fast_path` from outer `load_config()` | `llama_updater.py` | 1068, 1230 | NON-COMPLIANT — `verify_installation` called before download/extraction; `is_fast_path` computed from fresh `load_config()` inside `_install_release_core` |

## Immediate Next Steps

1. Update `__version__` from `"1.1.3"` to `"1.1.4"` in `main.py:11`.
2. Move `--version` check to immediately after argument parsing, before `load_config()` and `LoggerSetup` in `main.py`.
3. Move `--self-update` check to before `load_config()` and `LoggerSetup` in `main.py`.
4. Fix `--version` output format to include the `llama-server-manager version` prefix per §5.2.1.
5. Replace the `print(text)` headless fallback in `ui_manager.py:374` with an alternative that does not use the `print()` builtin.
6. Fix `--update-llama` fast path: move `verify_installation` to after download/extraction in `llama_updater.py:1230`; compute `is_fast_path` from the outer `load_config()` call instead of a fresh one inside `_install_release_core` at line 1068.
