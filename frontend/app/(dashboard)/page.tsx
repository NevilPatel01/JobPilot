"use client";

import { useEffect, useState } from "react";
import { Briefcase, Send, TrendingUp, Database, ArrowRight, CheckCircle2, AlertCircle } from "lucide-react";
import Link from "next/link";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatCard } from "@/components/ui/StatCard";

export default function DashboardPage() {
  const [stats, setStats] = useState({
    total_tracked: 0,
    total_applied: 0,
    interview_rate: 0,
    active_jobs_in_db: 0,
  });
  const [health, setHealth] = useState<"ok" | "offline" | "checking">("checking");

  useEffect(() => {
    api.health().then((h) => setHealth(h.status === "ok" ? "ok" : "offline")).catch(() => setHealth("offline"));
    api.getAnalytics()
      .then((a) =>
        setStats({
          total_tracked: a.total_tracked,
          total_applied: a.total_applied,
          interview_rate: a.interview_rate,
          active_jobs_in_db: a.active_jobs_in_db,
        })
      )
      .catch(() => {});
  }, []);

  const steps = [
    { label: "Scrape remote jobs", href: "/scraper", desc: "Pull listings from RemoteOK, WWR, and HN" },
    { label: "Track applications", href: "/tracker", desc: "Manage your pipeline on the Kanban board" },
    { label: "Paste your resume", href: "/profile", desc: "Enable match scoring on every listing" },
    { label: "Review analytics", href: "/analytics", desc: "Track interview rate and trends" },
  ];

  return (
    <div>
      <PageHeader title="Dashboard" description="Your job search command centre" />

      <div className="mb-6 flex items-center gap-2 rounded-lg border border-zinc-800/80 bg-zinc-900/50 px-4 py-2.5 text-sm">
        {health === "ok" ? (
          <CheckCircle2 className="h-4 w-4 text-emerald-500" />
        ) : (
          <AlertCircle className="h-4 w-4 text-amber-500" />
        )}
        <span className="text-zinc-500">API</span>
        <span className={health === "ok" ? "font-medium text-emerald-400" : "font-medium text-amber-400"}>
          {health === "checking" ? "Connecting..." : health === "ok" ? "Connected" : "Offline"}
        </span>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Jobs Tracked" value={stats.total_tracked} icon={Briefcase} accent="text-indigo-400" />
        <StatCard label="Applications Sent" value={stats.total_applied} icon={Send} accent="text-sky-400" />
        <StatCard label="Interview Rate" value={`${stats.interview_rate}%`} icon={TrendingUp} accent="text-emerald-400" />
        <StatCard label="Active Listings" value={stats.active_jobs_in_db} icon={Database} accent="text-amber-400" />
      </div>

      <div className="mt-8 glass-panel p-6">
        <h2 className="text-base font-semibold text-white">Quick start</h2>
        <p className="mt-1 text-sm text-zinc-500">Four steps to get the most out of JobPilot</p>
        <div className="mt-5 grid gap-3 sm:grid-cols-2">
          {steps.map((step, i) => (
            <Link
              key={step.href}
              href={step.href}
              className="group flex items-center gap-4 rounded-lg border border-zinc-800/60 bg-zinc-950/40 p-4 transition-all duration-200 hover:border-indigo-500/30 hover:bg-indigo-600/5"
            >
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-indigo-600/15 text-sm font-semibold text-indigo-400 ring-1 ring-indigo-500/20">
                {i + 1}
              </span>
              <div className="min-w-0 flex-1">
                <p className="font-medium text-zinc-200 group-hover:text-white">{step.label}</p>
                <p className="text-xs text-zinc-500">{step.desc}</p>
              </div>
              <ArrowRight className="h-4 w-4 shrink-0 text-zinc-600 transition-transform group-hover:translate-x-0.5 group-hover:text-indigo-400" />
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
