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
`Bin win` and `Bin ubuntu` indicate the fixed `Type` segment (`bin`, per §7.3.0 — explicitly "not user-selectable") is leaking into this screen's option list, most likely for backend-less assets (e.g. `llama-b10154-bin-ubuntu-x64.tar.gz`) where a positional/regex split is misaligning segments when the optional Backend field is absent. This is very likely the same root cause behind the "Compute Backend missing `cpu` option" bug below — the backend-less asset is being mis-consumed at this screen instead of correctly resolving to `ubuntu / x64` and later offering `cpu` as a backend choice.
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
3. **Actual Result:** `openvino-2026.2.1 (default)`, `rocm-7.2`, `sycl-fp16`, `sycl-fp32`, `vulkan` are listed. No `cpu` entry appears, even though a backend-less asset (e.g. `llama-b10154-bin-ubuntu-x64.tar.gz`) exists for this OS/Architecture pair.
4. **Expected Result:** Per §7.3.3, a `cpu` entry should represent any asset with no Backend segment in its filename, alongside the other real backends.
**Analysis:**
Consistent with the OS/Architecture bug above: the backend-less asset is being mis-parsed/mis-consumed one screen earlier (as `Bin ubuntu`) rather than reaching this screen as a valid `ubuntu / x64` candidate offering `cpu`. Fixing the §7.3.0 parser to correctly detect the optional Backend segment should resolve both bugs simultaneously.
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

Resolved by removing the 'Select Archive' screen from the installation workflow in `llama_updater.py`. The application now automatically selects the first matching asset from the filtered list and proceeds directly to the confirmation screen, following the four-screen sequence required by the specification.
---

## 📋 Project Roadmap / Status Summary

| Section | Status |
|---------|--------|
| **Bug Reports** | 3 open |
| **Documentation Status** | Out of sync: `Testing Strategy.md`, `Requirements.md` reference removed/unused features |
| **Install Workflow (§7.3)** | 3 open bugs — OS/Architecture screen still leaks the `Type` (`bin`) segment for backend-less assets, Compute Backend screen is missing a `cpu` fallback for the same backend-less assets, and the non-spec "Select Archive" fifth screen is still present (now single-option rather than a raw dump). |

**Current Priorities:**
1. **P1** — Fix `llama_updater.py`'s handling of the *optional* Backend segment in §7.3.0 filename parsing (root cause of both the OS/Architecture and Compute Backend bugs): backend-less assets must resolve to their correct OS/Architecture pair and offer `cpu` as a backend, not leak `bin` as a pseudo-OS.
2. **P1** — Actually remove the "Select Archive" screen from the install flow (`llama_updater.py`/`ui_manager.py` sequencing) — the raw-filename-dump symptom is gone but the screen itself was never removed; also fix the duplicated `(default)` label on it.