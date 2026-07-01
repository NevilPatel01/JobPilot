import { API_URL, getAuthToken, request } from "./_client";
import type { ResumeDocument, ResumeStatus, ResumeContent, CoverLetterMeta, ChatMessage, ChatExchange, ATSScore } from "@/types/resume";

export const resumesApi = {
  getResumes: (search?: string) => {
    const qs = search ? `?search=${encodeURIComponent(search)}` : "";
    return request<{ resumes: ResumeDocument[]; total: number }>(`/api/v1/resumes${qs}`);
  },

  getResume: (id: string) =>
    request<ResumeDocument>(`/api/v1/resumes/${id}`),

  getResumeStatus: (id: string) =>
    request<ResumeStatus>(`/api/v1/resumes/${id}/status`),

  createResume: (data: {
    title: string;
    job_title?: string;
    company_name?: string;
    job_url?: string;
    job_description: string;
    company_url?: string;
    source_type?: string;
    content_json?: ResumeContent;
    create_cover_letter?: boolean;
    cover_letter_meta?: CoverLetterMeta;
  }) =>
    request<ResumeDocument>("/api/v1/resumes", { method: "POST", body: JSON.stringify(data) }),

  updateResume: (
    id: string,
    data: Partial<{
      title: string;
      company_name: string;
      content_json: ResumeContent;
      latex_source: string;
      application_id: string;
    }>,
    options?: { rescore?: boolean }
  ) => {
    const qs = options?.rescore ? "?rescore=true" : "";
    return request<ResumeDocument>(`/api/v1/resumes/${id}${qs}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  deleteResume: (id: string) =>
    request<{ ok: boolean }>(`/api/v1/resumes/${id}`, { method: "DELETE" }),

  regenerateResume: (id: string) =>
    request<ResumeDocument>(`/api/v1/resumes/${id}/regenerate`, { method: "POST" }),

  regenerateTailoredResume: (id: string, aggressive = false) =>
    request<ResumeDocument>(`/api/v1/resumes/${id}/regenerate/resume${aggressive ? "?aggressive=true" : ""}`, { method: "POST" }),

  getResumeLatex: (id: string) =>
    request<{ latex: string }>(`/api/v1/resumes/${id}/preview`),

  regenerateResumeLatex: (id: string) =>
    request<ResumeDocument>(`/api/v1/resumes/${id}/regenerate-latex`, { method: "POST" }),

  downloadResumePdf: async (id: string, options?: { inline?: boolean }): Promise<Blob> => {
    const token = getAuthToken();
    const qs = options?.inline ? "?inline=true" : "";
    const res = await fetch(`${API_URL}/api/v1/resumes/${id}/pdf${qs}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "PDF export failed");
    }
    return res.blob();
  },

  getResumeMessages: (id: string) =>
    request<ChatMessage[]>(`/api/v1/resumes/${id}/messages`),

  sendResumeChat: (id: string, message: string) =>
    request<ChatExchange>(`/api/v1/resumes/${id}/chat`, {
      method: "POST",
      body: JSON.stringify({ message }),
    }),

  atsFixResume: (id: string) =>
    request<ChatExchange>(`/api/v1/resumes/${id}/ats-fix`, { method: "POST" }),

  handleResumeChange: (id: string, change_id: string, action: "accept" | "reject") =>
    request<{
      ok: boolean;
      content_json: ResumeContent;
      latex_source?: string | null;
      ats_score?: ATSScore | null;
    }>(`/api/v1/resumes/${id}/changes`, { method: "POST", body: JSON.stringify({ change_id, action }) }),

  handleResumeChangesBatch: (id: string, change_ids: string[], action: "accept" | "reject") =>
    request<{
      ok: boolean;
      content_json: ResumeContent;
      latex_source?: string | null;
      ats_score?: ATSScore | null;
    }>(`/api/v1/resumes/${id}/changes/batch`, {
      method: "POST",
      body: JSON.stringify({ change_ids, action }),
    }),

  runATSScore: (id: string) =>
    request<ATSScore>(`/api/v1/resumes/${id}/ats-score`, { method: "POST" }),

  getATSScore: (id: string) =>
    request<ATSScore | null>(`/api/v1/resumes/${id}/ats-score`),

  getATSScoreHistory: (id: string, limit = 5) =>
    request<{ scores: ATSScore[]; total: number }>(
      `/api/v1/resumes/${id}/ats-score/history?limit=${limit}`
    ),
};
