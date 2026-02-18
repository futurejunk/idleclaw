const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export async function GET() {
  const res = await fetch(`${BACKEND_URL}/api/models`);
  const data = await res.json();
  return Response.json(data);
}
