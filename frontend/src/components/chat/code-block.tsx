"use client";

import { useState, useEffect } from "react";
import { Copy, Check } from "lucide-react";
import { codeToHtml } from "shiki";

interface CodeBlockProps {
  code: string;
  language?: string;
}

export function CodeBlock({ code, language }: CodeBlockProps) {
  const [html, setHtml] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    let cancelled = false;
    codeToHtml(code, {
      lang: language || "text",
      theme: "github-light",
    })
      .then((result) => {
        if (!cancelled) setHtml(result);
      })
      .catch(() => {
        // Unsupported language — fall back to plain text
        if (!cancelled) setHtml(null);
      });
    return () => { cancelled = true; };
  }, [code, language]);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="group relative my-2">
      <button
        onClick={handleCopy}
        className="absolute right-2 top-2 rounded-md bg-foreground/10 p-1.5 text-foreground/50 opacity-0 transition-opacity hover:text-foreground group-hover:opacity-100"
        title="Copy code"
      >
        {copied ? <Check size={14} /> : <Copy size={14} />}
      </button>
      {html ? (
        <div
          className="overflow-x-auto rounded-[9px] border border-border text-xs [&>pre]:p-3 [&>pre]:!bg-surface"
          dangerouslySetInnerHTML={{ __html: html }}
        />
      ) : (
        <pre className="overflow-x-auto rounded-[9px] border border-border bg-surface p-3">
          <code className="text-xs">{code}</code>
        </pre>
      )}
    </div>
  );
}
