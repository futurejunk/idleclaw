## Requirements

### Requirement: Models endpoint
The server SHALL expose a `GET /api/models` endpoint that returns a deduplicated list of model names available across all currently connected node agents.

#### Scenario: Models available
- **WHEN** a client sends `GET /api/models` and one or more nodes are connected with models `["llama3.2:1b"]` and `["llama3.2:1b", "mistral:7b"]`
- **THEN** the server returns status 200 with `{"models": ["llama3.2:1b", "mistral:7b"]}` (deduplicated, order not guaranteed)

#### Scenario: No nodes connected
- **WHEN** a client sends `GET /api/models` and no nodes are connected
- **THEN** the server returns status 200 with `{"models": []}`

### Requirement: Model selector UI
The frontend SHALL display a dropdown in the header that lists all models returned by `GET /api/models`. The selected model SHALL be used as the `model` field in all subsequent chat requests.

#### Scenario: Models loaded on mount
- **WHEN** the page loads and `GET /api/models` returns `["llama3.2:1b", "mistral:7b"]`
- **THEN** the header shows a dropdown with both models and the first model pre-selected

#### Scenario: Model selected and sent with request
- **WHEN** the user selects `mistral:7b` from the dropdown and sends a message
- **THEN** the chat request body contains `model: "mistral:7b"`

#### Scenario: No models available
- **WHEN** `GET /api/models` returns an empty list
- **THEN** the dropdown is disabled and shows placeholder text indicating no models are available
