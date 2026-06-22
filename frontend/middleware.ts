import { withAuth } from "next-auth/middleware";
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const authDisabled =
  process.env.AUTH_DISABLED === "true" || process.env.NEXT_PUBLIC_AUTH_DISABLED === "true";

const publicPaths = ["/", "/login"];

function isPublicPath(pathname: string): boolean {
  if (publicPaths.includes(pathname)) return true;
  if (pathname.startsWith("/api/auth")) return true;
  return false;
}

const protectedMiddleware = withAuth({
  pages: { signIn: "/login" },
});

export default function middleware(req: NextRequest) {
  if (authDisabled) {
    return NextResponse.next();
  }
  if (isPublicPath(req.nextUrl.pathname)) {
    return NextResponse.next();
  }
  return (protectedMiddleware as (req: NextRequest) => ReturnType<typeof NextResponse.next>)(req);
}

export const config = {
  matcher: [
    "/dashboard/:path*",
    "/scraper/:path*",
    "/tracker/:path*",
    "/profile/:path*",
    "/analytics/:path*",
    "/community/:path*",
    "/resumes/:path*",
    "/cover-letters/:path*",
    "/settings/:path*",
  ],
};
