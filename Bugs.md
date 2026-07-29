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

**Status:** ✅ **COMPLETE** **Priority:** **P1** — Core workflow broken **Description:** The "Select Operating System & Architecture" screen (§7.3.2) should list a de-duplicated set of OS/Architecture pairs only, with the Backend segment ignored at this stage. Observed instead: several entries have the Backend/version segment merged into the OS/Arch label — `Ubuntu-openvino-2026.2.1 x64`, `Ubuntu-rocm-7.2 x64`, `Win-cuda-12.4 x64`, `Win-cuda-13.3 x64`, `Win-openvino-2026.2.1 x64` — inflating a 7-pair list into 12 rows, plus a stray trailing line, `1 asset`, with no basis in §7.3.2. **Reproduction Steps:**

1. Run `llama-server-manager --install-llama` and select a release with openvino/rocm/cuda variant assets.
2. Observe the second menu, "Select Operating System & Architecture."
3. **Actual Result:** 12 rows shown, including hybrid entries `Ubuntu-openvino-2026.2.1 x64`, `Ubuntu-rocm-7.2 x64`, `Win-cuda-12.4 x64`, `Win-cuda-13.3 x64`, `Win-openvino-2026.2.1 x64` alongside the correct plain pairs, plus a stray `1 asset` footer line.
4. Select `Ubuntu x64`, then observe the third menu, "Select Compute Backend."
5. **Actual Result (downstream):** Only `cpu`, `sycl-fp16`, `sycl-fp32`, `vulkan` are offered — `openvino` and `rocm` are missing for `ubuntu / x64`, because those assets were already consumed as pseudo-OS/Arch entries one screen earlier.
6. **Expected Result:** A de-duplicated list of OS/Architecture pairs only (e.g. `Android arm64`, `Macos arm64`, `Macos x64`, `Ubuntu arm64`, `Ubuntu x64`, `Win arm64`, `Win x64` — 7 rows), no hybrid Backend-in-label entries, no asset-count footer; the Compute Backend screen for `ubuntu / x64` should then correctly list `cpu`, `openvino`, `rocm`, `sycl-fp16`, `sycl-fp32`, `vulkan`. **Analysis:** The §7.3.0 filename parser is failing to split off the Backend segment (and its version suffix, e.g. `openvino-2026.2.1`, `rocm-7.2`, `cuda-12.4`) for assets where Backend is present, instead folding it into the OS token. This looks like the same class of parsing defect as the previously closed backend-less/`Type`-leak bug, but on the opposite case: here the Backend segment *is* present and isn't being separated out, rather than being absent and misread as `bin`. Fixing the §7.3.0 parser to consistently isolate the Backend segment (present or absent) should resolve both the OS/Architecture inflation and the downstream missing-backend symptom in one change. **Affected Components:**
- `llama_updater.py` (`parse_asset_name`, §7.3.0)
- `ui_manager.py` (rendering) **Dependencies:**
- `llama_updater.py`
- GitHub Releases API asset list (§7.2) **Test Coverage:**
- None currently; needs a regression test covering assets with a present Backend segment (including versioned backends like `openvino-2026.2.1`, `rocm-7.2`, `cuda-12.4`), asserting they collapse to the correct OS/Architecture pair and surface their backend later in §7.3.3. **Verification:**
- Confirmed via manual walkthrough — 12-row OS/Architecture menu with hybrid entries and stray `1 asset` line; downstream Compute Backend menu for `ubuntu / x64` missing `openvino` and `rocm`.

**Resolution:** Fixed the §7.3.0 filename parser in `llama_updater.py` to consistently isolate the Backend segment (including version suffixes). This prevents the Backend segment from being folded into the OS token during the OS/Architecture selection phase and ensures that all backends are correctly identified and surfaced in the subsequent Compute Backend screen.


---

### ✅ COMPLETE: OS/Architecture selection menu fails to highlight current platform as default

**Status:** ✅ COMPLETE
**Title:** OS/Architecture selection menu fails to highlight current platform as default
**Severity:** Medium
**Description:** 
When running `./llama-server-manager --install-llama`, the "Select Operating System & Architecture" menu fails to automatically highlight the current platform/architecture as the recommended option. The user is required to manually select the correct entry. This violates Requirements.md §7.3.2, which specifies that the current platform/architecture should be highlighted as the recommended option and act as the default if the user presses Enter without a selection.

**Reproduction Steps:**
1. Run `./llama-server-manager --install-llama`.
2. Select a release (e.g., the default option 1).
3. Observe the "Select Operating System & Architecture" menu.
4. Note that no option is highlighted as the default, even if it matches the current system (e.g., on Linux x64, "Ubuntu x64" is not highlighted).

**Affected Components:**
- `llama_updater.py`
- `ui_manager.py`

**Dependencies:**
- `llama_updater.py`
- GitHub Releases API asset list (§7.2)

**Test Coverage:**
- A new regression test should be added to `test_ui_manager_pytest.py` or `test_ui_manager_comprehensive.py` to verify that the correct OS/Architecture pair is highlighted as the default based on the `platform` module's output.

**Verification:**
- Confirmed via manual dynamic testing on Linux x64; "Ubuntu x64" was not highlighted as the default in the OS/Architecture selection menu.

**Resolution:** Updated `detect_platform` in `llama_updater.py` to detect specific Linux distributions using `platform.freedesktop_os_release()` and return "Darwin" for Darwin-based systems, ensuring correct platform highlighting in the installation menu.
---

## 📋 Project Roadmap / Status Summary

| Section                     | Status                                                                                                                                                                                                                                                                                                                                      |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Bug Reports** | 2 open |
| **Documentation Status**    | Out of sync: `Testing Strategy.md`, `Requirements.md` reference removed/unused features                                                                                                                                                                                                                      |
| **Install Workflow (§7.3)** | 2 open bugs. Previously closed bugs (backend-less `Type`/`bin` leak, missing `cpu` fallback, extraneous "Select Archive" screen) remain fixed. |

**Current Priorities:**

1. **P1** — Fix `llama_updater.py`'s §7.3.0 filename parser to consistently isolate the *present* Backend segment (including versioned backends like `openvino-2026.2.1`, `rocm-7.2`, `cuda-12.4`) so it no longer folds into the OS token on the OS/Architecture screen, and so all real backends surface correctly on the Compute Backend screen.