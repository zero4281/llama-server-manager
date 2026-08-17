**Version 1.2.0**

### Revision Jump Context
- 1.1.4 -> 1.1.5 (complete): Resolved `verify_installation` deferral and `__version__` update to 1.1.5.
- 1.1.5 -> 1.2.0 (active): Current planning cycle.

### Section 1: Current State Assessment
| Component | Status | Drift / Note |
|------------|--------|--------------|
| Versioning | Partial | `main.py` still at 1.1.5 |
| Update Logic | Drift | `is_fast_path` uses hardcoded logic |
| HF Management | Missing | No dedicated manager for HF Hub |
| Configuration | Drift | `config.json` missing HF options |
| Persistence | Missing | HF options not persisted in `config.py` |
| UI / Headless | Pending | Verification of 1.1.5 specs required |

**Drift Breakdown:**
- `llama_updater.py`: Logic for `is_fast_path` is not aligned with configuration-driven architecture.
- `model_manager.py`: Lack of abstraction for HuggingFace Hub interactions.
- `config.py`: Missing persistence layer for new HF-specific configuration parameters.

### Section 2: Core Engineering Decisions or Filename Consistency
- **HF Hub Management:** Implement `model_manager.py` to centralize interaction with `huggingface_hub`.
- **Config-Driven Logic:** Refactor `llama_updater.py` to retrieve `is_fast_path` from the configuration dictionary rather than local state.
- **Persistence:** Ensure all new HF options in `config.json` are persisted via `config.py`.

### Section 3: Testing & Verification Status
**Unit Tests**
- [ ] `model_manager.py` - Verify HF Hub connectivity and model metadata retrieval.
- [ ] `config.py` - Test persistence of HF options to/from `config.json`.
- [ ] `llama_updater.py` - Verify `is_fast_path` correctly reads from config.

**Integration Tests**
- [ ] Verify `main.py` correctly initializes with `1.2.0` versioning.
- [ ] End-to-end check of model download/update flow using `model_manager.py`.

**Manual Checklists**
- [ ] Verify `print_message` and headless fallbacks meet 1.1.5 specifications in a headless environment.
- [ ] Confirm `requirements.txt` includes `huggingface_hub`.

### Section 4: Exit Codes
- 0: Success
- 1: Configuration Error
- 2: Network/HF Hub Connectivity Error
- 3: Model Download Failure
- 4: Permission Denied

### Section 5: Security
- Validate HF Hub token handling (ensure no secrets in `config.json`).
- Sanitize paths passed to `model_manager.py`.

### Section 6: Dependencies
- `huggingface_hub`

### Section 7: Non-Functional Requirements
- **Performance:** Fast-path detection should be O(1) via config lookup.
- **Portability:** Headless fallbacks must work across different terminal environments.
- **Maintainability:** `model_manager.py` should be the sole entry point for HF interactions.
