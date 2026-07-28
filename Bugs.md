## Current Bug Reports

### ✅ RESOLVED: test_styling fails in test_ui_manager_comprehensive.py
**Status:** 🔴 **RESOLVED**  
**Priority:** **P3** - Test suite failure  
**Description:**  
Running `pytest Tests/test_ui_manager_comprehensive.py::test_styling` results in a `StopIteration` error.
**Reproduction Steps:**
1. Run: `pytest Tests/test_ui_manager_comprehensive.py::test_styling`
2. **Actual Result:** Test fails with `StopIteration`.
3. **Expected Result:** Test should pass, verifying the styling attributes (A_BOLD and A_REVERSE) are correctly applied to the menu.
**Analysis:**
The failure occurs because `ui_manager.py`'s `render_menu` method enters an input loop that calls `menu_win.getch()`. The test mocks `getch()` with a single-element list `[curses.KEY_RESIZE]`. While the first call returns the key and matches the cancellation check, a subsequent call to `getch()` (triggered by the loop or internal recovery logic) raises `StopIteration` as the mock side-effect list is exhausted.
**Affected Components:**
- `ui_manager.py`
- `Tests/test_ui_manager_comprehensive.py`
**Dependencies:**
- `ui_manager.py`
- `Tests/test_ui_manager_comprehensive.py`
**Test Coverage:**
- `Tests/test_ui_manager_comprehensive.py`
**Verification:**
- ✅ Confirmed failure with `StopIteration` in a clean sandbox environment.

---

### ✅ RESOLVED: timeout parameter removed from render_menu() and render_confirmation()
**Status:** 🟢 **RESOLVED**  
**Priority:** **P2** — Dead code / API hygiene  
**Resolution:** Removed unused `timeout` parameter from both methods, deleted 10 related tests in `test_timeout_pytest.py`, removed 2 test functions from `test_ui_manager_comprehensive.py`, updated `Testing Strategy.md`, `Requirements.md`, and cleared pytest cache. No functional impact — dead code cleanup only.

---

### ✅ COMPLETE: OS/Architecture selection menu displays redundant asset counts in descriptions

**Status:** ✅ **COMPLETE**
**Severity:** Medium

---

### ✅ RESOLVED: Install menu titles hardcoded to a single generic string across all screens
**Status:** 🟢 **RESOLVED**
**Priority:** **P2** — Spec violation / UX
**Description:**
Every screen in the four-screen llama.cpp install workflow (`ui_manager.py`) renders the same hardcoded title, `Select a Tag for llama.cpp`, instead of a title describing the content of that specific screen.
**Reproduction Steps:**
1. Run `llama-server-manager --install-llama`.
2. Step through Release selection, OS/Architecture selection, Compute Backend selection, and Confirmation.
3. **Actual Result:** All screens display the title `Select a Tag for llama.cpp`.
4. **Expected Result:** Per `Requirements.md` §9.3 and §7.3, each screen supplies its own title: `Select a Release` (§7.3.1), `Select Operating System & Architecture` (§7.3.2), `Select Compute Backend` (§7.3.3), and `Confirm Installation` (§7.3.4).
**Analysis:**
`UIManager`'s menu-rendering method appears to be called with a title argument that is either hardcoded or defaulted at the call site, rather than passed per-invocation as required. §9.3 explicitly prohibits reusing a single generic title across different menus.

**Resolution:** Updated `ui_manager.py` to accept dynamic titles from `llama_updater.py` call sites, ensuring each screen displays its unique title as required by §7.3 and §9.3.
**Affected Components:**
- `llama_updater.py` (`install_release` function)

**Dependencies:**
- None

**Test Coverage:**
- A new regression test should be added to `test_ui_manager_pytest.py` to verify that the description field for OS/Architecture options does not contain asset counts, but still correctly displays variant information.

**Verification:**
- Confirmed via manual dynamic testing: The OS/Architecture menu displays "X asset(s)" for every entry, which is not requested in the **Resolution:** Removed redundant asset counts from platform descriptions in `llama_updater.py` to only display variant information (e.g., "(variant: vulkan)"), adhering to §7.3.2 of the requirements.

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
- `llama_updater.py` (call sites for each of the four screens)
**Dependencies:**
- `ui_manager.py`
**Test Coverage:**
- None currently; needs a test asserting the title argument passed to `UIManager` differs per screen.
**Verification:**
- ✅ Confirmed via manual walkthrough of the install flow — all four/five screens show the identical title string.

---

