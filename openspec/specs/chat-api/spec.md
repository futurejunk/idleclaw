## Requirements

### Requirement: SSE chat streaming endpoint
The server SHALL expose a `POST /api/chat` endpoint that accepts a JSON body with `model` (string) and `messages` (array of `{role, content}` objects) and returns a `text/event-stream` response streaming tokens in OpenAI Chat Completions chunk format.

Each SSE event SHALL be a JSON object with fields: `id` (string), `object` ("chat.completion.chunk"), `model` (string), and `choices` (array with one entry containing `delta.content` and `index`).

The stream SHALL end with a `data: [DONE]` event.

The endpoint SHALL route requests to a connected node agent that has the requested model, streaming real Ollama inference tokens via the WebSocket-to-SSE bridge. If no node is available with the requested model, the endpoint SHALL return HTTP 503.

#### Scenario: Successful streaming response from real node
- **WHEN** a client sends `POST /api/chat` with `{"model": "llama3.2:3b", "messages": [{"role": "user", "content": "hello"}]}` and a node with that model is connected
- **THEN** the server returns status 200 with `Content-Type: text/event-stream` and streams SSE events containing real Ollama inference tokens in OpenAI chunk format, ending with `data: [DONE]`

#### Scenario: No node available
- **WHEN** a client sends `POST /api/chat` with `{"model": "llama3.2:3b", "messages": [...]}` and no node has that model
- **THEN** the server returns status 503 with `{"detail": "No nodes available with model llama3.2:3b"}`

#### Scenario: Missing required fields
- **WHEN** a client sends `POST /api/chat` with an empty body or missing `messages` field
- **THEN** the server returns status 422 with a Pydantic validation error

### Requirement: Health check endpoint
The server SHALL expose a `GET /health` endpoint that returns a JSON object with `status` ("healthy"), `uptime_seconds` (number), and `node_count` (integer count of currently connected nodes in the registry).

#### Scenario: Health check with nodes
- **WHEN** a client sends `GET /health` and 2 nodes are connected
- **THEN** the server returns status 200 with `{"status": "healthy", "uptime_seconds": <number>, "node_count": 2}`

#### Scenario: Health check with no nodes
- **WHEN** a client sends `GET /health` and no nodes are connected
- **THEN** the server returns status 200 with `{"status": "healthy", "uptime_seconds": <number>, "node_count": 0}`

### Requirement: CORS configuration
The server SHALL allow cross-origin requests from `http://localhost:3000` so the frontend can call the API directly during development.

#### Scenario: Preflight CORS request from frontend
- **WHEN** the frontend sends an `OPTIONS` request from `http://localhost:3000` to `/api/chat`
- **THEN** the server responds with `Access-Control-Allow-Origin: http://localhost:3000` and allows `POST` method with `Content-Type` header

### Requirement: Models list endpoint
The server SHALL expose a `GET /api/models` endpoint that aggregates and deduplicates model names from all currently connected nodes in the registry and returns them as a JSON array.

#### Scenario: Models returned from connected nodes
- **WHEN** a client sends `GET /api/models` and connected nodes advertise models `["llama3.2:1b"]` and `["llama3.2:1b", "mistral:7b"]`
- **THEN** the server returns `{"models": ["llama3.2:1b", "mistral:7b"]}` with no duplicates

#### Scenario: Empty registry
- **WHEN** no nodes are connected and a client sends `GET /api/models`
- **THEN** the server returns `{"models": []}`

### Requirement: Pydantic request models
The server SHALL validate incoming chat requests using Pydantic models. The `ChatRequest` model SHALL require `model` (string) and `messages` (list of `ChatMessage`). The `ChatMessage` model SHALL require `role` (string) and `content` (string).

#### Scenario: Valid request passes validation
- **WHEN** a client sends a request with `model` as a string and `messages` as a list of objects each having `role` and `content` strings
- **THEN** the request is accepted and processed

#### Scenario: Invalid message structure rejected
- **WHEN** a client sends a request where a message is missing the `role` field
- **THEN** the server returns status 422 with a validation error describing the missing field
