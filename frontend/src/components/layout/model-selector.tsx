interface ModelSelectorProps {
  models: string[];
  capabilities: Record<string, Record<string, boolean>>;
  selected: string;
  onChange: (model: string) => void;
  error: boolean;
}

export function ModelSelector({ models, capabilities, selected, onChange, error }: ModelSelectorProps) {
  if (error) {
    return (
      <select
        disabled
        className="rounded-[9px] border border-white/20 bg-white/10 px-3 py-1.5 text-xs text-banner-text/50 disabled:opacity-60"
      >
        <option>Models unavailable</option>
      </select>
    );
  }

  if (models.length === 0) {
    return (
      <select
        disabled
        className="rounded-[9px] border border-white/20 bg-white/10 px-3 py-1.5 text-xs text-banner-text/50 disabled:opacity-60"
      >
        <option>No models available</option>
      </select>
    );
  }

  return (
    <select
      value={selected}
      onChange={(e) => onChange(e.target.value)}
      className="rounded-[9px] border border-white/20 bg-white/10 px-3 py-1.5 text-xs text-banner-text focus:border-brand focus:outline-none"
    >
      {models.map((m) => (
        <option key={m} value={m}>
          {m}
        </option>
      ))}
    </select>
  );
}
