"use client";

import Link from "next/link";
import { Download, RefreshCw, Loader2, Columns2, FileCode } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ResumeDocument } from "@/types/resume";

interface EditorHeaderProps {
  id: string;
  resume: ResumeDocument;
  contentSaved: boolean;
  latexSaved: boolean;
  pipelineBusy: boolean;
  previewMode: "split" | "source" | "preview";
  onSetPreviewMode: (mode: "split" | "source" | "preview") => void;
  onRunPipeline: (mode: "full" | "tailor") => void;
  onExportPdf: () => void;
  onApplyWithResume: () => void;
}

export function EditorHeader({
  id,
  resume,
  contentSaved,
  latexSaved,
  pipelineBusy,
  previewMode,
  onSetPreviewMode,
  onRunPipeline,
  onExportPdf,
  onApplyWithResume,
}: EditorHeaderProps) {
  const saveLabel = !contentSaved || !latexSaved ? "Saving..." : "Saved";

  return (
    <header className="flex items-center justify-between border-b border-border px-4 py-2">
      <div className="flex items-center gap-3">
        <Link href="/resumes" className="text-xs text-muted-foreground hover:text-foreground">← Resumes</Link>
        <h1 className="truncate text-sm font-medium text-foreground">{resume.title}</h1>
        <span className={cn("text-xs", contentSaved && latexSaved ? "text-emerald-400" : "text-amber-400")}>
          {saveLabel}
        </span>
        {resume.status === "processing" && (
          <span className="flex items-center gap-1 text-xs text-amber-400">
            <Loader2 className="h-3 w-3 animate-spin" /> Processing
          </span>
        )}
      </div>
      <div className="flex items-center gap-2">
        {(resume.status === "failed" || resume.status === "completed") && (
          <>
            <button
              type="button"
              disabled={pipelineBusy}
              onClick={() => onRunPipeline("tailor")}
              className="btn-secondary text-xs"
            >
              <RefreshCw className={cn("h-3 w-3", pipelineBusy && "animate-spin")} /> Re-tailor
            </button>
            {resume.status === "failed" && (
              <button
                type="button"
                disabled={pipelineBusy}
                onClick={() => onRunPipeline("full")}
                className="btn-secondary text-xs"
              >
                Regenerate all
              </button>
            )}
          </>
        )}
        <Link href={`/resumes/${id}/review`} className="btn-secondary text-xs">ATS Review</Link>
        <button onClick={onApplyWithResume} className="btn-secondary text-xs">Apply with Resume</button>
        <button
          type="button"
          onClick={() => onSetPreviewMode("source")}
          className={cn("btn-secondary text-xs", previewMode === "source" && "ring-1 ring-primary/40")}
        >
          <FileCode className="h-3 w-3" /> Source
        </button>
        <button
          type="button"
          onClick={() => onSetPreviewMode("split")}
          className={cn("btn-secondary text-xs", previewMode === "split" && "ring-1 ring-primary/40")}
        >
          <Columns2 className="h-3 w-3" /> Split
        </button>
        <button
          type="button"
          onClick={() => onSetPreviewMode("preview")}
          className={cn("btn-secondary text-xs", previewMode === "preview" && "ring-1 ring-primary/40")}
        >
          PDF
        </button>
        <button onClick={onExportPdf} className="btn-primary text-xs">
          <Download className="h-3 w-3" /> PDF
        </button>
      </div>
    </header>
  );
}
