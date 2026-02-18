## ADDED Requirements

### Requirement: List local Ollama models
The ollama-bridge module SHALL provide a function that queries the local Ollama instance and returns a list of available models with their names and sizes.

#### Scenario: Ollama running with models pulled
- **WHEN** the function is called and Ollama is running at `localhost:11434` with at least one model pulled
- **THEN** it returns a list of model objects each containing at minimum `name` (string) and `size` (number in bytes)

#### Scenario: Ollama not running
- **WHEN** the function is called and Ollama is not running or unreachable
- **THEN** it raises a connection error with a message indicating Ollama is unavailable at the configured host

### Requirement: Stream chat completion
The ollama-bridge module SHALL provide an async function that sends a chat request to the local Ollama instance and yields response tokens as they are generated, one at a time.

The function SHALL accept `model` (string) and `messages` (list of `{role, content}` dicts) as parameters.

#### Scenario: Successful streaming chat
- **WHEN** the function is called with a valid model name and a messages list containing `[{"role": "user", "content": "Why is the sky blue?"}]`
- **THEN** it yields a sequence of string tokens that together form a coherent response, and completes without error

#### Scenario: Invalid model name
- **WHEN** the function is called with a model name that is not pulled locally
- **THEN** it raises an error indicating the model was not found

### Requirement: Standalone test mode
The ollama-bridge module SHALL be executable as a standalone script (`python ollama_bridge.py`) that lists available models, prompts a hardcoded test message, and prints streamed tokens to stdout in real-time.

#### Scenario: Run as standalone script
- **WHEN** the user runs `python ollama_bridge.py` with Ollama running and at least one model available
- **THEN** the script prints the list of available models, selects the first one, sends a test message, and prints response tokens to stdout as they arrive

### Requirement: Configurable Ollama host
The ollama-bridge module SHALL read the Ollama host URL from the `OLLAMA_HOST` environment variable, defaulting to `http://localhost:11434` if not set.

#### Scenario: Default host
- **WHEN** `OLLAMA_HOST` is not set and Ollama is running on `localhost:11434`
- **THEN** the module connects successfully

#### Scenario: Custom host
- **WHEN** `OLLAMA_HOST` is set to `http://192.168.1.50:11434` and Ollama is running at that address
- **THEN** the module connects to the custom host successfully
