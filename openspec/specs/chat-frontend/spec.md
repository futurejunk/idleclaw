## Requirements

### Requirement: Chat message input
The frontend SHALL render a text input and a send button at the bottom of the page. The user SHALL be able to type a message and submit it by clicking the send button or pressing Enter.

#### Scenario: Send message via button
- **WHEN** the user types "hello" in the input and clicks the send button
- **THEN** the message appears in the message list as a user message and the input is cleared

#### Scenario: Send message via Enter key
- **WHEN** the user types "hello" in the input and presses Enter
- **THEN** the message appears in the message list as a user message and the input is cleared

#### Scenario: Empty message prevented
- **WHEN** the user clicks send or presses Enter with an empty input
- **THEN** no message is sent and no request is made to the server

### Requirement: Streaming response rendering
The frontend SHALL connect to the server's `POST /api/chat` SSE endpoint using the Vercel AI SDK `useChat` hook and render assistant response tokens in real-time as they arrive.

#### Scenario: Tokens stream into message bubble
- **WHEN** the user sends a message and the server begins streaming tokens
- **THEN** an assistant message bubble appears and its content grows token-by-token as SSE events arrive

#### Scenario: Stream completion
- **WHEN** the server sends the `[DONE]` event
- **THEN** the assistant message is finalized, the loading indicator disappears, and the input is re-enabled

### Requirement: Message list with conversation history
The frontend SHALL display all messages in a scrollable list, with user messages visually distinct from assistant messages. The list SHALL auto-scroll to the bottom when new messages arrive.

#### Scenario: Multiple exchanges displayed
- **WHEN** the user sends three messages and receives three responses
- **THEN** all six messages are displayed in chronological order in the message list

#### Scenario: Auto-scroll on new content
- **WHEN** the assistant is streaming a response and new tokens extend beyond the visible area
- **THEN** the message list scrolls to keep the latest content visible

### Requirement: Loading state during streaming
The frontend SHALL show a visual indicator while waiting for and receiving the assistant's response. The message input SHALL be disabled during streaming to prevent concurrent requests. The typing indicator (three animated dots) serves as the visual indicator while `status` is `"submitted"` or `"streaming"` and no tokens have yet arrived.

#### Scenario: Input disabled during streaming
- **WHEN** a request is in-flight and tokens are being received
- **THEN** the input field and send button are disabled

#### Scenario: Input re-enabled after completion
- **WHEN** the streaming response completes
- **THEN** the input field and send button are re-enabled and the input is focused

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
