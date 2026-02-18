## Why

Phase 1 proved the streaming pipeline with a mock response. Now the server needs to route chat requests to real Ollama instances running on community nodes. WebSocket connections let node agents initiate outbound connections (solving NAT traversal) while the server pushes inference requests down the open socket.

## What Changes

- Add a WebSocket endpoint (`ws/node_handler.py`) to the server that accepts node agent connections, handles registration and heartbeat messages
- Add a `NodeRegistry` service that tracks connected nodes, their available models, and health status (heartbeats, eviction after 45s timeout)
- Add a `NodeConnection` service that bridges WebSocket inference chunks to the SSE response via `asyncio.Queue` keyed by request_id
- Replace the mock response in `POST /api/chat` with real routing: pick a connected node with the requested model, send an inference request via WebSocket, stream chunks back as SSE
- Add a WebSocket client to the node agent (`connection.py`) that connects to the server, sends registration with discovered Ollama models, runs a heartbeat loop, and dispatches incoming inference requests to `ollama_bridge`
- Add `websockets` dependency to both server and node-agent

## Capabilities

### New Capabilities
- `node-registration`: WebSocket-based node connection lifecycle — register, heartbeat, eviction, reconnection
- `inference-routing`: End-to-end inference request routing from SSE endpoint through WebSocket to Ollama and back

### Modified Capabilities
- `chat-api`: Replace mock response with real node-routed inference; add "no nodes available" error handling
- `ollama-bridge`: No requirement changes (existing interface is sufficient)

## Impact

- **server/src/routers/chat.py**: Replace mock streaming with node selection + WebSocket forwarding
- **server/src/main.py**: Register WebSocket endpoint, start/stop registry
- **server/pyproject.toml**: Add `websockets` dependency
- **node-agent/src/**: New `connection.py` and `main.py` entry point
- **node-agent/pyproject.toml**: Add `websockets` dependency
- New files: `server/src/ws/node_handler.py`, `server/src/services/registry.py`, `server/src/services/node_connection.py`, `server/src/models/node.py`
