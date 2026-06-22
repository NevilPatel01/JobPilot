/** Shared site metadata for SEO, Open Graph, and sitemap references. */
export const siteConfig = {
  name: "JobPilot",
  title: "JobPilot — Open-Source Job Search & AI Resume Builder",
  description:
    "Free, self-hostable job search command centre for tech professionals. Scrape Canadian jobs, track applications on a Kanban board, and build ATS-optimized resumes and cover letters with AI.",
  url: process.env.NEXT_PUBLIC_SITE_URL || "https://jobs.nevil.ca",
  github: "https://github.com/NevilPatel01/JobPilot",
  keywords: [
    "job search",
    "resume builder",
    "cover letter generator",
    "application tracker",
    "ATS resume",
    "Kanban job tracker",
    "Canadian jobs",
    "open source",
    "self-hosted",
    "AI resume",
    "LaTeX resume",
    "FastAPI",
    "Next.js",
    "PostgreSQL",
    "pgvector",
  ],
} as const;
