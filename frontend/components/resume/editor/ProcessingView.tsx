"use client";

import { Check, Circle, Loader2, X, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import { PIPELINE_STEPS, type PipelineStepStatus } from "@/components/resume/PipelineProgressBar";

interface ProcessingViewProps {
  steps: Record<string, PipelineStepStatus>;
  includeCoverLetter?: boolean;
  title?: string;
}

export function ProcessingView({ steps, includeCoverLetter = false, title }: ProcessingViewProps) {
  const visible = PIPELINE_STEPS.filter((s) => s.id !== "cover_letter" || includeCoverLetter);
  const done = visible.filter((s) => ["completed", "skipped"].includes(steps[s.id])).length;
  const pct = Math.round((done / visible.length) * 100);

  return (
    <div className="flex flex-1 items-center justify-center overflow-y-auto p-6">
      <div className="w-full max-w-md rounded-2xl border border-border bg-card p-6 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10">
            <Sparkles className="h-5 w-5 text-primary" />
          </div>
          <div className="min-w-0">
            <h2 className="text-sm font-semibold text-foreground">Tailoring your resume</h2>
            <p className="truncate text-xs text-muted-foreground">
              {title ? `for ${title}` : "Analyzing the job and optimizing for ATS"}
            </p>
          </div>
        </div>

        <div className="mt-5 flex items-center gap-3">
          <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
            <div className="h-full rounded-full bg-primary transition-all duration-500 ease-out" style={{ width: `${pct}%` }} />
          </div>
          <span className="text-xs font-medium tabular-nums text-muted-foreground">{pct}%</span>
        </div>

        <ul className="mt-5 space-y-0.5">
          {visible.map((step) => {
            const status = steps[step.id] || "pending";
            const active = status === "running";
            return (
              <li
                key={step.id}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
                  active && "bg-primary/5"
                )}
              >
                <span className="flex h-4 w-4 shrink-0 items-center justify-center">
                  {status === "completed" ? (
                    <Check className="h-4 w-4 text-emerald-500" />
                  ) : status === "skipped" ? (
                    <Check className="h-4 w-4 text-muted-foreground/40" />
                  ) : status === "failed" ? (
                    <X className="h-4 w-4 text-destructive" />
                  ) : status === "running" ? (
                    <Loader2 className="h-4 w-4 animate-spin text-primary" />
                  ) : (
                    <Circle className="h-3.5 w-3.5 text-muted-foreground/30" />
                  )}
                </span>
                <span
                  className={cn(
                    active ? "font-medium text-foreground" : status === "completed" ? "text-foreground" : "text-muted-foreground",
                    status === "skipped" && "line-through opacity-60"
                  )}
                >
                  {step.label}
                </span>
              </li>
            );
          })}
        </ul>

        <p className="mt-5 text-center text-xs text-muted-foreground">
          Stay on this page — your editor opens automatically when it&apos;s ready.
        </p>
      </div>
    </div>
  );
}
