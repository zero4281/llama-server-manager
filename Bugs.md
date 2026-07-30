## Current Bug Reports

### ✅ COMPLETE: Menu items overlap and concatenate in narrow terminals due to lack of wrapped text handling

**Status:** ✅ **COMPLETE**
**Severity:** Medium
**Description:**
When running `./llama-server-manager --self-update` in a narrow terminal, the source selection menu displays concatenated labels. This occurs because the `render_menu` method in `ui_manager.py` uses a fixed vertical offset for each menu item but does not account for the fact that `curses.addstr` will wrap long strings to subsequent lines. Consequently, a wrapped portion of one item's label overlaps with the label of the next item, resulting in concatenated text (e.g., "Previous releaserelease").

**Reproduction Steps:**
1. Run `./llama-server-manager --self-update` in a narrow terminal (e.g., 40 columns).
2. Observe the "Select update source" menu.
3. Note how items like "Previous release" wrap and concatenate with the following items.

**Affected Components:**
- `ui_manager.py` (`render_menu` and `render_confirmation` methods)

**Dependencies:**
- None

**Test Coverage:**
- No automated tests currently cover terminal wrapping behavior. A new test case should be added to `test_ui_manager_terminal_sizes.py` to verify correct layout and non-overlapping labels in narrow terminals (e.g., 40x20).

**Verification:**
- Confirmed via manual dynamic testing in a 40-column terminal, where "Previous release" and "Repository HEAD" labels were concatenated.

**Resolution:** Fixed by implementing dynamic line count calculation for labels/descriptions, dynamic menu height adjustment, and y-coordinate tracking in the redraw loop.

---

### ✅ COMPLETE: OS/Architecture selection menu leaks the `Backend` segment for multi-backend assets

**Status:** ✅ **COMPLETE** **Priority:** **P1** — Core workflow broken
**Description:**
The "Select Operating System & Architecture" screen (§7.3.2) should list a de-duplicated set of OS/Architecture pairs only, with the Backend segment ignored at this stage. Observed instead: several entries have the Backend/version segment merged into the OS/Arch label — `Ubuntu-openvino-2026.2.1 x64`, `Ubuntu-rocm-7.2 x64`, `Win-cuda-12.4 x64`, `Win-cuda-13.3 x64`, `Win-openvino-2026.2.1 x64` — inflating a 7-pair list into 12 rows, plus a stray trailing line, `1 asset`, with no basis in §7.3.2.

**Reproduction Steps:**
1. Run `llama-server-manager --install-llama` and select a release with openvino/rocm/cuda variant assets.
2. Observe the second menu, "Select Operating System & Architecture."
3. **Actual Result:** 12 rows shown, including hybrid entries `Ubuntu-openvino-2026.2.1 x64`, `Ubuntu-rocm-7.2 x64`, `Win-cuda-12.4 x64`, `Win-cuda-13.3 x64`, `Win-openvino-2026.2.1 x64` alongside the correct plain pairs, plus a stray `1 asset` footer line.
4. Select `Ubuntu x64`, then observe the third menu, "Select Compute Backend."
5. **Actual Result (downstream):** Only `cpu`, `sycl-fp16`, `sycl-fp32`, `vulkan` are offered — `openvino` and `rocm` are missing for `ubuntu / x64`, because those assets were already consumed as pseudo-OS/Arch entries one screen earlier.
6. **Expected Result:** A de-duplicated list of OS/Architecture pairs only (e.g. `Android arm64`, `Macos arm64`, `Macos x64`, `Ubuntu arm64`, `Ubuntu x64`, `Win arm64`, `Win x64` — 7 rows), no hybrid Backend-in-label entries, no asset-count footer; the Compute Backend screen for `ubuntu / x64` should then correctly list `cpu`, `openvino`, `rocm`, `sycl-fp16`, `sycl-fp32`, `vulkan`.

**Analysis:**
The §7.3.0 filename parser is failing to split off the Backend segment (and its version suffix, e.g. `openvino-2026.2.1`, `rocm-7.2`, `cuda-12.4`) for assets where Backend is present, instead folding it into the OS token. This looks like the same class of parsing defect as the previously closed backend-less/`Type`-leak bug, but on the opposite case: here the Backend segment *is* present and isn't being separated out, rather than being absent and misread as `bin`. Fixing the §7.3.0 parser to consistently isolate the Backend segment (present or absent) should resolve both the OS/Architecture inflation and the downstream missing-backend symptom in one change.

**Affected Components:**
- `llama_updater.py` (`parse_asset_name`, §7.3.0)
- `ui_manager.py` (rendering)

**Dependencies:**
- `llama_updater.py`
- GitHub Releases API asset list (§7.2)

**Test Coverage:**
- None currently; needs a regression test covering assets with a present Backend segment (including versioned backends like `openvino-2026.2.1`, `rocm-7.2`, `cuda-12.4`), asserting they collapse to the correct OS/Architecture pair and surface their backend later in §7.3.3.

**Verification:**
- Confirmed via manual walkthrough — 12-row OS/Architecture menu with hybrid entries and stray `1 asset` line; downstream Compute Backend menu for `ubuntu / x64` missing `openvino` and `rocm`.

**Resolution:**
Fixed the §7.3.0 filename parser in `llama_updater.py` to consistently isolate the Backend segment (including version suffixes). This prevents the Backend segment from being folded into the OS token during the OS/Architecture selection phase and ensures that all backends are correctly identified and surfaced in the subsequent Compute Backend screen.

---

