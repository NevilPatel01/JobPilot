import Link from "next/link";
import { ArrowRight, BriefcaseBusiness, Inbox, Navigation, Sparkles } from "lucide-react";

const inboxItems = [
  { company: "Northstar Labs", role: "Senior Product Designer", score: "92", status: "Strong match" },
  { company: "Mercury Works", role: "Frontend Engineer", score: "86", status: "Review" },
  { company: "Cedar Health", role: "Product Engineer", score: "78", status: "New" },
];

export function MarketingHero() {
  return (
    <section className="relative overflow-hidden border-b border-border/60">
      <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(to_right,hsl(var(--border)/0.18)_1px,transparent_1px),linear-gradient(to_bottom,hsl(var(--border)/0.18)_1px,transparent_1px)] bg-[size:64px_64px] [mask-image:linear-gradient(to_bottom,black,transparent_85%)]" />
      <div className="relative mx-auto grid max-w-6xl items-center gap-14 px-6 py-20 lg:grid-cols-[0.9fr_1.1fr] lg:py-28">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.14em] text-primary">
            <Navigation className="h-3.5 w-3.5 fill-current" />
            Your private career workspace
          </div>
          <h1 className="mt-7 max-w-xl text-5xl font-semibold leading-[1.02] tracking-[-0.055em] text-foreground sm:text-6xl lg:text-[4.35rem]">
            A calmer way to run your job search.
          </h1>
          <p className="mt-6 max-w-lg text-base leading-7 text-muted-foreground sm:text-lg">
            Capture roles while you browse, understand your fit, tailor every application, and keep the full process
            moving in one focused workspace.
          </p>
          <div className="mt-9 flex flex-col gap-3 sm:flex-row">
            <Link href="/login" className="btn-primary px-6 py-3 text-base">
              Build your workspace
              <ArrowRight className="h-4 w-4" />
            </Link>
            <a
              href="https://github.com/NevilPatel01/JobPilot"
              target="_blank"
              rel="noopener noreferrer"
              className="btn-secondary px-6 py-3 text-base"
            >
              Explore the project
            </a>
          </div>
          <div className="mt-8 flex flex-wrap gap-x-5 gap-y-2 text-xs text-muted-foreground">
            <span>Open source</span>
            <span className="text-border">/</span>
            <span>Self-hostable</span>
            <span className="text-border">/</span>
            <span>Your data stays yours</span>
          </div>
        </div>

        <div className="relative mx-auto w-full max-w-xl lg:mx-0">
          <div className="absolute -inset-10 -z-10 rounded-full bg-primary/10 blur-3xl" />
          <div className="overflow-hidden rounded-[22px] border border-border/80 bg-card/95 shadow-[0_32px_90px_hsl(var(--foreground)/0.14)] backdrop-blur-xl">
            <div className="flex items-center justify-between border-b border-border/70 px-5 py-4">
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary/12 text-primary">
                  <Inbox className="h-4 w-4" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-foreground">Job inbox</p>
                  <p className="text-xs text-muted-foreground">12 roles worth your attention</p>
                </div>
              </div>
              <span className="rounded-full bg-success/10 px-2.5 py-1 text-[11px] font-semibold text-success">
                Live
              </span>
            </div>
            <div className="space-y-2 p-3">
              {inboxItems.map((item, index) => (
                <div
                  key={item.company}
                  className="grid grid-cols-[auto_1fr_auto] items-center gap-3 rounded-xl border border-border/60 bg-background/55 p-3.5"
                >
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-muted text-muted-foreground">
                    <BriefcaseBusiness className="h-4 w-4" />
                  </div>
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-foreground">{item.role}</p>
                    <p className="mt-0.5 truncate text-xs text-muted-foreground">{item.company} · Canada remote</p>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-semibold tracking-tight text-primary">{item.score}</p>
                    <p className="text-[10px] text-muted-foreground">{item.status}</p>
                  </div>
                  {index === 0 && <div className="col-span-3 h-0.5 rounded-full bg-primary/70" />}
                </div>
              ))}
            </div>
            <div className="flex items-center gap-2 border-t border-border/70 bg-muted/35 px-5 py-3 text-xs text-muted-foreground">
              <Sparkles className="h-3.5 w-3.5 text-primary" />
              Fit scoring and duplicate checks happen automatically
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
