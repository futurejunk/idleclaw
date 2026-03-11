import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { MessageBubble } from "../message-bubble";
import type { UIMessage } from "ai";

function makeMessage(overrides: Partial<UIMessage> & { role: UIMessage["role"]; text: string }): UIMessage {
  const { text, ...rest } = overrides;
  return {
    id: "test-id",
    parts: [{ type: "text", text }],
    ...rest,
  };
}

describe("MessageBubble", () => {
  it("renders user message as plain text (no markdown)", () => {
    const msg = makeMessage({ role: "user", text: "hello **world**" });
    render(<MessageBubble message={msg} />);

    // User messages render as plain text via whitespace-pre-wrap <p>
    const el = screen.getByText("hello **world**");
    expect(el).toBeInTheDocument();
    expect(el.tagName).toBe("P");
    // No <strong> tag should exist in the output
    expect(el.querySelector("strong")).toBeNull();
  });

  it("renders assistant message with markdown formatting", () => {
    const msg = makeMessage({ role: "assistant", text: "hello **world**" });
    render(<MessageBubble message={msg} />);

    // ReactMarkdown should render the bold text
    const bold = screen.getByText("world");
    expect(bold.tagName).toBe("STRONG");
  });

  it("does not render empty assistant message", () => {
    const msg: UIMessage = {
      id: "test-id",
      role: "assistant",
      parts: [{ type: "text", text: "" }],
    };
    const { container } = render(<MessageBubble message={msg} />);
    expect(container.firstChild).toBeNull();
  });
});
