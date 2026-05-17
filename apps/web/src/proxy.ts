import { NextResponse, type NextRequest } from "next/server";

/**
 * Edge-safe proxy: does a lightweight cookie check to gate /app routes.
 * The full session validation (DB lookup) happens in apps/web/src/app/app/layout.tsx.
 */
export default function proxy(req: NextRequest) {
  const isOnApp = req.nextUrl.pathname.startsWith("/app");
  if (!isOnApp) return NextResponse.next();

  // next-auth v5 stores the session token in one of these cookies
  const hasSession =
    req.cookies.has("authjs.session-token") ||
    req.cookies.has("__Secure-authjs.session-token") ||
    req.cookies.has("next-auth.session-token") ||
    req.cookies.has("__Secure-next-auth.session-token");

  if (!hasSession) {
    const url = new URL("/login", req.url);
    url.searchParams.set("callbackUrl", req.nextUrl.pathname);
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/app/:path*"],
};
