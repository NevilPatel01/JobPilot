"use client";

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  BarElement,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import { Line, Doughnut, Bar } from "react-chartjs-2";
import type { AnalyticsSummary } from "@/types";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, ArcElement, BarElement, Tooltip, Legend, Filler);

const chartDefaults = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { labels: { color: "#71717a", font: { size: 11 } } },
  },
  scales: {
    x: { ticks: { color: "#52525b", font: { size: 10 } }, grid: { color: "rgba(39, 39, 42, 0.5)" } },
    y: { ticks: { color: "#52525b", font: { size: 10 } }, grid: { color: "rgba(39, 39, 42, 0.5)" } },
  },
};

const statusColors: Record<string, string> = {
  to_apply: "#6366f1",
  applied: "#38bdf8",
  interviewing: "#fbbf24",
  offer: "#34d399",
  rejected: "#f87171",
};

export function AnalyticsCharts({ data }: { data: AnalyticsSummary }) {
  const lineData = {
    labels: data.applications_over_time.map((d) => d.week),
    datasets: [
      {
        label: "Applications",
        data: data.applications_over_time.map((d) => d.count),
        borderColor: "#818cf8",
        backgroundColor: "rgba(99, 102, 241, 0.12)",
        fill: true,
        tension: 0.35,
        pointRadius: 3,
        pointBackgroundColor: "#818cf8",
      },
    ],
  };

  const statusLabels = Object.keys(data.status_breakdown);
  const doughnutData = {
    labels: statusLabels.map((s) => s.replace("_", " ")),
    datasets: [
      {
        data: statusLabels.map((s) => data.status_breakdown[s]),
        backgroundColor: statusLabels.map((s) => statusColors[s] || "#52525b"),
        borderWidth: 0,
        spacing: 2,
      },
    ],
  };

  const barData = {
    labels: data.top_companies.map((c) => c.company),
    datasets: [
      {
        label: "Applications",
        data: data.top_companies.map((c) => c.count),
        backgroundColor: "rgba(99, 102, 241, 0.7)",
        borderRadius: 6,
        borderSkipped: false,
      },
    ],
  };

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <div className="glass-panel p-5">
        <h3 className="mb-4 text-sm font-semibold text-zinc-200">Applications Over Time</h3>
        <div className="h-64">
          <Line data={lineData} options={chartDefaults} />
        </div>
      </div>
      <div className="glass-panel p-5">
        <h3 className="mb-4 text-sm font-semibold text-zinc-200">Status Breakdown</h3>
        <div className="flex h-64 items-center justify-center">
          <Doughnut data={doughnutData} options={{ ...chartDefaults, scales: undefined, cutout: "68%" }} />
        </div>
      </div>
      {data.top_companies.length > 0 && (
        <div className="glass-panel p-5 lg:col-span-2">
          <h3 className="mb-4 text-sm font-semibold text-zinc-200">Top Companies</h3>
          <div className="h-64">
            <Bar data={barData} options={{ ...chartDefaults, indexAxis: "y" as const }} />
          </div>
        </div>
      )}
    </div>
  );
}
