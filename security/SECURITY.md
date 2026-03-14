# IdleClaw Security Assessment

**Last updated:** 2026-03-14
**Scope:** Full application stack (frontend, server, node-agent, skill)

## Threat Model

IdleClaw is a community inference network where anonymous users chat with anonymous GPU contributors. The core security assumption is that **nodes are untrusted** — any contributor could act maliciously. The server treats all node output as adversarial input and limits what node responses can trigger server-side.

## Assessment Methodology

White-box code review and proof-of-concept testing across all components. Findings were categorized by severity (Critical, High, Medium, Low) and remediated in priority order.

## Findings and Remediation Status

### Critical Findings — All Remediated

| Finding | Description | Status |
|---------|-------------|--------|
| Unauthenticated node response poisoning | Any node could return arbitrary content | Mitigated: server treats all node output as untrusted, sanitizes before delivery |
| Node-triggered tool execution | Malicious nodes could embed tool call tags in responses | Fixed: tool call parsing is gated — only active when tools are offered in the request |
| Tool argument injection | Unvalidated kwargs passed to tool handlers | Fixed: arguments validated against JSON schema before execution; unknown tools silently dropped |

### High Findings — All Remediated

| Finding | Description | Status |
|---------|-------------|--------|
| System prompt extraction via prompt injection | System prompt visible to models | Accepted risk: system prompts are not treated as secrets |
| Indirect tool invocation via prompt injection | Users could trick models into emitting tool call tags | Fixed: tool parsing gated behind `tools_offered` check; native-only mode skips regex fallback |
| System/tool role message injection | Clients could send system-role messages | Fixed: message roles restricted to `user` and `assistant` via Pydantic validation |
| X-Forwarded-For rate limit bypass | Spoofable header when accessed directly | Fixed: server binds to localhost only, accessed through Caddy reverse proxy |

### Medium Findings — Mostly Remediated

| Finding | Description | Status |
|---------|-------------|--------|
| Tool registry mutation | Tools could theoretically be registered after startup | Fixed: registry frozen at startup via `freeze()` method |
| Queue blocking on full queue | `asyncio.Queue.put()` could block handler | Open (low risk): default queue is unbounded; practical overflow unlikely |
| Public metrics endpoint | `/metrics` exposes network health data | Open (low risk): information disclosure only, no sensitive data |
| No client-side input length validation | Frontend textarea has no maxLength | Open (low risk): server enforces 10,000 char limit via Pydantic |

### Low Findings

| Finding | Description | Status |
|---------|-------------|--------|
| Tool name markdown injection | Tool names interpolated into markdown | Low risk: ReactMarkdown sanitizes HTML |
| No circuit breaker for slow nodes | Slow nodes keep receiving requests | Accepted: monitoring via heartbeat is sufficient for current scale |
| Async race conditions in registry | Concurrent access without locking | Accepted: Python asyncio is single-threaded; no true parallelism |

## Defense-in-Depth Layers

### Server-Side
- IP-based rate limiting: chat (20 RPM), node registration (5 RPM), general (60 RPM)
- Input validation: max 50 messages, 10,000 chars per message, roles restricted to user/assistant
- Output sanitization: response content stripped of markup tags before delivery
- Tool execution gating: only when tools offered, schema validation, 15s timeout, per-node rate limiting
- Tool registry frozen after startup
- Node registration limits: max 3 per IP, max concurrent requests capped
- Server binds to localhost, accessed through Caddy with auto-TLS
- NLP content classification: layered inbound (regex → injection → toxicity) and post-stream outbound (toxicity + injection)
- Safety system prompt: prepended to all conversations, instructs model to refuse harmful requests
- Response compute limits: max 4096 chars, 120s timeout
- Node probing with NLP toxicity check on responses

### Client-Side (Skill and Node-Agent)
- Inference parameter whitelist: only known keys forwarded to Ollama
- Model verification: requested model must match registered models
- Message limits: max 50 messages, 10,000 chars per content (mirrors server)
- Response field whitelist: only role, content, thinking, tool_calls forwarded
- No shell execution, no file access, no credential storage

## Reporting

To report a security issue, open a GitHub issue or contact the maintainers directly.
