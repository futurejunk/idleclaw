## 1. Server Models & Dependencies

- [x] 1.1 Add `websockets` to `server/pyproject.toml` dependencies and sync the venv
- [x] 1.2 Create `server/src/models/node.py` with Pydantic models: `ModelInfo` (name, size), `NodeInfo` (node_id, models, max_concurrent, last_heartbeat, active_requests, websocket reference)

## 2. Node Registry Service

- [x] 2.1 Create `server/src/services/registry.py` with `NodeRegistry` class: `add_node()`, `remove_node()`, `get_node_for_model()`, `update_heartbeat()` methods, backed by an in-memory dict keyed by node_id
- [x] 2.2 Add a background task to `NodeRegistry` that runs every 15 seconds and evicts nodes with no heartbeat for 45 seconds (closes their WebSocket)
- [x] 2.3 Instantiate a global `NodeRegistry` in `server/src/main.py` lifespan (start eviction task on startup, cancel on shutdown)

## 3. WebSocket Node Handler

- [x] 3.1 Create `server/src/ws/node_handler.py` with a FastAPI WebSocket endpoint at `/ws/node` that accepts connections, waits for a `register` message (10s timeout), and adds the node to the registry
- [x] 3.2 Add a message loop in the handler that processes `heartbeat`, `inference_chunk`, and `inference_error` messages, routing chunks/errors to the appropriate request queue
- [x] 3.3 Handle WebSocket disconnect (graceful and unexpected): remove node from registry, send error to any pending request queues for that node
- [x] 3.4 Register the WebSocket endpoint in `server/src/main.py`

## 4. Inference Bridge

- [x] 4.1 Create `server/src/services/node_connection.py` with a shared `request_queues` dict (`request_id` → `asyncio.Queue`) and helper functions: `create_request_queue()`, `remove_request_queue()`, `push_chunk(request_id, data)`
- [x] 4.2 Update `server/src/routers/chat.py`: replace mock streaming with real routing — look up a node via registry, create a request queue, send `inference_request` via WebSocket, yield chunks from the queue as SSE events, clean up on completion
- [x] 4.3 Add 60-second timeout when reading from the request queue; yield an error SSE event and clean up if timeout fires
- [x] 4.4 Return HTTP 503 when no node is available for the requested model

## 5. Node Agent Connection

- [x] 5.1 Add `websockets` to `node-agent/pyproject.toml` dependencies and sync the venv
- [x] 5.2 Create `node-agent/src/connection.py` with an async WebSocket client that connects to the server, sends a `register` message with discovered Ollama models, and waits for `registered` acknowledgment
- [x] 5.3 Add a heartbeat loop in `connection.py` that sends heartbeat messages every 15 seconds with current active_requests count
- [x] 5.4 Add a message listener that receives `inference_request` messages and dispatches them to an inference worker

## 6. Node Agent Inference Worker

- [x] 6.1 Add an inference worker function in `connection.py` that calls `ollama_bridge.stream_chat()`, sends `inference_chunk` messages for each token, and sends a final chunk with `done: true`
- [x] 6.2 Add error handling: if `stream_chat()` raises, send `inference_error` with the error message
- [x] 6.3 Create `node-agent/src/main.py` entry point that discovers models, connects to the server, and runs the WebSocket listener + heartbeat concurrently with `asyncio.gather`

## 7. End-to-End Verification

- [x] 7.1 Start server, start node agent (with Ollama running), send a chat request via curl to `POST /api/chat` and verify real Ollama tokens stream back as SSE
- [x] 7.2 Start frontend, send a message in the browser, confirm real Ollama response streams token-by-token
- [x] 7.3 Verify `POST /api/chat` returns 503 when no node agent is connected
- [x] 7.4 Stop the node agent and verify the server removes it from the registry (check via heartbeat eviction logs)
