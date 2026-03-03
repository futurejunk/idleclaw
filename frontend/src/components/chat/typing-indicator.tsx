export function TypingIndicator() {
  return (
    <div className="flex justify-start">
      <div className="rounded-[20px] bg-surface shadow-sm px-4 py-3">
        <div className="flex gap-1 items-center h-3">
          <span className="h-1.5 w-1.5 rounded-full bg-muted animate-bounce [animation-delay:0ms]" />
          <span className="h-1.5 w-1.5 rounded-full bg-muted animate-bounce [animation-delay:150ms]" />
          <span className="h-1.5 w-1.5 rounded-full bg-muted animate-bounce [animation-delay:300ms]" />
        </div>
      </div>
    </div>
  );
}
