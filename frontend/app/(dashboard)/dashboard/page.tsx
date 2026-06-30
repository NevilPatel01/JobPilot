"use client";

import { useEffect, useState } from "react";
import { Briefcase, Send, TrendingUp, ArrowRight, CheckCircle2, Circle, Key, User, FileText, X } from "lucide-react";
import Link from "next/link";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatCard } from "@/components/ui/StatCard";
import { cn } from "@/lib/utils";

type SetupStatus = {
  hasApiKey: boolean;
  hasProfile: boolean;
  hasResume: boolean;
};

const SETUP_DISMISSED_KEY = "jobpilot_setup_dismissed";

export default function DashboardPage() {
  const [stats, setStats] = useState({ total_tracked: 0, total_applied: 0, interview_rate: 0 });
  const [setup, setSetup] = useState<SetupStatus | null>(null);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    setDismissed(localStorage.getItem(SETUP_DISMISSED_KEY) === "1");

    api.getAnalytics()
      .then((a) => setStats({ total_tracked: a.total_tracked, total_applied: a.total_applied, interview_rate: a.interview_rate }))
      .catch(() => {});

    Promise.all([
      api.getApiKeys().catch(() => [] as { id: string }[]),
      api.getStructuredProfile().catch(() => null),
      api.getResumes().catch(() => ({ resumes: [], total: 0 })),
    ]).then(([keys, profile, resumes]) => {
      setSetup({
        hasApiKey: Array.isArray(keys) && keys.length > 0,
        hasProfile: !!(profile?.content?.contact?.full_name?.trim()),
        hasResume: (resumes?.total ?? 0) > 0,
      });
    });
  }, []);

  const dismiss = () => {
    localStorage.setItem(SETUP_DISMISSED_KEY, "1");
    setDismissed(true);
  };

  const allDone = setup ? setup.hasApiKey && setup.hasProfile && setup.hasResume : false;
  const showSetup = setup !== null && !dismissed && !allDone;

  const steps = setup
    ? [
        {
          done: setup.hasApiKey,
          icon: Key,
          title: "Add your AI key",
          desc: "Paste your Claude (Anthropic) or OpenAI key. It's encrypted and never shared.",
          href: "/settings",
          cta: "Go to Settings",
        },
        {
          done: setup.hasProfile,
          icon: User,
          title: "Set up your profile",
          desc: "Add your experience, skills, and education — the AI tailors from this.",
          href: "/profile",
          cta: "Edit Profile",
        },
        {
          done: setup.hasResume,
          icon: FileText,
          title: "Create your first resume",
          desc: "Paste a job description and get a tailored, ATS-ready PDF in minutes.",
          href: "/resumes/new",
          cta: "Build Resume",
        },
      ]
    : [];

  const completedCount = steps.filter((s) => s.done).length;

  return (
    <div>
      <PageHeader title="Home" description="A focused view of your active job search." />

      {showSetup && (
        <div className="mb-6 glass-panel p-5 relative">
          <button
            onClick={dismiss}
            className="absolute right-4 top-4 text-muted-foreground hover:text-foreground transition-colors"
            aria-label="Dismiss setup"
          >
            <X className="h-4 w-4" />
          </button>

          <div className="flex items-start gap-3">
            <div className="flex-1">
              <p className="text-xs font-medium uppercase tracking-widest text-primary">Get started</p>
              <h2 className="mt-1 text-base font-semibold text-foreground">
                {completedCount === 0
                  ? "Three steps to your first tailored resume"
                  : `${completedCount} of ${steps.length} steps complete`}
              </h2>
            </div>
            <div className="shrink-0 text-right">
              <span className="text-sm font-semibold text-primary">{completedCount}/{steps.length}</span>
              <div className="mt-1 h-1.5 w-24 overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full rounded-full bg-primary transition-all duration-500"
                  style={{ width: `${(completedCount / steps.length) * 100}%` }}
                />
              </div>
            </div>
          </div>

          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            {steps.map((step, i) => {
              const Icon = step.icon;
              return (
                <div
                  key={i}
                  className={cn(
                    "rounded-lg border p-4 transition-all",
                    step.done
                      ? "border-primary/20 bg-primary/5"
                      : "border-border bg-background/40"
                  )}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <Icon className={cn("h-4 w-4 shrink-0", step.done ? "text-primary" : "text-muted-foreground")} />
                      <p className={cn("text-sm font-medium", step.done ? "text-foreground" : "text-foreground")}>{step.title}</p>
                    </div>
                    {step.done
                      ? <CheckCircle2 className="h-4 w-4 shrink-0 text-primary" />
                      : <Circle className="h-4 w-4 shrink-0 text-muted-foreground/40" />}
                  </div>
                  <p className="mt-2 text-xs text-muted-foreground leading-relaxed">{step.desc}</p>
                  {!step.done && (
                    <Link
                      href={step.href}
                      className="mt-3 inline-flex items-center gap-1 text-xs font-medium text-primary hover:underline"
                    >
                      {step.cta} <ArrowRight className="h-3 w-3" />
                    </Link>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard label="Jobs Tracked" value={stats.total_tracked} icon={Briefcase} accent="text-primary" />
        <StatCard label="Applications Sent" value={stats.total_applied} icon={Send} accent="text-primary" />
        <StatCard label="Interview Rate" value={`${stats.interview_rate}%`} icon={TrendingUp} accent="text-success" />
      </div>

      <div className="mt-8 glass-panel p-6">
        <h2 className="text-base font-semibold text-foreground">Continue where it matters</h2>
        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          {[
            { label: "Review your Inbox", href: "/inbox", desc: "Decide which roles deserve attention" },
            { label: "Open To Apply", href: "/tracker", desc: "Move your next applications forward" },
            { label: "Update your profile", href: "/profile", desc: "Keep fit scores and tailored resumes accurate" },
          ].map((step) => (
            <Link
              key={step.href}
              href={step.href}
              className="group flex items-center gap-4 rounded-lg border border-border/60 bg-background/40 p-4 transition-all duration-200 hover:border-primary/30 hover:bg-primary/5"
            >
              <div className="min-w-0 flex-1">
                <p className="font-medium text-foreground">{step.label}</p>
                <p className="text-xs text-muted-foreground">{step.desc}</p>
              </div>
              <ArrowRight className="h-4 w-4 shrink-0 text-muted-foreground transition-transform group-hover:translate-x-0.5 group-hover:text-primary" />
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
