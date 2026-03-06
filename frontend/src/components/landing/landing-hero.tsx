"use client";

import { useEffect, useState } from "react";
import { ArrowDown, Github, Cpu, Route, MessageSquare, Shield } from "lucide-react";

interface LandingHeroProps {
  onDismiss: () => void;
  entering?: boolean;
}

export function LandingHero({ onDismiss, entering }: LandingHeroProps) {
  const [nodeCount, setNodeCount] = useState<number | null>(null);
  const [modelCount, setModelCount] = useState<number | null>(null);
  const [sliding, setSliding] = useState(false);
  const [entered, setEntered] = useState(!entering);

  useEffect(() => {
    async function fetchStats() {
      try {
        const [healthRes, modelsRes] = await Promise.all([
          fetch("/api/health", { signal: AbortSignal.timeout(5000) }),
          fetch("/api/models", { signal: AbortSignal.timeout(5000) }),
        ]);
        if (healthRes.ok) {
          const health = await healthRes.json();
          setNodeCount(health.node_count ?? 0);
        }
        if (modelsRes.ok) {
          const models = await modelsRes.json();
          setModelCount(models.models?.length ?? 0);
        }
      } catch {
        // Stats will show fallback
      }
    }
    fetchStats();
  }, []);

  // Trigger slide-down entrance
  useEffect(() => {
    if (entering && !entered) {
      requestAnimationFrame(() => setEntered(true));
    }
  }, [entering, entered]);

  const handleStart = () => {
    setSliding(true);
    setTimeout(onDismiss, 500);
  };

  return (
    <div
      className={`fixed inset-0 z-50 flex flex-col bg-background transition-transform duration-500 ease-in-out ${
        sliding ? "-translate-y-full" : entered ? "translate-y-0" : "-translate-y-full"
      }`}
    >
      <div className="px-8 py-8 sm:px-10 sm:py-10 shrink-0 text-center" style={{ background: "linear-gradient(to right, #1a110c, #2a1f19 50%, #1a110c)" }}>
        <h1 className="text-5xl sm:text-6xl font-bold font-heading text-transparent bg-clip-text bg-gradient-to-r from-brand to-brand-hover">IdleClaw</h1>
      </div>
      <div className="flex-1 overflow-y-auto flex flex-col items-center px-4 text-center py-10 sm:py-14">
      <h2 className="text-4xl sm:text-5xl font-bold font-heading text-foreground leading-tight max-w-2xl">
        Free AI chat powered by{" "}
        <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand to-brand-hover">community GPUs</span>
      </h2>
      <p className="mt-4 text-base sm:text-lg text-muted max-w-xl">
        No accounts, no API keys, no cost. Community volunteers share their idle
        GPU compute so anyone can chat with open-source AI models.
      </p>

      {/* Live stats */}
      <div className="mt-6 flex items-center gap-4 text-sm text-muted">
        {nodeCount !== null && (
          <span>
            <strong className="text-foreground">{nodeCount}</strong>{" "}
            {nodeCount === 1 ? "node" : "nodes"} online
          </span>
        )}
        {nodeCount !== null && modelCount !== null && (
          <span className="text-border-ui">|</span>
        )}
        {modelCount !== null && (
          <span>
            <strong className="text-foreground">{modelCount}</strong>{" "}
            {modelCount === 1 ? "model" : "models"} available
          </span>
        )}
      </div>

      {/* How it works */}
      <div className="mt-12 grid grid-cols-1 sm:grid-cols-3 gap-6 sm:gap-8 max-w-2xl w-full">
        <Step
          icon={<Cpu size={24} />}
          title="Contribute"
          description="Volunteers run Ollama and the IdleClaw agent, sharing their idle GPU"
        />
        <Step
          icon={<Route size={24} />}
          title="Route"
          description="The server picks the best available node for your request"
        />
        <Step
          icon={<MessageSquare size={24} />}
          title="Chat"
          description="You get free, streaming AI responses — no account needed"
        />
      </div>

      {/* Privacy & safety */}
      <div className="mt-10 flex items-start gap-3 max-w-md text-left rounded-[14px] border border-border-ui bg-surface px-4 py-3">
        <Shield size={20} className="text-brand mt-0.5 shrink-0" />
        <p className="text-xs text-muted leading-relaxed">
          <strong className="text-foreground">Text only — no files, no code execution.</strong>{" "}
          Messages pass through community nodes. Don&apos;t share sensitive info.{" "}
          <a href="/privacy" className="text-brand-hover underline hover:text-brand">
            Privacy policy
          </a>
        </p>
      </div>

      {/* CTAs */}
      <div className="mt-12 flex flex-col sm:flex-row items-center gap-3">
        <button
          onClick={handleStart}
          className="inline-flex items-center gap-2 rounded-[14px] bg-gradient-to-r from-brand to-brand-hover px-6 py-3 text-sm font-semibold text-white hover:from-brand-hover hover:to-brand transition-all cursor-pointer"
        >
          Start chatting
          <ArrowDown size={16} />
        </button>
        <a
          href="https://github.com/futurejunk/idleclaw"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 rounded-[14px] border border-border-ui bg-surface px-6 py-3 text-sm font-semibold text-brand-hover hover:bg-accent-soft transition-colors"
        >
          <Github size={16} />
          Contribute your GPU
        </a>
      </div>
      </div>
    </div>
  );
}

function Step({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="flex flex-col items-center gap-2 text-center">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-accent-soft text-brand">
        {icon}
      </div>
      <h3 className="text-sm font-semibold font-heading text-foreground">
        {title}
      </h3>
      <p className="text-xs text-muted leading-relaxed">{description}</p>
    </div>
  );
}
