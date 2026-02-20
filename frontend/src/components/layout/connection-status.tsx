import type { ConnectionState } from "@/hooks/use-health";

interface ConnectionStatusProps {
  state: ConnectionState;
  nodeCount: number;
}

export function ConnectionStatus({ state, nodeCount }: ConnectionStatusProps) {
  const dot =
    state === "online"
      ? "bg-green-500"
      : state === "no-nodes"
        ? "bg-amber-400"
        : "bg-red-500";

  const label =
    state === "online"
      ? `${nodeCount} node${nodeCount === 1 ? "" : "s"} online`
      : state === "no-nodes"
        ? "No nodes"
        : "Offline";

  return (
    <div className="flex items-center gap-1.5 text-xs text-zinc-400">
      <span className={`h-2 w-2 rounded-full ${dot}`} />
      {label}
    </div>
  );
}
