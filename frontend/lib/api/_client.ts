const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const AUTH_DISABLED =
  process.env.AUTH_DISABLED === "true" || process.env.NEXT_PUBLIC_AUTH_DISABLED === "true";

let authToken: string | null = null;
let authReadyResolver: (() => void) | null = null;
const authReadyPromise: Promise<void> = AUTH_DISABLED
  ? Promise.resolve()
  : new Promise<void>((resolve) => {
      authReadyResolver = resolve;
    });

export function markAuthReady() {
  authReadyResolver?.();
  authReadyResolver = null;
}

export async function waitForAuthReady() {
  await authReadyPromise;
}

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

export async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  await waitForAuthReady();
  const token = getAuthToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });
  if (!res.ok) {
    const detail = await readErrorDetail(res);
    if (res.status === 401 || isInvalidToken(detail)) setAuthToken(null);
    throw new Error(detail);
  }
  return res.json();
}

export { API_URL };
