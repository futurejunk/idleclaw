import { SquarePen } from "lucide-react";
import type { ConnectionState } from "@/hooks/use-health";
import { ConnectionStatus } from "./connection-status";
import { ModelSelector } from "./model-selector";

interface HeaderProps {
  models: string[];
  selectedModel: string;
  onModelChange: (model: string) => void;
  modelError: boolean;
  healthState: ConnectionState;
  nodeCount: number;
  onNewChat?: () => void;
}

export function Header({ models, selectedModel, onModelChange, modelError, healthState, nodeCount, onNewChat }: HeaderProps) {
  return (
    <header className="border-b border-zinc-800 bg-zinc-950 px-4 py-3 sm:px-6 sm:py-4 flex flex-wrap items-center justify-between gap-2">
      <div className="flex items-center gap-2">
        {onNewChat && (
          <button
            onClick={onNewChat}
            className="rounded-lg p-1.5 text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200"
            title="New chat"
          >
            <SquarePen size={18} />
          </button>
        )}
        <h1 className="text-lg font-semibold text-zinc-100">IdleClaw</h1>
      </div>
      <div className="flex items-center gap-3 sm:gap-4">
        <ModelSelector
          models={models}
          selected={selectedModel}
          onChange={onModelChange}
          error={modelError}
        />
        <ConnectionStatus state={healthState} nodeCount={nodeCount} />
      </div>
    </header>
  );
}
