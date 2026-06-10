"use client";

import { useEffect, useState } from "react";
import { Briefcase, Send, TrendingUp, Database } from "lucide-react";
import { api } from "@/lib/api";

export default function DashboardPage() {
  const [stats, setStats] = useState({
    total_tracked: 0,
    total_applied: 0,
    interview_rate: 0,
    active_jobs_in_db: 0,
  });
  const [health, setHealth] = useState("checking...");

  useEffect(() => {
    api.health().then((h) => setHealth(h.status)).catch(() => setHealth("offline"));
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

  const cards = [
    { label: "Jobs Tracked", value: stats.total_tracked, icon: Briefcase, color: "text-indigo-400" },
    { label: "Applications Sent", value: stats.total_applied, icon: Send, color: "text-blue-400" },
    { label: "Interview Rate", value: `${stats.interview_rate}%`, icon: TrendingUp, color: "text-green-400" },
    { label: "Active Listings", value: stats.active_jobs_in_db, icon: Database, color: "text-amber-400" },
  ];

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <p className="mt-1 text-sm text-zinc-400">Your job search command centre</p>
      </div>

      <div className="mb-6 rounded-xl border border-zinc-800 bg-zinc-900 px-4 py-3 text-sm">
        API status:{" "}
        <span className={health === "ok" ? "text-green-500" : "text-amber-500"}>{health}</span>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {cards.map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="rounded-xl border border-zinc-800 bg-zinc-900 p-5">
            <div className="flex items-center justify-between">
              <p className="text-sm text-zinc-400">{label}</p>
              <Icon className={`h-5 w-5 ${color}`} />
            </div>
            <p className="mt-2 text-3xl font-bold text-white">{value}</p>
          </div>
        ))}
      </div>

      <div className="mt-8 rounded-xl border border-zinc-800 bg-zinc-900 p-6">
        <h2 className="text-lg font-semibold text-white">Getting Started</h2>
        <ol className="mt-4 space-y-2 text-sm text-zinc-400 list-decimal list-inside">
          <li>Go to <strong className="text-zinc-300">Scraper</strong> and click &quot;Scrape Now&quot; to pull remote jobs</li>
          <li>Track interesting jobs with one click</li>
          <li>Paste your resume in <strong className="text-zinc-300">Profile</strong> to see match scores</li>
          <li>Manage applications on the <strong className="text-zinc-300">Tracker</strong> Kanban board</li>
        </ol>
      </div>
    </div>
  );
}
