"use client";

import { useEffect, useState, useCallback } from "react";

interface HealthResponse {
  status: string;
  node_count: number;
}

export type ConnectionState = "online" | "no-nodes" | "offline";

export function useHealth() {
  const [state, setState] = useState<ConnectionState>("offline");
  const [nodeCount, setNodeCount] = useState(0);

  const poll = useCallback(async () => {
    try {
      const res = await fetch("/api/health", { signal: AbortSignal.timeout(5000) });
      if (!res.ok) throw new Error("not ok");
      const data: HealthResponse = await res.json();
      setNodeCount(data.node_count);
      setState(data.node_count >= 1 ? "online" : "no-nodes");
    } catch {
      setState("offline");
    }
  }, []);

  useEffect(() => {
    poll();
    const id = setInterval(poll, 10_000);
    return () => clearInterval(id);
  }, [poll]);

  return { state, nodeCount };
}
