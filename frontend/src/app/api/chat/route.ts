import { createUIMessageStream, createUIMessageStreamResponse, generateId } from "ai";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export async function POST(req: Request) {
  const body = await req.json();

  const messages = (body.messages ?? []).map(
    (m: { role: string; parts?: { type: string; text?: string }[] }) => ({
      role: m.role,
      content: (m.parts ?? [])
        .filter((p) => p.type === "text")
        .map((p) => p.text ?? "")
        .join(""),
    })
  );

  const partId = generateId();
  const reasoningId = generateId();

  const stream = createUIMessageStream({
    execute: async ({ writer }) => {
      const res = await fetch(`${BACKEND_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model: body.model, messages, think: body.think ?? false }),
      });

      if (!res.ok || !res.body) {
        throw new Error(`Backend returned ${res.status}`);
      }

      writer.write({ type: "start" });

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let inReasoning = false;
      let inText = false;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith("data:")) continue;

          const data = trimmed.slice(5).trim();
          if (data === "[DONE]") break;

          try {
            const chunk = JSON.parse(data);
            const delta = chunk.choices?.[0]?.delta;

            // Handle tool call status events
            if (delta?.tool_call) {
              const { name, status: toolStatus } = delta.tool_call;
              if (toolStatus === "executing") {
                if (inReasoning) {
                  writer.write({ type: "reasoning-end", id: reasoningId });
                  inReasoning = false;
                }
                if (!inText) {
                  writer.write({ type: "text-start", id: partId });
                  inText = true;
                }
                const label = name === "web_search" ? "Searching the web" : `Running ${name}`;
                writer.write({ type: "text-delta", delta: `\n\n---\n**${label}...**\n---\n\n`, id: partId });
              }
              continue;
            }

            const token = delta?.content;
            const isReasoning = delta?.reasoning === true;

            if (token) {
              if (isReasoning) {
                if (!inReasoning) {
                  writer.write({ type: "reasoning-start", id: reasoningId });
                  inReasoning = true;
                }
                writer.write({ type: "reasoning-delta", delta: token, id: reasoningId });
              } else {
                if (inReasoning) {
                  writer.write({ type: "reasoning-end", id: reasoningId });
                  inReasoning = false;
                }
                if (!inText) {
                  writer.write({ type: "text-start", id: partId });
                  inText = true;
                }
                writer.write({ type: "text-delta", delta: token, id: partId });
              }
            }
          } catch {
            // skip non-JSON lines
          }
        }
      }

      if (inReasoning) {
        writer.write({ type: "reasoning-end", id: reasoningId });
      }
      if (!inText) {
        writer.write({ type: "text-start", id: partId });
      }
      writer.write({ type: "text-end", id: partId });
      writer.write({ type: "finish", finishReason: "stop" });
    },
  });

  return createUIMessageStreamResponse({ stream });
}
