export function TypingIndicator() {
  return (
    <div className="flex justify-start">
      <div className="rounded-2xl bg-zinc-800 px-4 py-3">
        <div className="flex gap-1 items-center h-4">
          <span className="h-2 w-2 rounded-full bg-zinc-400 animate-bounce [animation-delay:0ms]" />
          <span className="h-2 w-2 rounded-full bg-zinc-400 animate-bounce [animation-delay:150ms]" />
          <span className="h-2 w-2 rounded-full bg-zinc-400 animate-bounce [animation-delay:300ms]" />
        </div>
      </div>
    </div>
  );
}
