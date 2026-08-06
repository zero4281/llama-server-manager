# Llama Server Manager — Software Requirements Document

**Version:** 1.1.3  
**Date:** August 2026  
**Repository:** https://github.com/zero4281/llama-server-manager

---

## Table of Contents

1. [Overview](#1-overview)
2. [Project Structure](#2-project-structure)
3. [Configuration File](#3-configuration-file-configjson)
4. [Start Script](#4-start-script-llama-server-manager)
5. [Main Entry Point](#5-main-entry-point-mainpy)
6. [Configuration Module](#6-configuration-module-configpy)
7. [Logging Module](#7-logging-module-loggerpy)
8. [llama.cpp Update/Download Module](#8-llamacpp-updatedownload-module-llama_updaterpy)
9. [Run Script](#9-run-script-runnerpy)
10. [CLI User Interface Module](#10-cli-user-interface-module-ui_managerpy)
11. [Non-Functional Requirements](#11-non-functional-requirements)
12. [Out of Scope](#12-out-of-scope)
13. [Revision History](#revision-history)

---

## 1. Overview

This document defines the requirements for the Llama Server Manager project — a set of Python and Bash scripts that automate the download, installation, updating, and execution of `llama-server` from the llama.cpp project. It covers eight components: the Bash start script, the Python entry point (`main.py`), the configuration module (`config.py`), the logging module (`logger.py`), the llama.cpp update/download module, the run script, the shared configuration file, and the CLI user interface module (`ui_manager.py`).

All interactive menus, prompts, progress bars, and confirmation dialogs are rendered using the `curses` module (Python standard library) with a black background and green text.

| Property | Value |
|---|---|
| Repository | https://github.com/zero4281/llama-server-manager |
| Primary Language | Python 3.12+ |
| Secondary Language | Bash (start script only) |
| Minimum Python Version | 3.12 |
| Target Platforms | Linux, macOS, Windows (via WSL only) |
| llama.cpp Source | https://github.com/ggml-org/llama.cpp/releases |

---

## 2. Project Structure

```
llama-server-manager/
├── llama-server-manager   # Bash start script
├── main.py                # Entry point
├── config.py              # Configuration loading module (Section 6)
├── logger.py               # Program logging configuration module (Section 7)
├── llama_updater.py       # llama.cpp download/update module
├── runner.py              # Run script
├── ui_manager.py          # ncurses CLI user interface module
├── requirements.txt       # Python dependencies
├── config.json            # Runtime configuration (auto-generated if missing)
├── .venv/                 # Python virtual environment (created by user)
│   └── bin/activate
├── llama-cpp/             # Extracted llama.cpp release binaries
│   └── llama-server       # (llama-server.exe on Windows/WSL)
├── llama-server.log       # llama-server output log (when enabled)
└── llama-server-manager.log  # Program's own log file (default path; Section 7.3)
```

---

## 3. Configuration File (config.json)

`config.json` lives in the same directory as `main.py`. If the file does not exist when `main.py` is launched, a default `config.json` must be auto-generated before any other operations proceed. Reading, writing, and default-generation for this file are implemented exclusively by the configuration module described in Section 6 (`config.py`); no other module accesses `config.json` directly.

The file has three top-level keys: `options`, `llama-server`, and `logging`. `llama-server.options` is a pass-through — its key-value pairs are forwarded directly as CLI arguments to `llama-server` and are not interpreted by the wrapper (see Section 9.2). `options` and `logging` are described below; program-logging settings live under the dedicated top-level `logging` key, never nested under `options`.

### 3.1 `options` — program settings

Top-level `options` keys control the program itself. The `llama-server.options` key-value pairs are passed as command-line arguments to `llama-server`. Example:

```json
{
  "options": {
    "llama-cpp": {
      "os-architecture": "ubuntu/x64",
      "backend": "vulkan"
    }
  },
  "llama-server": {
    "options": {
      "host": "0.0.0.0",
      "port": "11235",
      "models-max": "1",
      "log-file": "llama-server.log"
    }
  },
  "logging": {
    "enabled": true,
    "level": "INFO",
    "file": null
  }
}
```

### 3.1.1 `options.llama-cpp` — saved OS/Architecture & Compute Backend

| Key | Type | Description |
|---|---|---|
| `os-architecture` | string (absent if never installed) | The OS/Architecture pair last resolved during a successful llama.cpp install or update (Section 8.3.2), stored as `"<os>/<architecture>"` (e.g. `"ubuntu/x64"`). |
| `backend` | string (absent if never installed) | The Compute Backend last resolved during a successful llama.cpp install or update (Section 8.3.3), e.g. `"vulkan"`. |

These two keys are written automatically by `LlamaUpdater` — never by the user or by `config.py` — after every successful install or update (Section 8.3.5). They are **not** part of `DEFAULT_CONFIG` (Section 6.1) and are simply absent from `config.json` until the first successful install. Their presence or absence together determines whether `--update-llama` takes the fast path or falls back to the full interactive `--install-llama` workflow (Section 8.7).

### 3.2 `logging` — program logging settings

Controls verbosity and destination of the program's own log output (separate from llama-server output).

| Key | Type | Default | Description |
|---|---|---|---|
| `enabled` | boolean | `true` | Whether program logging is active. When `false`, no log record is written anywhere, regardless of `file` (see Section 7.3). |
| `level` | string | `"INFO"` | One of `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `file` | string\|null | `null` | Path to the program log file. If `null` (default), logs are written to `llama-server-manager.log` in the project directory rather than stdout — the program log is never written to stdout/stderr, since the interactive workflow occupies the terminal via `curses` for effectively its entire runtime (see Section 5.1 and Section 7.3). |

This section's schema is implemented by the dedicated logging module described in Section 7 (`logger.py`); no other module configures logging directly.

> **Note:** The llama-server output log is controlled separately via the `log-file` key in `config.json`'s `llama-server.options` section, or overridden at runtime via the `--log-file` CLI flag (see Section 9). It is distinct from the program's own log described above.

---

## 4. Start Script (llama-server-manager)

### 4.1 Language & purpose

- Written in Bash.
- Activates the Python virtual environment, then invokes `main.py` with all arguments forwarded.

### 4.2 Behaviour

- Before launching `main.py`, check whether `.venv/bin/activate` exists in the project directory.
  - If it **does not exist**, print a message prompting the user to create the virtual environment and exit without launching `main.py`:
    ```
    Virtual environment not found. Please create it first:
      python3 -m venv .venv
      source .venv/bin/activate
      pip install -r requirements.txt
    ```
  - If it **exists**, activate it with:
    ```bash
    source .venv/bin/activate
    ```
- After activation, call `main.py` using the Python interpreter, passing through all command-line arguments unchanged:
  ```bash
  python3 main.py "$@"
  ```
- Must be executable (`chmod +x`).

---

## 5. Main Entry Point (main.py)

### 5.1 Language & structure

- Written in Python 3.12+.
- All logic must be encapsulated in a class within an appropriate namespace (e.g. `llama_server_manager.Main`).
- The `if __name__ == '__main__'` block must only instantiate the class and call its `run` method.
- All interactive output (menus, prompts, progress, confirmations) must be delegated to `UIManager` from `ui_manager.py`.
- **The entire interactive workflow must remain within the curses environment.** Once `UIManager` initialises the curses session, no output may be written to stdout or stderr directly. Every menu, prompt, confirmation dialog, progress update, and message must be rendered through `UIManager` without exception: menus, confirmation prompts, and the progress bar use their respective bordered windows (Sections 10.3–10.5), while standalone success, warning, and error messages use `UIManager`'s `print_message` method (Section 10.8) rather than a bordered window. Plain-text output to the terminal is only permitted for messages emitted *before* `UIManager` is constructed (e.g. the WSL detection warning in Section 5.1.1, which is explicitly printed to stderr before curses initialisation, and the Bash-level venv check in Section 4.2, which never enters the Python process at all). Diagnostic output written via the standard library `logging` module (Section 7) is exempt from this restriction: it is always directed to a log file, never to stdout or stderr, so it cannot interfere with the curses display no matter when it is emitted.
- `main.py` must define a single module-level `__version__` string constant. This is the sole source of truth for `--version` (Section 5.2.1) and must be manually kept in sync with this document's own version number (title page and Revision History) on every release — the two values are always identical.

### 5.1.1 WSL detection

- On startup, detect whether the process is running on Windows outside of WSL by checking the platform with Python's `platform` module.
- If running on native Windows (i.e. not inside WSL), print a warning message to stderr before initialising the ncurses UI:
  ```
  Warning: Running on native Windows. Not all functionality may work as intended.
  For full support, please run inside Windows Subsystem for Linux (WSL).
  ```
- Continue execution after the warning; do not exit.

### 5.2 Command-line arguments

| Argument | Type | Description |
|---|---|---|
| `--self-update` | Flag | Update the program's own scripts from the project GitHub repository. Prompts the user to choose between the latest release, a previous release, or the repository `main` branch HEAD before proceeding. |
| `--version` | Flag | Display the program's version and exit (Section 5.2.1). Takes priority over every other argument. |
| `--install-llama` | Flag | Download and install the newest release of llama.cpp. Delegates to `LlamaUpdater` in `llama_updater.py`. If `llama-server` was already running, it is restarted after a successful install (Section 8.5.1). |
| `--update-llama` | Flag | Update to the latest llama.cpp release. If `options.llama-cpp.os-architecture` and `options.llama-cpp.backend` (Section 3.1.1) are both present in `config.json`, downloads automatically with no menu interaction (fast path, Section 8.7). If either is missing, falls back to running the full interactive `--install-llama` workflow instead (Section 8.7). Delegates to `LlamaUpdater`. If `llama-server` was already running, it is restarted after a successful update (Section 8.5.1). |
| `--stop-server` | Flag | Signal `runner.py` to gracefully stop a running `llama-server` process. |
| `--log-file` | String | Path for llama-server output log. Overrides the `log-file` value in `config.json`. Defaults to `llama-server.log` in the project folder if not set in either place. |

### 5.2.1 Version display (`--version`)

- If `--version` is present anywhere among the parsed arguments, it takes priority over every other flag; all other arguments are ignored, including `--self-update`.
- Displaying the version must not print directly to stdout/stderr. `main.py` instantiates `UIManager` and calls `print_message` (Section 10.8, `level="info"`) with the `__version__` constant (Section 5.1) — this is a standalone message, not a menu or confirmation, so it is **not** rendered in a bordered window. Example output:
  ```
  llama-server-manager version 1.1.2
  ```
- After the message is printed, exit with status code `0`.
- `--version` does not require `config.json` to be loaded, the logger to be configured, or the `./llama-cpp` directory to exist; it is handled immediately after argument parsing, before Section 5.4 steps 3 onward.

### 5.3 Self-update behaviour (`--self-update`)

#### 5.3.1 Source selection

Before downloading anything, present the user with a numbered menu (rendered via `UIManager`) to choose the update source:

```
Select update source:
  1) Latest release (recommended)
  2) Previous release
  3) Repository HEAD (main branch)
Choice [1]:
```

- Pressing Enter without input selects the default (option 1, latest release).
- Selecting **option 2** fetches the list of available releases from the GitHub Releases API (same endpoints as Section 8.2, with `owner = zero4281`, `repo = llama-server-manager`) and presents a numbered list for the user to choose from.
- Selecting **option 3** downloads the current `main` branch HEAD as a ZIP archive from:
  ```
  https://github.com/zero4281/llama-server-manager/archive/refs/heads/main.zip
  ```

#### 5.3.2 Confirmation prompt

After the user selects a source, `UIManager` must render a bordered curses window displaying the resolved version or commit reference and prompt for confirmation before modifying any local files. This prompt must **not** drop out of the curses environment; it must be rendered entirely through `UIManager` consistent with Section 10.4. Example layout:

```
┌─────────────────────────────────────────────────────┐
│  Selected: v1.2.0 (llama-server-manager-v1.2.0.zip) │
│  Proceed with update?                               │
│                                                     │
│            ▶ [ Yes ]          [ No  ]               │
└─────────────────────────────────────────────────────┘
```

For a HEAD update the label should reflect the branch rather than a release tag, e.g.:

```
┌─────────────────────────────────────────────┐
│  Selected: main branch HEAD                 │
│  Proceed with update?                       │
│                                             │
│         ▶ [ Yes ]          [ No  ]          │
└─────────────────────────────────────────────┘
```

Pressing Enter confirms (default yes). Entering `n` or `Esc` cancels and exits with status code `0` without modifying any files.

#### 5.3.3 Update execution

- Download the selected archive or branch ZIP to a temporary location.
- Replace local project files with the downloaded versions.
- After a successful update, display a success message via `UIManager` and exit with status code `0`. `main.py` is **not** restarted; the user must invoke the program again to run the updated scripts.
- If the download or file replacement fails, display an error via `UIManager` and exit with a non-zero status code. Local files must not be left in a partially modified state; restore originals if replacement has already begun.

### 5.4 Startup sequence

1. Parse CLI arguments.
2. If `--version`: instantiate `UIManager`, print the version message (Section 5.2.1), and exit with status code `0`. All other arguments are ignored.
3. Call `load_config()` from `config.py` (Section 6) to obtain the configuration dict; a default `config.json` is auto-generated first if the file is missing (Section 6.3).
4. Instantiate `LoggerSetup` and configure the root logger from the `logging` section of the loaded configuration (Section 7). This must complete before `LlamaUpdater`, `Runner`, or `UIManager` are instantiated.
5. If `--self-update`: perform update; exit on completion. All other arguments are ignored.
6. If `--install-llama` or `--update-llama`: instantiate `LlamaUpdater` and call the appropriate method; exit on completion.
7. If `--stop-server`: signal `runner.py` to stop `llama-server`; exit on completion.
8. Otherwise: check whether the `./llama-cpp` directory exists.
   - If it **does not exist**, display the following error via `UIManager`'s `print_message` (Section 10.8, `level="error"`) — plain text, not a bordered window — and exit with a non-zero status code:
```
llama-cpp not found. Please install it first:
  llama-server-manager --install-llama
```
   - If it **exists**, pass the loaded configuration dict to `Runner`.

---

## 6. Configuration Module (config.py)

### 6.1 Language & structure

- Written in Python 3.12+.
- Configuration retrieval is exposed as a single function, `load_config() -> dict`, alongside a module-level `DEFAULT_CONFIG` dictionary constant matching the three-key schema (`options`, `llama-server`, `logging`) described in Section 3.
- `load_config()` is called exactly once by `main.py` during startup (Section 5.4, step 2), before `LoggerSetup`, `LlamaUpdater`, `Runner`, or `UIManager` are instantiated. The returned dict is passed to whichever modules need configuration values.

### 6.2 Responsibility

- `config.py` is the single place in the codebase responsible for locating, creating, reading, and falling back to defaults for `config.json`. No other module reads or writes `config.json` directly — modules that need configuration values (e.g. `Runner`, Section 9.2) receive the already-loaded dict rather than opening the file themselves.

### 6.3 Load behaviour

`load_config()` must behave as follows:

1. Resolve the path to `config.json` (Section 3).
2. If the file does not exist, write `DEFAULT_CONFIG` to that path as pretty-printed JSON (`indent=4`) before proceeding.
3. Open and parse the file as JSON and return the resulting dict.
4. If parsing fails (`json.JSONDecodeError`) or the file cannot be read (`IOError`), print a warning to stderr — `Warning: Could not parse config.json, using default configuration.` — and return `DEFAULT_CONFIG` in memory, without modifying the file on disk.

This stderr warning is permitted under the exception in Section 5.1: `load_config()` runs during startup step 2, before `LoggerSetup` or `UIManager` is instantiated, so no curses session is active yet and program logging is not yet configured.

### 6.4 Error handling

- `load_config()` must never raise on a missing or malformed `config.json`; it always returns a usable dict (either the parsed contents or `DEFAULT_CONFIG`).
- Any other module needing configuration values must obtain them from the dict returned by `load_config()`.

---

## 7. Logging Module (logger.py)

### 7.1 Language & structure

- Written in Python 3.12+.
- All logic must be encapsulated in a class (e.g. `llama_server_manager.logger.LoggerSetup`).
- Never executed directly; instantiated exactly once by `main.py`, immediately after the configuration has been loaded via `config.py`'s `load_config()` (Section 6, Section 5.4 step 2) and before `LlamaUpdater`, `Runner`, or `UIManager` are instantiated.
- Uses Python's standard library `logging` module exclusively; no third-party logging libraries are permitted.

### 7.2 Responsibility

- Reads the `logging` section of `config.json` (Section 3.2) and configures the **root logger** for the lifetime of the process. This is the single place in the codebase where log handlers, formatters, and levels are set up.
- `LoggerSetup` does not create or hold a logger instance that gets passed around to other classes. Every other module (`LlamaUpdater`, `Runner`, `UIManager`, and `main.py` itself) obtains its own logger independently using the standard idiom:

  ```python
  import logging
  logger = logging.getLogger(__name__)
  ```

  Because Python's `logging` module resolves loggers hierarchically by module name, every module-level logger automatically inherits the handler(s), formatter, and level that `LoggerSetup` configured on the root logger — no dependency injection is required, unlike `UIManager`.

### 7.3 Configuration behaviour

- `enabled: false` — no handler is attached to the root logger (or logging is suppressed via `logging.disable(logging.CRITICAL)`); no log record is written anywhere for the duration of the process, regardless of the `file` value.
- `enabled: true` (default):
  - `level` is mapped to the corresponding `logging` constant (`DEBUG`, `INFO`, `WARNING`, `ERROR`) and applied to the root logger.
  - `file` resolution:
    - If `file` is a non-null path, a `logging.FileHandler` is attached at that path.
    - If `file` is `null` (default), a `logging.FileHandler` is attached at the default path `llama-server-manager.log` in the project directory.
  - **Program log output must never be attached to a `StreamHandler` targeting stdout or stderr.** The interactive workflow occupies the terminal via `curses` for effectively the entire runtime of the program (Section 5.1), so writing log records to the terminal outside of `UIManager` would corrupt the display. A file destination is therefore always used whenever logging is enabled — `file: null` selects the default filename rather than stdout.

### 7.4 Formatting

- Log records must include, at minimum, a timestamp, the log level, the originating module/logger name, and the message (e.g. `%(asctime)s [%(levelname)s] %(name)s: %(message)s`).

### 7.5 Relationship to llama-server's own log

- This module is unrelated to `llama-server`'s own output log, which is a separate file controlled via `llama-server.options.log-file` in `config.json` or the `--log-file` CLI flag (Section 3.2, Section 9.4). `logger.py` governs only the manager program's own diagnostic logging.

---

## 8. llama.cpp Update/Download Module (llama_updater.py)

### 8.1 Language & structure

- Written in Python 3.12+.
- All logic must be encapsulated in a class (e.g. `llama_server_manager.updater.LlamaUpdater`).
- Never executed directly; always instantiated by `main.py`.
- All interactive output (menus, prompts, progress bars, confirmations) must be delegated to `UIManager` from `ui_manager.py`.
- Obtains a module-level logger via `logging.getLogger(__name__)` (Section 7) and logs significant events — release resolved, download started/completed, checksum result, errors — at the appropriate level.

### 8.2 GitHub API usage

Release discovery must use the GitHub REST API (API version `2022-11-28`). Full reference:
https://docs.github.com/en/enterprise-server@3.17/rest/releases/releases?apiVersion=2022-11-28

All requests must include the following headers:

```
Accept: application/vnd.github+json
X-GitHub-Api-Version: 2022-11-28
```

The following endpoints are used:

| Purpose | Method | Endpoint |
|---|---|---|
| Get the latest release | `GET` | `/repos/{owner}/{repo}/releases/latest` |
| List all releases (for version selection) | `GET` | `/repos/{owner}/{repo}/releases` |
| Get a specific release by tag | `GET` | `/repos/{owner}/{repo}/releases/tags/{tag}` |

For llama.cpp these map to `owner = ggml-org` and `repo = llama.cpp`. Example:

```
GET https://api.github.com/repos/ggml-org/llama.cpp/releases/latest
```

The `assets` array in each release response contains the downloadable files. Each asset includes a `browser_download_url`, `name`, and `size` field used for platform selection and download.

> **Note:** The GitHub API applies rate limits to unauthenticated requests (60 requests/hour). The module must handle `403` / `429` rate-limit responses gracefully, inform the user, and include the `X-RateLimit-Reset` time from the response headers where available.

### 8.3 Release selection

Selecting a release to install is a four-screen workflow, in this order: **(1)** Release/tag selection, **(2)** Operating System & Architecture selection, **(3)** Compute Backend selection, **(4)** Confirmation of the resolved zip/archive file. Each screen is a distinct `UIManager` menu with its own title reflecting the items being displayed on that screen (see Section 10.3); the title bar must never be reused verbatim from a different screen.

#### 7.3.0 Naming pattern

Release archive filenames follow this exact template:

```
[Project]-[Build/Tag]-[Type]-[OS]-[Backend]-[Architecture].[Ext]
```

For example, `llama-b10107-bin-ubuntu-vulkan-x64.tar.gz` decomposes as:

| Segment | Value | Meaning |
|---|---|---|
| Project | `llama` | Always `llama`; not user-selectable. |
| Build/Tag | `b10107` | The release tag, resolved in Section 8.3.1. |
| Type | `bin` | Must literally equal `bin` (pre-compiled binary); not user-selectable. This segment is validated by value, not merely by position — see below. |
| OS | `ubuntu` | Resolved together with Architecture in Section 8.3.2. |
| Backend | `vulkan` | Compute backend, resolved in Section 8.3.3. Optional — some OS/Architecture combinations ship a single build with no backend segment in the filename. |
| Architecture | `x64` | Resolved together with OS in Section 8.3.2. |

`LlamaUpdater` must parse each asset filename from the resolved release against this template to drive the OS/Architecture and Compute Backend menus described below, and to reconstruct the final filename for the confirmation screen (Section 8.3.4). A filename must be excluded from all selection menus unless **both** of the following hold:

1. **Segment shape matches** — the filename splits into the expected number of dash-separated segments for the template (five, or six when the optional Backend segment is present), plus a recognised extension.
2. **Type segment equals `bin`** — the segment in the Type position must be the literal string `bin`. Matching segment *shape* alone is not sufficient; an asset with the correct number of segments but a different Type value (e.g. a source or auxiliary archive that happens to parse into the right number of dash-separated parts) must still be excluded.

Non-bin assets such as `llama-b10297-xcframework.zip` (wrong segment count) and redistributable archives like `cudart-llama-bin-win-cuda-12.4-x64.zip` (extra leading segment, `Project` segment does not equal `llama`) are both excluded by these rules — the first by segment-shape mismatch, the second by segment-shape mismatch on the `Project` position. Superficial presence or absence of the substring `bin` anywhere in the filename is not itself the criterion; exclusion is always determined by full positional template matching.

#### 7.3.1 Tag selection prompt

**Title:** `Select a Release`

Present a numbered menu of release tags (rendered via `UIManager`) fetched from the GitHub Releases API. Option `0` allows the user to type a tag manually; options `1`–`5` are the five most recent release tags. Pressing Enter without a selection installs the most recent release (option `1`). Example:

```
Select a Release
  0) Enter a tag manually
  1) b8800 (latest)
  2) b8790
  3) b8780
  4) b8770
  5) b8760
Choice [1]:
```

If the user selects option `0`, prompt for the tag string:

```
Enter release tag: 
```

#### 7.3.2 Operating System & Architecture selection prompt

**Title:** `Select Operating System & Architecture`

After a release tag is resolved, fetch its asset list from the GitHub API and parse every asset filename per the naming pattern in Section 8.3.0. Build a de-duplicated, numbered list of the distinct **OS / Architecture** pairs present across all assets for that release (the Backend segment is ignored at this stage). Auto-detect the current platform and architecture using Python's `platform` module and highlight the matching pair as the recommended option; the recommended option is also the default if the user presses Enter without a selection. Example:

```
Select Operating System & Architecture
  1) ubuntu / x64      ← recommended
  2) win / x64
  3) macos / arm64
  4) macos / x64
