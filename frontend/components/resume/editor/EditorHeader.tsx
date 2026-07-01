"use client";

import Link from "next/link";
import { Download, RefreshCw, Loader2, FileCode, MessageSquare, PanelRight } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ResumeDocument } from "@/types/resume";

interface EditorHeaderProps {
  id: string;
  resume: ResumeDocument;
  contentSaved: boolean;
  latexSaved: boolean;
  pipelineBusy: boolean;
  leftInset?: boolean;
  showChat: boolean;
  showLatex: boolean;
  showDetails: boolean;
  onToggleChat: () => void;
  onToggleLatex: () => void;
  onToggleDetails: () => void;
  onRunPipeline: (mode: "full" | "tailor") => void;
  onExportPdf: () => void;
  onApplyWithResume: () => void;
}

function PanelToggle({ active, onClick, icon, label }: { active: boolean; onClick: () => void; icon: React.ReactNode; label: string }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      title={`${active ? "Hide" : "Show"} ${label}`}
      className={cn(
        "btn-secondary text-xs",
        active ? "ring-1 ring-primary/50 text-foreground" : "opacity-60"
      )}
    >
      {icon} {label}
    </button>
  );
}

export function EditorHeader({
  id,
  resume,
  contentSaved,
  latexSaved,
  pipelineBusy,
  leftInset = false,
  showChat,
  showLatex,
  showDetails,
  onToggleChat,
  onToggleLatex,
  onToggleDetails,
  onRunPipeline,
  onExportPdf,
  onApplyWithResume,
}: EditorHeaderProps) {
  const saveLabel = !contentSaved || !latexSaved ? "Saving..." : "Saved";

  return (
    <header className={cn("flex flex-wrap items-center justify-between gap-y-2 border-b border-border px-4 py-2", leftInset && "pl-14")}>
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
        <div className="mx-1 flex items-center gap-1.5 rounded-lg border border-border/60 bg-muted/40 px-1.5 py-1">
          <PanelToggle active={showChat} onClick={onToggleChat} icon={<MessageSquare className="h-3 w-3" />} label="Chat" />
          <PanelToggle active={showLatex} onClick={onToggleLatex} icon={<FileCode className="h-3 w-3" />} label="LaTeX" />
          <PanelToggle active={showDetails} onClick={onToggleDetails} icon={<PanelRight className="h-3 w-3" />} label="Details" />
        </div>
        <button onClick={onExportPdf} className="btn-primary text-xs">
          <Download className="h-3 w-3" /> PDF
        </button>
      </div>
    </header>
  );
}
