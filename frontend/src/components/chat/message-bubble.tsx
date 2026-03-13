"use client";

import { isValidElement, useState, type ReactNode } from "react";
import type { UIMessage } from "ai";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Copy, Check, RefreshCw } from "lucide-react";
import { CodeBlock } from "./code-block";

function extractCodeFromPre(children: ReactNode): { code: string; language?: string } | null {
  // react-markdown renders fenced blocks as <pre><code className="language-x">...</code></pre>
  // Extract the text and optional language from the child <code> element.
  if (!isValidElement(children)) return null;
  const props = children.props as { className?: string; children?: ReactNode };
  const match = props.className?.match(/language-(\w+)/);
  const code = String(props.children ?? "").replace(/\n$/, "");
  return { code, language: match?.[1] };
}

const markdownComponents = {
  pre({ children }: { children?: ReactNode }) {
    const extracted = extractCodeFromPre(children);
    if (extracted) {
      return <CodeBlock code={extracted.code} language={extracted.language} />;
    }
    return <pre>{children}</pre>;
  },
  code({ className, children }: { className?: string; children?: ReactNode }) {
    if (className?.startsWith("language-")) {
      return <code className={className}>{children}</code>;
    }
    return (
      <code className="rounded-[8px] bg-accent-soft px-1.5 py-0.5 text-xs font-mono">
        {children}
      </code>
    );
  },
  a({ children, href, ...props }: { children?: ReactNode; href?: string }) {
    const isSafeHref = href && /^https?:/i.test(href);
    if (!isSafeHref) {
      return <span>{children}</span>;
    }
    return (
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className="text-brand underline hover:text-brand-hover"
        {...props}
      >
        {children}
      </a>
    );
  },
};

interface MessageBubbleProps {
  message: UIMessage;
  isStreaming?: boolean;
  onRegenerate?: () => void;
}

export function MessageBubble({ message, isStreaming, onRegenerate }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const [copied, setCopied] = useState(false);

  const reasoningText = message.parts
    .filter((p): p is { type: "reasoning"; text: string } => p.type === "reasoning")
    .map((p) => p.text)
    .join("");

  const text = message.parts
    .filter((p): p is { type: "text"; text: string } => p.type === "text")
    .map((p) => p.text)
    .join("");

  const hasReasoning = reasoningText.length > 0;
  const hasContent = text.length > 0;
  // Thinking is "active" when we have reasoning but no content yet and still streaming
  const isThinking = hasReasoning && !hasContent && !!isStreaming;

  // Don't render empty assistant bubble (SDK creates it before tokens arrive)
  if (!isUser && !hasReasoning && !hasContent) return null;

  const handleCopy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={`group flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div className="max-w-[90%] sm:max-w-[80%]">
        <div
          className={`rounded-[20px] px-4 py-2.5 text-sm leading-relaxed ${
            isUser
              ? "bg-gradient-to-br from-brand to-brand-hover text-white"
              : "bg-surface text-foreground shadow-sm"
          }`}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{text}</p>
          ) : (
            <>
              {hasReasoning && (
                <details open={isThinking} className="mb-2">
                  <summary className="cursor-pointer text-xs text-muted select-none hover:text-foreground/70 transition-colors">
                    {isThinking ? "Thinking..." : "Thought process"}
                  </summary>
                  <div className="mt-1.5 text-xs italic text-muted/80 leading-relaxed border-l-2 border-border-ui pl-3">
                    {reasoningText}
                  </div>
                </details>
              )}
              <div className="prose prose-sm max-w-none">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={markdownComponents}
                >
                  {text}
                </ReactMarkdown>
              </div>
            </>
          )}
        </div>
        {!isUser && !isStreaming && hasContent && (
          <div className="mt-1 flex gap-1 opacity-0 transition-opacity group-hover:opacity-100">
            <button
              onClick={handleCopy}
              className="flex items-center gap-1 rounded-lg px-2 py-1 text-xs text-muted hover:text-foreground hover:bg-surface transition-colors"
              aria-label={copied ? "Copied" : "Copy message"}
            >
              {copied ? <Check size={14} /> : <Copy size={14} />}
              {copied ? "Copied" : "Copy"}
            </button>
            {onRegenerate && (
              <button
                onClick={onRegenerate}
                className="flex items-center gap-1 rounded-lg px-2 py-1 text-xs text-muted hover:text-foreground hover:bg-surface transition-colors"
                aria-label="Regenerate response"
              >
                <RefreshCw size={14} />
                Regenerate
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
