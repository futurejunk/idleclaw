## MODIFIED Requirements

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
