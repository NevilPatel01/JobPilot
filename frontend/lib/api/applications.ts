import { getAuthToken, request, API_URL, readErrorDetail } from "./_client";
import type { Application } from "@/types";

export const applicationsApi = {
  getApplications: (q?: string) => {
    const qs = q?.trim() ? `?q=${encodeURIComponent(q.trim())}` : "";
    return request<Application[]>(`/api/v1/applications${qs}`);
  },

  getApplication: (id: string) =>
    request<Application>(`/api/v1/applications/${id}`),

  createApplication: (data: Partial<Application>) =>
    request<Application>("/api/v1/applications", { method: "POST", body: JSON.stringify(data) }),

  updateApplication: (id: string, data: Partial<Application> & { resume_id?: string | null }) =>
    request<Application>(`/api/v1/applications/${id}`, { method: "PATCH", body: JSON.stringify(data) }),

  deleteApplication: (id: string) =>
    request<{ ok: boolean }>(`/api/v1/applications/${id}`, { method: "DELETE" }),

  quickSaveJob: (job_id: string) =>
    request<Application>("/api/v1/applications/quick-save", { method: "POST", body: JSON.stringify({ job_id }) }),

  uploadApplicationResume: async (id: string, file: File): Promise<Application> => {
    const token = getAuthToken();
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${API_URL}/api/v1/applications/${id}/upload-resume`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: form,
    });
    if (!res.ok) throw new Error(await readErrorDetail(res, "Upload failed"));
    return res.json();
  },

  deleteApplicationUploadedResume: (id: string) =>
    request<Application>(`/api/v1/applications/${id}/uploaded-resume`, { method: "DELETE" }),

  downloadApplicationResumePdf: async (id: string): Promise<Blob> => {
    const token = getAuthToken();
    const res = await fetch(`${API_URL}/api/v1/applications/${id}/resume-pdf`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) throw new Error(await readErrorDetail(res, "Resume PDF not available"));
    return res.blob();
  },
};
