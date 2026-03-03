import { SquarePen } from "lucide-react";
import type { ConnectionState } from "@/hooks/use-health";
import { ConnectionStatus } from "./connection-status";
import { ModelSelector } from "./model-selector";

interface HeaderProps {
  models: string[];
  modelCapabilities: Record<string, Record<string, boolean>>;
  selectedModel: string;
  onModelChange: (model: string) => void;
  modelError: boolean;
  healthState: ConnectionState;
  nodeCount: number;
  onNewChat?: () => void;
  thinkingEnabled: boolean;
  onThinkingChange: (enabled: boolean) => void;
}

export function Header({ models, modelCapabilities, selectedModel, onModelChange, modelError, healthState, nodeCount, onNewChat, thinkingEnabled, onThinkingChange }: HeaderProps) {
  return (
    <header className="border-b border-banner/20 bg-banner px-4 py-3 sm:px-6 sm:py-4 flex flex-wrap items-center justify-between gap-2">
      <div className="flex items-center gap-2">
        {onNewChat && (
          <button
            onClick={onNewChat}
            className="rounded-lg p-1.5 text-banner-text/70 hover:bg-white/10 hover:text-banner-text"
            title="New chat"
          >
            <SquarePen size={18} />
          </button>
        )}
        <h1 className="text-lg font-semibold font-heading text-brand">IdleClaw</h1>
      </div>
      <div className="flex items-center gap-3 sm:gap-4">
        <ModelSelector
          models={models}
          capabilities={modelCapabilities}
          selected={selectedModel}
          onChange={onModelChange}
          error={modelError}
        />
        <button
          onClick={() => onThinkingChange(!thinkingEnabled)}
          className={`rounded-lg px-2.5 py-1.5 text-xs font-medium transition-colors ${
            thinkingEnabled
              ? "bg-brand/20 text-brand hover:bg-brand/30"
              : "text-banner-text/50 hover:bg-white/10 hover:text-banner-text/70"
          }`}
          title={thinkingEnabled ? "Thinking mode on" : "Thinking mode off"}
        >
          {thinkingEnabled ? "Think: On" : "Think: Off"}
        </button>
        <ConnectionStatus state={healthState} nodeCount={nodeCount} />
        <a
          href="https://github.com/futurejunk/idleclaw"
          target="_blank"
          rel="noopener noreferrer"
          className="hidden sm:inline-flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-xs font-medium text-banner-text/70 hover:bg-white/10 hover:text-banner-text transition-colors"
        >
          Contribute your GPU
        </a>
      </div>
    </header>
  );
}