### ✅ RESOLVED: Release/tag selection menu shows duplicate entries beyond the required five
**Status:** 🟢 **RESOLVED**
**Priority:** **P3** — Minor data issue
**Description:**
The Release/tag selection screen (`llama_updater.py` §7.3.1) displays 7 rows (options 0–6) instead of the 6 specified (option 0 + options 1–5), with options 5 and 6 duplicating the values already shown in options 1 and 2.
**Reproduction Steps:**
1. Run `llama-server-manager --install-llama`.
2. Observe the first menu, "Select a Release."
3. **Actual Result:** Options 1–6 are shown; options 5 (`b10106`) and 6 (`b10105`) repeat options 1 and 2.
4. **Expected Result:** Per `Requirements.md` §7.3.1, only option 0 (manual tag entry) plus options 1–5 (the five most recent release tags, no repeats) should be shown.
**Analysis:**
The release-tag fetch/list-building logic in `LlamaUpdater` likely appends tags from more than one source (e.g. two separate API pages or a merge of "latest" + "all releases" results) without de-duplicating or capping the list at 5.
**Resolution:** Fixed navigation logic in `main.py` to ensure "Previous release" opens the correct menu and removed descriptions from source selection options to fix mangled labels. Refactored `llama_updater.py` to correctly display a "manual entry" plus up to 5 unique recent release tags without duplicates.
**Affected Components:**
- `llama_updater.py`
**Dependencies:**
- `llama_updater.py`
- GitHub Releases API response handling (§7.2)
**Test Coverage:**
- None currently; needs a test asserting exactly 6 rows (0–5) with unique tag values.
**Verification:**
- ✅ Confirmed via manual walkthrough — duplicate tag values visible in rows 5 and 6.

---

### ✅ RESOLVED: OS/Architecture selection menu leaks the `Backend` segment for multi-backend assets

**Status:** ✅ **COMPLETE**
**Priority:** **P1** — Core workflow broken
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

**Resolution:** Fixed the §7.3.0 filename parser in `llama_updater.py` to consistently isolate the Backend segment (including version suffixes). This prevents the Backend segment from being folded into the OS token during the OS/Architecture selection phase and ensures that all backends are correctly identified and surfaced in the subsequent Compute Backend screen.

---

### 🔴 OPEN: OS/Architecture selection menu leaks the `Type` segment for backend-less assets
**Status:** 🔴 **OPEN**
**Priority:** **P1** — Core workflow broken
**Description:**
The "Select Operating System & Architecture" screen (§7.3.2) should list a de-duplicated set of OS/Architecture pairs only, with the Backend segment ignored at this stage. On release `b10154` it instead shows two bogus entries, `Bin win` and `Bin ubuntu`, alongside the valid pairs, plus a stray trailing line, `7 assets`, that has no basis in §7.3.2.
**Reproduction Steps:**
1. Run `llama-server-manager --install-llama` and select release `b10154`.
2. Observe the second menu, "Select Operating System & Architecture."
3. **Actual Result:** 9 rows are shown: `Bin win`, `Android arm64`, `Macos arm64`, `Macos x64`, `Linux arm64`, `Linux x64 (default)`, `Bin ubuntu`, `Windows arm64`, `Windows x64` — plus a stray trailing line, `7 assets`.
4. **Expected Result:** A de-duplicated list of OS/Architecture pairs only (e.g. `ubuntu / x64`, `win / x64`, `macos / arm64`, `macos / x64`), no `Bin ...` entries, no asset-count footer.
**Analysis:**
`Bin win` and `Bin ubuntu` indicate the fixed `Type` segment (`bin`, per §7.3.0 — explicitly "not user-selectable") is leaking into this screen's option list, most likely for backend-less assets (e.g. `llama-b10154-bin-ubuntu-x64.tar.gz`) where a positional/regex split is misaligning segments when the optional Backend field is absent. This is very likely the same root cause behind the "Compute Backend missing `cpu` option" bug below — the backend-less asset is being mis-consumed one screen earlier (as `Bin ubuntu`) rather than correctly resolving to `ubuntu / x64` and later offering `cpu` as a backend choice.
**Affected Components:**
- `llama_updater.py` (`parse_asset_name`, §7.3.0)
- `ui_manager.py` (rendering)
**Dependencies:**
- `llama_updater.py`
- GitHub Releases API asset list (§7.2)
**Test Coverage:**
- None currently; needs a regression test specifically covering backend-less filenames (no Backend segment).
**Verification:**
- ✅ Confirmed via manual walkthrough on `b10154` — `Bin win` / `Bin ubuntu` rows and stray `7 assets` line present.

---

