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
