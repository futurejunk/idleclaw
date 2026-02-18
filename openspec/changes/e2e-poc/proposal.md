## Why

There is no working prototype yet. Before building robustness, multi-node routing, or the OpenClaw skill, we need to prove the core data flow works end-to-end: a user types a message in a browser, it routes through a central server to a node running Ollama, and the response streams back token-by-token. This is the foundation everything else builds on.

## What Changes

- Add a FastAPI routing server with a `/api/chat` SSE endpoint that streams responses in OpenAI-compatible format, and a `/health` endpoint.
- Add a Next.js frontend with a chat interface using Vercel AI SDK's `useChat` hook to consume the SSE stream.
- Add a standalone node agent script that connects to a local Ollama instance, lists available models, and streams chat completions.
- For Phase 1, the server returns a hardcoded/mock streaming response. The node agent is tested standalone (prints to stdout). The frontend consumes the server's SSE stream. This proves each layer works independently before wiring them together in Phase 2.

## Capabilities

### New Capabilities
- `chat-api`: FastAPI server with SSE streaming `/api/chat` endpoint (OpenAI-compatible format), `/health` endpoint, CORS config, and Pydantic request/response models.
- `chat-frontend`: Next.js chat UI with Vercel AI SDK `useChat` hook, message list, input box, and streaming response rendering.
- `ollama-bridge`: Python module wrapping the `ollama` AsyncClient to list local models and stream chat completions.

### Modified Capabilities
<!-- None — greenfield project, no existing specs. -->

## Impact

- **New directories**: `server/`, `frontend/`, `node-agent/` at project root.
- **Dependencies**: Python (fastapi, uvicorn, sse-starlette, pydantic, ollama, websockets), Node.js (next, react, ai, tailwindcss).
- **Ports**: Server on `localhost:8000`, frontend on `localhost:3000`, Ollama assumed at `localhost:11434`.
- **No external services**: Everything runs locally for Phase 1. No databases, no auth, no cloud.
