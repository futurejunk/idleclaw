## 1. Server Setup

- [x] 1.1 Create `server/` directory with `pyproject.toml` declaring dependencies: fastapi, uvicorn[standard], sse-starlette, pydantic
- [x] 1.2 Create `server/src/models/chat.py` with Pydantic models: `ChatMessage` (role, content) and `ChatRequest` (model, messages)
- [x] 1.3 Create `server/src/config.py` with server settings (host, port, allowed CORS origins)
- [x] 1.4 Create `server/src/main.py` with FastAPI app, CORS middleware allowing `localhost:3000`, and startup timestamp for uptime tracking

## 2. Server Endpoints

- [x] 2.1 Create `server/src/routers/health.py` with `GET /health` returning `{"status": "healthy", "uptime_seconds": N}`
- [x] 2.2 Create `server/src/routers/chat.py` with `POST /api/chat` that accepts `ChatRequest`, streams a hardcoded mock response word-by-word (~50ms delay) as SSE events in OpenAI chunk format, ending with `data: [DONE]`
- [x] 2.3 Register both routers in `main.py` and verify server starts with `uv run uvicorn server.src.main:app --reload`
- [x] 2.4 Test with curl: `POST /api/chat` returns streaming SSE chunks; `GET /health` returns JSON; empty body returns 422

## 3. Node Agent Setup

- [x] 3.1 Create `node-agent/` directory with `pyproject.toml` declaring dependencies: ollama, python-dotenv
- [x] 3.2 Create `node-agent/src/config.py` reading `OLLAMA_HOST` from environment, defaulting to `http://localhost:11434`
- [x] 3.3 Create `node-agent/src/ollama_bridge.py` with async `list_models()` function using `ollama.AsyncClient` that returns model names and sizes
- [x] 3.4 Add async `stream_chat(model, messages)` function that yields token strings from `ollama.AsyncClient.chat(stream=True)`
- [x] 3.5 Add `__main__` block that lists models, picks the first, sends a test message, and prints streamed tokens to stdout
- [x] 3.6 Test standalone: `uv run python node-agent/src/ollama_bridge.py` lists models and streams a response

## 4. Frontend Setup

- [x] 4.1 Scaffold `frontend/` with `npx create-next-app@latest` (App Router, TypeScript, Tailwind, no src/ prefix — use `src/`)
- [x] 4.2 Install Vercel AI SDK: `ai` and `@ai-sdk/openai`
- [x] 4.3 Create `frontend/src/lib/types.ts` with shared TypeScript types

## 5. Frontend Chat UI

- [x] 5.1 Create `frontend/src/components/chat/chat-input.tsx` — text input with send button, submits on Enter or click, prevents empty sends
- [x] 5.2 Create `frontend/src/components/chat/message-bubble.tsx` — renders a single message, visually distinct for user vs assistant roles
- [x] 5.3 Create `frontend/src/components/chat/message-list.tsx` — scrollable list of message bubbles, auto-scrolls to bottom on new content
- [x] 5.4 Create `frontend/src/components/chat/chat-container.tsx` — uses Vercel AI SDK `useChat` hook pointed at `http://localhost:8000/api/chat`, composes message-list and chat-input, disables input during streaming
- [x] 5.5 Wire `chat-container` into `frontend/src/app/page.tsx` as the main page content
- [x] 5.6 Create `frontend/src/components/layout/header.tsx` — simple top bar with "IdleClaw" title

## 6. End-to-End Verification

- [x] 6.1 Start server (`uv run uvicorn server.src.main:app`) and frontend (`npm run dev`), send a message in the browser, confirm mock response streams token-by-token
- [x] 6.2 Verify input disables during streaming and re-enables after `[DONE]`
- [x] 6.3 Verify multiple exchanges render in order with auto-scroll
- [x] 6.4 Verify `GET /health` returns uptime from browser or curl
