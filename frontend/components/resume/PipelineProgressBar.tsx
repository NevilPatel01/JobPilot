"use client";

import { Check, Circle, Loader2, X } from "lucide-react";
import { cn } from "@/lib/utils";

export type PipelineStepStatus = "pending" | "running" | "completed" | "failed" | "skipped";

export const PIPELINE_STEPS = [
  { id: "ingest_context", label: "Ingest context" },
  { id: "analyze_jd", label: "Analyze job description" },
  { id: "research_company", label: "Research company" },
  { id: "tailor_resume", label: "Tailor resume" },
  { id: "cover_letter", label: "Cover letter" },
  { id: "ats_score", label: "ATS score" },
] as const;

interface PipelineProgressBarProps {
  steps: Record<string, PipelineStepStatus>;
  includeCoverLetter?: boolean;
  className?: string;
}

export function PipelineProgressBar({ steps, includeCoverLetter = false, className }: PipelineProgressBarProps) {
  const visibleSteps = PIPELINE_STEPS.filter((s) => s.id !== "cover_letter" || includeCoverLetter);

  return (
    <div className={cn("flex flex-wrap items-center gap-x-4 gap-y-2", className)}>
      {visibleSteps.map((step, index) => {
        const status = steps[step.id] || "pending";
        return (
          <div key={step.id} className="flex items-center gap-2 text-xs">
            {index > 0 && <span className="hidden text-muted-foreground sm:inline">→</span>}
            <span
              className={cn(
                "flex items-center gap-1.5 rounded-full px-2 py-1",
                status === "running" && "bg-amber-500/20 text-amber-200",
                status === "completed" && "bg-emerald-500/15 text-emerald-300",
                status === "failed" && "bg-red-500/20 text-red-300",
                status === "skipped" && "bg-muted text-muted-foreground",
                status === "pending" && "bg-card text-muted-foreground"
              )}
            >
              {status === "running" && <Loader2 className="h-3 w-3 animate-spin" />}
              {status === "completed" && <Check className="h-3 w-3" />}
              {status === "failed" && <X className="h-3 w-3" />}
              {status === "pending" && <Circle className="h-3 w-3" />}
              {status === "skipped" && <Check className="h-3 w-3 opacity-50" />}
              {step.label}
            </span>
          </div>
        );
      })}
    </div>
  );
}
