"use client";

import { useEffect, useState } from "react";
import { Briefcase, Send, TrendingUp, ArrowRight } from "lucide-react";
import Link from "next/link";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatCard } from "@/components/ui/StatCard";

export default function DashboardPage() {
  const [stats, setStats] = useState({
    total_tracked: 0,
    total_applied: 0,
    interview_rate: 0,
  });

  useEffect(() => {
    api.getAnalytics()
      .then((a) =>
        setStats({
          total_tracked: a.total_tracked,
          total_applied: a.total_applied,
          interview_rate: a.interview_rate,
        })
      )
      .catch(() => {});
  }, []);

  const steps = [
    { label: "Review your Inbox", href: "/inbox", desc: "Decide which roles deserve attention" },
    { label: "Open To Apply", href: "/tracker", desc: "Move your next applications forward" },
    { label: "Update your profile", href: "/profile", desc: "Keep fit scores and tailored resumes accurate" },
  ];

  return (
    <div>
      <PageHeader title="Home" description="A focused view of your active job search." />

      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard label="Jobs Tracked" value={stats.total_tracked} icon={Briefcase} accent="text-primary" />
        <StatCard label="Applications Sent" value={stats.total_applied} icon={Send} accent="text-primary" />
        <StatCard label="Interview Rate" value={`${stats.interview_rate}%`} icon={TrendingUp} accent="text-success" />
      </div>

      <div className="mt-8 glass-panel p-6">
        <h2 className="text-base font-semibold text-foreground">Continue where it matters</h2>
        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          {steps.map((step) => (
            <Link
              key={step.href}
              href={step.href}
              className="group flex items-center gap-4 rounded-lg border border-border/60 bg-background/40 p-4 transition-all duration-200 hover:border-primary/30 hover:bg-primary/5"
            >
              <div className="min-w-0 flex-1">
                <p className="font-medium text-foreground group-hover:text-foreground">{step.label}</p>
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
