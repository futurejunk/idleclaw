import { describe, it, expect, vi, beforeEach } from "vitest";
import { POST } from "../route";

// Mock global fetch for backend calls
const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

function makeRequest(body: object): Request {
  return new Request("http://localhost:3000/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

function sseBody(chunks: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();
  const payload = chunks.map((c) => `data: ${c}\n\n`).join("") + "data: [DONE]\n\n";
  return new ReadableStream({
    start(controller) {
      controller.enqueue(encoder.encode(payload));
      controller.close();
    },
  });
}

describe("POST /api/chat", () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  it("forwards request to backend and returns streaming response", async () => {
    const chunk = JSON.stringify({
      choices: [{ delta: { content: "Hello" } }],
    });

    mockFetch.mockResolvedValueOnce(
      new Response(sseBody([chunk]), { status: 200 })
    );

    const req = makeRequest({
      messages: [{ role: "user", parts: [{ type: "text", text: "hi" }] }],
      model: "llama3.2",
    });

    const res = await POST(req);

    expect(res.status).toBe(200);
    expect(res.body).toBeTruthy();

    // Verify the backend was called with correct payload
    expect(mockFetch).toHaveBeenCalledOnce();
    const [url, opts] = mockFetch.mock.calls[0];
    expect(url).toContain("/api/chat");
    const backendBody = JSON.parse(opts.body);
    expect(backendBody.model).toBe("llama3.2");
    expect(backendBody.messages[0]).toEqual({ role: "user", content: "hi" });

    // Read the response stream to verify it contains data
    const reader = res.body!.getReader();
    const decoder = new TextDecoder();
    let output = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      output += decoder.decode(value, { stream: true });
    }
    expect(output.length).toBeGreaterThan(0);
  });

  it("returns error when backend is unreachable", async () => {
    mockFetch.mockRejectedValueOnce(new Error("fetch failed"));

    const req = makeRequest({
      messages: [{ role: "user", parts: [{ type: "text", text: "hi" }] }],
      model: "llama3.2",
    });

    const res = await POST(req);

    // The route uses createUIMessageStream which catches errors internally
    // and writes them to the stream, so we still get a 200 with an error in the stream
    expect(res.body).toBeTruthy();

    const reader = res.body!.getReader();
    const decoder = new TextDecoder();
    let output = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      output += decoder.decode(value, { stream: true });
    }
    // The stream should contain an error event
    expect(output).toContain("error");
  });
});
