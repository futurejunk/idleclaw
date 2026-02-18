# IdleClaw: Implementation Plan

## Context

Build a ChatGPT alternative where user messages route to idle community OpenClaw/Ollama nodes instead of big tech servers. Distributed as an OpenClaw skill on ClawHub (200K+ users with Ollama already configured). The skill serves dual roles: contributors share idle inference capacity, consumers use it when API credits run out.

The system has four deliverables: a web chat frontend, a routing server, a node agent, and an OpenClaw skill package for ClawHub distribution.

---

## Architecture Overview

```
[Browser Chat UI]  --SSE-->  [Routing Server]  --WebSocket-->  [Node Agent]  --HTTP-->  [Ollama]
     Next.js                  Python/FastAPI                    Python script            localhost:11434
                                    |
                              Node Registry
                              (in-memory, MVP)
```

- **Frontend -> Server**: SSE (OpenAI-compatible streaming format). Standard for LLM chat, works with Vercel AI SDK `useChat` hook.
- **Server -> Node Agent**: WebSocket. Node initiates outbound connection (solves NAT traversal — no port forwarding needed). Server pushes inference requests down the open socket.
- **Node Agent -> Ollama**: `ollama` Python SDK, async streaming.

---

## Project Structure

```
idleclaw/
  docs/                                    # Existing research doc
  frontend/                                # Next.js 15 chat app
    src/app/
      page.tsx                             # Main chat page (useChat hook)
      layout.tsx                           # Root layout
      globals.css                          # Tailwind styles
    src/components/
      chat/
        chat-container.tsx                 # Core chat component
        message-list.tsx                   # Scrollable message history
        message-bubble.tsx                 # User/assistant message rendering
        chat-input.tsx                     # Text input + send button
      layout/
        header.tsx                         # Top bar with model selector + status
        model-selector.tsx                 # Available models dropdown
        connection-status.tsx              # Network health indicator
    src/lib/
      types.ts                             # Shared types
  server/                                  # FastAPI routing server
    pyproject.toml
    src/
      main.py                              # App entry, CORS, lifespan
      config.py                            # pydantic-settings config
      models/
        node.py                            # NodeInfo, NodeStatus, ModelInfo
        chat.py                            # ChatRequest, ChatMessage, ChatChunk
      routers/
        chat.py                            # POST /api/chat (SSE streaming)
        nodes.py                           # GET /api/models, GET /api/nodes
        health.py                          # GET /health
      services/
        registry.py                        # NodeRegistry: track nodes, models, health
        router.py                          # RequestRouter: pick best node, score
        node_connection.py                 # Bridge WebSocket <-> SSE via asyncio.Queue
      ws/
        node_handler.py                    # WebSocket endpoint for node agents
  node-agent/                              # Lightweight Python agent
    pyproject.toml
    src/
      main.py                              # Entry: connect, register, listen
      config.py                            # Env-based config
      ollama_bridge.py                     # Wraps ollama AsyncClient
      connection.py                        # WebSocket client + reconnection
      rate_limiter.py                      # Token bucket rate limiter
  skill/                                   # OpenClaw skill for ClawHub
    SKILL.md                               # Skill definition (YAML frontmatter + instructions)
    scripts/
      contribute.py                        # Start node agent (contributor mode)
      consume.py                           # Route to community nodes (consumer mode)
      status.py                            # Check network status
    install.sh                             # Dependency installer
```

---

## Data Flow

### User sends a chat message:
1. Browser POSTs to `/api/chat` with `{model, messages}`, accepts SSE stream
2. Server looks up `NodeRegistry` for a node running the requested model
3. Server sends `inference_request` to the node via its open WebSocket
4. Node agent calls `ollama.chat(stream=True)` on local Ollama
5. Ollama streams tokens back to node agent
6. Node agent sends `inference_chunk` messages back via WebSocket
7. Server yields each chunk as an SSE event (OpenAI format) to the browser
8. Browser renders tokens in real-time via `useChat` hook

