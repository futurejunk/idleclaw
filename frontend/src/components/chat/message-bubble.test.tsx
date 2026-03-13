import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { MessageBubble } from "./message-bubble";
import type { UIMessage } from "ai";

function makeMessage(markdown: string): UIMessage {
  return {
    id: "test-1",
    role: "assistant",
    content: markdown,
    parts: [{ type: "text", text: markdown }],
    createdAt: new Date(),
  };
}

describe("MessageBubble link protocol validation", () => {
  it("renders http links as clickable anchors", () => {
    render(<MessageBubble message={makeMessage("[click](http://example.com)")} />);
    const link = screen.getByRole("link", { name: "click" });
    expect(link).toHaveAttribute("href", "http://example.com");
  });

  it("renders https links as clickable anchors", () => {
    render(<MessageBubble message={makeMessage("[click](https://example.com)")} />);
    const link = screen.getByRole("link", { name: "click" });
    expect(link).toHaveAttribute("href", "https://example.com");
  });

  it("renders javascript: links as plain text", () => {
    render(<MessageBubble message={makeMessage("[click](javascript:alert(1))")} />);
    expect(screen.queryByRole("link", { name: "click" })).toBeNull();
    expect(screen.getByText("click")).toBeInTheDocument();
  });

  it("renders data: links as plain text", () => {
    render(<MessageBubble message={makeMessage("[click](data:text/html,<script>alert(1)</script>)")} />);
    expect(screen.queryByRole("link", { name: "click" })).toBeNull();
    expect(screen.getByText("click")).toBeInTheDocument();
  });

  it("renders links with no href as plain text", () => {
    render(<MessageBubble message={makeMessage("[click]()")} />);
    expect(screen.queryByRole("link", { name: "click" })).toBeNull();
  });
});
