"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { MessageSquare, RefreshCw } from "lucide-react";
import { api } from "@/lib/api";
import type { ATSScore, ATSSuggestionItem } from "@/types/resume";
import { PageHeader } from "@/components/ui/PageHeader";
import { formatDate } from "@/lib/utils";

function ScoreBar({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <div className="mb-1 flex justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span className="text-foreground">{value}%</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full bg-primary transition-all"
          style={{ width: `${Math.min(100, value)}%` }}
        />
      </div>
    </div>
  );
}

function ScoreRing({ score }: { score: number }) {
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const stroke =
    score >= 80 ? "#34d399" : score >= 60 ? "#fbbf24" : "#f87171";

  return (
    <div className="relative flex h-36 w-36 items-center justify-center">
      <svg className="-rotate-90" width="144" height="144" viewBox="0 0 144 144">
        <circle cx="72" cy="72" r={radius} fill="none" stroke="#27272a" strokeWidth="10" />
        <circle
          cx="72"
          cy="72"
          r={radius}
          fill="none"
          stroke={stroke}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-700"
        />
      </svg>
      <div className="absolute text-center">
        <div className="text-4xl font-bold text-foreground">{score}</div>
        <div className="text-xs text-muted-foreground">Overall</div>
      </div>
    </div>
  );
}

function priorityClass(priority: string): string {
  if (priority === "high") return "ring-red-500/30 text-red-300 bg-red-500/10";
  if (priority === "low") return "ring-border text-muted-foreground bg-muted/80";
  return "ring-amber-500/30 text-amber-300 bg-amber-500/10";
}

function SuggestionList({ items, resumeId }: { items: ATSSuggestionItem[]; resumeId: string }) {
  if (items.length === 0) return null;
  return (
    <div className="mt-4 space-y-3">
      <h3 className="text-sm font-semibold text-foreground">Suggestions</h3>
      {items.map((item, i) => (
        <div key={i} className="rounded-lg border border-border bg-card/50 p-3">
          <div className="flex flex-wrap items-start justify-between gap-2">
            <p className="text-sm text-foreground">{item.text}</p>
            <span className={`rounded-full px-2 py-0.5 text-[10px] uppercase ring-1 ${priorityClass(item.priority)}`}>
              {item.priority}
            </span>
          </div>
          <Link
            href={`/resumes/${resumeId}?chat=${encodeURIComponent(item.prompt)}`}
            className="mt-2 inline-flex items-center gap-1 text-xs text-primary hover:text-primary"
          >
            <MessageSquare className="h-3 w-3" /> Fix in chat
          </Link>
        </div>
      ))}
    </div>
  );
}

export default function ResumeReviewPage() {
  const { id } = useParams<{ id: string }>();
  const [score, setScore] = useState<ATSScore | null>(null);
  const [history, setHistory] = useState<ATSScore[]>([]);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    const [latest, hist] = await Promise.all([
      api.getATSScore(id).catch(() => null),
      api.getATSScoreHistory(id, 5).catch(() => ({ scores: [], total: 0 })),
    ]);
    setScore(latest);
    setHistory(hist.scores);
  }, [id]);

  useEffect(() => {
    load().catch(console.error);
  }, [load]);

  const rescore = async () => {
    setLoading(true);
    try {
      const s = await api.runATSScore(id);
      setScore(s);
      await load();
    } finally {
      setLoading(false);
    }
  };

  const suggestionItems =
    score?.suggestion_items && score.suggestion_items.length > 0
      ? score.suggestion_items
      : (score?.suggestions || []).map((text) => ({
          text,
          prompt: text,
          priority: "medium",
          category: "general",
        }));

  return (
    <div>
      <PageHeader
        title="Resume Review"
        description="ATS score and keyword analysis against the job description"
        action={
          <div className="flex gap-2">
            <Link href={`/resumes/${id}`} className="btn-secondary">Back to Editor</Link>
            <button onClick={rescore} disabled={loading} className="btn-primary">
              <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} /> Re-score
            </button>
          </div>
        }
      />

      {score ? (
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="glass-panel flex flex-col items-center justify-center gap-4 p-8">
            <ScoreRing score={score.overall_score} />
            <p className="text-center text-xs text-muted-foreground">
              Scored {formatDate(score.created_at)}
            </p>
            {history.length > 1 && (
              <div className="w-full border-t border-border pt-4">
                <p className="mb-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">Score history</p>
                <div className="flex items-end justify-center gap-1 h-12">
                  {[...history].reverse().map((h) => (
                    <div key={h.id} className="flex flex-col items-center gap-1">
                      <div
                        className="w-6 rounded-t bg-primary/80"
                        style={{ height: `${Math.max(8, h.overall_score * 0.4)}px` }}
                        title={`${h.overall_score} — ${formatDate(h.created_at)}`}
                      />
                      <span className="text-[10px] text-muted-foreground">{h.overall_score}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
          <div className="glass-panel space-y-4 p-6 lg:col-span-2">
            <ScoreBar label="Keyword match" value={score.keyword_match} />
            <ScoreBar label="Semantic similarity" value={score.semantic_score ?? 0} />
            <ScoreBar label="Skills coverage" value={score.skills_coverage ?? 0} />
            <ScoreBar label="Section completeness" value={score.section_score ?? 0} />
            <ScoreBar label="Formatting" value={score.formatting_score} />

            {score.matched_keywords && score.matched_keywords.length > 0 && (
              <div className="mt-4">
                <h3 className="text-sm font-semibold text-foreground">Matched Keywords</h3>
                <div className="mt-2 flex flex-wrap gap-2">
                  {score.matched_keywords.map((k) => (
                    <span key={k} className="rounded-full bg-emerald-500/10 px-3 py-1 text-xs text-emerald-300 ring-1 ring-emerald-500/20">{k}</span>
                  ))}
                </div>
              </div>
            )}
            {score.missing_keywords && score.missing_keywords.length > 0 && (
              <div className="mt-4">
                <h3 className="text-sm font-semibold text-foreground">Missing Keywords</h3>
                <div className="mt-2 flex flex-wrap gap-2">
                  {score.missing_keywords.map((k) => (
                    <span key={k} className="rounded-full bg-red-500/10 px-3 py-1 text-xs text-red-300 ring-1 ring-red-500/20">{k}</span>
                  ))}
                </div>
              </div>
            )}
            <SuggestionList items={suggestionItems} resumeId={id} />
          </div>
        </div>
      ) : (
        <div className="glass-panel p-8 text-center text-muted-foreground">
          No ATS score yet.{" "}
          <button onClick={rescore} className="text-primary hover:underline">Run analysis</button>
        </div>
      )}
    </div>
  );
}
