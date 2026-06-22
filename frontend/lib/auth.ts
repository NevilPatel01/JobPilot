import type { NextAuthOptions } from "next-auth";
import GitHubProvider from "next-auth/providers/github";
import GoogleProvider from "next-auth/providers/google";
import { authDisabled, hasGithub, hasGoogle } from "@/lib/authFlags";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export { authDisabled, hasGithub, hasGoogle };

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
      if (account && profile) {
        const provider = account.provider;
        const oauthId = account.providerAccountId;
        const email = profile.email || user?.email || `${oauthId}@${provider}.local`;
        try {
          const res = await fetch(`${API_URL}/api/v1/auth/callback`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              email,
              name: profile.name || user?.name,
              avatar_url: (profile as { image?: string }).image,
              oauth_provider: provider,
              oauth_id: oauthId,
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
