"use client";

import { useEffect, useState, useCallback, useRef, useMemo } from "react";
import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import { useHealth } from "@/hooks/use-health";
import { MessageList } from "./message-list";
import { ChatInput } from "./chat-input";
import { Header } from "../layout/header";

export function ChatContainer() {
  const { state: healthState, nodeCount } = useHealth();
  const [models, setModels] = useState<string[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [modelError, setModelError] = useState(false);
  const [bannerDismissed, setBannerDismissed] = useState(false);
  const prevHealthState = useRef(healthState);

  const fetchModels = useCallback(async () => {
    try {
      const r = await fetch("/api/models");
      if (!r.ok) throw new Error("not ok");
      const data: { models: string[] } = await r.json();
      setModels(data.models);
      setModelError(false);
      if (data.models.length > 0) setSelectedModel((prev) => prev || data.models[0]);
    } catch {
      setModelError(true);
    }
  }, []);

  // Initial model fetch
  useEffect(() => {
    fetchModels();
  }, [fetchModels]);

  // Retry model fetch when health transitions to online
  useEffect(() => {
    if (prevHealthState.current === "offline" && healthState !== "offline") {
      fetchModels();
      setBannerDismissed(false);
    }
    prevHealthState.current = healthState;
  }, [healthState, fetchModels]);

  // Use a ref so the transport body always reads the latest selected model.
  // useChat captures the Chat instance (and its transport) once on mount,
  // so a plain inline transport would be stale.
  const selectedModelRef = useRef(selectedModel);
  selectedModelRef.current = selectedModel;

  const transport = useMemo(
    () =>
      new DefaultChatTransport({
        api: "/api/chat",
        body: () =>
          selectedModelRef.current
            ? { model: selectedModelRef.current }
            : undefined,
      }),
    [],
  );

  const [chatError, setChatError] = useState<string | null>(null);

  const { messages, setMessages, sendMessage, status } = useChat({
    transport,
    onError: (error) => {
      if (error.message?.includes("503")) {
        setChatError("No nodes available with this model. Try a different model or wait for nodes to come online.");
      } else {
        setChatError("Something went wrong. Try again.");
      }
    },
  });
  const [input, setInput] = useState("");

  const isLoading = status === "submitted" || status === "streaming";
  const isOffline = healthState === "offline";
  const showBanner = isOffline && !bannerDismissed;

  const handleSend = (text?: string) => {
    const msg = (text ?? input).trim();
    if (!msg || isLoading || isOffline) return;
    setChatError(null);
    setInput("");
    sendMessage({ text: msg });
  };

  const [focusTrigger, setFocusTrigger] = useState(0);

  const handleNewChat = () => {
    setMessages([]);
    setInput("");
    setChatError(null);
    setFocusTrigger((n) => n + 1);
  };

  return (
    <div className="flex h-dvh flex-col">
      <Header
        models={models}
        selectedModel={selectedModel}
        onModelChange={setSelectedModel}
        modelError={modelError}
        healthState={healthState}
        nodeCount={nodeCount}
        onNewChat={messages.length > 0 ? handleNewChat : undefined}
      />
      {showBanner && (
        <div className="flex items-center justify-between bg-red-50 border-b border-red-200 px-4 sm:px-6 py-2.5 text-sm text-red-700">
          <span>Network is starting up — try again in a moment.</span>
          <button
            onClick={() => setBannerDismissed(true)}
            className="ml-4 text-red-500 hover:text-red-700 text-xs"
          >
            Dismiss
          </button>
        </div>
      )}
      <div className="flex flex-1 flex-col overflow-hidden">
        <MessageList
          messages={messages}
          isLoading={isLoading}
          chatError={chatError}
          onSuggestionClick={handleSend}
        />
        <ChatInput
          input={input}
          isLoading={isLoading}
          disabled={isOffline}
          focusTrigger={focusTrigger}
          onInputChange={setInput}
          onSend={handleSend}
        />
      </div>
    </div>
  );
}
