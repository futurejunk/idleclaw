# IdleClaw

Free AI chat powered by community GPU contributors. No accounts, no API keys — just open your browser and start chatting.

**Live:** [idleclaw.com](https://idleclaw.com)

## How it works

IdleClaw is a community-owned AI inference network. Contributors share idle GPU compute running [Ollama](https://ollama.com) on their local machines. Users get free access to language models through the web chat or the OpenClaw skill.

```
Browser / Skill consumer
        │
        ▼
┌───────────────┐       ┌──────────────────┐
│ Routing Server │◄─WSS─►│  Node Agent       │
│  (FastAPI)     │       │  (contributor PC) │
└───────────────┘       │  └─► Ollama        │
        │               └──────────────────┘
        │               ┌──────────────────┐
        └──────WSS─────►│  Node Agent       │
                        │  (contributor PC) │
                        │  └─► Ollama        │
                        └──────────────────┘
```

1. **Contributors** run the node agent, which connects to the routing server via WebSocket and shares available models
2. **The server** tracks connected nodes and routes inference requests to the best available node
3. **Users** chat through the web UI or use the OpenClaw skill — prompts are routed to contributor nodes, responses stream back

## Project structure

```
idleclaw/
├── frontend/       Next.js chat UI
├── server/         FastAPI routing server
├── node-agent/     Python agent (runs on contributor machines)
├── skill/          OpenClaw skill package for ClawHub
└── deploy/         Systemd units, Caddy config, provisioning scripts
```

## Local development

**Prerequisites:** Node.js 18+, Python 3.11+, [Ollama](https://ollama.com) running locally

### Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

### Server

```bash
cd server
python -m venv .venv && source .venv/bin/activate
pip install -e .
uvicorn server.src.main:app --host 127.0.0.1 --port 8000
```

### Node agent

```bash
cd node-agent
python -m venv .venv && source .venv/bin/activate
pip install -e .
IDLECLAW_SERVER=ws://localhost:8000 python -m src.main
```

The node agent will connect to the server and register your local Ollama models.

## OpenClaw skill

IdleClaw is distributed as an [OpenClaw](https://openclaw.com) skill on [ClawHub](https://clawhub.ai). The skill supports three modes:

- **consume** — use community inference from any AI agent
- **contribute** — share your GPU with the network
- **status** — check network health and available models

See [`skill/SKILL.md`](skill/SKILL.md) for full details.

## Tech stack

- **Frontend:** Next.js 16, React 19, Tailwind CSS 4, Vercel AI SDK
- **Server:** FastAPI, WebSockets, SSE streaming
- **Node agent:** Python, Ollama SDK, WebSockets
- **Fonts:** Bricolage Grotesque, Manrope (via Google Fonts)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

[AGPL-3.0](LICENSE)
