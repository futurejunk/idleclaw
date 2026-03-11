import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ChatInput } from "../chat-input";

// Mock next/link since we're outside Next.js runtime
vi.mock("next/link", () => ({
  default: ({ children, ...props }: { children: React.ReactNode; href: string }) => (
    <a {...props}>{children}</a>
  ),
}));

function renderChatInput(overrides: Partial<Parameters<typeof ChatInput>[0]> = {}) {
  const props = {
    input: "",
    isLoading: false,
    disabled: false,
    onInputChange: vi.fn(),
    onSend: vi.fn(),
    onStop: vi.fn(),
    ...overrides,
  };
  return { ...render(<ChatInput {...props} />), props };
}

describe("ChatInput", () => {
  it("calls onSend when Enter is pressed with text", () => {
    const { props } = renderChatInput({ input: "hello" });

    const textarea = screen.getByPlaceholderText("Send a message...");
    fireEvent.keyDown(textarea, { key: "Enter" });

    expect(props.onSend).toHaveBeenCalledOnce();
  });

  it("does not call onSend when Enter is pressed with empty input", () => {
    const { props } = renderChatInput({ input: "" });

    const textarea = screen.getByPlaceholderText("Send a message...");
    fireEvent.keyDown(textarea, { key: "Enter" });

    expect(props.onSend).not.toHaveBeenCalled();
  });

  it("disables send button when input is empty", () => {
    renderChatInput({ input: "" });

    const button = screen.getByRole("button");
    expect(button).toBeDisabled();
  });

  it("shows stop button (enabled) when isLoading is true", () => {
    const { props } = renderChatInput({ isLoading: true });

    const button = screen.getByRole("button");
    expect(button).not.toBeDisabled();

    fireEvent.click(button);
    expect(props.onStop).toHaveBeenCalledOnce();
  });

  it("shows enabled send button when input has text", () => {
    renderChatInput({ input: "hello" });

    const button = screen.getByRole("button");
    expect(button).not.toBeDisabled();
  });
});
