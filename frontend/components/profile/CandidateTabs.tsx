"use client";

import { useEffect, useState, type ReactNode } from "react";
import { candidateApi } from "@/lib/api/candidate";
import { FactsPanel } from "@/components/profile/FactsPanel";
import { GitHubSyncCard } from "@/components/profile/GitHubSyncCard";
import { AchievementsPanel } from "@/components/profile/AchievementsPanel";
import { AnswerBankPanel } from "@/components/profile/AnswerBankPanel";
import { CareerProfilesPanel } from "@/components/profile/CareerProfilesPanel";
import { cn } from "@/lib/utils";

const TABS = [
  { id: "profile", label: "Profile" },
  { id: "facts", label: "Facts" },
  { id: "achievements", label: "Achievements" },
  { id: "answers", label: "Answer Bank" },
  { id: "career-profiles", label: "Career Profiles" },
] as const;

type TabId = (typeof TABS)[number]["id"];

/** Tabbed shell for the profile page. Renders only the legacy editor until the
 * candidate-intelligence feature flag probe succeeds (backend returns 404 when off). */
export function CandidateTabs({ children }: { children: ReactNode }) {
  const [enabled, setEnabled] = useState(false);
  const [tab, setTab] = useState<TabId>("profile");
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    candidateApi.isEnabled().then(setEnabled).catch(() => setEnabled(false));
  }, []);

  if (!enabled) return <>{children}</>;

  return (
    <div>
      <div className="mb-6 flex flex-wrap gap-1 rounded-xl border border-border bg-card/40 p-1">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={cn(
              "rounded-lg px-4 py-2 text-sm transition-colors",
              tab === t.id ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground",
            )}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className={tab === "profile" ? "" : "hidden"}>{children}</div>
      {tab === "facts" && (
        <div className="space-y-6" key={refreshKey}>
          <GitHubSyncCard onImported={() => setRefreshKey((k) => k + 1)} />
          <FactsPanel />
        </div>
      )}
      {tab === "achievements" && <AchievementsPanel />}
      {tab === "answers" && <AnswerBankPanel />}
      {tab === "career-profiles" && <CareerProfilesPanel />}
    </div>
  );
}
