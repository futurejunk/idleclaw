"use client";

import { useEffect, useState } from "react";

interface HealthResponse {
  status: string;
  node_count: number;
}

type ConnectionState = "online" | "no-nodes" | "offline";

export function ConnectionStatus() {
  const [state, setState] = useState<ConnectionState>("offline");
  const [nodeCount, setNodeCount] = useState(0);

  async function poll() {
    try {
      const res = await fetch("/api/health", { signal: AbortSignal.timeout(5000) });
      if (!res.ok) throw new Error("not ok");
      const data: HealthResponse = await res.json();
      setNodeCount(data.node_count);
      setState(data.node_count >= 1 ? "online" : "no-nodes");
    } catch {
      setState("offline");
    }
  }

  useEffect(() => {
    poll();
    const id = setInterval(poll, 10_000);
    return () => clearInterval(id);
  }, []);

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
