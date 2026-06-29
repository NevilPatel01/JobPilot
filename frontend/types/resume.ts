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
  job_title: string | null;
  job_url: string | null;
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
  job_id: string | null;
  inbox_job_id: string | null;
  resume_category: string | null;
  why_this_version: {
    category?: string;
    category_source?: string;
    category_confidence?: number | null;
    matched_keywords?: string[];
    missing_keywords?: string[];
    fit_score?: number | null;
    truthfulness?: string;
    template_notes?: Record<string, unknown>;
  } | null;
  cover_letter_id: string | null;
  pipeline_error?: string | null;
  last_step?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CoverLetterContent {
  recipient_name: string;
  recipient_title: string;
  company_name: string;
  company_address: string;
  date: string;
  salutation: string;
  paragraphs: string[];
  closing: string;
}

export function emptyCoverLetterContent(): CoverLetterContent {
  return {
    recipient_name: "",
    recipient_title: "",
    company_name: "",
    company_address: "",
    date: "",
    salutation: "Dear Hiring Manager,",
    paragraphs: [""],
    closing: "Sincerely,",
  };
}

export function parseCoverLetterContent(raw: Record<string, unknown>): CoverLetterContent {
  const base = emptyCoverLetterContent();
  const paragraphs = raw.paragraphs;
  return {
    ...base,
    recipient_name: String(raw.recipient_name || ""),
    recipient_title: String(raw.recipient_title || ""),
    company_name: String(raw.company_name || ""),
    company_address: String(raw.company_address || ""),
    date: String(raw.date || ""),
    salutation: String(raw.salutation || base.salutation),
    closing: String(raw.closing || base.closing),
    paragraphs: Array.isArray(paragraphs) && paragraphs.length
      ? paragraphs.map((p) => String(p))
      : [""],
  };
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
  path_label?: string | null;
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

export interface ChatExchange {
  user_message: ChatMessage;
  assistant_message: ChatMessage;
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

export interface ResumeStatus {
  id: string;
  status: string;
  last_step?: string | null;
  pipeline_error?: string | null;
  cover_letter_id?: string | null;
  ats_score?: ATSScore | null;
  updated_at: string;
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
