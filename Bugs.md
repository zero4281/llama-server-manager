### 🟢 OBSOLETE: test_styling fails in test_ui_manager_comprehensive.py
**Status:** 🔴 **OBSOLETE**  
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

### ✅ RESOLVED: timeout parameter removed from render_menu() and render_confirmation()
**Status:** 🟢 **RESOLVED**  
**Priority:** **P2** — Dead code / API hygiene  
**Resolution:** Removed unused `timeout` parameter from both methods, deleted 10 related tests in `test_timeout_pytest.py`, removed 2 test functions from `test_ui_manager_comprehensive.py`, updated `Testing Strategy.md`, `Requirements.md`, and cleared pytest cache. No functional impact — dead code cleanup only.

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
- `ui_manager.py`
- `llama_updater.py` (call sites for each of the four screens)
**Dependencies:**
- `ui_manager.py`
**Test Coverage:**
- None currently; needs a test asserting the title argument passed to `UIManager` differs per screen.
**Verification:**
- ✅ Confirmed via manual walkthrough of the install flow — all four/five screens show the identical title string.

---

### 🆕 NEW: Release/tag selection menu shows duplicate entries beyond the required five
**Status:** 🔴 **OPEN**
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

### 🆕 NEW: OS/Architecture selection menu leaks Compute Backend values into the list
**Status:** 🔴 **OPEN**
**Priority:** **P1** — Core workflow broken
**Description:**
The "Select Operating System & Architecture" screen (§7.3.2) should list de-duplicated OS/Architecture pairs only, with the Backend segment ignored at this stage. Instead it displays 13 rows mixing OS values with Backend values (e.g. `Win-hip-radeon x64`, `Win-sycl x64`, `Win-vulkan x64`, `Win-opencl-adreno arm64`, `Win-cpu arm64`, `Win-cpu x64`, `Bin win`, `Bin ubuntu`), plus a stray trailing line, `1 asset`, not defined anywhere in the spec.
**Reproduction Steps:**
1. Run `llama-server-manager --install-llama` and select a release tag.
2. Observe the second menu.
3. **Actual Result:** 13 rows combining OS and Backend segments, plus a stray `1 asset` line; wrong title (see hardcoded-title bug above).
4. **Expected Result:** Per §7.3.2, a short de-duplicated list of OS/Architecture pairs only, e.g. `ubuntu / x64`, `win / x64`, `macos / arm64`, `macos / x64`, with the current-platform match auto-detected and marked as recommended/default.
**Analysis:**
The §7.3.0 asset-filename parser is very likely not stopping at the OS segment when building this screen's option list — it's carrying the Backend segment (and possibly the raw asset count) forward instead of deferring Backend to the third screen. This is likely the same root-cause parser issue behind the Compute Backend and extra-screen bugs below.
**Affected Components:**
- `llama_updater.py` (asset-filename parsing, §7.3.0)
- `ui_manager.py` (rendering)
**Dependencies:**
- `llama_updater.py`
- GitHub Releases API asset list (§7.2)
**Test Coverage:**
- None currently; needs a test asserting the OS/Architecture screen's option list contains only OS/Architecture pairs, with no Backend text and no auxiliary lines.
**Verification:**
- ✅ Confirmed via manual walkthrough — Backend-only values (`sycl`, `vulkan`, `hip-radeon`, `opencl-adreno`, `cpu`) appearing as if they were OS options.

---

### 🆕 NEW: Compute Backend selection doesn't filter by chosen OS/Architecture, and re-renders itself instead of advancing
**Status:** 🔴 **OPEN**
**Priority:** **P1** — Core workflow broken
**Description:**
The "Select Compute Backend" screen (§7.3.3) always shows a single `0. cpu (default)` option (with a stray duplicate `(default)` line) regardless of which OS/Architecture pair was selected, instead of listing the distinct backends actually available for that pair. Pressing Enter re-renders an identical copy of the same screen rather than advancing to Confirmation.
**Reproduction Steps:**
1. Run `llama-server-manager --install-llama`, select a release tag, then select `ubuntu / x64` on the OS/Architecture screen.
2. Observe the third menu, then press Enter.
3. **Actual Result:** Third menu shows only `0. cpu (default)` plus a stray extra `(default)` line. Pressing Enter re-displays an identical screen instead of proceeding.
4. **Expected Result:** Per §7.3.3, assets should be filtered down to the chosen OS/Architecture pair, and the distinct backends parsed from the remaining assets should be listed (for `ubuntu / x64` this release has at least `sycl` and `vulkan` variants, plus a plain build — confirmed by the raw asset list surfaced in the related extra-screen bug below). The single `cpu (default)` fallback is only correct when the OS/Architecture pair has exactly one matching asset with no Backend segment. Pressing Enter should accept the default and advance directly to the Confirmation screen (§7.3.4).
**Analysis:**
Likely the same root-cause parser issue as the OS/Architecture bug above: the Backend-filtering step isn't correctly scoping assets to the previously-selected OS/Architecture pair before checking for available backends, so it falls through to the "single default" branch every time. Separately, the screen transition logic isn't advancing state after Enter is pressed on this screen — it re-invokes the same render call instead of moving to Confirmation.
**Affected Components:**
- `llama_updater.py` (Backend filtering/parsing, §7.3.0/§7.3.3)
- `ui_manager.py` (screen transition after selection)
**Dependencies:**
- `llama_updater.py`
**Test Coverage:**
- None currently; needs tests asserting (a) the Backend list reflects only backends present for the selected OS/Architecture pair, and (b) confirming a selection advances to the Confirmation screen rather than re-rendering the Backend screen.
**Verification:**
- ✅ Confirmed via manual walkthrough — identical screen shown twice in a row after pressing Enter.

