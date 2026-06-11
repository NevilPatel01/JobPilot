import { withAuth } from "next-auth/middleware";
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const authDisabled =
  process.env.AUTH_DISABLED === "true" || process.env.NEXT_PUBLIC_AUTH_DISABLED === "true";

const protectedMiddleware = withAuth({
  pages: { signIn: "/login" },
});

export default function middleware(req: NextRequest) {
  if (authDisabled) {
    return NextResponse.next();
  }
  return (protectedMiddleware as (req: NextRequest) => ReturnType<typeof NextResponse.next>)(req);
}

export const config = {
  matcher: [
    "/",
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