### Node registration:
1. Node agent starts, discovers local Ollama models via `ollama.list()`
2. Opens WebSocket to `ws://server/ws/node`
3. Sends `register` message: `{node_id, models[], max_concurrent, rate_limit}`
4. Server stores in `NodeRegistry`, acknowledges
5. Node sends heartbeat every 15s: `{load, active_requests, available}`
6. Server evicts nodes with no heartbeat for 45s

---

## WebSocket Protocol (Server <-> Node Agent)

**Node -> Server:**
- `register` — node_id, models list, capacity
- `heartbeat` — load, active_requests, availability
- `inference_chunk` — request_id, token, done flag
- `inference_error` — request_id, error message

**Server -> Node:**
- `registered` — acknowledgment
- `inference_request` — request_id, model, messages, options
- `cancel_request` — request_id

---

## OpenClaw Skill (ClawHub Distribution)

### SKILL.md structure:
```yaml
---
name: idleclaw
description: Share your idle Ollama inference with the community, or use community
  inference when your API credits run out.
tools: Bash, Read
metadata: {"clawdbot":{"emoji":"🦀","os":["darwin","linux"],"requires":{"bins":["python3","ollama"]}}}
---
```

The skill body instructs the OpenClaw agent how to:
- **Contribute**: Run `python scripts/contribute.py` to register as an inference node
- **Consume**: Run `python scripts/consume.py` to route queries to community nodes
- **Status**: Run `python scripts/status.py` to check network health

### ClawHub Publishing Requirements:
- VirusTotal clean scan (SHA-256 hash checked, Code Insight verdict: benign)
- Identity verified (GitHub account, 1+ week old)
- No hardcoded credentials, no code obfuscation
- Transparent documentation of external endpoints contacted
- Security model explanation in SKILL.md
- Target the Verified badge (3-5 day review)

---

## Monetization Strategy

**Freemium model. No crypto/bitcoin.**

### Free Tier (MVP — build now)
- All access is free. No accounts required.
- Contributors share compute voluntarily, get nothing in return.
- Consumers use the network at no cost.
- Purpose: grow the network, prove the concept, build trust.

### Pro Tier (Future)
- **Users pay for**: access to higher-tier models (14B+, 70B on Mac Studios), priority routing (skip queue when network is busy), higher rate limits, conversation history/persistence.
- **Contributors earn a share**: revenue split based on uptime in the network and number of requests served. Contributors with better hardware, higher uptime, and more requests served earn more.
- **IdleClaw takes a cut**: platform fee as the middleman operating the routing infrastructure.
- Payment via standard methods (Stripe, credit card). No tokens, no wallets, no crypto.

### What this means for MVP architecture:
- The server already tracks node uptime (heartbeats) and request counts — these become the basis for future contributor payouts. No extra work needed now, just ensure the data is captured.
- User accounts and billing are deferred entirely. No auth in MVP.
- The routing `score` algorithm already supports priority weighting — pro users would get a boost factor later.

---

## Key Technical Decisions

| Decision | Choice | Reason |
|---|---|---|
| Frontend streaming | SSE (not WebSocket) | Industry standard for LLM chat. Vercel AI SDK consumes it natively. Simpler than WebSocket for request-response streaming. |
| Node connection | WebSocket | Bidirectional needed. Node initiates connection (NAT traversal). Server pushes requests to node. |
| Response format | OpenAI-compatible chunks | Works with Vercel AI SDK `useChat`. Any OpenAI client can connect. Future mobile apps use existing SDKs. |
| Backend language | Python/FastAPI | First-class Ollama SDK. Native async. Pydantic models. Fast to prototype. |
| State management | In-memory dicts | MVP simplicity. Move to Redis for production. |
| Node selection | Score: `(1-load) * w1 + (1/latency) * w2 + model_match` | Simple, extensible. Picks lowest-load node with the requested model. |

