import { request } from "./_client";
import type { ApiKeyConfig, ApiToken } from "@/types/resume";

export const settingsApi = {
  getApiKeys: () => request<ApiKeyConfig[]>("/api/v1/settings/api-keys"),

  upsertApiKey: (data: {
    provider: string;
    api_key: string;
    base_url?: string;
    model_name?: string;
    embedding_model?: string;
    is_default?: boolean;
  }) =>
    request<ApiKeyConfig>("/api/v1/settings/api-keys", { method: "PUT", body: JSON.stringify(data) }),

  testApiKey: (data: {
    provider: string;
    api_key: string;
    base_url?: string;
    model_name?: string;
    embedding_model?: string;
  }) =>
    request<{ ok: boolean }>("/api/v1/settings/api-keys/test", { method: "POST", body: JSON.stringify(data) }),

  probeApiKeyModels: (data: { provider: string; api_key: string; base_url?: string }) =>
    request<{ chat_models: string[]; embedding_models: string[] }>("/api/v1/settings/api-keys/models", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  autoSelectApiKeyModels: (data: { provider: string; api_key: string; base_url?: string }) =>
    request<{ model_name: string; embedding_model: string; reason: string }>(
      "/api/v1/settings/api-keys/auto-select",
      { method: "POST", body: JSON.stringify(data) }
    ),

  deleteApiKey: (id: string) =>
    request<{ ok: boolean }>(`/api/v1/settings/api-keys/${id}`, { method: "DELETE" }),

  getApiTokens: () => request<ApiToken[]>("/api/v1/settings/api-tokens"),

  createApiToken: (name: string) =>
    request<ApiToken & { token: string }>("/api/v1/settings/api-tokens", {
      method: "POST",
      body: JSON.stringify({ name }),
    }),

  deleteApiToken: (id: string) =>
    request<{ ok: boolean }>(`/api/v1/settings/api-tokens/${id}`, { method: "DELETE" }),
};
