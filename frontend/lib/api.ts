const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

let authToken: string | null = null;

export function setAuthToken(token: string | null) {
  authToken = token;
  if (typeof window !== "undefined") {
    if (token) localStorage.setItem("jobpilot_token", token);
    else localStorage.removeItem("jobpilot_token");
  }
}

export function getAuthToken(): string | null {
  if (authToken) return authToken;
  if (typeof window !== "undefined") {
    return localStorage.getItem("jobpilot_token");
  }
  return null;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getAuthToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  return res.json();
}

export const api = {
  health: () => request<{ status: string; version: string }>("/api/v1/health"),

  authCallback: (data: {
    email: string;
    name?: string | null;
    avatar_url?: string | null;
    oauth_provider: string;
    oauth_id: string;
  }) =>
    request<{ access_token: string; user: import("@/types").UserProfile }>("/api/v1/auth/callback", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getJobs: (params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return request<{ jobs: import("@/types").Job[]; total: number }>(`/api/v1/jobs${qs}`);
  },

  importJobUrl: (url: string) =>
    request<import("@/types").Job>("/api/v1/jobs/import-url", {
      method: "POST",
      body: JSON.stringify({ url }),
    }),

  triggerScraper: () =>
    request<{ new_jobs: number; message: string }>("/api/v1/scraper/trigger", { method: "POST" }),

  getScraperSources: () => request<{ sources: { source: string; job_count: number }[] }>("/api/v1/scraper/sources"),

  getApplications: () => request<import("@/types").Application[]>("/api/v1/applications"),

  createApplication: (data: Partial<import("@/types").Application>) =>
    request<import("@/types").Application>("/api/v1/applications", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  updateApplication: (id: string, data: Partial<import("@/types").Application>) =>
    request<import("@/types").Application>(`/api/v1/applications/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  deleteApplication: (id: string) =>
    request<{ ok: boolean }>(`/api/v1/applications/${id}`, { method: "DELETE" }),

  quickSaveJob: (job_id: string) =>
    request<import("@/types").Application>("/api/v1/applications/quick-save", {
      method: "POST",
      body: JSON.stringify({ job_id }),
    }),

  getProfile: () => request<import("@/types").UserProfile>("/api/v1/profile"),

  updateProfile: (data: { resume_text?: string; skills_keywords?: string[] }) =>
    request<import("@/types").UserProfile>("/api/v1/profile", {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  getMatchScores: () => request<import("@/types").MatchScore[]>("/api/v1/profile/match-scores"),

  getAnalytics: () => request<import("@/types").AnalyticsSummary>("/api/v1/analytics/summary"),
};
