import { auth } from "@/auth";
import { NextResponse } from "next/server";

export default auth((req) => {
  const isOnApp = req.nextUrl.pathname.startsWith("/app");
  if (!isOnApp) return NextResponse.next();
  if (!req.auth) {
    const url = new URL("/login", req.url);
    url.searchParams.set("callbackUrl", req.nextUrl.pathname);
    return NextResponse.redirect(url);
  }
  return NextResponse.next();
});

export const config = {
  matcher: ["/app/:path*"],
};
