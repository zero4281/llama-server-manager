## Current Bug Reports

**Title:** Missing Vulkan option in compute backend menu
**Status:** **COMPLETED**
**Severity/Priority:** **Medium**
**Dependencies:** `llama_updater.py`, `ui_manager.py`
**Description:**
When running `./llama-server-manager --install-llama`, the "Select Compute Backend" menu is missing the "Vulkan" option. Other menus (Release, OS/Arch, Confirmation) appear correctly. The installation succeeds but the user is unable to select Vulkan as a compute backend.

**Resolution:**
Updated the regex in `llama_updater.py` to correctly capture the backend segment in asset names (e.g., 'vulkan'), ensuring it appears in the Compute Backend selection menu.

**Verified Reproduction Workflow:**
1. Run `./llama-server-manager --install-llama`.
2. Press Enter to select the default release.
3. Press Enter to select the default Operating System & Architecture (Ubuntu x64).
4. Observe that the "Select Compute Backend" menu lists `cpu`, `openvino-2026.2.1`, `rocm-7.2`, `sycl-fp16`, and `sycl-fp32`, but lacks `vulkan`.

**Test Suitability:**
A new automated test case should be added to `Tests/test_ui_manager_pytest.py` to verify that `llama_updater.py` correctly parses the backend segment from the release assets and includes "vulkan" in the selection menu when available for the selected OS/Architecture.

## Project Roadmap
- [x] Fix missing Vulkan option in compute backend menu
