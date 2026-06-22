import { BriefcaseBusiness, FileText, Inbox, Kanban, Puzzle, ShieldCheck } from "lucide-react";
import { cn } from "@/lib/utils";

const features = [
  {
    icon: Inbox,
    title: "One intelligent job inbox",
    description:
      "Bring discovered and manually captured roles into one queue, with duplicate checks, Canada validation, and fit scoring built in.",
    className: "sm:col-span-2 lg:col-span-2",
    detail: "Score · Prioritize · Shortlist",
  },
  {
    icon: Puzzle,
    title: "Capture from your browser",
    description: "Save the role on your current tab to your inbox or tracker with a deliberate click.",
    className: "lg:col-span-1",
  },
  {
    icon: Kanban,
    title: "A tracker that stays current",
    description: "Move applications from saved to applied, interview, offer, or closed without losing context.",
    className: "lg:col-span-1",
  },
  {
    icon: FileText,
    title: "Tailored application documents",
    description: "Create role-specific resumes and cover letters, review the changes, then export polished PDFs.",
    className: "sm:col-span-2 lg:col-span-2",
    detail: "Tailor · Review · Export",
  },
  {
    icon: BriefcaseBusiness,
    title: "Built for Canadian searches",
    description: "Focus results on roles you can actually apply to, with dedicated Canadian source handling.",
    className: "lg:col-span-1",
  },
  {
    icon: ShieldCheck,
    title: "Private by default",
    description: "Self-host the workspace and bring your own model keys. Your career data remains under your control.",
    className: "sm:col-span-2 lg:col-span-2",
    detail: "Open source · Self-hosted · Yours",
  },
];

export function MarketingFeatureGrid() {
  return (
    <section className="mx-auto max-w-6xl px-6 py-24">
      <div className="max-w-2xl">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-primary">One focused system</p>
        <h2 className="mt-4 text-3xl font-semibold tracking-[-0.035em] text-foreground sm:text-4xl">
          Less tab chaos. Better applications.
        </h2>
        <p className="mt-4 text-base leading-7 text-muted-foreground">
          JobPilot connects discovery, decision-making, documents, and follow-up without turning your search into a
          second full-time job.
        </p>
      </div>
      <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {features.map(({ icon: Icon, title, description, className, detail }) => (
          <article key={title} className={cn("glass-panel group flex min-h-56 flex-col p-6", className)}>
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary ring-1 ring-primary/15 transition-transform duration-200 group-hover:-rotate-3 group-hover:scale-105">
              <Icon className="h-[18px] w-[18px]" />
            </div>
            <h3 className="mt-8 text-lg font-semibold tracking-[-0.02em] text-foreground">{title}</h3>
            <p className="mt-2 max-w-xl text-sm leading-6 text-muted-foreground">{description}</p>
            {detail && (
              <p className="mt-auto pt-6 text-[11px] font-semibold uppercase tracking-[0.15em] text-primary/80">
                {detail}
              </p>
            )}
          </article>
        ))}
      </div>
    </section>
  );
}
