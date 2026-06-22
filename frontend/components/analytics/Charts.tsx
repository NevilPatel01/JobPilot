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
import { useTheme } from "next-themes";
import { useMemo } from "react";
import type { AnalyticsSummary } from "@/types";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, ArcElement, BarElement, Tooltip, Legend, Filler);

const statusColors: Record<string, string> = {
  to_apply: "#6366f1",
  applied: "#0ea5e9",
  interviewing: "#f59e0b",
  offer: "#10b981",
  rejected: "#ef4444",
};

function chartTheme(isDark: boolean) {
  return {
    tick: isDark ? "#a1a1aa" : "#64748b",
    grid: isDark ? "rgba(63, 63, 70, 0.45)" : "rgba(203, 213, 225, 0.8)",
    line: isDark ? "#818cf8" : "#4f46e5",
    lineFill: isDark ? "rgba(99, 102, 241, 0.15)" : "rgba(79, 70, 229, 0.12)",
    bar: isDark ? "rgba(99, 102, 241, 0.75)" : "rgba(79, 70, 229, 0.7)",
  };
}

export function AnalyticsCharts({ data }: { data: AnalyticsSummary }) {
  const { resolvedTheme } = useTheme();
  const isDark = resolvedTheme === "dark";
  const theme = useMemo(() => chartTheme(isDark), [isDark]);

  const chartDefaults = useMemo(
    () => ({
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: theme.tick, font: { size: 11 } } },
      },
      scales: {
        x: { ticks: { color: theme.tick, font: { size: 10 } }, grid: { color: theme.grid } },
        y: { ticks: { color: theme.tick, font: { size: 10 } }, grid: { color: theme.grid } },
      },
    }),
    [theme]
  );

  const lineData = {
    labels: data.applications_over_time.map((d) => d.week),
    datasets: [
      {
        label: "Applications",
        data: data.applications_over_time.map((d) => d.count),
        borderColor: theme.line,
        backgroundColor: theme.lineFill,
        fill: true,
        tension: 0.35,
        pointRadius: 3,
        pointBackgroundColor: theme.line,
      },
    ],
  };

  const statusLabels = Object.keys(data.status_breakdown);
  const doughnutData = {
    labels: statusLabels.map((s) => s.replace("_", " ")),
    datasets: [
      {
        data: statusLabels.map((s) => data.status_breakdown[s]),
        backgroundColor: statusLabels.map((s) => statusColors[s] || theme.tick),
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
        backgroundColor: theme.bar,
        borderRadius: 6,
        borderSkipped: false,
      },
    ],
  };

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <div className="glass-panel p-5">
        <h3 className="mb-4 text-sm font-semibold text-foreground">Applications Over Time</h3>
        <div className="h-64">
          <Line data={lineData} options={chartDefaults} />
        </div>
      </div>
      <div className="glass-panel p-5">
        <h3 className="mb-4 text-sm font-semibold text-foreground">Status Breakdown</h3>
        <div className="flex h-64 items-center justify-center">
          <Doughnut data={doughnutData} options={{ ...chartDefaults, scales: undefined, cutout: "68%" }} />
        </div>
      </div>
      {data.top_companies.length > 0 && (
        <div className="glass-panel p-5 lg:col-span-2">
          <h3 className="mb-4 text-sm font-semibold text-foreground">Top Companies</h3>
          <div className="h-64">
            <Bar data={barData} options={{ ...chartDefaults, indexAxis: "y" as const }} />
          </div>
        </div>
      )}
    </div>
  );
}
