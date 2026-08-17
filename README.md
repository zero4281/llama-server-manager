# Llama CPP Server Manager

![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20WSL-blue)
![Python](https://img.shields.io/badge/python-3.12.3%2B-blue)
![License](https://img.shields.io/badge/license-GPL%20v3.0-green)
![Status](https://img.shields.io/badge/status-active-brightgreen)

A lightweight wrapper around [llama.cpp](https://github.com/ggerganov/llama.cpp)'s `llama-server` that simplifies installation, configuration, and lifecycle management of a local LLM inference server. It supports OpenAI-compatible REST API endpoints, making it easy to drop into existing tooling and workflows.

---

## Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Install Llama CPP](#install-llama-cpp)
- [Configuration](#configuration)
- [Usage](#usage)
- [Model Management](#model-management)
- [Starting the Server](#starting-the-server)
- [Stopping the Server](#stopping-the-server)
- [API Usage](#api-usage)

---

## Requirements

- Python 3.12.3 with `pip` — [Download Python](https://www.python.org/downloads/) (pip is included with Python 3.4+)
- Linux, MacOS, or Windows (WSL)

---

## Installation

Create and activate a Python virtual environment before installing dependencies.

### Create the environment:

#### Linux / MacOS / WSL
```bash
python3 -m venv .venv
```

#### Windows (native)
```bash
python -m venv .venv
```

### Activate the environment:

#### Linux / MacOS / WSL
```bash
source .venv/bin/activate
```

#### Windows (native)
```bash
.venv\Scripts\activate
```

### Install the project dependencies:

```bash
pip install -r requirements.txt
```

Model management (search, download, list, and delete) is built into the wrapper itself and uses the `huggingface_hub` library, which is already included in `requirements.txt` — no separate install is required. If you'd also like to use the standalone `hf` CLI tool alongside the wrapper (e.g. for other Hugging Face workflows), it reads from the same local cache, so the two stay in sync:

```bash
pip install -U "huggingface_hub[cli]"
```

---

## Install Llama CPP

Run the install command to download and set up `llama.cpp`:

```bash
./llama-server-manager --install-llama
```

This will walk you through an interactive menu to install llama.cpp. The script attempts to detect your OS and hardware automatically — review each option carefully to make sure the correct build is selected for your system.

Once installation completes, a `llama-cpp/` folder will appear in your install directory and you're ready to run the server.

---

## Configuration

On first run, the wrapper generates a `config.json` with safe defaults. You can customize it to pass additional options directly to `llama-server`.

### Example `config.json`:

```json
{
  "options": {
    "llama-cpp": {
      "os-architecture": "ubuntu/x64",
      "backend": "vulkan"
    },
    "huggingface": {
      "token": null,
      "cache-dir": null
    }
  },
  "llama-server": {
    "options": {
      "host": "0.0.0.0",
      "port": "11235",
      "models-dir": "/home/user/.cache/huggingface/hub",
      "models-max": "1",
      "sleep-idle-seconds": 600
    }
  },
  "logging": {
    "enabled": true,
    "level": "INFO",
    "file": null
  }
}
```

> `llama-server.options` keys always use `llama-server`'s **long-form** flag names (e.g. `models-dir`, not `-m`) so it's unambiguous which CLI argument each key maps to.

### Key options:

| Option | Default | Description |
|---|---|---|
| `host` | `127.0.0.1` | Set to `0.0.0.0` to expose the server on your local network |
| `port` | *(llama.cpp default)* | Set to override the port llama-server listens on |
| `models-dir` | *(unset)* | Directory `llama-server` scans for GGUF models. Point this at your Hugging Face cache (default `~/.cache/huggingface/hub`, or your `options.huggingface.cache-dir` if you've overridden it) to pick up models downloaded via [Model Management](#model-management). |
| `models-max` | `1` | Maximum number of models loaded simultaneously — keep at `1` if VRAM is limited |
| `sleep-idle-seconds` | `600` | Unloads the model after this many seconds of inactivity (similar to Ollama's behavior) |

The `options.huggingface` block controls model management specifically — see [Model Management](#model-management) for details on `token` and `cache-dir`.

---

## Usage

### Command Reference

| Command | Description |
|---|---|
| `./llama-server-manager` | Start the server |
| `./llama-server-manager --install-llama` | Download and install the latest llama.cpp release |
| `./llama-server-manager --update-llama` | Update an existing llama.cpp installation to the latest release |
| `./llama-server-manager --version` | Display the program's version and exit |
| `./llama-server-manager --self-update` | Pull the latest manager code from GitHub |
| `./llama-server-manager --stop-server` | Gracefully stop a running llama-server |
| `./llama-server-manager --log-file <path>` | Override the llama-server output log path for this run |
| `./llama-server-manager --models` | Open the Model Manager menu (search, download, list, delete) |
| `./llama-server-manager --search-models [query]` | Search the Hugging Face Hub for models |
| `./llama-server-manager --download-model [repo-id]` | Download a specific GGUF file from a model repo |
| `./llama-server-manager --list-models` | List models currently downloaded to the local cache |
| `./llama-server-manager --delete-model [repo-id]` | Delete a downloaded model from the local cache |
| `./llama-server-manager --hf-token <token>` | Set a Hugging Face access token, for gated/private repos |
| `./llama-server-manager --hf-cache-dir <path>` | Override the local Hugging Face cache directory |

### Command Details

`llama-server` launch arguments are configured entirely through `config.json` (see [Configuration](#configuration)) — the wrapper does not accept arbitrary pass-through arguments on the command line.

**`--install-llama`** — Run this once after cloning the repo to download and install llama.cpp. The installer will attempt to detect your OS and hardware, but review each prompt carefully to confirm the correct build for your system. If `llama-server` was already running, it will be restarted after a successful installation.

```bash
./llama-server-manager --install-llama
```

**`--update-llama`** — Updates your existing llama.cpp installation to the latest release. If `options.llama-cpp.os-architecture` and `options.llama-cpp.backend` are present in `config.json`, it will perform a "fast path" update (skipping selection menus). If either is missing, it will fall back to the interactive installation workflow. If `llama-server` was already running, it will be restarted after a successful update.

```bash
./llama-server-manager --update-llama
```

**`--self-update`** — Pulls the latest manager code from the project's GitHub repository. After a successful update the program exits — it does **not** restart itself — so run `./llama-server-manager` again to use the updated version. No prerequisites required.

```bash
./llama-server-manager --self-update
```

**`--stop-server`** — Gracefully stops a running `llama-server` process.

```bash
./llama-server-manager --stop-server
```

**`--log-file`** — Overrides the path used for `llama-server`'s own output log for this run, taking precedence over the `log-file` value in `config.json`. If neither is set, it defaults to `llama-server.log` in the project folder.

```bash
./llama-server-manager --log-file /path/to/llama-server.log
```

**`--models`, `--search-models`, `--download-model`, `--list-models`, `--delete-model`, `--hf-token`, `--hf-cache-dir`** — Model management. See [Model Management](#model-management) below for details.

---

## Model Management

The wrapper can search, download, list, and delete GGUF models from the Hugging Face Hub directly — no separate tool required. All five commands take an optional argument; if you omit it, you'll get an interactive prompt or menu instead.

Downloaded files are stored in the **standard Hugging Face Hub cache** (`~/.cache/huggingface/hub` by default), not a project-local folder. This means model management here supplements the `hf` CLI tool rather than replacing it — files downloaded one way are visible to the other, and vice versa.

### Open the Model Manager menu

```bash
./llama-server-manager --models
```

This opens an interactive menu with access to Search, Download, List, and Delete.

### Search

```bash
./llama-server-manager --search-models "qwen coder"
```

Omit the query to be prompted for one interactively.

### Download

```bash
./llama-server-manager --download-model TheBloke/example-model-GGUF
```

You'll be shown a list of the repo's `.gguf` files (with sizes) to choose from, then asked to confirm before downloading — only the single file you pick is downloaded, never the whole repo. Omit the repo ID to search first.

### List downloaded models

```bash
./llama-server-manager --list-models
```

Always reflects what's actually in the cache right now, including anything you or the `hf` CLI downloaded outside this program.

### Delete a downloaded model

```bash
./llama-server-manager --delete-model TheBloke/example-model-GGUF
```

Asks for confirmation, then removes the file from the local cache. Omit the repo ID to pick from a list of everything currently downloaded.

### Gated or private repos

If a model requires a Hugging Face access token, provide one with `--hf-token`. It's saved to `config.json` automatically the first time you use it, so you only need to pass it once:

```bash
./llama-server-manager --hf-token hf_xxxxxxxxxxxx --download-model some-org/gated-model
```

### Using a custom cache location

By default, models go into the standard Hugging Face cache. To use a different directory (e.g. a larger disk), pass `--hf-cache-dir` once — it's saved to `config.json`, and `llama-server.options.models-dir` is updated to match automatically so `llama-server` keeps scanning the right place:

```bash
./llama-server-manager --hf-cache-dir /mnt/big-disk/hf-cache
```

### Pointing `llama-server` at your models

`llama-server` loads models from whatever directory is set in `llama-server.options.models-dir` in `config.json` (see [Configuration](#configuration)). If you're using the default Hugging Face cache location and haven't set `--hf-cache-dir`, set `models-dir` to that path yourself once so `llama-server` can find your downloads:

```json
"models-dir": "/home/user/.cache/huggingface/hub"
```

### Alternative: `hf` CLI or `llama-cli`

Since everything lives in the standard cache, you can still use the Hugging Face CLI or `llama-cli` directly if you prefer:

```bash
hf download {model-name}
# or
llama-cli -hf {model-name}
```

---

## Starting the Server

```bash
./llama-server-manager
```

This starts `llama-server` as a background process. Output is streamed to your terminal, but you can safely close the terminal window — the server will continue running.

---

## Stopping the Server

```bash
./llama-server-manager --stop-server
```

This cleanly stops the `llama-server` process.

---

## API Usage

`llama-server` exposes an OpenAI-compatible REST API, so you can use it as a drop-in replacement with any OpenAI SDK or client.

**Chat Completions:**

```bash
curl http://localhost:11235/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "your-model-name",
    "messages": [
      { "role": "user", "content": "Hello!" }
    ]
  }'
```

**Using the OpenAI Python SDK:**

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:11235/v1",
    api_key="not-needed"  # llama-server does not require an API key
)

response = client.chat.completions.create(
    model="your-model-name",
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.choices[0].message.content)
```

> Update `base_url` to match the `host` and `port` values in your `config.json`.

---

**Read My Article About This Journey**

[I Built a Local AI Coding Assistant on Consumer Hardware…and It Works. I think.](https://joshrising.com/i-built-a-local-ai-coding-assistant-on-consumer-hardware-and-it-works-i-think/)

---

## Testing & Development

### Testing Strategy
- All automated tests live in the `Tests/` directory.
- The test suite uses **mocked curses**, ensuring that tests run cleanly in any environment, including CI/CD pipelines.
- For manual verification against a real terminal, see `Testing Strategy.md`.
- `Requirements.md` and `Testing Strategy.md` are written to be compatible with the `sdlc-skills` repository (https://github.com/zero4281/sdlc-skills).

### Development Notes
- **Version Source of Truth**: The `__version__` constant in `main.py` is the source of truth for the `--version` flag.
- **Restart Logic**: The manager uses `llama-server.pid` to track and manage the lifecycle of the `llama-server` process, allowing for graceful shutdowns and automatic restarts after updates.
- **Path Handling**: Uses `pathlib` throughout for cross-platform compatibility.
- **Model Storage**: Model management is built on the `huggingface_hub` library and reads/writes only the standard Hugging Face Hub cache — never a project-local models directory — so it stays interoperable with the `hf` CLI and other `huggingface_hub`-based tooling.