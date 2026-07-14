"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { GitBranch, X } from "lucide-react";
import { candidateApi } from "@/lib/api/candidate";

const DISMISS_KEY = "jobpilot_github_prompt_dismissed";

/** One-time dashboard nudge: shows only when candidate intelligence is enabled
 * and the user has no project facts yet. Self-hides otherwise. */
export function GitHubPromptCard() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (typeof window !== "undefined" && localStorage.getItem(DISMISS_KEY)) return;
    candidateApi
      .listFacts("project")
      .then((facts) => setVisible(facts.length === 0))
      .catch(() => setVisible(false)); // flag off → 404 → stay hidden
  }, []);

  if (!visible) return null;

  return (
    <div className="mb-6 flex flex-wrap items-center gap-4 rounded-xl border border-primary/30 bg-primary/5 p-4">
      <GitBranch className="h-5 w-5 shrink-0 text-foreground" />
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-foreground">Import your GitHub projects</p>
        <p className="mt-0.5 text-xs text-muted-foreground">
          Sync your public repos once — the resume AI picks the most relevant projects for each job, backed by
          verified facts.
        </p>
      </div>
      <Link href="/profile" className="btn-primary shrink-0">Sync projects</Link>
      <button
        aria-label="Dismiss"
        onClick={() => {
          localStorage.setItem(DISMISS_KEY, "1");
          setVisible(false);
        }}
        className="rounded p-1 text-muted-foreground hover:text-foreground"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}
