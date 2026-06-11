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

  // Structured profile
  getStructuredProfile: () =>
    request<import("@/types/resume").StructuredProfile>("/api/v1/profile/structured"),

  updateStructuredProfile: (content: import("@/types/resume").ResumeContent) =>
    request<import("@/types/resume").StructuredProfile>("/api/v1/profile/structured", {
      method: "PUT",
      body: JSON.stringify({ content }),
    }),

  uploadResumePdf: async (file: File) => {
    const token = getAuthToken();
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${API_URL}/api/v1/profile/upload-resume`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: form,
    });
    if (!res.ok) throw new Error("Upload failed");
    return res.json() as Promise<{ content: import("@/types/resume").ResumeContent; warnings: string[] }>;
  },

  // Settings / BYOK
  getApiKeys: () => request<import("@/types/resume").ApiKeyConfig[]>("/api/v1/settings/api-keys"),

  upsertApiKey: (data: {
    provider: string;
    api_key: string;
    base_url?: string;
    model_name?: string;
    embedding_model?: string;
    is_default?: boolean;
  }) =>
    request<import("@/types/resume").ApiKeyConfig>("/api/v1/settings/api-keys", {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  testApiKey: (data: {
    provider: string;
    api_key: string;
    base_url?: string;
    model_name?: string;
    embedding_model?: string;
  }) =>
    request<{ ok: boolean }>("/api/v1/settings/api-keys/test", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  deleteApiKey: (id: string) =>
    request<{ ok: boolean }>(`/api/v1/settings/api-keys/${id}`, { method: "DELETE" }),

  getApiTokens: () => request<import("@/types/resume").ApiToken[]>("/api/v1/settings/api-tokens"),

  createApiToken: (name: string) =>
    request<import("@/types/resume").ApiToken & { token: string }>("/api/v1/settings/api-tokens", {
      method: "POST",
      body: JSON.stringify({ name }),
    }),

  deleteApiToken: (id: string) =>
    request<{ ok: boolean }>(`/api/v1/settings/api-tokens/${id}`, { method: "DELETE" }),

  // Resumes
  getResumes: (search?: string) => {
    const qs = search ? `?search=${encodeURIComponent(search)}` : "";
    return request<{ resumes: import("@/types/resume").ResumeDocument[]; total: number }>(
      `/api/v1/resumes${qs}`
    );
  },

  getResume: (id: string) =>
    request<import("@/types/resume").ResumeDocument>(`/api/v1/resumes/${id}`),

  createResume: (data: {
    title: string;
    job_description: string;
    company_url?: string;
    source_type?: string;
    content_json?: import("@/types/resume").ResumeContent;
    create_cover_letter?: boolean;
    cover_letter_meta?: import("@/types/resume").CoverLetterMeta;
  }) =>
    request<import("@/types/resume").ResumeDocument>("/api/v1/resumes", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  updateResume: (
    id: string,
    data: Partial<{
      title: string;
      content_json: import("@/types/resume").ResumeContent;
      latex_source: string;
      application_id: string;
    }>,
    options?: { rescore?: boolean }
  ) => {
    const qs = options?.rescore ? "?rescore=true" : "";
    return request<import("@/types/resume").ResumeDocument>(`/api/v1/resumes/${id}${qs}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  deleteResume: (id: string) =>
    request<{ ok: boolean }>(`/api/v1/resumes/${id}`, { method: "DELETE" }),

  regenerateResume: (id: string) =>
    request<import("@/types/resume").ResumeDocument>(`/api/v1/resumes/${id}/regenerate`, {
      method: "POST",
    }),

  regenerateTailoredResume: (id: string) =>
    request<import("@/types/resume").ResumeDocument>(`/api/v1/resumes/${id}/regenerate/resume`, {
      method: "POST",
    }),

  getResumePreviewHtml: async (id: string): Promise<string> => {
    const token = getAuthToken();
    const res = await fetch(`${API_URL}/api/v1/resumes/${id}/preview`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    return res.text();
  },

  getResumeLatex: (id: string) =>
    request<{ latex: string }>(`/api/v1/resumes/${id}/preview?format=latex`),

  downloadResumePdf: async (id: string): Promise<Blob> => {
    const token = getAuthToken();
    const res = await fetch(`${API_URL}/api/v1/resumes/${id}/pdf`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) throw new Error("PDF export failed");
    return res.blob();
  },

  getResumeMessages: (id: string) =>
    request<import("@/types/resume").ChatMessage[]>(`/api/v1/resumes/${id}/messages`),

  sendResumeChat: (id: string, message: string) =>
    request<import("@/types/resume").ChatMessage>(`/api/v1/resumes/${id}/chat`, {
      method: "POST",
      body: JSON.stringify({ message }),
    }),

  handleResumeChange: (id: string, change_id: string, action: "accept" | "reject") =>
    request<{
      ok: boolean;
      content_json: import("@/types/resume").ResumeContent;
      ats_score?: import("@/types/resume").ATSScore | null;
    }>(`/api/v1/resumes/${id}/changes`, { method: "POST", body: JSON.stringify({ change_id, action }) }),

  runATSScore: (id: string) =>
    request<import("@/types/resume").ATSScore>(`/api/v1/resumes/${id}/ats-score`, { method: "POST" }),

  getATSScore: (id: string) =>
    request<import("@/types/resume").ATSScore | null>(`/api/v1/resumes/${id}/ats-score`),

  getATSScoreHistory: (id: string, limit = 5) =>
    request<{ scores: import("@/types/resume").ATSScore[]; total: number }>(
      `/api/v1/resumes/${id}/ats-score/history?limit=${limit}`
    ),

  // Cover letters
  getCoverLetters: () =>
    request<{ cover_letters: import("@/types/resume").CoverLetterDocument[]; total: number }>(
      "/api/v1/cover-letters"
    ),

  getCoverLetter: (id: string) =>
    request<import("@/types/resume").CoverLetterDocument>(`/api/v1/cover-letters/${id}`),

  updateCoverLetter: (id: string, data: { title?: string; content_json?: Record<string, unknown> }) =>
    request<import("@/types/resume").CoverLetterDocument>(`/api/v1/cover-letters/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  regenerateCoverLetter: (id: string) =>
    request<import("@/types/resume").CoverLetterDocument>(`/api/v1/cover-letters/${id}/regenerate`, {
      method: "POST",
    }),

  getCoverLetterPreviewHtml: async (id: string): Promise<string> => {
    const token = getAuthToken();
    const res = await fetch(`${API_URL}/api/v1/cover-letters/${id}/preview`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    return res.text();
  },
};
