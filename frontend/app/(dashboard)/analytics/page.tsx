"use client";

import { useEffect, useState } from "react";
import { Briefcase, Send, TrendingUp, Database } from "lucide-react";
import { api } from "@/lib/api";
import type { AnalyticsSummary } from "@/types";
import { AnalyticsCharts } from "@/components/analytics/Charts";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatCard } from "@/components/ui/StatCard";

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsSummary | null>(null);

  useEffect(() => {
    api.getAnalytics().then(setData).catch(console.error);
  }, []);

  if (!data) {
    return (
      <div>
        <PageHeader title="Analytics" description="Loading..." />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="glass-panel h-28 animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div>
      <PageHeader title="Analytics" description="Application trends and pipeline insights" />

      <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Jobs Tracked" value={data.total_tracked} icon={Briefcase} accent="text-indigo-400" />
        <StatCard label="Applications Sent" value={data.total_applied} icon={Send} accent="text-sky-400" />
        <StatCard label="Interview Rate" value={`${data.interview_rate}%`} icon={TrendingUp} accent="text-emerald-400" />
        <StatCard label="Active Listings" value={data.active_jobs_in_db} icon={Database} accent="text-amber-400" />
      </div>

      <AnalyticsCharts data={data} />
    </div>
  );
}
