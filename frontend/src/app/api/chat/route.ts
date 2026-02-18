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

  const stream = createUIMessageStream({
    execute: async ({ writer }) => {
      const res = await fetch(`${BACKEND_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model: body.model ?? "llama3.2:1b", messages }),
      });

      if (!res.ok || !res.body) {
        throw new Error(`Backend returned ${res.status}`);
      }

      writer.write({ type: "start" });
      writer.write({ type: "text-start", id: partId });

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

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
            const token = chunk.choices?.[0]?.delta?.content;
            if (token) {
              writer.write({ type: "text-delta", delta: token, id: partId });
            }
          } catch {
            // skip non-JSON lines
          }
        }
      }

      writer.write({ type: "text-end", id: partId });
      writer.write({ type: "finish", finishReason: "stop" });
    },
  });

  return createUIMessageStreamResponse({ stream });
}
