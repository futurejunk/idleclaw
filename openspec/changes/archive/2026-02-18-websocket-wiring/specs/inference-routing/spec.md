## ADDED Requirements

### Requirement: Inference request routing
When the server receives a `POST /api/chat` request, it SHALL look up the registry for a connected node that has the requested model. The server SHALL send an `inference_request` message via WebSocket: `{"type": "inference_request", "request_id": "<uuid>", "model": "<model>", "messages": [{"role": "...", "content": "..."}]}`.

#### Scenario: Request routed to available node
- **WHEN** a client sends `POST /api/chat` with `model: "llama3.2:3b"` and a node with that model is connected
- **THEN** the server sends an `inference_request` to that node's WebSocket with a unique request_id and the chat messages

#### Scenario: No node available for requested model
- **WHEN** a client sends `POST /api/chat` with `model: "llama3.2:3b"` and no connected node has that model
- **THEN** the server returns HTTP 503 with `{"detail": "No nodes available with model llama3.2:3b"}`

### Requirement: WebSocket-to-SSE bridge
The server SHALL bridge inference chunks from the WebSocket to the SSE response using an `asyncio.Queue` per request. When the node sends `{"type": "inference_chunk", "request_id": "<id>", "token": "<text>", "done": false}`, the server SHALL yield the token as an SSE event in OpenAI chunk format. When `done` is true, the server SHALL yield `data: [DONE]` and close the stream.

#### Scenario: Tokens stream from node to browser
- **WHEN** a node sends inference_chunk messages with tokens `["Hello", " world", "!"]` followed by a chunk with `done: true`
- **THEN** the SSE response contains three OpenAI-format data events with those tokens, followed by `data: [DONE]`

#### Scenario: Request cleanup after completion
- **WHEN** an inference stream completes (done: true received)
- **THEN** the server removes the request's queue from the shared dict

#### Scenario: Request timeout
- **WHEN** a node does not send any inference_chunk for a request within 60 seconds
- **THEN** the server yields an SSE error event and closes the stream

### Requirement: Node agent inference dispatch
When the node agent receives an `inference_request` message via WebSocket, it SHALL call `ollama_bridge.stream_chat(model, messages)` and send each yielded token back as an `inference_chunk` message. After the stream completes, it SHALL send a final chunk with `done: true`.

#### Scenario: Successful inference
- **WHEN** the node agent receives an inference_request for model `llama3.2:3b` with messages `[{"role": "user", "content": "hi"}]`
- **THEN** it calls ollama_bridge.stream_chat, sends an inference_chunk for each token with `done: false`, and sends a final inference_chunk with `done: true` and an empty token

#### Scenario: Ollama error during inference
- **WHEN** the node agent receives an inference_request but Ollama returns an error (e.g., model not found)
- **THEN** the agent sends `{"type": "inference_error", "request_id": "<id>", "error": "<error message>"}` via WebSocket

### Requirement: Inference error propagation
When the server receives an `inference_error` message for an active request, it SHALL propagate the error to the SSE stream and close it.

#### Scenario: Node reports inference error
- **WHEN** a node sends `{"type": "inference_error", "request_id": "<id>", "error": "model not found"}`
- **THEN** the server yields an SSE error event and closes the stream with an appropriate error status
