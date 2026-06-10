"use client";

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import { Line, Doughnut, Bar } from "react-chartjs-2";
import type { AnalyticsSummary } from "@/types";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, ArcElement, BarElement, Title, Tooltip, Legend, Filler);

const chartDefaults = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { labels: { color: "#a1a1aa" } },
  },
  scales: {
    x: { ticks: { color: "#71717a" }, grid: { color: "#27272a" } },
    y: { ticks: { color: "#71717a" }, grid: { color: "#27272a" } },
  },
};

const statusColors: Record<string, string> = {
  to_apply: "#4f46e5",
  applied: "#3b82f6",
  interviewing: "#f59e0b",
  offer: "#22c55e",
  rejected: "#ef4444",
};

export function AnalyticsCharts({ data }: { data: AnalyticsSummary }) {
  const lineData = {
    labels: data.applications_over_time.map((d) => d.week),
    datasets: [
      {
        label: "Applications",
        data: data.applications_over_time.map((d) => d.count),
        borderColor: "#818cf8",
        backgroundColor: "rgba(79, 70, 229, 0.15)",
        fill: true,
        tension: 0.4,
      },
    ],
  };

  const statusLabels = Object.keys(data.status_breakdown);
  const doughnutData = {
    labels: statusLabels.map((s) => s.replace("_", " ")),
    datasets: [
      {
        data: statusLabels.map((s) => data.status_breakdown[s]),
        backgroundColor: statusLabels.map((s) => statusColors[s] || "#71717a"),
        borderWidth: 0,
      },
    ],
  };

  const barData = {
    labels: data.top_companies.map((c) => c.company),
    datasets: [
      {
        label: "Applications",
        data: data.top_companies.map((c) => c.count),
        backgroundColor: "#4f46e5",
        borderRadius: 4,
      },
    ],
  };

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-5">
        <h3 className="mb-4 text-sm font-medium text-white">Applications Over Time</h3>
        <div className="h-64">
          <Line data={lineData} options={chartDefaults} />
        </div>
      </div>
      <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-5">
        <h3 className="mb-4 text-sm font-medium text-white">Status Breakdown</h3>
        <div className="h-64 flex items-center justify-center">
          <Doughnut
            data={doughnutData}
            options={{ ...chartDefaults, scales: undefined, cutout: "65%" }}
          />
        </div>
      </div>
      {data.top_companies.length > 0 && (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-5 lg:col-span-2">
          <h3 className="mb-4 text-sm font-medium text-white">Top Companies Applied To</h3>
          <div className="h-64">
            <Bar data={barData} options={{ ...chartDefaults, indexAxis: "y" as const }} />
          </div>
        </div>
      )}
    </div>
  );
}
