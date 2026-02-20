"use client";

import { useEffect, useRef } from "react";
import type { UIMessage } from "ai";
import { MessageBubble } from "./message-bubble";
import { TypingIndicator } from "./typing-indicator";

interface MessageListProps {
  messages: UIMessage[];
  isLoading: boolean;
  chatError: string | null;
}

export function MessageList({ messages, isLoading, chatError }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  // Show typing indicator when loading and the last message is from the user
  // (i.e. no assistant response has started yet)
  const lastMessage = messages[messages.length - 1];
  const showTyping = isLoading && (!lastMessage || lastMessage.role === "user");

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-4">
      {messages.length === 0 && !isLoading && (
        <div className="flex h-full items-center justify-center">
          <p className="text-zinc-500 text-sm">Send a message to get started.</p>
        </div>
      )}
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}
      {showTyping && <TypingIndicator />}
      {chatError && (
        <div className="flex justify-start">
          <div className="max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed bg-red-950 text-red-200 border border-red-900">
            {chatError}
          </div>
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  );
}
