interface ModelSelectorProps {
  models: string[];
  selected: string;
  onChange: (model: string) => void;
  error: boolean;
}

export function ModelSelector({ models, selected, onChange, error }: ModelSelectorProps) {
  if (error) {
    return (
      <select
        disabled
        className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-1.5 text-xs text-zinc-500 disabled:opacity-60"
      >
        <option>Models unavailable</option>
      </select>
    );
  }

  if (models.length === 0) {
    return (
      <select
        disabled
        className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-1.5 text-xs text-zinc-500 disabled:opacity-60"
      >
        <option>No models available</option>
      </select>
    );
  }

  return (
    <select
      value={selected}
      onChange={(e) => onChange(e.target.value)}
      className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-1.5 text-xs text-zinc-200 focus:border-blue-500 focus:outline-none"
    >
      {models.map((m) => (
        <option key={m} value={m}>
          {m}
        </option>
      ))}
    </select>
  );
}
