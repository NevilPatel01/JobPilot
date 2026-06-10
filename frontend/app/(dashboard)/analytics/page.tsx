"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { AnalyticsSummary } from "@/types";
import { StatCard } from "@/components/analytics/StatCard";
import { AnalyticsCharts } from "@/components/analytics/Charts";

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsSummary | null>(null);

  useEffect(() => {
    api.getAnalytics().then(setData).catch(console.error);
  }, []);

  if (!data) {
    return <div className="text-zinc-400">Loading analytics...</div>;
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Analytics</h1>
        <p className="text-sm text-zinc-400">Track your job search progress</p>
      </div>

      <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Total Tracked" value={data.total_tracked} />
        <StatCard label="Applications Sent" value={data.total_applied} />
        <StatCard label="Interview Rate" value={`${data.interview_rate}%`} />
        <StatCard label="Active Jobs in DB" value={data.active_jobs_in_db} />
      </div>

      <AnalyticsCharts data={data} />
    </div>
  );
}
