import { API_URL, getAuthToken, request } from "./_client";
import type { CoverLetterDocument, ChatMessage, ChatExchange } from "@/types/resume";

export const coverLettersApi = {
  getCoverLetters: () =>
    request<{ cover_letters: CoverLetterDocument[]; total: number }>("/api/v1/cover-letters"),

  getCoverLetter: (id: string) =>
    request<CoverLetterDocument>(`/api/v1/cover-letters/${id}`),

  updateCoverLetter: (
    id: string,
    data: Partial<{
      title: string;
      content_json: Record<string, unknown>;
      latex_source: string;
      hiring_manager_name: string;
      hiring_manager_email: string;
      street_address: string;
      city: string;
      state_province: string;
      postal_code: string;
      letter_date: string;
      additional_context: string;
    }>
  ) =>
    request<CoverLetterDocument>(`/api/v1/cover-letters/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  createCoverLetter: (data: {
    title?: string;
    resume_id: string;
    hiring_manager_name?: string;
    hiring_manager_email?: string;
    street_address?: string;
    city?: string;
    state_province?: string;
    postal_code?: string;
    letter_date?: string;
    additional_context?: string;
  }) =>
    request<CoverLetterDocument>("/api/v1/cover-letters", { method: "POST", body: JSON.stringify(data) }),

  regenerateCoverLetter: (id: string) =>
    request<CoverLetterDocument>(`/api/v1/cover-letters/${id}/regenerate`, { method: "POST" }),

  getCoverLetterPreviewHtml: async (id: string): Promise<string> => {
    const token = getAuthToken();
    const res = await fetch(`${API_URL}/api/v1/cover-letters/${id}/preview`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    return res.text();
  },

  getCoverLetterMessages: (id: string) =>
    request<ChatMessage[]>(`/api/v1/cover-letters/${id}/messages`),

  sendCoverLetterChat: (id: string, message: string) =>
    request<ChatExchange>(`/api/v1/cover-letters/${id}/chat`, {
      method: "POST",
      body: JSON.stringify({ message }),
    }),

  handleCoverLetterChange: (id: string, change_id: string, action: "accept" | "reject") =>
    request<{ ok: boolean; content_json: Record<string, unknown> }>(
      `/api/v1/cover-letters/${id}/changes`,
      { method: "POST", body: JSON.stringify({ change_id, action }) }
    ),

  downloadCoverLetterPdf: async (id: string): Promise<Blob> => {
    const token = getAuthToken();
    const res = await fetch(`${API_URL}/api/v1/cover-letters/${id}/pdf`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) throw new Error("PDF export failed");
    return res.blob();
  },
};
