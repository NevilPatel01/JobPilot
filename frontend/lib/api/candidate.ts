import { request } from "./_client";

// ─── Types ────────────────────────────────────────────────────────────────────

export type FactType =
  | "personal" | "contact" | "work_authorization" | "location" | "target_role"
  | "target_industry" | "employment" | "education" | "certification"
  | "project" | "skill" | "achievement" | "metric";

export type VerificationStatus = "unverified" | "user_confirmed" | "contradicted";

export interface CandidateFact {
  id: string;
  fact_type: FactType;
  payload: Record<string, unknown>;
  source: string;
  verification_status: VerificationStatus;
  confidence: number;
  is_prohibited: boolean;
  created_at: string;
  updated_at: string;
}

export interface DraftFact {
  fact_type: FactType;
  payload: Record<string, unknown>;
  source: string;
  is_prohibited?: boolean;
}

export interface Achievement {
  id: string;
  related_fact_id: string | null;
  situation: string;
  task: string;
  action: string;
  result: string;
  metrics: Record<string, unknown>;
  tags: string[];
  verification_status: VerificationStatus;
  created_at: string;
}

export interface CareerProfile {
  id: string;
  name: string;
  description: string;
  emphasis_fact_ids: string[];
  positioning_statement: string;
  is_default: boolean;
}

export interface AnswerBankEntry {
  id: string;
  question_text: string;
  question_category: string;
  answer_text: string;
  is_sensitive: boolean;
  usage_count: number;
}

export interface GitHubSyncResponse {
  draft_facts: DraftFact[];
  skipped_unchanged: number;
  rate_limited: boolean;
  warning: string | null;
}

export interface DigestResponse {
  content_text: string;
  token_estimate: number;
  generated_at: string;
}

// ─── API ──────────────────────────────────────────────────────────────────────

const base = "/api/v1/candidate";

export const candidateApi = {
  // feature probe: 404 when FEATURE_CANDIDATE_INTELLIGENCE is off
  async isEnabled(): Promise<boolean> {
    try {
      await request<CandidateFact[]>(`${base}/facts?fact_type=personal`);
      return true;
    } catch {
      return false;
    }
  },

  listFacts: (factType?: string) =>
    request<CandidateFact[]>(`${base}/facts${factType ? `?fact_type=${factType}` : ""}`),
  createFact: (body: DraftFact) =>
    request<CandidateFact>(`${base}/facts`, { method: "POST", body: JSON.stringify(body) }),
  verifyFact: (id: string) => request<CandidateFact>(`${base}/facts/${id}/verify`, { method: "POST" }),
  disputeFact: (id: string) => request<CandidateFact>(`${base}/facts/${id}/dispute`, { method: "POST" }),
  supersedeFact: (id: string, payload: Record<string, unknown>) =>
    request<CandidateFact>(`${base}/facts/${id}/supersede`, { method: "POST", body: JSON.stringify({ payload }) }),
  pinFact: (id: string) => request<CandidateFact>(`${base}/facts/${id}/pin`, { method: "POST" }),
  unpinFact: (id: string) => request<CandidateFact>(`${base}/facts/${id}/unpin`, { method: "POST" }),

  listAchievements: () => request<Achievement[]>(`${base}/achievements`),
  createAchievement: (body: Partial<Achievement>) =>
    request<Achievement>(`${base}/achievements`, { method: "POST", body: JSON.stringify(body) }),
  verifyAchievement: (id: string) =>
    request<Achievement>(`${base}/achievements/${id}/verify`, { method: "POST" }),
  deleteAchievement: (id: string) =>
    request<{ deleted: boolean }>(`${base}/achievements/${id}`, { method: "DELETE" }),

  listCareerProfiles: () => request<CareerProfile[]>(`${base}/career-profiles`),
  createCareerProfile: (body: Partial<CareerProfile>) =>
    request<CareerProfile>(`${base}/career-profiles`, { method: "POST", body: JSON.stringify(body) }),
  setDefaultCareerProfile: (id: string) =>
    request<CareerProfile>(`${base}/career-profiles/${id}/set-default`, { method: "POST" }),
  deleteCareerProfile: (id: string) =>
    request<{ deleted: boolean }>(`${base}/career-profiles/${id}`, { method: "DELETE" }),

  listAnswers: () => request<AnswerBankEntry[]>(`${base}/answers`),
  createAnswer: (body: Partial<AnswerBankEntry>) =>
    request<AnswerBankEntry>(`${base}/answers`, { method: "POST", body: JSON.stringify(body) }),
  deleteAnswer: (id: string) =>
    request<{ deleted: boolean }>(`${base}/answers/${id}`, { method: "DELETE" }),

  importLegacyProfile: () =>
    request<{ created: number; skipped: number }>(`${base}/import/legacy-profile`, { method: "POST" }),
  importResumeText: (text: string) =>
    request<{ draft_facts: DraftFact[]; rejected: number; warning: string | null }>(
      `${base}/import/resume-text`,
      { method: "POST", body: JSON.stringify({ text }) },
    ),
  importGitHub: (username?: string) =>
    request<GitHubSyncResponse>(`${base}/import/github`, {
      method: "POST",
      body: JSON.stringify({ username: username || null }),
    }),
  confirmImport: (facts: DraftFact[]) =>
    request<{ created: number; superseded: number }>(`${base}/import/confirm`, {
      method: "POST",
      body: JSON.stringify({ facts }),
    }),
  getProjectsDigest: () => request<DigestResponse>(`${base}/digest/github_projects`),
};