### ✅ COMPLETE: OS/Architecture selection menu displays redundant asset counts in descriptions

**Status:** ✅ **COMPLETE**
**Severity:** Medium

**Description:**
When running `./llama-server-manager --install-llama`, the "Select Operating System & Architecture" menu (the second menu in the installation flow) displays a second line for each option that lists the number of assets (e.g., "6 assets" for "Ubuntu x64"). 

Requirements.md §7.3.2 specifies that this menu should list the de-duplicated OS/Architecture pairs. While the UI supports a description field (used for variant information), the current implementation in `llama_updater.py` automatically populates this field with the asset count. The asset count is redundant and should be removed from the description, while maintaining the ability to display variant information (e.g., "(variant: vulkan)") if present.

**Reproduction Steps:**
1. Run `./llama-server-manager --install-llama`.
2. Select the first release option (latest).
3. Observe the "Select Operating System & Architecture" menu.
4. Note that each option is followed by a second line showing the number of assets (e.g., "6 assets").
5. Verify that this count is being injected into the `description` field of the `platform_options` list in `llama_updater.py`.

**Affected Components:**
- `llama_updater.py` (`install_release` function)

**Dependencies:**
- None

**Test Coverage:**
- A new regression test should be added to `test_ui_manager_pytest.py` to verify that the description field for OS/Architecture options does not contain asset counts, but still correctly displays variant information.

**Verification:**
- Confirmed via manual dynamic testing: The OS/Architecture menu displays "X asset(s)" for every entry, which is not requested in the requirements.

**Resolution:** Updated `llama_updater.py` to remove asset counts from the `description` field of OS/Architecture options while preserving variant information, ensuring compliance with §7.3.2.

---

### ✅ COMPLETE: Duplicate "(default)" marker in "Select Compute Backend" menu

**Status:** ✅ **COMPLETE**
**Severity:** Medium
**Description:**
When running `./llama-server-manager --install-llama`, the "Select Compute Backend" menu (the third menu in the installation flow) displays the "(default)" marker twice for the first option. The first occurrence is appended to the option's label (e.g., "0. cpu (default)"), and the second occurrence is rendered on a new line as the option's description.

**Reproduction Steps:**
1. Run `./llama-server-manager --install-llama`.
2. Select the first release option (latest).
3. Select a platform that results in a single compute backend (e.g., Ubuntu x64).
4. Observe the "Select Compute Backend" menu.

**Affected Components:**
- `ui_manager.py`
- `llama_updater.py`

**Dependencies:**
- None

**Test Coverage:**
- A new test case should be added to `test_ui_manager_pytest.py` or `test_ui_manager_comprehensive.py` to verify that the `(default)` marker is only rendered once for the default option in the Compute Backend menu.

**Verification:**
- Confirmed via manual dynamic testing: "0. cpu (default)" was rendered followed by a second line with "(default)".

**Resolution:**
Modified `ui_manager.py` to ensure that the `(default)` marker is only appended to the label if it is not already present in the label string. This prevents the marker from being duplicated when it is already part of the option's label.

---

### ✅ COMPLETE: Program crashes if config.json is missing on startup

**Status:** ✅ **COMPLETE** **Priority:** **P1** — Core workflow broken
**Description:**
When running `./llama-server-manager` with any option (e.g., `--install-llama`), the program crashes with a `FileNotFoundError` if `config.json` is missing from the project directory.

Requirements.md §3 and §5.4 specify that `config.json` must be auto-generated if it does not exist when `main.py` is launched. The current implementation fails to do this, leading to a crash in `logger.py` when it attempts to open the missing file during the initialization sequence.

**Reproduction Steps:**
1. Delete the `config.json` file from the project directory.
2. Run `./llama-server-manager --install-llama`.
3. Observe the program crashing with a `FileNotFoundError: [Errno 2] No such file or directory: '.../config.json'`.

**Affected Components:**
- `main.py` (startup sequence)
- `logger.py` (initialization)

**Dependencies:**
- `main.py`
- `logger.py`

**Test Coverage:**
A new integration test should be added to verify that `main.py` correctly auto-generates a default `config.json` if it is missing from the working directory, ensuring the program continues to start successfully without crashing.

**Verification:**
Confirmed via manual dynamic testing in a sandbox environment: deleting `config.json` and running the manager resulted in a `FileNotFoundError` in `logger.py` during the `LoggerSetup().setup()` call.
**Resolution:** Modified `config.py` to auto-generate `config.json` if missing, refactored `logger.py` to accept config dictionary, and updated `main.py` startup sequence.

---

### 📋 Project Roadmap / Status Summary

| Section                     | Status                                                                                                                                                                                                                                                                                                                                      |
| --------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Bug Reports** | 1 open |
| **Documentation Status**    | Out of sync: `Testing Strategy.md`, `Requirements.md` reference removed/unused features                                                                                                                                                                                                                      |
| **Install Workflow (§7.3)** | 3 open bugs. Previously closed bugs (backend-less `Type`/`bin` leak, missing `cpu` fallback, extraneous "Select Archive" screen) remain fixed. |

**Current Priorities:**

1. **P1** — Fix `llama_updater.py`'s §7.3.0 filename parser to consistently isolate the *present* Backend segment (including versioned backends like `openvino-2026.2.1`, `rocm-7.2`, `cuda-12.4`) so it no longer folds into the OS token on the OS/Architecture screen, and so all real backends surface correctly on the Compute Backend screen.
2. **P1** — Ensure `config.json` is auto-generated on startup if missing, as per Requirements.md §3 and §5.4.

---
