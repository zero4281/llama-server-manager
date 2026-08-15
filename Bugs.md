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
 
**Title:** `--install-llama` ignores menu selection and incorrectly defaults to second-latest release
**Status:** **Pending**
**Severity/Priority:** **Medium**
**Dependencies:** `llama_updater.py`, `ui_manager.py`
**Description:**
When running `./llama-server-manager --install-llama`, the "Select a Release" menu displays the second-latest release (e.g., `b10356`) as the default selection. This is because the latest release (e.g., `b10357`) is correctly fetched but then excluded from the "recent releases" list to prevent duplicates.
 
Furthermore, the program ignores the user's selection from this menu. Even if the user selects a different release from the list, the program proceeds to install the latest release because `install_release` is called with the initial "latest" release object rather than the one corresponding to the user's menu choice.
 
**Verified Reproduction Workflow:**
1. Run `./llama-server-manager --install-llama`.
2. Observe the "Select a Release" menu. The default option is the second-latest release (e.g., `b10356`).
3. Press Enter to confirm the default.
4. Observe that the program proceeds to download and install the latest release (e.g., `b10357`) instead of the selected `b10356`.
5. (Optional) Navigate the menu to select a different release (e.g., `b10355`) and press Enter; observe that the program still installs the latest release (`b10357`).
 
**Test Suitability:**
Update the tests in `Tests/test_ui_manager_pytest.py` (or a relevant integration test) to ensure that the `release` object passed to `install_release` matches the selection made in the `render_menu` call.



**Title:** "latest" text appears as a separate line in "Select a Release" menu
**Status:** **COMPLETED**
**Severity/Priority:** **Low**
**Dependencies:** `llama_updater.py`, `ui_manager.py`
**Description:**
When running `./llama-server-manager --install-llama`, the "Select a Release" menu lists the default release but includes a "latest" line on the second line. This happens because the `description` field for the default release is set to "latest", and `ui_manager.py` renders descriptions on a new line. This is out of spec for the menu.

**Resolution:**
Modified `llama_updater.py` to ensure the "latest" string is not included in the description of the default release option when rendering the selection menu, preventing it from appearing as a separate line.

**Verified Reproduction Workflow:**
1. Run `./llama-server-manager --install-llama`.
2. Observe the "Select a Release" menu.
3. Notice the "latest" line between the first and second options.

**Test Suitability:**
Add a test case to `Tests/test_ui_manager_pytest.py` to verify that the default release option in the tag selection menu does not have a description that triggers an extra line in the rendered menu.

**Title:** `stop_server` incorrectly returns success when process is still alive
**Status:** **COMPLETED**
**Dependencies:** `runner.py`
**Description:**
The `stop_server` method in `runner.py` has a logic error in its process exit verification loop. It calls `os.kill(pid, 0)` to check if the process is alive. If the call succeeds (meaning the process is still running), the code proceeds to `return 0` (line 166), incorrectly signaling a successful shutdown. This causes the method to exit early without removing the PID file or proceeding to the force-kill logic.
 
**Resolution:**
Modified the stop_server method in runner.py to correctly wait for the process to exit before returning success, and ensured the PID_FILE is unlinked upon clean shutdown. Also added a unit test to verify the fix.
 
**Verified Reproduction Workflow:**
1. Start `llama-server` and ensure a PID file is created.
2. Run `./llama-server-manager --stop-server`.
3. Observe that the command returns 0 almost immediately, but the `llama-server` process is still running and the PID file remains in the directory.
 
**Test Suitability:**
Add a unit test for `Runner.stop_server` in `Tests/test_runner_pytest.py` that mocks `os.kill` and the PID file to verify that it correctly waits for the process to exit and unlinks the file.

## Project Roadmap
- [ ] Fix `--install-llama` menu selection and default release bug
- [x] Fix "latest" text appearing as a separate line in "Select a Release" menu
- [ ] Fix `--install-llama` menu selection and default release bug


