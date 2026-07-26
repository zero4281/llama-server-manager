# Llama Server Manager — Software Requirements Document

**Version:** 1.0.7  
**Date:** July 2026  
**Repository:** https://github.com/zero4281/llama-server-manager

---

## Table of Contents

1. [Overview](#1-overview)
2. [Project Structure](#2-project-structure)
3. [Configuration File](#3-configuration-file-configjson)
4. [Start Script](#4-start-script-llama-server-manager)
5. [Main Entry Point](#5-main-entry-point-mainpy)
6. [Logging Module](#6-logging-module-loggerpy)
7. [llama.cpp Update/Download Module](#7-llamacpp-updatedownload-module-llama_updaterpy)
8. [Run Script](#8-run-script-runnerpy)
9. [CLI User Interface Module](#9-cli-user-interface-module-ui_managerpy)
10. [Non-Functional Requirements](#10-non-functional-requirements)
11. [Out of Scope](#11-out-of-scope)
12. [Revision History](#revision-history)

---

## 1. Overview

This document defines the requirements for the Llama Server Manager project — a set of Python and Bash scripts that automate the download, installation, updating, and execution of `llama-server` from the llama.cpp project. It covers seven components: the Bash start script, the Python entry point (`main.py`), the logging module (`logger.py`), the llama.cpp update/download module, the run script, the shared configuration file, and the CLI user interface module (`ui_manager.py`).

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
├── logger.py               # Program logging configuration module (Section 6)
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
└── llama-server-manager.log  # Program's own log file (default path; Section 6.3)
```

---

## 3. Configuration File (config.json)

`config.json` lives in the same directory as `main.py`. If the file does not exist when `main.py` is launched, a default `config.json` must be auto-generated before any other operations proceed.

The file has three top-level keys: `options`, `llama-server`, and `logging`. `llama-server.options` is a pass-through — its key-value pairs are forwarded directly as CLI arguments to `llama-server` and are not interpreted by the wrapper (see Section 8.2). `options` and `logging` are described below; program-logging settings live under the dedicated top-level `logging` key, never nested under `options`.

### 3.1 `options` — program settings

Top-level `options` keys control the program itself. The `llama-server.options` key-value pairs are passed as command-line arguments to `llama-server`. Example:

```json
{
  "options": {},
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

### 3.2 `logging` — program logging settings

Controls verbosity and destination of the program's own log output (separate from llama-server output).

| Key | Type | Default | Description |
|---|---|---|---|
| `enabled` | boolean | `true` | Whether program logging is active. When `false`, no log record is written anywhere, regardless of `file` (see Section 6.3). |
| `level` | string | `"INFO"` | One of `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `file` | string\|null | `null` | Path to the program log file. If `null` (default), logs are written to `llama-server-manager.log` in the project directory rather than stdout — the program log is never written to stdout/stderr, since the interactive workflow occupies the terminal via `curses` for effectively its entire runtime (see Section 5.1 and Section 6.3). |

This section's schema is implemented by the dedicated logging module described in Section 6 (`logger.py`); no other module configures logging directly.

> **Note:** The llama-server output log is controlled separately via the `log-file` key in `config.json`'s `llama-server.options` section, or overridden at runtime via the `--log-file` CLI flag (see Section 8). It is distinct from the program's own log described above.

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
- **The entire interactive workflow must remain within the curses environment.** Once `UIManager` initialises the curses session, no output may be written to stdout or stderr directly. Every menu, prompt, confirmation dialog, progress update, success message, and error message must be rendered through `UIManager` without exception. Plain-text output to the terminal is only permitted for messages emitted *before* `UIManager` is constructed (e.g. the WSL detection warning in Section 5.1.1, which is explicitly printed to stderr before curses initialisation, and the Bash-level venv check in Section 4.2, which never enters the Python process at all). Diagnostic output written via the standard library `logging` module (Section 6) is exempt from this restriction: it is always directed to a log file, never to stdout or stderr, so it cannot interfere with the curses display no matter when it is emitted.

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
| `--install-llama` | Flag | Download and install the newest release of llama.cpp. Delegates to `LlamaUpdater` in `llama_updater.py`. |
| `--update-llama` | Flag | Update an existing llama.cpp installation to the latest release. Delegates to `LlamaUpdater`. |
| `--stop-server` | Flag | Signal `runner.py` to gracefully stop a running `llama-server` process. |
| `--log-file` | String | Path for llama-server output log. Overrides the `log-file` value in `config.json`. Defaults to `llama-server.log` in the project folder if not set in either place. |
| `<llama args>` | Pass-through | Any other arguments are collected and forwarded verbatim to `llama-server` via `runner.py`. |

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
- Selecting **option 2** fetches the list of available releases from the GitHub Releases API (same endpoints as Section 7.2, with `owner = zero4281`, `repo = llama-server-manager`) and presents a numbered list for the user to choose from.
- Selecting **option 3** downloads the current `main` branch HEAD as a ZIP archive from:
  ```
  https://github.com/zero4281/llama-server-manager/archive/refs/heads/main.zip
  ```

#### 5.3.2 Confirmation prompt

After the user selects a source, `UIManager` must render a bordered curses window displaying the resolved version or commit reference and prompt for confirmation before modifying any local files. This prompt must **not** drop out of the curses environment; it must be rendered entirely through `UIManager` consistent with Section 9.4. Example layout:

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
- After a successful update, restart `main.py` with the same arguments that were originally passed.
- If the download or file replacement fails, display an error via `UIManager` and exit with a non-zero status code. Local files must not be left in a partially modified state; restore originals if replacement has already begun.

### 5.4 Startup sequence

1. Parse CLI arguments.
2. Check for `config.json`; auto-generate a default if missing.
3. Instantiate `LoggerSetup` and configure the root logger from the `logging` section of `config.json` (Section 6). This must complete before `LlamaUpdater`, `Runner`, or `UIManager` are instantiated.
4. If `--self-update`: perform update and restart; all other arguments are ignored.
5. If `--install-llama` or `--update-llama`: instantiate `LlamaUpdater` and call the appropriate method; exit on completion.
6. If `--stop-server`: signal `runner.py` to stop `llama-server`; exit on completion.
7. Otherwise: check whether the `./llama-cpp` directory exists.
   - If it **does not exist**, display the following error via `UIManager` (bordered curses window) and exit with a non-zero status code:
```
┌────────────────────────────────────────────────┐
│ llama-cpp not found. Please install it first:  │
│   llama-server-manager --install-llama         │
└────────────────────────────────────────────────┘
```
   - If it **exists**, load `config.json`, merge pass-through args, and invoke `Runner`.

---

## 6. Logging Module (logger.py)

### 6.1 Language & structure

- Written in Python 3.12+.
- All logic must be encapsulated in a class (e.g. `llama_server_manager.logger.LoggerSetup`).
- Never executed directly; instantiated exactly once by `main.py`, immediately after `config.json` has been loaded or auto-generated (Section 5.4, step 3) and before `LlamaUpdater`, `Runner`, or `UIManager` are instantiated.
- Uses Python's standard library `logging` module exclusively; no third-party logging libraries are permitted.

### 6.2 Responsibility

- Reads the `logging` section of `config.json` (Section 3.2) and configures the **root logger** for the lifetime of the process. This is the single place in the codebase where log handlers, formatters, and levels are set up.
- `LoggerSetup` does not create or hold a logger instance that gets passed around to other classes. Every other module (`LlamaUpdater`, `Runner`, `UIManager`, and `main.py` itself) obtains its own logger independently using the standard idiom:

  ```python
  import logging
  logger = logging.getLogger(__name__)
  ```

  Because Python's `logging` module resolves loggers hierarchically by module name, every module-level logger automatically inherits the handler(s), formatter, and level that `LoggerSetup` configured on the root logger — no dependency injection is required, unlike `UIManager`.

### 6.3 Configuration behaviour

- `enabled: false` — no handler is attached to the root logger (or logging is suppressed via `logging.disable(logging.CRITICAL)`); no log record is written anywhere for the duration of the process, regardless of the `file` value.
- `enabled: true` (default):
  - `level` is mapped to the corresponding `logging` constant (`DEBUG`, `INFO`, `WARNING`, `ERROR`) and applied to the root logger.
  - `file` resolution:
    - If `file` is a non-null path, a `logging.FileHandler` is attached at that path.
    - If `file` is `null` (default), a `logging.FileHandler` is attached at the default path `llama-server-manager.log` in the project directory.
  - **Program log output must never be attached to a `StreamHandler` targeting stdout or stderr.** The interactive workflow occupies the terminal via `curses` for effectively the entire runtime of the program (Section 5.1), so writing log records to the terminal outside of `UIManager` would corrupt the display. A file destination is therefore always used whenever logging is enabled — `file: null` selects the default filename rather than stdout.

### 6.4 Formatting

- Log records must include, at minimum, a timestamp, the log level, the originating module/logger name, and the message (e.g. `%(asctime)s [%(levelname)s] %(name)s: %(message)s`).

### 6.5 Relationship to llama-server's own log

- This module is unrelated to `llama-server`'s own output log, which is a separate file controlled via `llama-server.options.log-file` in `config.json` or the `--log-file` CLI flag (Section 3.2, Section 8.4). `logger.py` governs only the manager program's own diagnostic logging.

---

## 7. llama.cpp Update/Download Module (llama_updater.py)

### 7.1 Language & structure

- Written in Python 3.12+.
- All logic must be encapsulated in a class (e.g. `llama_server_manager.updater.LlamaUpdater`).
- Never executed directly; always instantiated by `main.py`.
- All interactive output (menus, prompts, progress bars, confirmations) must be delegated to `UIManager` from `ui_manager.py`.
- Obtains a module-level logger via `logging.getLogger(__name__)` (Section 6) and logs significant events — release resolved, download started/completed, checksum result, errors — at the appropriate level.

### 7.2 GitHub API usage

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

### 7.3 Release selection

#### 7.3.1 Tag selection prompt

Present a numbered menu of release tags (rendered via `UIManager`) fetched from the GitHub Releases API. Option `0` allows the user to type a tag manually; options `1`–`5` are the five most recent release tags. Pressing Enter without a selection installs the most recent release (option `1`). Example:

```
Select a llama.cpp release to install:
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

#### 7.3.2 Asset (zip file) selection prompt

After a release tag is resolved, fetch its asset list from the GitHub API and present all available zip files as a numbered list via `UIManager`. Auto-detect the current platform and architecture using Python's `platform` module and highlight the recommended asset. The recommended option is also the default if the user presses Enter without a selection. Example:

```
Select a zip file to install:
  1) llama-b8800-bin-ubuntu-x64.zip  ← recommended
  2) llama-b8800-bin-win-avx2-x64.zip
  3) llama-b8800-bin-macos-arm64.zip
  4) llama-b8800-bin-macos-x64.zip
  ...
Choice [1]:
```

If auto-detection fails (platform or architecture cannot be determined), no option is highlighted and no default is pre-selected; the user must choose explicitly.

#### 7.3.3 Confirmation prompt

After the user selects a release tag and asset, `UIManager` must render a bordered curses window displaying both selections and prompt for confirmation before downloading anything. This prompt must **not** drop out of the curses environment; it must be rendered entirely through `UIManager` consistent with Section 9.4. Example layout:

```
┌──────────────────────────────────────────────────────────┐
│ Selected release: b8800 (llama-b8800-bin-ubuntu-x64.zip) │
│ Proceed with installation?                               │
│                                                          │
│             ▶ [ Yes ]          [ No  ]                   │
└──────────────────────────────────────────────────────────┘
```

Pressing Enter confirms (default yes). Entering `n` or `Esc` cancels and exits with status code `0` without modifying any files.

### 7.4 Platform & architecture detection

- Auto-detect the current platform (Linux, Windows, macOS) and architecture (`x86_64`, `arm64`, etc.) using Python's `platform` module.
- Use the detected platform/architecture to determine and highlight the recommended asset in the selection list (see Section 7.3.2).
- If detection fails, display all assets without a highlighted recommendation and require the user to select explicitly.

### 7.5 Download & extraction

- Download the selected release archive (`.zip` or `.tar.gz`) using the asset's `browser_download_url`.
- Display a ncurses progress bar (rendered via `UIManager`) during the download so the user can track progress.
- **Checksum verification:** After the download completes, check whether the release provides a checksum file (e.g. `sha256sum.txt` or a similarly named asset). If one is present, download it and verify the archive before proceeding. If verification fails, delete the downloaded archive, display a clear error via `UIManager`, and exit with a non-zero status code.
- If no checksum asset is available for the release, skip verification and proceed directly to extraction.
- Decompress and extract the full archive contents — all binaries and supporting files — into the `./llama-cpp/` folder in the **same directory as the script**.
- If a `./llama-cpp/` folder already exists, delete it entirely before extraction without prompting or creating a backup.
- Ensure `llama-server` (or `llama-server.exe` on Windows) is executable after extraction.
- Remove the downloaded archive file after successful extraction.
- After a successful install, display a success message via `UIManager` and run a quick sanity check by executing `llama-server --version` and displaying its output through `UIManager`. If the sanity check fails, display a warning via `UIManager` but still exit with status code `0` (the binaries were installed; the version check is informational).

### 7.6 Error handling

- Handle `403` and `429` responses from the GitHub API as rate-limit errors; display a clear message via `UIManager` including the `X-RateLimit-Reset` time if present in the response headers.
- If the GitHub API is otherwise unreachable, display a clear error via `UIManager` and exit with a non-zero status.
- If the download fails or the archive is corrupt, clean up any partial files and report the error via `UIManager`.

---

## 8. Run Script (runner.py)

### 8.1 Language & structure

- Written in Python 3.12+.
- All logic must be encapsulated in a class (e.g. `llama_server_manager.runner.Runner`).
- Never executed directly; always instantiated by `main.py`.
- Any user-facing status output must be delegated to `UIManager` from `ui_manager.py`.
- Obtains a module-level logger via `logging.getLogger(__name__)` (Section 6) and logs process launch, PID, and shutdown events.

### 8.2 Configuration loading

- Read `config.json` from the project directory.
- Extract key-value pairs from the `llama-server.options` section and convert them to CLI arguments for `llama-server`.
- Merge any pass-through arguments received from `main.py`, with CLI arguments taking precedence over `config.json` values on conflict.

### 8.3 Process execution

- Launch `./llama-cpp/llama-server` (`./llama-cpp/llama-server.exe` on Windows) with the assembled argument list.
- Record the PID of the launched `llama-server` process.
- Write the PID to `llama-server.pid` in the project directory.
- `main.py` returns control to the shell immediately after launch.

### 8.4 Logging (llama-server output)

This is the log produced by the `llama-server` process itself and is distinct from the manager program's own log described in Section 6.

The log file path is resolved in the following order of precedence:

1. `--log-file` CLI argument
2. `llama-server.options.log-file` in `config.json`
3. Default: `llama-server.log` in the project folder

The resolved path is passed to `llama-server` via its `--log-file` flag.

### 8.5 Graceful shutdown

Shutdown is triggered by either a `SIGINT` / `KeyboardInterrupt` (Ctrl+C) or the `--stop-server` argument passed to `main.py`.

1. Send `SIGTERM` (or the platform equivalent) to the `llama-server` process.
2. Wait up to **60 seconds** for the process to exit cleanly.
3. If the process has not exited after 60 seconds, send `SIGKILL` (`TerminateProcess` on Windows) to forcibly terminate it.
4. Remove the PID file after the process has been stopped.
5. Exit the program with status code `0` on clean shutdown, non-zero if a force-kill was required.

---

## 9. CLI User Interface Module (ui_manager.py)

### 9.1 Language & structure

- Written in Python 3.12+.
- All logic must be encapsulated in a class (e.g. `llama_server_manager.ui.UIManager`).
- Uses Python's standard library `curses` module exclusively; no third-party terminal UI libraries are permitted.
- Never executed directly; always instantiated by `main.py` and passed to other modules that require user interaction.
- Obtains a module-level logger via `logging.getLogger(__name__)` (Section 6), like every other module.

### 9.2 Visual style

- Background: black (`curses.COLOR_BLACK`).
- Foreground text: green (`curses.COLOR_GREEN`).
- All windows and panels must use this colour pair consistently.
- Highlighted / selected items (e.g. the currently focused menu option) must be rendered in reverse video (`curses.A_REVERSE`) using the same green-on-black pair.

### 9.3 Numbered menus

- Render each menu inside a bordered `curses` window.
- Display a title line, then one numbered option per row.
- The currently highlighted option is shown in reverse video; the user navigates with the arrow keys or by typing the option number.
- Pressing Enter confirms the selection; pressing `q` or `Esc` cancels (equivalent to the user entering `n` at a confirmation prompt).
- A default option, where applicable, is indicated by appending `(default)` to the option label.

### 9.4 Confirmation prompts

- Render as a bordered curses window containing a status line (the resolved selection being confirmed) followed by a prompt line: `Proceed? [Y/n]:`.
- `Y` / Enter confirms; `n` / `Esc` cancels.
- Must never drop out of the curses environment; all rendering goes through `UIManager`.

### 9.5 Progress bar

- Render inside a bordered `curses` window with a title line (e.g. the filename being downloaded).
- Display a filled bar that updates in real time as download bytes are received.
- Show current progress as both a percentage and a `downloaded / total` byte count (human-readable, e.g. `12.4 MB / 98.0 MB`).
- If the total size is unknown (no `Content-Length` header), display a spinner animation instead of a filled bar.

### 9.6 Lifecycle

- `UIManager` must initialise the `curses` environment (`curses.initscr`, colour setup, `cbreak`, `noecho`, hidden cursor) on construction and restore the terminal to its original state on destruction or on any unhandled exception, ensuring the terminal is never left in a broken state.
- The `UIManager` instance must remain active and the curses session must remain open for the **entire duration** of the program's interactive workflow — from first menu to final success/error message. The curses session must not be torn down and re-entered mid-workflow; `UIManager` is constructed once and destroyed once.

### 9.7 Logging integration

- Whenever `UIManager` renders an error, warning, or success/informational message to the user, it must also emit a corresponding record to its module logger at a matching level:
  - Error messages → `logger.error(...)`
  - Warning messages → `logger.warning(...)`
  - Success / informational messages → `logger.info(...)`
- Whether a given message is actually persisted depends on the `enabled` and `level` settings configured for the process (Section 3.2, Section 6.3). For example, an informational success message logged at `INFO` will not appear in the log file if `level` is set to `WARNING` or `ERROR`.
- This dual output (curses display + log record) is independent of, and does not replace, the separate `llama-server` output log described in Section 8.4.

---

## 10. Non-Functional Requirements

### 10.1 Cross-platform compatibility

- All Python code must run on Linux and macOS without modification. Windows is supported via WSL only (see Section 5.1.1).
- Path handling must use `pathlib.Path` throughout to avoid OS-specific separator issues.
- Signal handling must use platform-appropriate mechanisms (`SIGTERM`/`SIGKILL` on POSIX; `TerminateProcess` on Windows/WSL).

### 10.2 Dependencies

- Standard library only where possible.
- The `requests` library (or `urllib`) may be used for GitHub API calls and file downloads.
- The `curses` module (standard library) is used for all CLI UI rendering; no third-party terminal UI libraries are permitted.
- The `logging` module (standard library) is used for all program log output; see Section 6. No third-party logging libraries are permitted.
- No third-party dependency should be required for core start/stop/run operations.

### 10.3 Error handling & exit codes

- All external calls (GitHub API, subprocess launches, file I/O) must be wrapped in `try/except` blocks.
- Errors must be logged (according to the logging config) and result in a non-zero exit code.
- The program must never silently swallow exceptions.

### 10.4 Code style

- Follow PEP 8 conventions.
- Each module must include a module-level docstring describing its purpose.
- Each class and public method must include a docstring.

---

## 11. Out of Scope

- Model file management (downloading, converting, or organising GGUF model files).
- A graphical user interface.
- Authentication or access control for `llama-server`.
- Automatic selection of quantisation level or GPU layers.

---

## Revision History

| Version | Date | Author | Notes |
|---|---|---|---|
| 1.0.7 | July 2026 | zero4281 | Added a dedicated Logging Module (`logger.py`, new §6) to clarify where program-logging logic lives. Clarified that all other modules obtain a logger via the standard `logging.getLogger(__name__)` idiom rather than dependency injection. Changed the effective behaviour of `logging.file: null`: program logs now default to `llama-server-manager.log` in the project directory instead of stdout, since stdout/stderr output is prohibited while curses is active (§5.1); `enabled: false` remains the way to disable logging entirely. Fixed the `config.json` example in §3.1, which previously showed a stray `options.logfile` key instead of the documented `logging` section. Added §9.7 requiring `UIManager` to mirror every displayed error/warning/success message to the program log at a matching level. Renumbered former §6–§10 to §7–§11 accordingly. |
| 1.0.6 | July 2026 | zero4281 | Removed §7.4 Daemon mode (the program is not a daemon); moved PID file (`llama-server.pid`) requirement and shell-return behaviour into §7.3 Process execution. Renumbered former §7.5 Logging → §7.4 and former §7.6 Graceful shutdown → §7.5. |
| 1.0.5 | April 2026 | zero4281 | Clarified that the entire interactive workflow must remain within the curses environment after UIManager initialisation; no stdout/stderr output is permitted post-init. Updated confirmation prompts in §5.3.2 and §6.3.3 to show curses bordered window layout. Updated §5.4 llama-cpp-not-found error, §5.3.3 update failure error, §6.5 success/warning messages, and §6.6 API error messages to use UIManager instead of direct print calls. Strengthened §8.4 and §8.6 to require UIManager to remain active for the full workflow duration. |
| 1.0.4 | April 2026 | zero4281 | Added ncurses CLI UI module (`ui_manager.py`, Section 8); all menus, prompts, and progress bars rendered with black background and green text; Windows now requires WSL with runtime detection warning; updated cross-platform and dependency requirements accordingly |
| 1.0.3 | April 2026 | zero4281 | Removed `--foreground` command-line option |
| 1.0.2 | April 2026 | zero4281 | Expanded Section 6 install workflow: interactive release tag + asset selection with auto-detected recommendation, all-assets display, checksum verification, download progress bar, delete-and-replace of existing llama-cpp folder, post-install success message and sanity check |
| 1.0.1 | April 2026 | zero4281 | Added user confirmation and source selection for `--self-update`; added user confirmation prompt to llama.cpp install/update |
| 1.0.0 | April 2026 | zero4281 | Initial draft |