import type { NextAuthOptions } from "next-auth";
import type { JWT } from "next-auth/jwt";
import GitHubProvider from "next-auth/providers/github";
import GoogleProvider from "next-auth/providers/google";
import { authDisabled, hasGithub, hasGoogle } from "@/lib/authFlags";
import { needsBackendExchange } from "@/lib/authRecovery";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export { authDisabled, hasGithub, hasGoogle };

/** Exchange OAuth identity for a backend JWT and store it on the NextAuth token.
 * Upserts by (oauth_provider, oauth_id) server-side, so it always resolves to the
 * user's existing account — safe to retry on later requests, not just at sign-in. */
async function exchangeForBackendToken(token: JWT): Promise<void> {
  if (!token.oauthProvider || !token.oauthId) return;
  try {
    const res = await fetch(`${API_URL}/api/v1/auth/callback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: token.email || `${token.oauthId}@${token.oauthProvider}.local`,
        name: token.name,
        avatar_url: token.picture,
        oauth_provider: token.oauthProvider,
        oauth_id: token.oauthId,
      }),
    });
    if (res.ok) {
      const result = await res.json();
      token.accessToken = result.access_token;
      token.userId = result.user.id;
    }
  } catch (e) {
    console.error("Auth callback failed:", e);
  }
}

export const authOptions: NextAuthOptions = {
  providers: [
    ...(process.env.GOOGLE_CLIENT_ID && process.env.GOOGLE_CLIENT_SECRET
      ? [
          GoogleProvider({
            clientId: process.env.GOOGLE_CLIENT_ID,
            clientSecret: process.env.GOOGLE_CLIENT_SECRET,
          }),
        ]
      : []),
    ...(process.env.GITHUB_ID && process.env.GITHUB_SECRET
      ? [
          GitHubProvider({
            clientId: process.env.GITHUB_ID,
            clientSecret: process.env.GITHUB_SECRET,
          }),
        ]
      : []),
  ],
  pages: { signIn: "/login" },
  callbacks: {
    async jwt({ token, account, profile, user }) {
      // At sign-in, persist the identity we need to (re)exchange for a backend token.
      if (account && profile) {
        token.oauthProvider = account.provider;
        token.oauthId = account.providerAccountId;
        token.email = profile.email || user?.email || `${account.providerAccountId}@${account.provider}.local`;
        token.name = profile.name || user?.name || token.name;
        token.picture = (profile as { image?: string }).image || token.picture;
      }
      // Mint the backend token at sign-in, and self-heal any existing session that
      // has an identity but never got one (e.g. the backend was down at sign-in, or
      // the session predates this exchange) — this is why "already created accounts"
      // were stuck on "Not authenticated".
      if (needsBackendExchange(token)) {
        await exchangeForBackendToken(token);
      }
      return token;
    },
    async session({ session, token }) {
      if (token.accessToken) {
        session.accessToken = token.accessToken as string;
      }
      return session;
    },
  },
  secret: process.env.NEXTAUTH_SECRET,
};