Choice [1]:
```

If auto-detection fails (platform or architecture cannot be determined, or no asset matches the detected pair), no option is highlighted and no default is pre-selected; the user must choose explicitly.

#### 7.3.3 Compute Backend selection prompt

**Title:** `Select Compute Backend`

After OS and Architecture are resolved, filter the release's assets down to those matching the selected OS/Architecture pair and parse the remaining Backend segment(s) per Section 8.3.0. Present the distinct backends as a numbered list; the first listed option is the default if the user presses Enter without a selection. There is no auto-detection for Compute Backend, since the correct choice depends on locally installed drivers/hardware that Python's `platform` module cannot report. Example:

```
Select Compute Backend
  1) vulkan
  2) cuda
  3) cpu
Choice [1]:
```

If the selected OS/Architecture pair only has a single matching asset with no Backend segment in its filename (e.g. some macOS builds), skip presenting multiple choices and instead show a single option so the screen remains consistent with the rest of the workflow:

```
Select Compute Backend
  1) cpu (default)
Choice [1]:
```

Pressing Enter accepts option `1` in either case.

#### 7.3.4 Confirmation prompt

After Release, OS/Architecture, and Compute Backend are all resolved, reconstruct the final archive filename per the template in Section 8.3.0 and use it to locate the matching asset. `UIManager` must render a bordered curses window titled `Confirm Installation` displaying the resolved filename and prompt for confirmation before downloading anything. This prompt must **not** drop out of the curses environment; it must be rendered entirely through `UIManager` consistent with Section 10.4. Example layout:

```
┌──────────────────────────────────────────────────────────┐
│ Confirm Installation                                     │
│ Selected release: b8800 (llama-b8800-bin-ubuntu-x64.zip) │
│ Proceed with installation?                               │
│                                                          │
│             ▶ [ Yes ]          [ No  ]                   │
└──────────────────────────────────────────────────────────┘
```

Pressing Enter confirms (default yes). Entering `n` or `Esc` cancels and exits with status code `0` without modifying any files.

#### 7.3.5 Saving selections

- Once the confirmation in Section 8.3.4 is accepted, and before the download begins, `LlamaUpdater` must write the resolved OS/Architecture pair and Compute Backend to `config.json` under `options.llama-cpp` (Section 3.1.1). This applies whether the four-screen workflow was reached via `--install-llama` directly or via the `--update-llama` fallback described in Section 8.7.
- Saving happens automatically; the user is never prompted separately to opt in or out.
- `LlamaUpdater` updates the `options.llama-cpp.os-architecture` and `options.llama-cpp.backend` keys on the already-loaded configuration dict and writes the full configuration back to `config.json` as pretty-printed JSON (`indent=4`), preserving every other existing key and value. `LlamaUpdater` is the only module permitted to write these two keys, consistent with the ownership rules in Section 6.2.
- If writing `config.json` fails (e.g. a permissions error), display a warning via `UIManager` and continue with the download regardless — a failure to persist the selection must not block installation.
- The Release tag itself is never saved to `config.json`; only OS/Architecture and Compute Backend persist. `--update-llama` (Section 8.7) always resolves the newest release at run time, regardless of which tag was previously installed.

### 8.4 Platform & architecture detection

- Auto-detect the current platform (Linux, Windows, macOS) and architecture (`x86_64`, `arm64`, etc.) using Python's `platform` module.
- Use the detected platform/architecture to determine and highlight the recommended OS/Architecture pair in the selection list (see Section 8.3.2).
- If detection fails, display all OS/Architecture pairs without a highlighted recommendation and require the user to select explicitly.
- Auto-detection applies only to OS and Architecture. Compute Backend (Section 8.3.3) is never auto-detected, since the correct backend depends on locally installed drivers/hardware that Python's `platform` module cannot report; the first listed backend is offered as the default instead.

### 8.5 Download & extraction

- Download the selected release archive (`.zip` or `.tar.gz`) using the asset's `browser_download_url`.
- Display a ncurses progress bar (rendered via `UIManager`) during the download so the user can track progress.
- **Checksum verification:** After the download completes, check whether the release provides a checksum file (e.g. `sha256sum.txt` or a similarly named asset). If one is present, download it and verify the archive before proceeding. If verification fails, delete the downloaded archive, display a clear error via `UIManager`, and exit with a non-zero status code.
- If no checksum asset is available for the release, skip verification and proceed directly to extraction.
- Decompress and extract the full archive contents — all binaries and supporting files — into the `./llama-cpp/` folder in the **same directory as the script**.
- If a `./llama-cpp/` folder already exists, delete it entirely before extraction without prompting or creating a backup.
- Ensure `llama-server` (or `llama-server.exe` on Windows) is executable after extraction.
- Remove the downloaded archive file after successful extraction.
- After a successful install, display a success message via `UIManager` and run a quick sanity check by executing `llama-server --version` and displaying its output through `UIManager`.
  - If the sanity check **passes**, proceed to Section 8.5.1 to restart `llama-server` if it was already running.
  - If the sanity check **fails**, display a warning via `UIManager`, stop any already-running `llama-server` instance per Section 8.5.1 (without starting a new one), and still exit with status code `0` (the binaries were installed; the version check is informational).

#### 8.5.1 Restarting `llama-server`

This applies after every successful download/extraction reached via `--install-llama` or `--update-llama` — including both the `--update-llama` fast path (Section 8.7, item 1) and its interactive fallback (Section 8.7, item 2), since both reach this point via Section 8.5.

- Check whether `llama-server.pid` (Section 9.3) exists in the project directory.
  - If it does not exist, no instance was running before the install/update; do nothing further.
  - If it exists, read the recorded PID and verify that it currently corresponds to a running `llama-server` process (not just that the file is present — the file may be stale, e.g. left over from a crash). If the PID does not correspond to a live `llama-server` process, delete the stale PID file and do nothing further.
- If the PID corresponds to a live `llama-server` process:
  - Stop it using `Runner`'s existing graceful shutdown logic (Section 9.5), called in-process — do not duplicate that logic here and do not shell out to `--stop-server`.
  - If the sanity check (Section 8.5) passed, start a new `llama-server` instance using `Runner`'s existing process execution logic (Section 9.3), called in-process. The new instance's launch arguments must be re-derived from `config.json` by calling `load_config()` (Section 6) fresh; no CLI pass-through arguments are used (Section 5.2 defines no such mechanism).
  - If the sanity check failed, do not start a new instance; instead display a message via `UIManager` explaining that the previously running `llama-server` instance was stopped because the newly installed binary failed its sanity check.

### 8.6 Error handling

- Handle `403` and `429` responses from the GitHub API as rate-limit errors; display a clear message via `UIManager` including the `X-RateLimit-Reset` time if present in the response headers.
- If the GitHub API is otherwise unreachable, display a clear error via `UIManager` and exit with a non-zero status.
- If the download fails or the archive is corrupt, clean up any partial files and report the error via `UIManager`.

### 8.7 `--update-llama` fast path

When `main.py` dispatches `--update-llama` (Section 5.2, Section 5.4 step 5), `LlamaUpdater` decides between two behaviours based on the already-loaded configuration dict, before issuing any network requests:

1. **Fast path — saved options present.** If both `options.llama-cpp.os-architecture` and `options.llama-cpp.backend` (Section 3.1.1) are present in the loaded configuration:
   - Skip Section 8.3.1 (Release selection) entirely — always resolve the newest release via `GET /repos/ggml-org/llama.cpp/releases/latest` (Section 8.2).
   - Skip Section 8.3.2 (OS/Architecture selection) — use the saved `os-architecture` value directly.
   - Skip Section 8.3.3 (Compute Backend selection) — use the saved `backend` value directly.
   - Skip Section 8.3.4 (Confirmation screen) — once the archive filename is reconstructed (Section 8.3.0) and the matching asset located, proceed directly to download.
   - No `UIManager` menu or confirmation prompt is shown at any point during selection. `UIManager` is still used for the download progress bar (Section 8.5, Section 10.5) and for the final success/warning/error message (Section 8.5, Section 10.7).
   - If no asset in the latest release matches the reconstructed filename (e.g. the saved OS/Architecture/Backend combination is no longer published for the newest release), display an error via `UIManager` stating that the saved selection could not be matched, and exit with a non-zero status code. Do **not** silently fall back to the interactive workflow in this case — the missing-options fallback in item 2 below applies only when the keys are absent from `config.json`, not when they fail to match.
   - The fast path never writes to `config.json`: `options.llama-cpp.os-architecture` and `options.llama-cpp.backend` are read but not re-saved, since they are already correct and unchanged. Only the four-screen workflow (Section 8.3.5) writes these keys — that is, `--install-llama` run directly, or the `--update-llama` fallback in item 2 below.
2. **Fallback — saved options absent or incomplete.** If either `options.llama-cpp.os-architecture` or `options.llama-cpp.backend` is missing from `config.json` (e.g. `config.json` was auto-generated from `DEFAULT_CONFIG` and llama.cpp has never been installed via this program), `LlamaUpdater` must run the identical interactive workflow used by `--install-llama` (Sections 8.3.1–8.3.5) instead — all four menu screens, including the Confirmation screen. In effect, `--update-llama` behaves exactly like `--install-llama` for the remainder of the run in this case.

---

## 9. Run Script (runner.py)

### 9.1 Language & structure

- Written in Python 3.12+.
- All logic must be encapsulated in a class (e.g. `llama_server_manager.runner.Runner`).
- Never executed directly; always instantiated by `main.py`.
- Any user-facing status output must be delegated to `UIManager` from `ui_manager.py`.
- Obtains a module-level logger via `logging.getLogger(__name__)` (Section 7) and logs process launch, PID, and shutdown events.

### 9.2 Configuration loading

- Receive the already-loaded configuration dict from `main.py` (obtained via `config.py`'s `load_config()`, Section 6); `Runner` must not read `config.json` directly.
- Extract key-value pairs from the `llama-server.options` section and convert them to CLI arguments for `llama-server`. The program accepts no CLI pass-through arguments for `llama-server` (Section 5.2); `config.json` is the sole source of these launch arguments.

### 9.3 Process execution

- Launch `./llama-cpp/llama-server` (`./llama-cpp/llama-server.exe` on Windows) with the assembled argument list.
- Record the PID of the launched `llama-server` process.
- Write the PID to `llama-server.pid` in the project directory.
- `main.py` returns control to the shell immediately after launch.

### 9.4 Logging (llama-server output)

This is the log produced by the `llama-server` process itself and is distinct from the manager program's own log described in Section 7.

The log file path is resolved in the following order of precedence:

1. `--log-file` CLI argument
2. `llama-server.options.log-file` in `config.json`
3. Default: `llama-server.log` in the project folder

The resolved path is passed to `llama-server` via its `--log-file` flag.

### 9.5 Graceful shutdown

Shutdown is triggered by either a `SIGINT` / `KeyboardInterrupt` (Ctrl+C) or the `--stop-server` argument passed to `main.py`.

1. Send `SIGTERM` (or the platform equivalent) to the `llama-server` process.
2. Wait up to **60 seconds** for the process to exit cleanly.
3. If the process has not exited after 60 seconds, send `SIGKILL` (`TerminateProcess` on Windows) to forcibly terminate it.
4. Remove the PID file after the process has been stopped.
5. Exit the program with status code `0` on clean shutdown, non-zero if a force-kill was required.

---

## 10. CLI User Interface Module (ui_manager.py)

### 10.1 Language & structure

- Written in Python 3.12+.
- All logic must be encapsulated in a class (e.g. `llama_server_manager.ui.UIManager`).
- Uses Python's standard library `curses` module exclusively; no third-party terminal UI libraries are permitted.
- Never executed directly; always instantiated by `main.py` and passed to other modules that require user interaction.
- Obtains a module-level logger via `logging.getLogger(__name__)` (Section 7), like every other module.

### 10.2 Visual style

- Background: black (`curses.COLOR_BLACK`).
- Foreground text: green (`curses.COLOR_GREEN`).
- All windows and panels must use this colour pair consistently.
- Highlighted / selected items (e.g. the currently focused menu option) must be rendered in reverse video (`curses.A_REVERSE`) using the same green-on-black pair.

### 10.3 Numbered menus

- Render each menu inside a bordered `curses` window.
- The title line is supplied by the caller on each invocation and must describe the specific items being displayed on that screen (e.g. `Select a Release`, `Select Operating System & Architecture`). `UIManager` must not reuse or hard-code a single generic title across different menus — each call renders its own title text.
- Display a title line, then one numbered option per row.
- The currently highlighted option is shown in reverse video; the user navigates with the arrow keys or by typing the option number.
- Pressing Enter confirms the selection; pressing `q` or `Esc` cancels (equivalent to the user entering `n` at a confirmation prompt).
- A default option, where applicable, is indicated by appending `(default)` to the option label.

### 10.4 Confirmation prompts

- Render as a bordered curses window containing a status line (the resolved selection being confirmed) followed by a prompt line: `Proceed? [Y/n]:`.
- `Y` / Enter confirms; `n` / `Esc` cancels.
- Must never drop out of the curses environment; all rendering goes through `UIManager`.

### 10.5 Progress bar

- Render inside a bordered `curses` window with a title line (e.g. the filename being downloaded).
- Display a filled bar that updates in real time as download bytes are received.
- Show current progress as both a percentage and a `downloaded / total` byte count (human-readable, e.g. `12.4 MB / 98.0 MB`).
- If the total size is unknown (no `Content-Length` header), display a spinner animation instead of a filled bar.

### 10.6 Lifecycle

- `UIManager` must initialise the `curses` environment (`curses.initscr`, colour setup, `cbreak`, `noecho`, hidden cursor) on construction and restore the terminal to its original state on destruction or on any unhandled exception, ensuring the terminal is never left in a broken state.
- The `UIManager` instance must remain active and the curses session must remain open for the **entire duration** of the program's interactive workflow — from first menu to final success/error message. The curses session must not be torn down and re-entered mid-workflow; `UIManager` is constructed once and destroyed once.

### 10.7 Logging integration

- Whenever `UIManager` renders an error, warning, or success/informational message to the user, it must also emit a corresponding record to its module logger at a matching level:
  - Error messages → `logger.error(...)`
  - Warning messages → `logger.warning(...)`
  - Success / informational messages → `logger.info(...)`
- Whether a given message is actually persisted depends on the `enabled` and `level` settings configured for the process (Section 3.2, Section 7.3). For example, an informational success message logged at `INFO` will not appear in the log file if `level` is set to `WARNING` or `ERROR`.
- This dual output (curses display + log record) is independent of, and does not replace, the separate `llama-server` output log described in Section 9.4.

### 10.8 Plain messages (`print_message`)

- For any output that is purely informational and does not require a menu (Section 10.3), confirmation prompt (Section 10.4), or progress bar (Section 10.5) — success messages, warnings, and errors — `UIManager` exposes a `print_message(text, level)` method. It writes the text as plain, unbordered lines within the active curses session; it is **not** a bordered window, and it never falls back to a direct stdout/stderr `print()` call.
- `level` is one of `info`, `warning`, `error`, matching Section 10.7's logging integration — the same call also emits the corresponding log record at a matching level.
- `print_message` is the correct rendering path for standalone messages such as: the `--version` output (Section 5.2.1), the `./llama-cpp` not-found error (Section 5.4), self-update success/failure messages (Section 5.3.3), and install/update success/warning/error messages (Sections 8.5, 8.5.1, 8.6, 8.7). Anywhere this document says a message is "displayed via `UIManager`" without describing a menu, confirmation prompt, or progress bar, `print_message` is the method used.
- `print_message` is distinct from the bordered constructs in Sections 10.3–10.5, which remain bordered `curses` windows because they require structured layout or direct user interaction (selection, confirmation, or a live-updating bar). A message rendered via `print_message` is never bordered, even when it is emitted immediately after a bordered menu or confirmation window closes.

---

## 11. Non-Functional Requirements

### 11.1 Cross-platform compatibility

- All Python code must run on Linux and macOS without modification. Windows is supported via WSL only (see Section 5.1.1).
- Path handling must use `pathlib.Path` throughout to avoid OS-specific separator issues.
- Signal handling must use platform-appropriate mechanisms (`SIGTERM`/`SIGKILL` on POSIX; `TerminateProcess` on Windows/WSL).

### 11.2 Dependencies

- Standard library only where possible.
- The `requests` library (or `urllib`) may be used for GitHub API calls and file downloads.
- The `curses` module (standard library) is used for all CLI UI rendering; no third-party terminal UI libraries are permitted.
- The `logging` module (standard library) is used for all program log output; see Section 7. No third-party logging libraries are permitted.
- No third-party dependency should be required for core start/stop/run operations.

### 11.3 Error handling & exit codes

- All external calls (GitHub API, subprocess launches, file I/O) must be wrapped in `try/except` blocks.
- Errors must be logged (according to the logging config) and result in a non-zero exit code.
- The program must never silently swallow exceptions.

### 11.4 Code style

- Follow PEP 8 conventions.
- Each module must include a module-level docstring describing its purpose.
- Each class and public method must include a docstring.

---

## 12. Out of Scope

- Model file management (downloading, converting, or organising GGUF model files).
- A graphical user interface.
- Authentication or access control for `llama-server`.
- Automatic selection of quantisation level or GPU layers.

---

## Revision History

| Version | Date | Author | Notes |
|---|---|---|---|
| 1.1.3 | August 2026 | zero4281 | Clarified §7.3.0's asset-filename matching rule: exclusion from selection menus now explicitly requires both correct segment shape *and* a literal `bin` value in the Type position, not segment shape alone. Closes a gap where a non-bin asset with an incidentally correct segment count (e.g. a hypothetical source/auxiliary archive) would have parsed successfully under the old wording. Added worked examples (`llama-b10297-xcframework.zip`, `cudart-llama-bin-win-cuda-12.4-x64.zip`) showing both are excluded via positional template matching, not via a filename substring check. |
| 1.1.2 | August 2026 | zero4281 | Added `--version` flag (new §5.2.1): prints the program's version via `UIManager`'s `print_message` (new §10.8) and exits, taking priority over all other arguments. Added a `main.py`-level `__version__` constant (§5.1) as the single source of truth, required to be kept manually in sync with this document's own version number on every release. Updated §5.4 startup sequence to check `--version` immediately after argument parsing, before `config.json` is loaded or the logger is configured. Added new §10.8 defining `print_message` as the correct rendering path for standalone success/warning/error messages, as distinct from the bordered windows used for menus, confirmation prompts, and the progress bar (§10.3–§10.5); clarified §5.1 accordingly. Fixed the §5.4 `llama-cpp` not-found error, which had incorrectly specified a bordered curses window (an artifact of the pre-`print_message` version of this spec) — it now uses `print_message` with plain, unbordered text. |
| 1.1.1 | August 2026 | zero4281 | Removed the CLI pass-through mechanism (`<llama args>`, old §5.2); `Runner` now derives all `llama-server` launch arguments solely from `config.json` (§9.2). Removed the incorrect `main.py` self-restart behaviour from §5.3.3/§5.4 step 4 — `--self-update` now exits after a successful update instead of relaunching itself. Removed the fast-path config re-save from §8.7 item 1; only the four-screen workflow (§8.3.5) — i.e. `--install-llama` run directly, or the `--update-llama` fallback — writes `options.llama-cpp.os-architecture`/`backend`, since the fast path's saved values are already correct and unchanged. Added new §8.5.1 defining `llama-server` restart behaviour: after a successful `--install-llama` or `--update-llama` (both fast path and fallback), if `llama-server.pid` exists and corresponds to a live `llama-server` process, `LlamaUpdater` stops and restarts it in-process by calling `Runner`'s existing shutdown (§9.5) and launch (§9.3) logic directly, rather than duplicating that logic or shelling out to `--stop-server`; if the post-install sanity check fails, the running instance is stopped but not restarted, with a message displayed via `UIManager`. |
| 1.1.0 | July 2026 | zero4281 | Added persistence of the Operating System & Architecture (§8.3.2) and Compute Backend (§8.3.3) selections to `config.json` under the new `options.llama-cpp` key (new §3.1.1), written automatically by `LlamaUpdater` after every successful install/update (new §8.3.5). Added §8.7 defining the `--update-llama` fast path: when both saved values are present, all four selection screens (§8.3.1–§8.3.4) are skipped and the newest release is downloaded automatically with the saved OS/Architecture/Backend and no `UIManager` prompts; when either value is missing, `--update-llama` falls back to running the identical interactive workflow as `--install-llama`. Updated the `config.json` example and the `--update-llama` row in §5.2 accordingly. |
| 1.0.9 | July 2026 | zero4281 | Added a dedicated Configuration Module (`config.py`, new §6) to clarify where config.json load/create/default-fallback logic lives, matching the module's `load_config()`/`DEFAULT_CONFIG` implementation. Clarified in §3 that `config.py` is the sole reader/writer of `config.json`. Updated §5.4 (Startup sequence) and §9.2 (Runner) so that `main.py` calls `load_config()` and passes the resulting dict to `Runner` rather than each module reading `config.json` independently. Renumbered former §6–§11 to §7–§12 accordingly. |
| 1.0.8 | July 2026 | zero4281 | Restructured the llama.cpp install/update flow (§7.3) into four distinct screens with per-screen titles: Release selection (§7.3.1), Operating System & Architecture selection (§7.3.2, replacing the old direct zip/asset picker), Compute Backend selection (§7.3.3, new), and a final Confirmation screen (§7.3.4) showing the resolved archive filename. Added §7.3.0 documenting the `[Project]-[Build/Tag]-[Type]-[OS]-[Backend]-[Architecture].[Ext]` naming template used to parse assets and reconstruct the final filename. Clarified in §7.4 that auto-detection applies only to OS/Architecture, not Compute Backend. Updated §9.3 to require menu titles to be supplied per-call and reflect the current screen's content rather than being reused across menus. |
| 1.0.7 | July 2026 | zero4281 | Added a dedicated Logging Module (`logger.py`, new §6) to clarify where program-logging logic lives. Clarified that all other modules obtain a logger via the standard `logging.getLogger(__name__)` idiom rather than dependency injection. Changed the effective behaviour of `logging.file: null`: program logs now default to `llama-server-manager.log` in the project directory instead of stdout, since stdout/stderr output is prohibited while curses is active (§5.1); `enabled: false` remains the way to disable logging entirely. Fixed the `config.json` example in §3.1, which previously showed a stray `options.logfile` key instead of the documented `logging` section. Added §9.7 requiring `UIManager` to mirror every displayed error/warning/success message to the program log at a matching level. Renumbered former §6–§10 to §7–§11 accordingly. |
| 1.0.6 | July 2026 | zero4281 | Removed §7.4 Daemon mode (the program is not a daemon); moved PID file (`llama-server.pid`) requirement and shell-return behaviour into §7.3 Process execution. Renumbered former §7.5 Logging → §7.4 and former §7.6 Graceful shutdown → §7.5. |
| 1.0.5 | April 2026 | zero4281 | Clarified that the entire interactive workflow must remain within the curses environment after UIManager initialisation; no stdout/stderr output is permitted post-init. Updated confirmation prompts in §5.3.2 and §6.3.3 to show curses bordered window layout. Updated §5.4 llama-cpp-not-found error, §5.3.3 update failure error, §6.5 success/warning messages, and §6.6 API error messages to use UIManager instead of direct print calls. Strengthened §8.4 and §8.6 to require UIManager to remain active for the full workflow duration. |
| 1.0.4 | April 2026 | zero4281 | Added ncurses CLI UI module (`ui_manager.py`, Section 8); all menus, prompts, and progress bars rendered with black background and green text; Windows now requires WSL with runtime detection warning; updated cross-platform and dependency requirements accordingly |
| 1.0.3 | April 2026 | zero4281 | Removed `--foreground` command-line option |
| 1.0.2 | April 2026 | zero4281 | Expanded Section 6 install workflow: interactive release tag + asset selection with auto-detected recommendation, all-assets display, checksum verification, download progress bar, delete-and-replace of existing llama-cpp folder, post-install success message and sanity check |
| 1.0.1 | April 2026 | zero4281 | Added user confirmation and source selection for `--self-update`; added user confirmation prompt to llama.cpp install/update |
| 1.0.0 | April 2026 | zero4281 | Initial draft |