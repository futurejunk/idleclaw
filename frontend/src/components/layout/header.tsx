import { ConnectionStatus } from "./connection-status";
import { ModelSelector } from "./model-selector";

interface HeaderProps {
  models: string[];
  selectedModel: string;
  onModelChange: (model: string) => void;
}

export function Header({ models, selectedModel, onModelChange }: HeaderProps) {
  return (
    <header className="border-b border-zinc-800 bg-zinc-950 px-6 py-4 flex items-center justify-between">
      <h1 className="text-lg font-semibold text-zinc-100">IdleClaw</h1>
      <div className="flex items-center gap-4">
        <ModelSelector
          models={models}
          selected={selectedModel}
          onChange={onModelChange}
        />
        <ConnectionStatus />
      </div>
    </header>
  );
}
