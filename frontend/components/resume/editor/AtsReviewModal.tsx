"use client";

import { X, Gauge, RefreshCw, Wand2, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ATSScore } from "@/types/resume";

function tone(score: number): { text: string; bar: string } {
  if (score >= 80) return { text: "text-emerald-400", bar: "bg-emerald-500" };
  if (score >= 60) return { text: "text-amber-400", bar: "bg-amber-500" };
  return { text: "text-red-400", bar: "bg-red-500" };
}

function SubScore({ label, value }: { label: string; value: number }) {
  const t = tone(value);
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span className={cn("font-semibold tabular-nums", t.text)}>{Math.round(value)}</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-muted">
        <div className={cn("h-full rounded-full transition-all duration-500", t.bar)} style={{ width: `${Math.min(100, Math.max(0, value))}%` }} />
      </div>
    </div>
  );
}

interface AtsReviewModalProps {
  atsScore: ATSScore | null;
  rerunning: boolean;
  fixing: boolean;
  onRerun: () => void;
  onFixAll: () => void;
  onClose: () => void;
}

export function AtsReviewModal({ atsScore, rerunning, fixing, onRerun, onFixAll, onClose }: AtsReviewModalProps) {
  const overall = atsScore?.overall_score ?? 0;
  const t = tone(overall);
  const hasGaps = Boolean(atsScore && ((atsScore.missing_keywords?.length ?? 0) > 0 || (atsScore.suggestions?.length ?? 0) > 0));

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 p-4 backdrop-blur-sm" onClick={onClose}>
      <div
        className="flex max-h-[85vh] w-full max-w-lg flex-col overflow-hidden rounded-2xl border border-border bg-card shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-border px-5 py-3">
          <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
            <Gauge className="h-4 w-4 text-primary" /> ATS Review
          </div>
          <button onClick={onClose} className="rounded-md p-1 text-muted-foreground hover:bg-muted hover:text-foreground">
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto">
          {!atsScore ? (
            <div className="p-8 text-center text-sm text-muted-foreground">
              {rerunning ? (
                <span className="inline-flex items-center gap-2"><Loader2 className="h-4 w-4 animate-spin" /> Scoring your resume…</span>
              ) : (
                <>No ATS score yet. Click <strong>Re-run</strong> below to score this resume.</>
              )}
            </div>
          ) : (
            <div className="space-y-5 p-5">
              <div className="flex items-center gap-5 rounded-xl border border-border bg-background/40 p-4">
                <div className="flex flex-col items-center">
                  <div className={cn("text-5xl font-bold leading-none tabular-nums", t.text)}>{overall}</div>
                  <div className="mt-1 text-[11px] uppercase tracking-wide text-muted-foreground">out of 100</div>
                </div>
                <div className="grid flex-1 grid-cols-1 gap-2.5">
                  <SubScore label="Keyword match" value={atsScore.keyword_match} />
                  <SubScore label="Skills coverage" value={atsScore.skills_coverage ?? 0} />
                  <SubScore label="Semantic" value={atsScore.semantic_score ?? 0} />
                  <SubScore label="Formatting" value={atsScore.formatting_score} />
                </div>
              </div>

              {atsScore.matched_keywords?.length ? (
                <div>
                  <p className="mb-1.5 text-xs font-medium text-foreground">Matched keywords ({atsScore.matched_keywords.length})</p>
                  <div className="flex flex-wrap gap-1">
                    {atsScore.matched_keywords.map((k) => (
                      <span key={k} className="rounded bg-emerald-500/10 px-1.5 py-0.5 text-xs text-emerald-300">{k}</span>
                    ))}
                  </div>
                </div>
              ) : null}

              {atsScore.missing_keywords?.length ? (
                <div>
                  <p className="mb-1.5 text-xs font-medium text-foreground">Missing keywords ({atsScore.missing_keywords.length})</p>
                  <div className="flex flex-wrap gap-1">
                    {atsScore.missing_keywords.map((k) => (
                      <span key={k} className="rounded bg-red-500/10 px-1.5 py-0.5 text-xs text-red-300">{k}</span>
                    ))}
                  </div>
                </div>
              ) : null}

              {atsScore.suggestion_items?.length ? (
                <div>
                  <p className="mb-1.5 text-xs font-medium text-foreground">Suggestions</p>
                  <ul className="space-y-1.5">
                    {atsScore.suggestion_items.map((s, i) => (
                      <li key={i} className="flex gap-2 rounded-md border border-border p-2 text-xs">
                        <span
                          className={cn(
                            "mt-0.5 h-fit rounded px-1 py-0.5 text-[10px] font-medium uppercase",
                            s.priority === "high" ? "bg-red-500/15 text-red-300" : s.priority === "medium" ? "bg-amber-500/15 text-amber-300" : "bg-muted text-muted-foreground"
                          )}
                        >
                          {s.priority}
                        </span>
                        <span className="text-muted-foreground">{s.text}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : atsScore.suggestions?.length ? (
                <ul className="space-y-1.5">
                  {atsScore.suggestions.map((s) => (
                    <li key={s} className="rounded-md border border-border p-2 text-xs text-muted-foreground">{s}</li>
                  ))}
                </ul>
              ) : null}
            </div>
          )}
        </div>

        <div className="flex items-center gap-2 border-t border-border px-5 py-3">
          <button onClick={onRerun} disabled={rerunning || fixing} className="btn-secondary flex-1 justify-center text-xs">
            <RefreshCw className={cn("h-3.5 w-3.5", rerunning && "animate-spin")} /> {rerunning ? "Scoring…" : "Re-run score"}
          </button>
          <button
            onClick={onFixAll}
            disabled={fixing || rerunning || !hasGaps}
            title={hasGaps ? "Generate targeted fixes to review one by one in chat" : "No gaps to fix"}
            className="btn-primary flex-[1.4] justify-center text-xs"
          >
            {fixing ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Wand2 className="h-3.5 w-3.5" />}
            {fixing ? "Preparing fixes…" : "Fix all issues"}
          </button>
        </div>
      </div>
    </div>
  );
}
