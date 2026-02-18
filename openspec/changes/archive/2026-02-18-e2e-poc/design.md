## Context

IdleClaw is a greenfield project. There is no existing code — only a research document and an implementation plan. This design covers Phase 1: getting three independent layers (server, frontend, node agent) working so each can be tested before wiring them together.

The three layers communicate via two protocols: SSE (frontend ← server) and the Ollama HTTP API (node agent → Ollama). In Phase 1, the server returns a mock streaming response — the real WebSocket wiring between server and node agent comes in Phase 2.

## Goals / Non-Goals

**Goals:**
- Stand up a FastAPI server that streams a mock chat response as SSE in OpenAI-compatible format
- Stand up a Next.js frontend that renders the streaming response in a chat UI
- Stand up a node agent script that can query local Ollama and stream a chat completion to stdout
- Each layer runs and is testable independently
- Establish the project structure, dependency management, and dev workflow for all three components

**Non-Goals:**
- No WebSocket connection between server and node agent (Phase 2)
- No real inference routing through the server (Phase 2)
- No multi-node support, health checks, or heartbeats (Phase 2/4)
- No authentication, accounts, or billing
- No OpenClaw skill packaging (Phase 5)
- No production deployment, Docker, or CI/CD

## Decisions

### 1. SSE with OpenAI-compatible chunk format for chat streaming

The server's `/api/chat` endpoint returns `text/event-stream` with chunks matching the OpenAI Chat Completions streaming format:

```
data: {"id":"chatcmpl-xxx","object":"chat.completion.chunk","choices":[{"delta":{"content":"token"},"index":0}]}

data: [DONE]
```

**Why over custom format:** The Vercel AI SDK `useChat` hook consumes this natively via the `openai` provider. Any OpenAI-compatible client (curl, Python openai SDK, mobile apps) can also connect without an adapter. This avoids building and maintaining a custom streaming parser.

**Why over WebSocket for frontend:** SSE is simpler for this use case (unidirectional server-to-client streaming). The user's message goes as a regular POST body, tokens stream back via SSE. Every major LLM chat product (ChatGPT, Claude) uses this pattern. WebSocket would add connection lifecycle complexity with no benefit here.

### 2. Python/FastAPI for the server

**Why over Node.js:** The `ollama` Python SDK is first-class and well-maintained. FastAPI has native async, Pydantic models for request validation, and `sse-starlette` for SSE responses. When we wire the node agent in Phase 2, both server and agent share the same language and models.

**Why over Go:** Faster to prototype. The bottleneck is Ollama inference latency (seconds), not server throughput. Go's concurrency advantages don't matter at MVP scale.

### 3. Next.js 15 + Vercel AI SDK for the frontend

**Why Vercel AI SDK:** The `useChat` hook handles SSE parsing, message state management, loading indicators, error states, and abort/cancel — all out of the box. Without it, we'd write ~200 lines of SSE parsing and state management boilerplate.

**Why Next.js over plain React:** App Router gives us API route proxying (`/app/api/chat/route.ts`) to avoid CORS issues if server and frontend run on different origins. Also sets up the project for SSR and future features cleanly.

### 4. Mock response in server for Phase 1

The server's `/api/chat` endpoint streams a hardcoded response word-by-word with a small delay between tokens. This lets us develop and test the frontend without needing Ollama running.

**Why not wire Ollama directly in Phase 1:** Separating concerns. If streaming breaks, we need to know whether the problem is in SSE formatting, frontend parsing, or Ollama integration. The mock isolates the first two.

### 5. Standalone node agent tested via stdout

The node agent's `ollama_bridge.py` is tested as a standalone script that streams tokens to stdout. No server connection yet.

**Why:** Validates that the Ollama SDK integration works, the async streaming loop is correct, and models can be discovered — all without the WebSocket complexity of Phase 2.

### 6. Monorepo with `server/`, `frontend/`, `node-agent/` directories

Each component has its own dependency management (`pyproject.toml` for Python, `package.json` for Node.js) but lives in one repo.

**Why monorepo over separate repos:** At this stage, everything changes together. A single repo makes it easier to keep the API contract, types, and documentation in sync. Can split later if needed.

### 7. uv for Python dependency management

Use `uv` instead of pip/poetry for the Python components. It's fast, handles virtual environments automatically, and supports `pyproject.toml` natively.

**Why over pip:** Lock files, reproducible installs, faster resolution. Why over poetry: simpler, faster, less configuration.

## Risks / Trade-offs

**Mock response masks real streaming issues** → Mitigated by keeping the mock format identical to what Ollama produces (same chunk structure, similar token sizes, realistic delays of ~50ms between tokens). Phase 2 replaces mock with real Ollama output through the same SSE pipe.

**Vercel AI SDK version churn** → The `ai` package moves fast. Pin to `^6.x` and use the `openai`-compatible provider which is the most stable integration path.

**Three separate dev processes to run** → For Phase 1 this is fine (each is tested independently). Phase 2 will benefit from a root-level script or Makefile to start all three.

**CORS between frontend (port 3000) and server (port 8000)** → FastAPI CORS middleware configured to allow `localhost:3000` in development. Alternatively, the Next.js API route proxy eliminates the issue entirely.
