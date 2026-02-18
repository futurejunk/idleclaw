## 1. Frontend Dependencies

- [x] 1.1 Install `react-markdown`, `remark-gfm`, and `lucide-react` in `frontend/`

## 2. Server: Models & Health

- [x] 2.1 Create `server/src/routers/nodes.py` with `GET /api/models` that reads the registry and returns a deduplicated model name list
- [x] 2.2 Register the nodes router in `server/src/main.py`
- [x] 2.3 Add `node_count` field to the `GET /health` response in `server/src/routers/health.py`

## 3. Markdown Rendering

- [x] 3.1 Update `message-bubble.tsx` to render assistant messages with `react-markdown` + `remark-gfm`; add custom `code` component (monospace, `bg-zinc-900` background) and `a` component (`target="_blank"`, blue link color)
- [x] 3.2 Keep user messages rendering as plain `whitespace-pre-wrap` text (no markdown)

## 4. Typing Indicator

- [x] 4.1 Create a `TypingIndicator` component (three bouncing dots using Tailwind `animate-bounce` with staggered delays) styled as an assistant bubble
- [x] 4.2 Render `TypingIndicator` in `message-list.tsx` when `isLoading` is true and no streaming tokens have arrived yet

## 5. Connection Status

- [x] 5.1 Create `frontend/src/app/api/models/route.ts` that proxies `GET` to the backend `GET /api/models`
- [x] 5.2 Create `frontend/src/components/layout/connection-status.tsx` that polls `GET /health` every 10 seconds and shows a green/amber/red dot + node count text
- [x] 5.3 Add `ConnectionStatus` to `header.tsx`

## 6. Model Selector

- [x] 6.1 Create `frontend/src/components/layout/model-selector.tsx` — a `<select>` dropdown populated from the models list prop; disabled with placeholder when empty
- [x] 6.2 Lift `selectedModel` state into `chat-container.tsx`; fetch `GET /api/models` on mount to populate the model list
- [x] 6.3 Pass `selectedModel` and `models` list as props to `Header` and render `ModelSelector` there
- [x] 6.4 Pass `selectedModel` to `DefaultChatTransport` via the `body` option so it's included in every chat POST request

## 7. End-to-End Verification

- [x] 7.1 Start server + node agent; open frontend — verify model selector shows `llama3.2:1b`, connection status shows green with node count
- [x] 7.2 Send a message asking for a markdown response (e.g. "give me a python hello world example") — verify code block renders with styling
- [x] 7.3 Send a message and verify the typing indicator appears before the first token arrives
- [x] 7.4 Stop the node agent and verify the connection status turns amber within ~10 seconds
