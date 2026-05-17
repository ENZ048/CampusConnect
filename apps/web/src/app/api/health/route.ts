import { env } from "@/lib/env";

export async function GET() {
  try {
    const res = await fetch(`${env.API_BASE_URL}/healthz`, { cache: "no-store" });
    const upstream = await res.json();
    return Response.json({ web: "ok", api: upstream.status });
  } catch {
    return Response.json({ web: "ok", api: "unreachable" }, { status: 200 });
  }
}