---

## Implementation Order

### Phase 1: End-to-End Proof of Life
Goal: One token streaming from Ollama to browser.

1. **Server skeleton** — FastAPI app with CORS, a hardcoded `/api/chat` SSE endpoint that streams fake "Hello world" tokens in OpenAI format. Pydantic models for ChatRequest/ChatMessage.
2. **Frontend skeleton** — Next.js + Tailwind + Vercel AI SDK. Minimal `page.tsx` with `useChat` pointed at server. Verify streaming renders.
3. **Node agent skeleton** — `ollama_bridge.py` that lists models and streams chat from local Ollama. Test standalone (print to stdout).

### Phase 2: WebSocket Wiring
Goal: Real inference flowing through the full stack.

4. **Server WebSocket endpoint** — `ws/node_handler.py` accepts node connections, parses register/heartbeat. `services/registry.py` stores node state.
5. **Node agent WebSocket client** — `connection.py` connects to server, sends register with model info, starts heartbeat loop.
6. **Wire inference end-to-end** — `services/node_connection.py` bridges WebSocket chunks to SSE via `asyncio.Queue` keyed by request_id. `routers/chat.py` picks a node, sends request, yields chunks as SSE. Node agent dispatches `inference_request` to `ollama_bridge`, streams chunks back.

### Phase 3: Polished Chat UI
Goal: Clean, usable interface.

7. **Chat components** — `message-list`, `message-bubble`, `chat-input` with Tailwind styling. Markdown rendering (`react-markdown`). Auto-scroll. Typing indicator.
8. **Model selector** — `GET /api/models` aggregates models from connected nodes. Dropdown in header.
9. **Connection status** — Polls `GET /health`, shows node count + status indicator.

### Phase 4: Robustness
Goal: Handle real-world failure modes.

10. **Node agent resilience** — WebSocket reconnection with exponential backoff. Graceful Ollama unavailability. Rate limiter.
11. **Server resilience** — Heartbeat eviction (45s timeout). Node disconnect mid-inference (error to frontend). Request timeout (60s).
12. **Multi-node routing** — Scoring algorithm in `services/router.py`. Test with 2+ nodes running different models.

### Phase 5: OpenClaw Skill + ClawHub
Goal: Distributable skill package.

13. **Write SKILL.md** — Frontmatter with metadata gates (`requires.bins: python3, ollama`). Contributor and consumer mode instructions.
14. **Skill scripts** — `contribute.py` (wraps node-agent), `consume.py` (wraps consumer mode), `status.py` (network health check).
15. **Security hardening** — Input sanitization in scripts, `set -euo pipefail` in shell scripts, document all external endpoints, security model explanation.
16. **Publish to ClawHub** — `clawhub publish`, pass VirusTotal scan, submit for Verified badge.

---

## Dependencies

### Frontend
- `next` ^15, `react` ^19, `ai` ^6 (Vercel AI SDK), `@ai-sdk/openai` ^1
- `tailwindcss` ^4, `react-markdown` ^9, `lucide-react`

### Server
- `fastapi`, `uvicorn[standard]`, `sse-starlette`, `pydantic`, `pydantic-settings`, `websockets`

### Node Agent
- `ollama`, `websockets`, `pydantic`, `pydantic-settings`, `python-dotenv`

---

## Verification

1. **Unit**: Start server, start node-agent pointing at local Ollama, open frontend — send a message, verify streaming response appears
2. **Multi-node**: Start 2 node agents with different models, verify model selector shows both, verify requests route correctly
3. **Failure**: Kill a node agent mid-inference, verify frontend shows error gracefully
4. **Reconnect**: Kill and restart node agent, verify it re-registers and accepts new requests
5. **Skill**: Install SKILL.md locally in `~/.openclaw/skills/idleclaw/`, verify `/idleclaw contribute` and `/idleclaw status` work
