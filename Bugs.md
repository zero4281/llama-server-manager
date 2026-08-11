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

**Title:** Inconsistent platform naming leads to missing compute backends for Ubuntu x64
**Status:** **COMPLETED**
**Severity/Priority:** **Medium**
**Dependencies:** None
**Description:**
The `parse_asset_name` function in `llama_updater.py` handles assets with and without backend segments inconsistently. For assets without a backend segment (e.g., `llama-b10357-bin-ubuntu-x64.tar.gz`), it capitalizes the platform name (e.g., `Ubuntu`). For assets with a backend segment (e.g., `llama-b10357-bin-ubuntu-vulkan-x64.tar.gz`), it does not capitalize it (e.g., `ubuntu`). 

This results in two distinct platform keys in `get_available_platforms`: `("Ubuntu", "x64")` and `("ubuntu", "x64")`. The `Ubuntu x64` entry only contains the `cpu` asset, while the `ubuntu x64` entry contains all backends. Consequently, when a user selects `Ubuntu x64`, the "Select Compute Backend" menu only lists `cpu`.

**Resolution:**
Normalized platform name parsing in `llama_updater.py` to ensure consistent case handling, correctly mapping all available backends to the Ubuntu x64 platform.

**Verified Reproduction Workflow:**
1. Run `./llama-server-manager --install-llama`.
2. Select the default release.
3. Select the `Ubuntu x64` platform.
4. Observe that the "Select Compute Backend" menu only lists `cpu`.
5. Verify that other backends (e.g., `vulkan`, `openvino-2026.2.1`, `rocm-7.14`, `sycl-fp16`, `sycl-fp32`) are missing from the menu despite being present in the release assets.

**Test Suitability:**
Add a test case to `Tests/test_ui_manager_pytest.py` to verify that for the `Ubuntu x64` platform, all available backends from the release assets (including `cpu`, `vulkan`, etc.) are correctly populated in the `backend_options` list.

## Project Roadmap
- [x] Fix missing Vulkan option in compute backend menu
- [x] Fix inconsistent platform naming for Ubuntu x64
