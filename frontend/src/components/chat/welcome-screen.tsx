export const IDLECLAW_QUESTION = "What is IdleClaw?";

export const IDLECLAW_ANSWER = `**IdleClaw** is a community-powered AI inference network. It provides free AI chat — no accounts, no API keys needed.

**How it works:** Community members share their idle GPU compute by running [Ollama](https://ollama.com) with the IdleClaw node agent. When you send a message here, it gets routed to an available community node and streamed back to you.

**Want to contribute?** You can share your Ollama models directly by running the IdleClaw node agent, or if you use [OpenClaw](https://openclaw.ai) you can install the IdleClaw skill. Check out the [GitHub repo](https://github.com/futurejunk/idleclaw) for setup instructions.

**No crypto, no tokens, no accounts.** Just people sharing compute.`;

const SUGGESTIONS = [
  IDLECLAW_QUESTION,
  "Explain recursion in simple terms",
  "What are the pros and cons of microservices?",
  "Help me write a cover letter for a software role",
];

interface WelcomeScreenProps {
  onSuggestionClick: (text: string) => void;
}

export function WelcomeScreen({ onSuggestionClick }: WelcomeScreenProps) {
  return (
    <div className="flex h-full flex-col items-center justify-center px-4 text-center">
      <h2 className="text-3xl font-semibold font-heading text-brand">IdleClaw</h2>
      <p className="mt-2 text-sm text-muted">Free AI chat powered by community GPUs</p>
      <div className="mt-8 flex flex-col items-center gap-2 max-w-lg">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => onSuggestionClick(s)}
            className="rounded-[14px] border border-border-ui bg-accent-soft px-4 py-2 text-sm text-brand-hover hover:border-border-ui/80 hover:bg-brand/10 transition-colors"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}
