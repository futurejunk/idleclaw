const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export async function GET() {
  try {
    const res = await fetch(`${BACKEND_URL}/health`);
    if (!res.ok) throw new Error(`Backend returned ${res.status}`);
    const data = await res.json();
    return Response.json(data);
  } catch {
    return Response.json(
      { status: "unhealthy", node_count: 0 },
      { status: 503 },
    );
  }
}
