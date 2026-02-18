## Context

The frontend is functional but skeletal: the header is a static title, messages render as plain text, and there's no way to know which model is running or whether any nodes are connected. The UI uses Tailwind v4 (dark zinc/blue color palette, already established). All chat components exist and are wired — this change layers polish on top without restructuring.

## Goals / Non-Goals

**Goals:**
- Markdown rendering in assistant bubbles (code blocks, lists, bold, links)
- Typing indicator while status is `submitted` or `streaming`
- Model selector in header backed by `GET /api/models`
- Connection status badge in header backed by `GET /health`
- Selected model wired from UI → Next.js route → FastAPI

**Non-Goals:**
- Conversation history / persistence (Phase 4+)
- User accounts or auth
- Mobile layout optimization
- Syntax highlighting in code blocks (adds bundle weight; plain monospace is fine for MVP)
- Rate limiting or per-model descriptions

## Decisions

### 1. Markdown: `react-markdown` + `remark-gfm`

`react-markdown` is the standard React markdown renderer. `remark-gfm` adds GitHub-Flavored Markdown (tables, strikethrough, task lists). Apply only to assistant messages — user messages render as plain `whitespace-pre-wrap` text (they're user input, not markdown).

Custom component overrides for `code` (monospace, `bg-zinc-900` background) and `a` (blue link color, `target="_blank"`). No syntax highlighter — keeps bundle lean and avoids the `prism`/`shiki` decision.

### 2. Typing indicator: local component, driven by `status` prop

A small `TypingIndicator` component shows three animated dots using Tailwind's `animate-bounce` with staggered `animation-delay`. Rendered as a fake assistant bubble at the bottom of the message list when `isLoading` is true. No server changes needed — purely client-side.

**Why not a spinner?** Animated dots are the established LLM chat pattern. Matches user expectations.

### 3. Model selector: React state lifted to `ChatContainer`, fetched once on mount

`ChatContainer` owns `selectedModel` state. On mount, it fetches `GET /api/models` (from the Next.js API route, which proxies to the backend). The model list is passed to `Header` as a prop; the selected model is passed to `DefaultChatTransport` via the `body` option so it's included in the POST body.

**Why fetch in `ChatContainer` not `Header`?** The selected model needs to be in scope when `sendMessage` is called. Lifting to the common ancestor avoids prop drilling through siblings.

**Why `body` option on `DefaultChatTransport`?** AI SDK v6's `DefaultChatTransport` accepts a `body` option for extra fields merged into every request. This is the idiomatic way to pass model selection without reimplementing the transport.

### 4. `GET /api/models`: new server endpoint, deduped model list

`GET /api/models` iterates the node registry and returns a deduplicated list of model names across all connected nodes: `{models: ["llama3.2:1b", "mistral:7b"]}`. No per-node metadata needed in the UI for now.

The Next.js route at `frontend/src/app/api/models/route.ts` proxies to the backend, same pattern as `/api/chat`.

### 5. Connection status: polling `GET /health` every 10s

`ConnectionStatus` is a client component that polls `GET /health` every 10 seconds using `setInterval`. The health response already includes `uptime_seconds` — we add `node_count` (count from registry) to make it useful. Shows a green/amber/red dot + "N nodes online" text.

**Why polling not WebSocket?** Health check doesn't need real-time precision. Polling is simpler, no new connection to manage.

## Risks / Trade-offs

- **`react-markdown` bundle size** (~30KB gzipped) → acceptable for MVP; no SSR concern since the chat page is already client-side.
- **Model list stale after new node connects** → user can manually refresh; auto-refresh would add complexity. Acceptable for MVP.
- **`GET /api/models` returns empty if no nodes connected** → UI falls back to a disabled selector with placeholder text. No crash.
- **`node_count` in health response** is a new field → backwards compatible addition, non-breaking.
