"use client";

import { useEffect, useState } from "react";
import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import { MessageList } from "./message-list";
import { ChatInput } from "./chat-input";
import { Header } from "../layout/header";

export function ChatContainer() {
  const [models, setModels] = useState<string[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>("");

  useEffect(() => {
    fetch("/api/models")
      .then((r) => r.json())
      .then((data: { models: string[] }) => {
        setModels(data.models);
        if (data.models.length > 0) setSelectedModel(data.models[0]);
      })
      .catch(() => {});
  }, []);

  const transport = new DefaultChatTransport({
    api: "/api/chat",
    body: selectedModel ? { model: selectedModel } : undefined,
  });

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
    <div className="flex h-screen flex-col">
      <Header
        models={models}
        selectedModel={selectedModel}
        onModelChange={setSelectedModel}
      />
      <div className="flex flex-1 flex-col overflow-hidden">
        <MessageList messages={messages} isLoading={isLoading} />
        <ChatInput
          input={input}
          isLoading={isLoading}
          onInputChange={setInput}
          onSend={handleSend}
        />
      </div>
    </div>
  );
}
