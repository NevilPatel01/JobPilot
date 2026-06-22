export interface Job {
  id: string;
  title: string;
  company: string;
  url: string;
  description: string | null;
  salary_min: number | null;
  salary_max: number | null;
  salary_currency: string;
  location: string | null;
  country: string | null;
  is_remote: boolean;
  tech_stack: string[] | null;
  source: string;
  first_seen: string;
  last_verified: string;
  is_active: boolean;
  province: string | null;
  city: string | null;
  remote_type: string | null;
  job_type: string | null;
  requirements: string[] | null;
  skills: string[] | null;
  seniority: string | null;
  experience_min: number | null;
  experience_max: number | null;
  apply_url: string | null;
  posted_date: string | null;
  closing_date: string | null;
}

export type InboxStatus =
  | "new"
  | "ai_reviewed"
  | "shortlisted"
  | "resume_ready"
  | "applied"
  | "archived"
  | "duplicate";

export interface InboxJob {
  id: string;
  user_id: string;
  status: InboxStatus;
  captured_via: string;
  ai_recommended_category: string | null;
  user_selected_category: string | null;
  tracker_summary: string | null;
  application_id: string | null;
  fit_score_id: string | null;
  resume_id: string | null;
  duplicate_of_id: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  job: Job;
  fit_score: JobFitScore | null;
}

export interface JobFitScore {
  id: string;
  score: number;
  label: "low" | "stretch" | "reviewed" | "recommended" | "priority";
  signals: Record<string, { points: number; max: number; detail: string }>;
  matched_skills: string[];
  missing_skills: string[];
  risk_flags: string[];
  recommended_action: string;
  explanation: string;
  recommended_category: string | null;
  category_confidence: number | null;
  scored_at: string;
  updated_at: string;
}

export interface InboxManualCreate {
  title: string;
  company: string;
  apply_url: string;
  description?: string;
  location?: string;
  skills?: string[];
}

export interface ScoringPreferences {
  user_id: string;
  work_authorization: string;
  target_provinces: string[];
  relocation_open: boolean;
  threshold_overrides: Record<string, number> | null;
  created_at: string;
  updated_at: string;
}

export interface Application {
  id: string;
  user_id: string;
  job_id: string | null;
  status: string;
  job_title: string | null;
  company: string | null;
  job_url: string | null;
  salary_range: string | null;
  notes: string | null;
  date_applied: string | null;
  kanban_order: number;
  created_at: string;
  updated_at: string;
}

export interface UserProfile {
  id: string;
  email: string;
  name: string | null;
  avatar_url: string | null;
  role: string;
  resume_text: string | null;
  skills_keywords: string[] | null;
}

export interface MatchScore {
  job_id: string;
  score: number;
  matched_keywords: string[];
}

export interface AnalyticsSummary {
  total_tracked: number;
  total_applied: number;
  interview_rate: number;
  active_jobs_in_db: number;
  applications_over_time: { week: string; count: number }[];
  status_breakdown: Record<string, number>;
  top_companies: { company: string; count: number }[];
  source_distribution: Record<string, number>;
}

export const KANBAN_COLUMNS = [
  { id: "to_apply", label: "To Apply" },
  { id: "applied", label: "Applied" },
  { id: "interviewing", label: "Interviewing" },
  { id: "offer", label: "Offer" },
  { id: "rejected", label: "Rejected" },
] as const;