### 🔴 OPEN: Compute Backend selection menu missing `cpu` fallback option for backend-less asset
**Status:** 🔴 **OPEN**
**Priority:** **P1** — Core workflow broken
**Description:**
The "Select Compute Backend" screen (§7.3.3) should list the distinct backends actually available for the chosen OS/Architecture pair, including a `cpu` entry representing any asset with no Backend segment in its filename. On release `b10154`, OS/Architecture `ubuntu / x64`, the `cpu` entry is missing even though a backend-less asset exists for that pair.
**Reproduction Steps:**
1. Run `llama-server-manager --install-llama`, select a release tag, then select `Linux x64` on the OS/Architecture screen.
2. Observe the third menu, "Select Compute Backend."
3. **Actual Result:** `openvino-2026.2.1 (default)`, `rocm-7.2`, `sycl-fp16`, `sycl-fp32`, `vulkan` are listed. No `cpu` entry appears, even though a backend-less asset exists for this OS/Architecture pair.
4. **Expected Result:** Per §7.3.3, a `cpu` entry should represent any asset with no Backend segment in its filename, alongside the other real backends.
**Analysis:**
Consistent with the OS/Architecture bug above: the backend-less asset is being mis-parsed/mis-consumed one screen earlier (as `Bin ubuntu`) rather than correctly resolving to `ubuntu / x64` and later offering `cpu` as a backend choice. Fixing the §7.3.0 parser to correctly detect the optional Backend segment should resolve both bugs simultaneously.
**Affected Components:**
- `llama_updater.py` (Backend filtering/parsing, §7.3.0/§7.3.3)
**Dependencies:**
- `llama_updater.py`
**Test Coverage:**
- None currently; needs a test asserting a backend-less asset for a given OS/Architecture pair surfaces as `cpu` alongside other real backends.
**Verification:**
- ✅ Confirmed via manual walkthrough on `b10154` / `ubuntu x64` — no `cpu` row present among 5 listed backends.

---

### ✅ CLOSED: Extra "Select Archive" screen present between Compute Backend and Confirmation
**Status:** ✅ **CLOSED**
**Priority:** **P1** — Core workflow broken / spec violation
**Description:**
`Requirements.md` §7.3 defines the install flow as exactly four screens: Release, OS/Architecture, Compute Backend, and Confirmation. On release `b10154`, a fifth screen, "Select Archive," appears after Compute Backend and before Confirmation, showing the single resolved archive as a selectable option rather than passing straight through to Confirmation.
**Reproduction Steps:**
1. Run `llama-server-manager --install-llama` and proceed through Release, OS/Architecture (`ubuntu / x64`), and Compute Backend (`openvino-2026.2.1`).
2. Observe the next screen.
3. **Actual Result:** A screen titled "Select Archive" appears with a single option, `llama-b10154-bin-ubuntu-openvino-2026.2.1-x64.tar.gz (default)`, and a malformed second line repeating `96MB (default)`.
4. **Expected Result:** Per §7.3, the install workflow has exactly four screens ending at Confirmation. Once Release, OS/Architecture, and Backend are resolved, the filename should be reconstructed per §7.3.0 and passed directly to the Confirmation screen (§7.3.4) — no intermediate archive-picker screen, single-option or otherwise.
**Analysis:**
An extra render step between Backend resolution and Confirmation has not been removed from `ui_manager.py`/`llama_updater.py`'s call sequence. There's also a distinct cosmetic bug on this screen: `(default)` is duplicated across two separate lines (filename line and size line).
**Affected Components:**
- `llama_updater.py` (screen sequencing, §7.3)
- `ui_manager.py` (extraneous render call; duplicate `(default)` label)
**Dependencies:**
- `llama_updater.py`
**Test Coverage:**
- None currently; needs a test asserting the workflow renders exactly four screens (Release, OS/Architecture, Backend, Confirmation) with no intermediate archive-selection screen, regardless of how many assets match.
**Verification:**
- ✅ Confirmed via manual walkthrough on `b10154` — "Select Archive" screen observed between Backend and Confirmation.

Resolved by removing the "Select Archive" screen from the installation workflow in `llama_updater.py`. The application now automatically selects the first matching asset from the filtered list and proceeds directly to the confirmation screen, following the four-screen sequence required by the specification.

---

## 📋 Project Roadmap / Status Summary

| Section | Status |
|---------|--------|
| **Bug Reports** | 4 open |
| **Documentation Status** | Out of sync: `Testing Strategy.md`, `Requirements.md` reference removed/unused features |
| **Install Workflow (§7.3)** | 3 open bugs — OS/Architecture screen still leaks the `Type` (`bin`) segment for backend-less assets, Compute Backend screen is missing a `cpu` fallback for the same backend-less assets, and the non-spec "Select Archive" fifth screen is still present (now single-option rather than a raw dump). |

**Current Priorities:**
1. **P1** — Fix `llama_updater.py` asset-filename parsing (§7.3.0) to correctly scope OS/Architecture and Backend segments and exclude non-conforming filenames (root cause of 3 of the 5 install-flow bugs)
2. **P1** — Actually remove the "Select Archive" screen from the install flow (`llama_updater.py`/`ui_manager.py` sequencing) — the raw-filename-dump symptom is gone but the screen itself was never removed; also fix the duplicated `(default)` label on it.
3. **P2** — Remove unused `timeout` parameter from `render_menu()` and `render_confirmation()`
4. **P2** — Fix hardcoded install-menu titles to be supplied per-screen (§9.3)
5. **P3** — Fix `test_styling` failure in `test_ui_manager_comprehensive.py`
6. **P3** — De-duplicate release/tag list on the Release selection screen (§7.3.1)
