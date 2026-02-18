## ADDED Requirements

### Requirement: WebSocket node endpoint
The server SHALL expose a WebSocket endpoint at `ws://<host>/ws/node` that accepts connections from node agents. Upon connection, the server SHALL wait for a `register` message before the node is considered active.

#### Scenario: Node agent connects and registers
- **WHEN** a node agent opens a WebSocket connection to `/ws/node` and sends `{"type": "register", "node_id": "<uuid>", "models": [{"name": "llama3.2:3b", "size": 2000000000}], "max_concurrent": 2}`
- **THEN** the server stores the node in the registry and responds with `{"type": "registered", "node_id": "<uuid>"}`

#### Scenario: Node connects without registering
- **WHEN** a node agent opens a WebSocket connection but does not send a `register` message within 10 seconds
- **THEN** the server closes the connection

### Requirement: Node registry
The server SHALL maintain an in-memory registry of connected nodes. Each entry SHALL store the node's WebSocket connection, node_id, list of available models, max concurrent requests, last heartbeat timestamp, and current active request count.

#### Scenario: Registry tracks connected node
- **WHEN** a node registers with models `["llama3.2:3b", "mistral:7b"]`
- **THEN** the registry contains an entry for that node_id with both models listed and active_requests at 0

#### Scenario: Node disconnects
- **WHEN** a registered node's WebSocket connection closes (graceful or unexpected)
- **THEN** the registry removes the node entry and cleans up any pending request queues associated with it

### Requirement: Heartbeat protocol
Node agents SHALL send a heartbeat message every 15 seconds: `{"type": "heartbeat", "node_id": "<uuid>", "active_requests": N, "available": true}`. The server SHALL update the node's last heartbeat timestamp and active request count on each heartbeat.

#### Scenario: Heartbeat updates node status
- **WHEN** a node sends a heartbeat with `active_requests: 1`
- **THEN** the registry updates that node's active_requests to 1 and refreshes the last_heartbeat timestamp

#### Scenario: Stale node eviction
- **WHEN** a node has not sent a heartbeat for 45 seconds
- **THEN** the server closes the node's WebSocket connection and removes it from the registry

### Requirement: Node agent WebSocket client
The node agent SHALL connect to the server's WebSocket endpoint, discover local Ollama models via `ollama_bridge.list_models()`, and send a `register` message with the discovered models. After registration, the agent SHALL send heartbeat messages every 15 seconds.

#### Scenario: Agent starts and registers
- **WHEN** the node agent starts with Ollama running and model `llama3.2:3b` available
- **THEN** the agent connects to the server WebSocket, sends a register message with `models: [{"name": "llama3.2:3b", "size": <bytes>}]`, and receives a `registered` acknowledgment

#### Scenario: Agent sends periodic heartbeats
- **WHEN** the agent is connected and registered
- **THEN** it sends a heartbeat message every 15 seconds with current active_requests count and available status
