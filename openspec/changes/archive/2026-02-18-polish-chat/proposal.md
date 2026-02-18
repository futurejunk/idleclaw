## Why

The chat UI works end-to-end but looks and feels like a prototype. The header is a static title, the model selector and connection status don't exist, assistant messages render as plain text (no markdown), and there's no typing indicator. This change makes the UI something a real user would want to use.

## What Changes

- Add markdown rendering to assistant messages (`react-markdown` + `remark-gfm`) so code blocks, lists, and bold text render correctly
- Add a typing indicator (animated dots) in the message list while the assistant is streaming
- Add a model selector dropdown to the header — fetches available models from `GET /api/models` and lets the user pick which model to chat with
- Add a connection status indicator to the header — polls `GET /health` and shows node count + online/offline state
- Add `GET /api/models` endpoint to the server that aggregates available models from connected nodes
- Wire the selected model from the UI through to the chat API request (currently hardcoded to `llama3.2:1b`)

## Capabilities

### New Capabilities
- `model-selector`: Frontend model picker backed by a server endpoint that lists models from connected nodes

### Modified Capabilities
- `chat-frontend`: Add markdown rendering, typing indicator, connection status, and model selector
- `chat-api`: Add `GET /api/models` endpoint; wire selected model from frontend request body

## Impact

- **frontend/**: Add `react-markdown`, `remark-gfm`, `lucide-react` dependencies
- **frontend/src/components/chat/message-bubble.tsx**: Add markdown rendering
- **frontend/src/components/chat/chat-container.tsx**: Add model state, pass to transport; add typing indicator
- **frontend/src/components/layout/header.tsx**: Add model selector + connection status components
- **frontend/src/components/layout/model-selector.tsx**: New component
- **frontend/src/components/layout/connection-status.tsx**: New component
- **server/src/routers/nodes.py**: New router with `GET /api/models`
- **server/src/main.py**: Register nodes router
