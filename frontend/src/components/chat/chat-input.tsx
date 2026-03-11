"use client";

import { useRef, useEffect } from "react";
import Link from "next/link";
import { Send, Square } from "lucide-react";

interface ChatInputProps {
  input: string;
  isLoading: boolean;
  disabled: boolean;
  focusTrigger?: number;
  onInputChange: (value: string) => void;
  onSend: () => void;
  onStop: () => void;
}

export function ChatInput({ input, isLoading, disabled, focusTrigger, onInputChange, onSend, onStop }: ChatInputProps) {
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
    <div className="border-t border-banner/20 p-3 sm:p-4" style={{ background: "linear-gradient(to right, #2a1f19, #1a110c)" }}>
      <div className="mx-auto flex max-w-3xl items-end gap-2 sm:gap-3">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => onInputChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              if (input.trim()) onSend();
            }
          }}
          placeholder="Send a message..."
          disabled={disabled}
          rows={1}
          className="flex-1 resize-none rounded-[14px] border border-white/20 bg-white/10 px-4 py-3 text-sm text-banner-text placeholder-banner-text/50 focus:border-brand focus:outline-none disabled:opacity-50 [field-sizing:content] max-h-40"
        />
        {isLoading ? (
          <button
            type="button"
            onClick={onStop}
            className="rounded-[14px] bg-gradient-to-br from-brand to-brand-hover p-3 text-white hover:opacity-90"
          >
            <Square size={18} fill="currentColor" />
          </button>
        ) : (
          <button
            type="button"
            onClick={() => onSend()}
            disabled={disabled || !input.trim()}
            className="rounded-[14px] bg-gradient-to-br from-brand to-brand-hover p-3 text-white hover:opacity-90 disabled:opacity-50"
          >
            <Send size={18} />
          </button>
        )}
      </div>
      <p className="mx-auto mt-1.5 max-w-3xl text-center text-[11px] text-banner-text/40">
        Messages are processed by community GPU contributors{" "}
        <Link href="/privacy" className="underline hover:text-banner-text/60">
          · Privacy
        </Link>
      </p>
    </div>
  );
}
