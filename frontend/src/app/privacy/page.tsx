import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Privacy — IdleClaw",
  description: "How IdleClaw handles your data.",
};

export default function PrivacyPage() {
  return (
    <div className="min-h-dvh bg-background text-foreground">
      <header className="border-b border-banner/20 bg-banner px-4 py-3 sm:px-6 sm:py-4">
        <Link href="/" className="text-lg font-semibold font-heading text-brand hover:opacity-80">
          IdleClaw
        </Link>
      </header>
      <main className="mx-auto max-w-2xl px-4 py-10 sm:px-6">
        <h1 className="text-2xl font-semibold font-heading text-foreground">Privacy</h1>
        <p className="mt-2 text-sm text-muted">
          This is not a legal document. It is an honest explanation of how your data flows through
          IdleClaw.
        </p>

        <section className="mt-8 space-y-6 text-sm leading-relaxed">
          <div>
            <h2 className="font-semibold text-foreground">How it works</h2>
            <p className="mt-1 text-muted">
              When you send a message, it is routed through the IdleClaw server to a community
              volunteer node running a local AI model. The volunteer&apos;s machine processes your
              prompt and streams a response back through the server to your browser.
            </p>
          </div>

          <div>
            <h2 className="font-semibold text-foreground">No data is stored</h2>
            <p className="mt-1 text-muted">
              IdleClaw does not store your messages, conversations, or any user data. There are no
              accounts, no cookies, and no tracking. Messages pass through the server in transit and
              are not logged or persisted.
            </p>
          </div>

          <div>
            <h2 className="font-semibold text-foreground">Community contributor routing</h2>
            <p className="mt-1 text-muted">
              Your prompts are processed on machines operated by community volunteers. These
              contributors share their GPU compute to power the network. While prompts pass through
              their machines for inference, contributors do not have access to a conversation history
              or user identity — each request is stateless.
            </p>
          </div>

          <div>
            <h2 className="font-semibold text-foreground">What this means for you</h2>
            <p className="mt-1 text-muted">
              Do not send sensitive personal information (passwords, financial details, private keys)
              through IdleClaw. Treat it like a public conversation — your prompts are processed on
              community hardware.
            </p>
          </div>
          <div>
            <h2 className="font-semibold text-foreground">Known risks</h2>
            <p className="mt-1 text-muted">
              IdleClaw is an open, community-run network. There are inherent risks you should be aware
              of:
            </p>
            <ul className="mt-2 list-disc pl-5 space-y-1.5 text-muted">
              <li>
                <strong className="text-foreground">Unverified nodes.</strong> Contributors run their
                own hardware. A malicious contributor could theoretically log prompts or return
                manipulated responses. Most traffic is handled by seed nodes we operate, but community
                nodes are not audited.
              </li>
              <li>
                <strong className="text-foreground">No content moderation.</strong> There is no
                server-side filtering of prompts or responses. Models have their own built-in safety
                tuning, but IdleClaw does not add an additional moderation layer.
              </li>
              <li>
                <strong className="text-foreground">No authentication.</strong> There are no user
                accounts. Anyone can use the chat, and rate limiting is the only abuse protection.
              </li>
            </ul>
          </div>
        </section>

        <div className="mt-10 border-t border-border pt-6">
          <Link href="/" className="text-sm text-brand hover:text-brand-hover">
            &larr; Back to chat
          </Link>
        </div>
      </main>
    </div>
  );
}
