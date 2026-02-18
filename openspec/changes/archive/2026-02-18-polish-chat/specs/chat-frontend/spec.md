## ADDED Requirements

### Requirement: Markdown rendering in assistant messages
The frontend SHALL render assistant message content as Markdown using `react-markdown` with `remark-gfm`. Inline code SHALL use a monospace font with a distinct background. Fenced code blocks SHALL be rendered in a scrollable monospace block. Links SHALL open in a new tab. User messages SHALL continue to render as plain text.

#### Scenario: Assistant message with code block
- **WHEN** the assistant responds with a fenced code block (e.g., ` ```python\nprint("hi")\n``` `)
- **THEN** the message bubble renders a styled code block with monospace font and a distinct background, not raw backtick text

#### Scenario: Assistant message with bold and list
- **WHEN** the assistant responds with `**bold** text` and a markdown list
- **THEN** "bold" renders in bold and the list items render as a proper HTML list

#### Scenario: User message not parsed as markdown
- **WHEN** the user sends a message containing `**not bold**`
- **THEN** it renders as the literal string `**not bold**` with whitespace preserved

### Requirement: Typing indicator while streaming
The frontend SHALL display an animated typing indicator (three bouncing dots) as a placeholder assistant message while `status` is `"submitted"` or `"streaming"`. The indicator SHALL disappear when the first token arrives and the real message begins rendering.

#### Scenario: Typing indicator appears after send
- **WHEN** the user sends a message and the server has not yet returned any tokens
- **THEN** an animated three-dot indicator appears in an assistant message bubble

#### Scenario: Typing indicator replaced by response
- **WHEN** the first token arrives from the server
- **THEN** the typing indicator is replaced by the streaming response text

### Requirement: Connection status in header
The frontend SHALL display a status badge in the header showing how many nodes are online. The badge SHALL poll `GET /health` every 10 seconds and update without a page reload. The badge SHALL show a green indicator when `node_count >= 1`, amber when `node_count === 0`, and red when the health endpoint is unreachable.

#### Scenario: Nodes online
- **WHEN** `GET /health` returns `{"node_count": 2, "status": "healthy"}`
- **THEN** the header shows a green badge reading "2 nodes online"

#### Scenario: No nodes connected
- **WHEN** `GET /health` returns `{"node_count": 0, "status": "healthy"}`
- **THEN** the header shows an amber badge reading "No nodes"

#### Scenario: Server unreachable
- **WHEN** `GET /health` request fails or times out
- **THEN** the header shows a red badge reading "Offline"

## MODIFIED Requirements

### Requirement: Loading state during streaming
The frontend SHALL show a visual indicator while waiting for and receiving the assistant's response. The message input SHALL be disabled during streaming to prevent concurrent requests. The typing indicator (three animated dots) serves as the visual indicator while `status` is `"submitted"` or `"streaming"` and no tokens have yet arrived.

#### Scenario: Input disabled during streaming
- **WHEN** a request is in-flight and tokens are being received
- **THEN** the input field and send button are disabled

#### Scenario: Input re-enabled after completion
- **WHEN** the streaming response completes
- **THEN** the input field and send button are re-enabled and the input is focused
