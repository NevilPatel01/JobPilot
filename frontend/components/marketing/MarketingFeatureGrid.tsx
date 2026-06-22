import {
  Briefcase,
  FileText,
  Kanban,
  Search,
  Shield,
  Sparkles,
} from "lucide-react";

const features = [
  {
    icon: Sparkles,
    title: "AI resume builder",
    description: "Multi-agent pipeline tailors your resume and cover letter per job with accept/reject diffs.",
  },
  {
    icon: FileText,
    title: "LaTeX PDF export",
    description: "Jake's Resume template compiled server-side for pixel-accurate, ATS-friendly PDFs.",
  },
  {
    icon: Search,
    title: "Canadian job scraper",
    description: "RemoteOK, WeWorkRemotely, and Hacker News with smart deduplication and Canada filter.",
  },
  {
    icon: Kanban,
    title: "Application tracker",
    description: "Drag-and-drop Kanban from To Apply through Offer or Rejected.",
  },
  {
    icon: Briefcase,
    title: "ATS scoring",
    description: "Keyword match, formatting score, and actionable improvement suggestions.",
  },
  {
    icon: Shield,
    title: "Bring your own keys",
    description: "OpenAI or Claude API keys encrypted at rest — no server-side LLM bill.",
  },
];

export function MarketingFeatureGrid() {
  return (
    <section className="mx-auto max-w-6xl px-6 py-16">
      <h2 className="text-center text-2xl font-semibold text-foreground">Everything you need to land your next role</h2>
      <p className="mx-auto mt-2 max-w-xl text-center text-sm text-muted-foreground">
        Paste a job URL, let AI tailor your documents, and track every application in one place.
      </p>
      <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {features.map(({ icon: Icon, title, description }) => (
          <div key={title} className="glass-panel p-6">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/12 ring-1 ring-primary/20">
              <Icon className="h-5 w-5 text-primary" />
            </div>
            <h3 className="mt-4 font-medium text-foreground">{title}</h3>
            <p className="mt-2 text-sm text-muted-foreground">{description}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
