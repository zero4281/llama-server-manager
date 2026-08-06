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

- Python 3.12+ with `pip` — [Download Python](https://www.python.org/downloads/) (pip is included with Python 3.4+)
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

### Install the Hugging Face CLI for model management:

```bash
pip install hf-cli
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
    }
  },
  "llama-server": {
    "options": {
      "host": "0.0.0.0",
      "port": "11235",
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

### Key options:

| Option | Default | Description |
|---|---|---|
| `host` | `127.0.0.1` | Set to `0.0.0.0` to expose the server on your local network |
| `port` | `8080` | Change if another process is already using port 8080 |
| `models-max` | `1` | Maximum number of models loaded simultaneously — keep at `1` if VRAM is limited |
| `sleep-idle-seconds` | `600` | Unloads the model after this many seconds of inactivity (similar to Ollama's behavior) |

---

## Usage

### Command Reference

| Command | Description |
|---|---|
| `./llama-server-manager` | Start the server |
| `./llama-server-manager [llama-server args]` | Start the server and pass arguments directly to llama-server |
| `./llama-server-manager --install-llama` | Download and install the latest llama.cpp release |
| `./llama-server-manager --update-llama` | Update an existing llama.cpp installation to the latest release |
| `./llama-server-manager --version` | Display the program's version and exit |
| `./llama-server-manager --self-update` | Pull the latest manager code from GitHub and restart |
| `./llama-server-manager --stop-server` | Gracefully stop a running llama-server |

### Command Details

**`[llama-server args]`** — Any additional arguments are passed through directly to `llama-server`, one at a time. Refer to the [llama.cpp server documentation](https://github.com/ggerganov/llama.cpp/blob/master/tools/server/README.md) for the full list of supported arguments.

```bash
./llama-server-manager --some-llama-arg value
```

**`--install-llama`** — Run this once after cloning the repo to download and install llama.cpp. The installer will attempt to detect your OS and hardware, but review each prompt carefully to confirm the correct build for your system. If `llama-server` was already running, it will be restarted after a successful installation.

```bash
./llama-server-manager --install-llama
```

**`--update-llama`** — Updates your existing llama.cpp installation to the latest release. If `options.llama-cpp.os-architecture` and `options.llama-cpp.backend` are present in `config.json`, it will perform a "fast path" update (skipping selection menus). If either is missing, it will fall back to the interactive installation workflow. If `llama-server` was already running, it will be restarted after a successful update.

```bash
./llama-server-manager --update-llama
```

**`--self-update`** — Pulls the latest manager code from the project's GitHub repository and restarts. No prerequisites required.

```bash
./llama-server-manager --self-update
```

**`--stop-server`** — Gracefully stops a running `llama-server` process.

```bash
./llama-server-manager --stop-server
```

---

## Model Management

> **Note:** Built-in model management commands are coming soon to the wrapper.

In the meantime, there are two ways to download models:

### Option 1 — Hugging Face CLI:

```bash
hf download {model-name}
```

### Option 2 — llama-cli (downloads directly into llama.cpp's format):

```bash
llama-cli -hf {model-name}
```

Both methods work well. Use `llama-cli` if you want the model pulled and placed directly in a format ready for `llama-server`.

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

### Development Notes
- **Version Source of Truth**: The `__version__` constant in `main.py` is the source of truth for the `--version` flag.
- **Restart Logic**: The manager uses `llama-server.pid` to track and manage the lifecycle of the `llama-server` process, allowing for graceful shutdowns and automatic restarts after updates.
- **Path Handling**: Uses `pathlib` throughout for cross-platform compatibility.

