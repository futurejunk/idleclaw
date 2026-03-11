import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { WelcomeScreen } from "../welcome-screen";

describe("WelcomeScreen", () => {
  it("renders four suggestion pills", () => {
    render(<WelcomeScreen onSuggestionClick={vi.fn()} />);

    const buttons = screen.getAllByRole("button");
    expect(buttons).toHaveLength(4);
  });

  it("calls onSuggestionClick with pill text when clicked", () => {
    const onSuggestionClick = vi.fn();
    render(<WelcomeScreen onSuggestionClick={onSuggestionClick} />);

    const pill = screen.getByText("Explain recursion in simple terms");
    fireEvent.click(pill);

    expect(onSuggestionClick).toHaveBeenCalledWith("Explain recursion in simple terms");
  });
});
