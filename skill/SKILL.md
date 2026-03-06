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

### Data Handling

- **No user data is persisted** locally or on the server beyond the active session.
- **No credentials or API keys** are required or stored.
- **Text-only chat inference** — no file uploads, no code execution, no system access. Only chat messages (text strings) flow through the network.
- **Chat messages** are transmitted from consumer to server to contributor node for inference, then discarded.
- **No telemetry or analytics** are collected.
- In contribute mode, the routing server sends text chat messages to your Ollama instance and the text response is streamed back. Contributors can point `IDLECLAW_SERVER` to a self-hosted instance.
- In consume mode, text prompts are sent to the routing server which routes them to an available contributor node.

### Sanitization

**Client-side:**
- Model names are validated against a strict pattern (alphanumeric, colons, periods, hyphens only).
- Server URLs are validated as HTTP/HTTPS URLs before use.
- No shell commands are constructed from user input — all execution is Python-only.
- No local files are read or accessed — the skill only communicates with Ollama and the routing server.

**Server-side (routing server):**
- IP-based rate limiting on all endpoints: chat (20 RPM), node registration (5 RPM), general (60 RPM).
- Input validation: max 50 messages per request, 10,000 chars per message, 64-char model names, roles restricted to `user` and `assistant`.
- Output sanitization: response content is stripped of markup tags before delivery to consumers.
- Node registration limits: max 3 nodes per IP, max concurrent requests clamped to 1-10.
- Tool execution safeguards: schema validation, argument type checking, 15-second timeout, per-node rate limiting (20 calls/min).
- Server binds to localhost only, accessed through Caddy reverse proxy with auto-TLS.
- Red team tested with documented findings and mitigations ([security assessment on GitHub](https://github.com/futurejunk/idleclaw/tree/main/security)).

## Installation

Run the installer to set up Python dependencies:

```bash
cd "$SKILL_DIR" && bash install.sh
```
