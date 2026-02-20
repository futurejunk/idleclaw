"use client";

import { useRef, useEffect } from "react";
import { Send } from "lucide-react";

interface ChatInputProps {
  input: string;
  isLoading: boolean;
  disabled: boolean;
  focusTrigger?: number;
  onInputChange: (value: string) => void;
  onSend: () => void;
}

export function ChatInput({ input, isLoading, disabled, focusTrigger, onInputChange, onSend }: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // JS fallback for auto-grow (Safari doesn't support field-sizing: content)
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }, [input]);

  // Focus textarea when focusTrigger changes
  useEffect(() => {
    if (focusTrigger) textareaRef.current?.focus();
  }, [focusTrigger]);

  return (
    <div className="border-t border-zinc-800 bg-zinc-950 p-3 sm:p-4">
      <div className="mx-auto flex max-w-3xl items-end gap-2 sm:gap-3">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => onInputChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              onSend();
            }
          }}
          placeholder="Send a message..."
          disabled={isLoading || disabled}
          rows={1}
          className="flex-1 resize-none rounded-xl border border-zinc-700 bg-zinc-900 px-4 py-3 text-sm text-zinc-100 placeholder-zinc-500 focus:border-blue-500 focus:outline-none disabled:opacity-50 [field-sizing:content] max-h-40"
        />
        <button
          type="button"
          onClick={() => onSend()}
          disabled={isLoading || disabled || !input.trim()}
          className="rounded-xl bg-blue-600 p-3 text-white hover:bg-blue-500 disabled:opacity-50 disabled:hover:bg-blue-600"
        >
          <Send size={18} />
        </button>
      </div>
    </div>
  );
}
