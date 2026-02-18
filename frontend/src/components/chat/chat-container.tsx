"use client";

import { useState } from "react";
import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import { MessageList } from "./message-list";
import { ChatInput } from "./chat-input";

const transport = new DefaultChatTransport({
  api: "/api/chat",
});

export function ChatContainer() {
  const { messages, sendMessage, status } = useChat({ transport });
  const [input, setInput] = useState("");

  const isLoading = status === "submitted" || status === "streaming";

  const handleSend = () => {
    const text = input.trim();
    if (!text || isLoading) return;
    setInput("");
    sendMessage({ text });
  };

  return (
    <div className="flex h-full flex-col">
      <MessageList messages={messages} />
      <ChatInput
        input={input}
        isLoading={isLoading}
        onInputChange={setInput}
        onSend={handleSend}
      />
    </div>
  );
}
