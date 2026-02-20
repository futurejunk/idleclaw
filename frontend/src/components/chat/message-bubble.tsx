import { isValidElement, type ReactNode } from "react";
import type { UIMessage } from "ai";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
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

export function MessageBubble({ message }: { message: UIMessage }) {
  const isUser = message.role === "user";
  const text = message.parts
    .filter((p): p is { type: "text"; text: string } => p.type === "text")
    .map((p) => p.text)
    .join("");

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[90%] sm:max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
          isUser
            ? "bg-blue-600 text-white"
            : "bg-zinc-800 text-zinc-100"
        }`}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap">{text}</p>
        ) : (
          <div className="prose prose-invert prose-sm max-w-none">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                pre({ children }) {
                  const extracted = extractCodeFromPre(children);
                  if (extracted) {
                    return <CodeBlock code={extracted.code} language={extracted.language} />;
                  }
                  return <pre>{children}</pre>;
                },
                code({ className, children }) {
                  // Only handles inline code — fenced blocks are handled by pre() above
                  if (className?.startsWith("language-")) {
                    // Inside a <pre> — pre() will handle this
                    return <code className={className}>{children}</code>;
                  }
                  return (
                    <code className="rounded bg-zinc-900 px-1 py-0.5 text-xs font-mono">
                      {children}
                    </code>
                  );
                },
                a({ children, href, ...props }) {
                  return (
                    <a
                      href={href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-400 underline hover:text-blue-300"
                      {...props}
                    >
                      {children}
                    </a>
                  );
                },
              }}
            >
              {text}
            </ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}
