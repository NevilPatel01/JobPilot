import { request } from "./_client";
import type { Application } from "@/types";

export const applicationsApi = {
  getApplications: () => request<Application[]>("/api/v1/applications"),

  createApplication: (data: Partial<Application>) =>
    request<Application>("/api/v1/applications", { method: "POST", body: JSON.stringify(data) }),

  updateApplication: (id: string, data: Partial<Application>) =>
    request<Application>(`/api/v1/applications/${id}`, { method: "PATCH", body: JSON.stringify(data) }),

  deleteApplication: (id: string) =>
    request<{ ok: boolean }>(`/api/v1/applications/${id}`, { method: "DELETE" }),

  quickSaveJob: (job_id: string) =>
    request<Application>("/api/v1/applications/quick-save", { method: "POST", body: JSON.stringify({ job_id }) }),
};
