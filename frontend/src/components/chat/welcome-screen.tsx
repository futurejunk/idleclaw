const SUGGESTIONS = [
  "Explain quantum computing in simple terms",
  "Write a Python function to find prime numbers",
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
      <div className="mt-8 flex flex-wrap justify-center gap-2 max-w-lg">
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
