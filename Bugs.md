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

## 📋 Project Roadmap / Status Summary

| Section                     | Status                                                                                                                                                                                                                                                                                                                                      |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Bug Reports**             | 0 open                                                                                                                                                                                                                                                                                                                                      |
| **Documentation Status**    | Out of sync: `Testing Strategy.md`, `Requirements.md` reference removed/unused features                                                                                                                                                                                                                      |
| **Install Workflow (§7.3)** | 0 open bugs. Previously closed bugs (backend-less `Type`/`bin` leak, missing `cpu` fallback, extraneous "Select Archive" screen) remain fixed. |

**Current Priorities:**

1. **P1** — Fix `llama_updater.py`'s §7.3.0 filename parser to consistently isolate the *present* Backend segment (including versioned backends like `openvino-2026.2.1`, `rocm-7.2`, `cuda-12.4`) so it no longer folds into the OS token on the OS/Architecture screen, and so all real backends surface correctly on the Compute Backend screen.