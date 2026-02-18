## ADDED Requirements

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
The frontend SHALL show a visual indicator while waiting for and receiving the assistant's response. The message input SHALL be disabled during streaming to prevent concurrent requests.

#### Scenario: Input disabled during streaming
- **WHEN** a request is in-flight and tokens are being received
- **THEN** the input field and send button are disabled

#### Scenario: Input re-enabled after completion
- **WHEN** the streaming response completes
- **THEN** the input field and send button are re-enabled and the input is focused
