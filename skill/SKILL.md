---
name: idleclaw
description: Share your idle Ollama inference with the community, or use community
  inference when your API credits run out.
tools: Bash, Read
metadata: {"clawdbot":{"emoji":"🦀","os":["darwin","linux"],"requires":{"bins":["python3","ollama"]}}}
---

# IdleClaw

A distributed inference network for Ollama. Contributors share idle GPU/CPU capacity, consumers use community compute when their API credits run out.

## Modes

### Contribute — Share your idle inference

Start your machine as an inference node. Your local Ollama models become available to the community.

```bash
cd "$SKILL_DIR" && python scripts/contribute.py
```

This connects to the IdleClaw routing server, registers your available models, and begins accepting inference requests. Press Ctrl+C to stop.

**Requirements:** Ollama must be running with at least one model pulled.

### Consume — Use community inference

Send a chat request to the community network instead of running locally.

```bash
cd "$SKILL_DIR" && python scripts/consume.py --model <model-name> --prompt "<your message>"
```

Streams the response to stdout as tokens arrive.

### Status — Check network health

See how many nodes are online and what models are available.

```bash
cd "$SKILL_DIR" && python scripts/status.py
```

## Configuration

| Variable | Default | Description |
|---|---|---|
| `IDLECLAW_SERVER` | `https://api.idleclaw.com` | Routing server URL |
| `OLLAMA_HOST` | `http://localhost:11434` | Local Ollama endpoint |

## Security

### External Endpoints

This skill contacts the following external endpoints:

1. **IdleClaw Routing Server** (`IDLECLAW_SERVER`, default `https://api.idleclaw.com`)
   - **Contribute mode**: Opens a WebSocket connection to register as an inference node. Sends: node ID, available model names, and inference response tokens. Receives: inference requests (model name + chat messages from consumers).
   - **Consume mode**: Sends HTTP POST to `/api/chat` with model name and chat messages. Receives: streaming token response via SSE.
   - **Status mode**: Sends HTTP GET to `/health` and `/api/models`. Receives: server health info and available model list.

2. **Local Ollama** (`OLLAMA_HOST`, default `http://localhost:11434`)
   - **Contribute mode only**: Calls Ollama's API to list models and run inference. All communication stays on localhost.

### Privacy & Trust Model

**Contribute mode risks:**
- Running contribute mode allows **remote parties to execute arbitrary prompts** on your local Ollama models via the routing server.
- Model outputs (including tool_call results and all response fields) are **streamed back to the routing server** and visible to the server operator and the requesting consumer.
- There is **no authentication or access control** on who can send inference requests to your node — any consumer on the network can use your GPU.
- **Do not run contribute mode on machines with sensitive data or private models.** Consider running in a container or VM for isolation.

**Consume mode risks:**
- Your prompts are sent to the routing server and forwarded to a community contributor's machine for inference. The contributor node operator can see your prompts.
- **Do not send sensitive or private information** through community inference.

**General:**
- No user data is persisted locally or on the server beyond the active session.
- No credentials or API keys are required or stored.
- No telemetry or analytics are collected.
- The default server (`api.idleclaw.com`) is operated by the project maintainers. You can point `IDLECLAW_SERVER` to a self-hosted server you control for greater trust.

### Input Sanitization

- Model names are validated against a strict pattern (alphanumeric, colons, periods, hyphens only).
- Server URLs are validated as HTTP/HTTPS URLs before use.
- No shell commands are constructed from user input — all execution is Python-only.
- No local files are read or accessed — the skill only communicates with Ollama and the routing server.

## Installation

Run the installer to set up Python dependencies:

```bash
cd "$SKILL_DIR" && bash install.sh
```