---

### 🆕 NEW: Extra raw-asset-list screen appears; spec defines exactly four install screens
**Status:** 🔴 **OPEN**
**Priority:** **P1** — Core workflow broken / spec violation
**Description:**
After the (broken) Compute Backend screen repeats itself, a fifth screen appears listing raw archive filenames directly (e.g. `llama-b10107-bin-ubuntu-sycl-fp16-x64.tar.gz`, `...sycl-fp32-x64.tar.gz`, `...vulkan-x64.tar.gz`, `...x64.tar.gz`) for the user to pick from. `Requirements.md` §7.3 defines the install flow as exactly four screens ending at Confirmation; this fifth, raw-asset-picker screen has no basis in the current spec and was explicitly removed in v1.0.8 (see Revision History entry for 1.0.8: OS/Architecture screen "replac[es] the old direct zip/asset picker").
**Reproduction Steps:**
1. Run `llama-server-manager --install-llama`, select a release tag, select `ubuntu / x64`, and proceed through the (repeating) Compute Backend screen.
2. **Actual Result:** A fifth screen appears listing four raw `.tar.gz` filenames with sizes, for direct selection.
3. **Expected Result:** No such screen should exist. Once Release, OS/Architecture, and Backend are resolved, the filename should be reconstructed directly per the §7.3.0 naming template and passed straight to the Confirmation screen (§7.3.4).
**Analysis:**
Two of the four assets shown (`llama-b10107-bin-ubuntu-sycl-fp16-x64.tar.gz` and `...sycl-fp32-x64.tar.gz`) have an extra filename segment (`fp16`/`fp32` in addition to `sycl`) that does not fit the 6-segment template `[Project]-[Build/Tag]-[Type]-[OS]-[Backend]-[Architecture].[Ext]`. Per §7.3.0, any filename that doesn't match the template must be excluded from all selection menus. The current implementation appears to fail parsing on these two non-conforming names and falls back to dumping the full raw asset list rather than excluding the bad entries and proceeding with the two valid ones (`vulkan` and the plain build).
**Affected Components:**
- `llama_updater.py` (asset-filename template validation, §7.3.0)
- `ui_manager.py` (extraneous screen should be removed)
**Dependencies:**
- `llama_updater.py`
**Test Coverage:**
- None currently; needs a test asserting non-conforming asset filenames (extra/missing segments) are excluded from every selection menu, and that the workflow contains exactly four screens with no raw-asset fallback screen.
**Verification:**
- ✅ Confirmed via manual walkthrough — fifth screen observed listing raw filenames including two non-conforming names.

---

## 📋 Project Roadmap / Status Summary

| Section | Status |
|---------|--------|
| **Bug Reports** | 5 open, 1 resolved |
| **Test Suite Health** | 1 known failing test (`test_styling`) |
| **Documentation Status** | Out of sync: `Testing Strategy.md`, `Requirements.md` reference removed/unused features |
| **Code Hygiene** | Dead code present: unused `timeout` parameter in UI methods |
| **Install Workflow (§7.3)** | 5 open bugs — OS/Architecture and Compute Backend screens leak/misparse Backend data, Compute Backend screen fails to advance, and a non-spec fifth screen (raw asset picker) appears |

**Current Priorities:**
1. **P1** — Fix `llama_updater.py` asset-filename parsing (§7.3.0) to correctly scope OS/Architecture and Backend segments and exclude non-conforming filenames (root cause of 3 of the 5 install-flow bugs)
2. **P1** — Remove the extra raw-asset-list screen and fix Compute Backend screen advancing to Confirmation
3. **P2** — Remove unused `timeout` parameter from `render_menu()` and `render_confirmation()`
4. **P2** — Fix hardcoded install-menu titles to be supplied per-screen (§9.3)
5. **P3** — Fix `test_styling` failure in `test_ui_manager_comprehensive.py`
6. **P3** — De-duplicate release/tag list on the Release selection screen (§7.3.1)