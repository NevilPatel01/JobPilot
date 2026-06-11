export interface ContactInfo {
  full_name: string;
  email: string;
  phone: string;
  location: string;
}

export interface LinkItem {
  id: string;
  label: string;
  url: string;
}

export interface ExperienceEntry {
  id: string;
  company: string;
  title: string;
  location: string;
  start_date: string;
  end_date: string;
  bullets: string[];
}

export interface EducationEntry {
  id: string;
  institution: string;
  degree: string;
  location: string;
  start_date: string;
  end_date: string;
  gpa: string;
}

export interface ProjectEntry {
  id: string;
  name: string;
  url: string;
  bullets: string[];
}

export interface SkillCategory {
  id: string;
  name: string;
  skills: string[];
}

export interface ResumeContent {
  contact: ContactInfo;
  links: LinkItem[];
  summary: string;
  experience: ExperienceEntry[];
  education: EducationEntry[];
  projects: ProjectEntry[];
  skills: SkillCategory[];
}

export interface ResumeDocument {
  id: string;
  title: string;
  status: string;
  job_description: string | null;
  company_url: string | null;
  company_name: string | null;
  source_type: string;
  content_json: ResumeContent;
  latex_source: string | null;
  insights_json: Record<string, unknown> | null;
  create_cover_letter: boolean;
  cover_letter_meta: Record<string, string> | null;
  application_id: string | null;
  cover_letter_id: string | null;
  pipeline_error?: string | null;
  last_step?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CoverLetterDocument {
  id: string;
  title: string;
  status: string;
  resume_id: string | null;
  hiring_manager_name: string | null;
  hiring_manager_email: string | null;
  street_address: string | null;
  city: string | null;
  state_province: string | null;
  postal_code: string | null;
  letter_date: string | null;
  additional_context: string | null;
  content_json: Record<string, unknown>;
  latex_source: string | null;
  created_at: string;
  updated_at: string;
}

export interface CoverLetterMeta {
  hiring_manager_name?: string;
  hiring_manager_email?: string;
  street_address?: string;
  city?: string;
  state_province?: string;
  postal_code?: string;
  letter_date?: string;
  additional_context?: string;
}

export interface ApiKeyConfig {
  id: string;
  provider: string;
  api_key_masked: string;
  base_url: string | null;
  model_name: string | null;
  embedding_model: string | null;
  is_default: boolean;
}

export interface ApiToken {
  id: string;
  name: string;
  token_prefix: string;
  created_at: string;
  last_used_at: string | null;
}

export interface PendingChange {
  id: string;
  path: string;
  old_value: string | null;
  new_value: string | null;
  status: string;
}

export interface ChatMessage {
  id: string;
  role: string;
  content: string;
  pending_changes: PendingChange[];
  created_at: string;
}

export interface ATSSuggestionItem {
  text: string;
  prompt: string;
  priority: string;
  category: string;
}

export interface ATSScore {
  id: string;
  overall_score: number;
  keyword_match: number;
  formatting_score: number;
  semantic_score?: number;
  skills_coverage?: number;
  section_score?: number;
  matched_keywords?: string[] | null;
  missing_keywords: string[] | null;
  suggestions: string[];
  suggestion_items?: ATSSuggestionItem[];
  breakdown?: Record<string, unknown> | null;
  created_at: string;
}

export interface StructuredProfile {
  content: ResumeContent;
  updated_at?: string;
}

export function emptyResumeContent(): ResumeContent {
  return {
    contact: { full_name: "", email: "", phone: "", location: "" },
    links: [],
    summary: "",
    experience: [],
    education: [],
    projects: [],
    skills: [],
  };
}

export function newId(): string {
  return crypto.randomUUID();
}
