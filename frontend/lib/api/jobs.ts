import { request } from "./_client";
import type { Job, InboxJob, InboxManualCreate, InboxStatus, ScoringPreferences } from "@/types";

export const jobsApi = {
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
    return request<{ jobs: Job[]; total: number }>(`/api/v1/jobs${qs}`);
  },

  importJobUrl: (url: string) =>
    request<Job>("/api/v1/jobs/import-url", { method: "POST", body: JSON.stringify({ url }) }),
};

export const inboxApi = {
  getInbox: (params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return request<{ items: InboxJob[]; total: number; page: number; limit: number }>(`/api/v1/inbox${qs}`);
  },

  addInboxJob: (data: InboxManualCreate) =>
    request<InboxJob>("/api/v1/inbox/manual", { method: "POST", body: JSON.stringify(data) }),

  saveJobToInbox: (jobId: string) =>
    request<InboxJob>(`/api/v1/inbox/jobs/${jobId}`, { method: "POST" }),

  importInboxUrl: (url: string) =>
    request<InboxJob>("/api/v1/inbox/import-url", { method: "POST", body: JSON.stringify({ url }) }),

  updateInboxStatus: (id: string, status: InboxStatus) =>
    request<InboxJob>(`/api/v1/inbox/${id}/status`, { method: "PATCH", body: JSON.stringify({ status }) }),

  rescoreInbox: () => request<{ scored: number }>("/api/v1/inbox/rescore", { method: "POST" }),

  rescoreInboxJob: (id: string) =>
    request<InboxJob>(`/api/v1/inbox/${id}/rescore`, { method: "POST" }),

  updateInboxResumeCategory: (id: string, category: string | null) =>
    request<InboxJob>(`/api/v1/inbox/${id}/resume-category`, {
      method: "PATCH",
      body: JSON.stringify({ category }),
    }),

  generateInboxResume: (id: string, data: { category?: string; create_cover_letter?: boolean } = {}) =>
    request<{ resume_id: string; status: string; inbox_status: string; category: string; existing: boolean }>(
      `/api/v1/inbox/${id}/generate-resume`,
      { method: "POST", body: JSON.stringify(data) }
    ),

  getScoringPreferences: () =>
    request<ScoringPreferences>("/api/v1/inbox/preferences"),

  updateScoringPreferences: (
    data: Pick<ScoringPreferences, "work_authorization" | "target_provinces" | "relocation_open" | "threshold_overrides">
  ) =>
    request<ScoringPreferences>("/api/v1/inbox/preferences", { method: "PUT", body: JSON.stringify(data) }),
};

export const scraperApi = {
  triggerScraper: () =>
    request<{ new_jobs: number; message: string }>("/api/v1/scraper/trigger", { method: "POST" }),

  getScraperSources: () =>
    request<{
      sources: {
        source: string;
        display_name: string;
        enabled: boolean;
        job_count: number;
        credential_status?: string;
        last_error?: string | null;
      }[];
      last_run?: string | null;
    }>("/api/v1/scraper/sources"),

  updateScraperSource: (source: string, enabled: boolean) =>
    request<{ source: string; enabled: boolean }>(`/api/v1/scraper/sources/${source}`, {
      method: "PATCH",
      body: JSON.stringify({ enabled }),
    }),
};

export const analyticsApi = {
  getAnalytics: () =>
    request<import("@/types").AnalyticsSummary>("/api/v1/analytics/summary"),
};
