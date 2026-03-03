"use client";

import { useEffect, useRef } from "react";
import type { UIMessage } from "ai";
import { MessageBubble } from "./message-bubble";
import { TypingIndicator } from "./typing-indicator";
import { WelcomeScreen } from "./welcome-screen";

interface MessageListProps {
  messages: UIMessage[];
  isLoading: boolean;
  chatError: string | null;
  onSuggestionClick: (text: string) => void;
}

export function MessageList({ messages, isLoading, chatError, onSuggestionClick }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  // Show typing indicator when loading and no visible assistant content yet.
  // The AI SDK creates an empty assistant message on stream start, so we also
  // check if the assistant message has any text/reasoning content.
  const lastMessage = messages[messages.length - 1];
  const lastAssistantHasContent = lastMessage?.role === "assistant" &&
    lastMessage.parts.some((p) => (p.type === "text" || p.type === "reasoning") && "text" in p && (p as { text: string }).text.length > 0);
  const showTyping = isLoading && !lastAssistantHasContent;

  return (
    <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
      {messages.length === 0 && !isLoading && (
        <WelcomeScreen onSuggestionClick={onSuggestionClick} />
      )}
      {messages.map((message, i) => (
        <MessageBubble
          key={message.id}
          message={message}
          isStreaming={isLoading && i === messages.length - 1 && message.role === "assistant"}
        />
      ))}
      {showTyping && <TypingIndicator />}
      {chatError && (
        <div className="flex justify-start">
          <div className="max-w-[90%] sm:max-w-[80%] rounded-[20px] px-4 py-2.5 text-sm leading-relaxed bg-red-50 text-red-700 border border-red-200">
            {chatError}
          </div>
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  );
}
