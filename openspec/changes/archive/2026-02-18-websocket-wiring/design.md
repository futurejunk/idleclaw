## Context

Phase 1 established the streaming pipeline with a mock response: browser → Next.js API route → FastAPI SSE → hardcoded text. The server currently returns fake tokens from `_mock_stream()` in `routers/chat.py`. The node agent has a working `ollama_bridge.py` that can list models and stream chat completions from a local Ollama instance, but it runs standalone — nothing connects it to the server.

This change wires the server and node agent together via WebSocket so real Ollama inference flows through the full stack.

## Goals / Non-Goals

**Goals:**
- Node agents connect to the server via WebSocket and register their available models
- Server tracks connected nodes and their health via heartbeats
- Chat requests route to a real node instead of returning mock responses
- Tokens stream from Ollama → node agent → WebSocket → server → SSE → browser
- Single-node operation works reliably (one node agent, one server)

**Non-Goals:**
- Multi-node scoring/load balancing (Phase 4)
- Node agent reconnection with exponential backoff (Phase 4)
- Model selector UI (Phase 3)
- Authentication or authorization
- Persistent state (Redis, database)

## Decisions

### 1. WebSocket message protocol: JSON with `type` field

All WebSocket messages are JSON objects with a `type` field for routing. Defined message types:

**Node → Server:**
- `register`: `{type, node_id, models: [{name, size}], max_concurrent}`
- `heartbeat`: `{type, node_id, active_requests, available}`
- `inference_chunk`: `{type, request_id, token, done}`
- `inference_error`: `{type, request_id, error}`

**Server → Node:**
- `registered`: `{type, node_id}`
- `inference_request`: `{type, request_id, model, messages}`

**Why JSON over binary protocols:** Simplicity, debuggability, matches the rest of the stack. Binary (msgpack, protobuf) is premature optimization for MVP.

### 2. Inference bridging: `asyncio.Queue` per request

When `/api/chat` receives a request:
1. Generate a `request_id` (UUID)
2. Create an `asyncio.Queue` in a shared dict keyed by `request_id`
3. Send `inference_request` to the chosen node's WebSocket
4. Yield from the queue as SSE events (the queue receives chunks from the WebSocket handler)
5. Clean up the queue when done or on error

**Why Queue:** Natural async producer-consumer pattern. The WebSocket handler (producer) and SSE generator (consumer) run in separate coroutines but share the event loop. No threading needed.

### 3. Node registry: in-memory dict with heartbeat eviction

`NodeRegistry` stores connected nodes as a dict keyed by `node_id`:
```
{node_id: NodeInfo(websocket, models, last_heartbeat, active_requests)}
```

Node selection for MVP: find the first node that has the requested model and is available. No scoring algorithm yet — that's Phase 4.

Heartbeat timeout: 45 seconds. A background task checks every 15 seconds and evicts stale nodes (closes their WebSocket).

### 4. WebSocket endpoint on FastAPI directly

Use FastAPI's built-in WebSocket support (`@app.websocket("/ws/node")`) rather than a separate WebSocket server. FastAPI handles the upgrade, and we get the same event loop as the SSE endpoints.

**Why not a separate `websockets` server:** Adds deployment complexity (two ports). FastAPI's WebSocket support wraps Starlette's, which is production-grade. We still add `websockets` as a dependency since uvicorn needs it for WebSocket protocol support.

### 5. Node agent architecture: single async event loop

The node agent runs one `asyncio` event loop with concurrent tasks:
- **WebSocket listener**: receives messages, dispatches `inference_request` to `ollama_bridge`
- **Heartbeat sender**: sends heartbeat every 15 seconds
- **Inference workers**: one per active request, streams from Ollama and sends chunks back

`connection.py` manages the WebSocket lifecycle. `main.py` is the entry point that discovers models, connects, registers, and runs the event loop.

### 6. Fallback to mock when no nodes connected

If no nodes are connected or none have the requested model, the server returns a 503 error with a clear message. The mock response is removed — it served its Phase 1 purpose.

**Why 503 over falling back to mock:** The browser should know when real inference is unavailable. Mixing mock and real responses silently would be confusing.

## Risks / Trade-offs

- **Single point of failure**: If the one connected node disconnects mid-inference, the SSE stream errors out. → Mitigation: clean error propagation to frontend. Resilience (retry, failover) is Phase 4.
- **No backpressure**: If Ollama produces tokens faster than the WebSocket/SSE can consume, the queue grows unbounded. → Mitigation: set a max queue size (1000 items). Unlikely to hit with LLM token rates (~50-100 tokens/sec).
- **No authentication on WebSocket**: Anyone can connect as a node. → Mitigation: acceptable for MVP running on localhost. Phase 5 adds auth for production.
- **Race condition on request cleanup**: The queue dict entry could be accessed after cleanup if timing is unlucky. → Mitigation: use `dict.pop()` for atomic removal, guard queue reads with timeout.
