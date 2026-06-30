import { API_URL, getAuthToken, isInvalidToken, readErrorDetail, request, setAuthToken } from "./_client";
import type { UserProfile, MatchScore } from "@/types";
import type { ResumeContent, StructuredProfile } from "@/types/resume";

export const profileApi = {
  getProfile: () => request<UserProfile>("/api/v1/profile"),

  updateProfile: (data: { resume_text?: string; skills_keywords?: string[] }) =>
    request<UserProfile>("/api/v1/profile", { method: "PUT", body: JSON.stringify(data) }),

  getMatchScores: () => request<MatchScore[]>("/api/v1/profile/match-scores"),

  getScoringStatus: () => request<{ ready: boolean }>("/api/v1/profile/scoring-status"),

  getStructuredProfile: () =>
    request<StructuredProfile>("/api/v1/profile/structured"),

  updateStructuredProfile: (content: ResumeContent) =>
    request<StructuredProfile>("/api/v1/profile/structured", {
      method: "PUT",
      body: JSON.stringify({ content }),
    }),

  uploadResumePdf: async (file: File) => {
    const token = getAuthToken();
    const form = new FormData();
    form.append("file", file);
    const upload = (bearerToken: string | null) =>
      fetch(`${API_URL}/api/v1/profile/upload-resume`, {
        method: "POST",
        headers: bearerToken ? { Authorization: `Bearer ${bearerToken}` } : {},
        body: form,
      });

    let res = await upload(token);
    if (!res.ok) {
      const detail = await readErrorDetail(res, "Upload failed");
      if (token && isInvalidToken(detail)) {
        setAuthToken(null);
        res = await upload(null);
        if (res.ok) {
          return res.json() as Promise<{
            content: ResumeContent;
            warnings: string[];
            confidence: number;
            section_counts: Record<string, number>;
          }>;
        }
        throw new Error(await readErrorDetail(res, "Upload failed"));
      }
      throw new Error(detail);
    }
    return res.json() as Promise<{
      content: ResumeContent;
      warnings: string[];
      confidence: number;
      section_counts: Record<string, number>;
    }>;
  },

  getProfilePreviewPdf: async (): Promise<Blob> => {
    const token = getAuthToken();
    const res = await fetch(`${API_URL}/api/v1/profile/preview-pdf`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "PDF preview failed");
    }
    return res.blob();
  },
};
