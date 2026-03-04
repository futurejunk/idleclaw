# IdleClaw Node Agent

The node agent connects your local [Ollama](https://ollama.com) instance to the IdleClaw network, making your models available to users at [idleclaw.com](https://idleclaw.com).

For architecture and project overview, see the [main README](../README.md).

## Prerequisites

- **Python 3.11+**
- **Ollama** installed and running ([install guide](https://ollama.com/download))
- At least one model pulled (e.g., `ollama pull llama3.2:3b`)

## Setup

```bash
cd node-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Run

```bash
python -m src.main
```

The agent will:
1. Discover your local Ollama models
2. Warm them up (first inference to load into memory)
3. Connect to the IdleClaw server and register
4. Start handling inference requests

## Configuration

Copy `.env.example` to `.env` and adjust as needed:

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama API address |
| `IDLECLAW_SERVER` | `wss://api.idleclaw.com/ws/node` | Server WebSocket endpoint |

For local development, point `IDLECLAW_SERVER` to your local server:

```
IDLECLAW_SERVER=ws://localhost:8000/ws/node
```

## How it works

The agent is a thin relay. It sends your model names to the server, receives inference requests over WebSocket, passes them to Ollama, and streams the responses back. The server handles all prompt construction, tool injection, and capability detection — the agent just forwards traffic.

This means you never need to update the agent when IdleClaw adds new features. Just keep Ollama running with your models.
