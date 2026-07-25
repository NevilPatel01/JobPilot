import { signOut } from "next-auth/react";

import { authFailureAction } from "@/lib/authRecovery";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const AUTH_DISABLED =
  process.env.AUTH_DISABLED === "true" || process.env.NEXT_PUBLIC_AUTH_DISABLED === "true";

let authToken: string | null = null;

export function setAuthToken(token: string | null) {
  if (AUTH_DISABLED) {
    authToken = null;
    if (typeof window !== "undefined") localStorage.removeItem("jobpilot_token");
    return;
  }
  authToken = token;
  if (typeof window !== "undefined") {
    if (token) localStorage.setItem("jobpilot_token", token);
    else localStorage.removeItem("jobpilot_token");
  }
}

export function getAuthToken(): string | null {
  if (AUTH_DISABLED) {
    authToken = null;
    if (typeof window !== "undefined") localStorage.removeItem("jobpilot_token");
    return null;
  }
  if (authToken) return authToken;
  if (typeof window !== "undefined") return localStorage.getItem("jobpilot_token");
  return null;
}

export async function readErrorDetail(res: Response, fallback = "Request failed"): Promise<string> {
  const err = await res.json().catch(() => ({ detail: res.statusText }));
  return typeof err.detail === "string" && err.detail ? err.detail : fallback;
}

export function isInvalidToken(detail: string): boolean {
  return detail.trim().toLowerCase() === "invalid token";
}

/** True once a sign-out is in flight, so concurrent 401s don't each trigger one. */
let signingOut = false;

/** Recover from a backend 401. The stored backend token is unusable — missing,
 * expired, minted under a rotated SECRET_KEY ("Invalid token"), or pointing at a
 * user that no longer exists in this DB ("User not found"). In every case the
 * NextAuth session has drifted out of sync with the backend.
 *
 * We must clear the NextAuth session too, not just the backend token. A bare
 * redirect to /login can't recover: useSession() still reports "authenticated",
 * so /login immediately bounces the user back to the protected page, which 401s
 * again — the infinite login loop. signOut() ends the NextAuth session and lands
 * on /login (carrying the original path as callbackUrl), where a fresh sign-in
 * mints a valid backend token. No-op when auth is disabled, already on /login, or
 * a sign-out is already under way.
 *
 * The recover-or-reauthenticate decision lives in authFailureAction() (pure, unit
 * tested). Here we only apply its side effects. */
function handleAuthFailure(status: number, detail: string, hadToken: boolean): void {
  if (AUTH_DISABLED) return;
  const action = authFailureAction(status, detail, hadToken);
  if (action === "ignore") return;

  setAuthToken(null);
  if (action === "clear-token") return; // startup race — let the self-heal + retry recover

  // "reauthenticate": clear the NextAuth session too, else /login bounces the
  // still-"authenticated" user straight back and 401s again — the login loop.
  if (typeof window === "undefined" || window.location.pathname === "/login" || signingOut) {
    return;
  }
  signingOut = true;
  const from = encodeURIComponent(window.location.pathname + window.location.search);
  void signOut({ callbackUrl: `/login?callbackUrl=${from}` });
}

export async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getAuthToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });
  if (!res.ok) {
    const detail = await readErrorDetail(res);
    handleAuthFailure(res.status, detail, Boolean(token));
    throw new Error(detail);
  }
  return res.json();
}

export { API_URL };
