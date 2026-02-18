## ADDED Requirements

### Requirement: Models list endpoint
The server SHALL expose a `GET /api/models` endpoint that aggregates and deduplicates model names from all currently connected nodes in the registry and returns them as a JSON array.

#### Scenario: Models returned from connected nodes
- **WHEN** a client sends `GET /api/models` and connected nodes advertise models `["llama3.2:1b"]` and `["llama3.2:1b", "mistral:7b"]`
- **THEN** the server returns `{"models": ["llama3.2:1b", "mistral:7b"]}` with no duplicates

#### Scenario: Empty registry
- **WHEN** no nodes are connected and a client sends `GET /api/models`
- **THEN** the server returns `{"models": []}`

## MODIFIED Requirements

### Requirement: Health check endpoint
The server SHALL expose a `GET /health` endpoint that returns a JSON object with `status` ("healthy"), `uptime_seconds` (number), and `node_count` (integer count of currently connected nodes in the registry).

#### Scenario: Health check with nodes
- **WHEN** a client sends `GET /health` and 2 nodes are connected
- **THEN** the server returns status 200 with `{"status": "healthy", "uptime_seconds": <number>, "node_count": 2}`

#### Scenario: Health check with no nodes
- **WHEN** a client sends `GET /health` and no nodes are connected
- **THEN** the server returns status 200 with `{"status": "healthy", "uptime_seconds": <number>, "node_count": 0}`
