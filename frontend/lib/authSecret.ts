/**
 * Single source of truth for the NextAuth secret.
 *
 * Both NextAuth (which *encodes* the session cookie) and the Edge middleware's
 * `getToken` (which *decodes* it) MUST use the identical secret. If they ever
 * disagree, `getToken` returns null while `useSession` reports "authenticated",
 * producing an infinite /login <-> /dashboard redirect loop.
 *
 * In development we fall back to a stable constant so the two sides always
 * agree even when NEXTAUTH_SECRET is not configured. In production we return
 * undefined when it's missing so NextAuth fails loudly instead of silently
 * looping — set NEXTAUTH_SECRET (e.g. `openssl rand -base64 32`).
 */
const DEV_FALLBACK_SECRET = "jobpilot-dev-insecure-secret-change-me";

export const nextAuthSecret =
  process.env.NEXTAUTH_SECRET ||
  (process.env.NODE_ENV !== "production" ? DEV_FALLBACK_SECRET : undefined);
