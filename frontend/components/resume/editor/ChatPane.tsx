"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { MessageSquare, Target, ShieldCheck, Gauge, Mail, Download, Check, X, FileEdit, Loader2, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ATSScore, ChatMessage, CoverLetterDocument, PendingChange, ResumeDocument } from "@/types/resume";

function formatDiffValue(value: string | null): string {
  if (!value) return "";
  try {
    const parsed = JSON.parse(value) as unknown;
    if (Array.isArray(parsed)) return parsed.map((item) => `• ${String(item)}`).join("\n");
    if (parsed && typeof parsed === "object") return JSON.stringify(parsed, null, 2);
  } catch {
    // plain text
  }
  return value;
}

function toLines(value: string | null): string[] {
  return formatDiffValue(value)
    .split("\n")
    .map((l) => l.replace(/\s+$/, ""))
    .filter((l) => l.length > 0);
}

// Claude-Code-style diff: a section header + removed (red, "−") and added
// (green, "+") lines with gutter markers.
function DiffBlock({ label, oldValue, newValue }: { label: string; oldValue: string | null; newValue: string | null }) {
  const removed = toLines(oldValue);
  const added = toLines(newValue);
  return (
    <div className="mt-3 overflow-hidden rounded-md border border-border">
      <div className="flex items-center gap-1.5 border-b border-border bg-muted/70 px-2 py-1 text-[11px] text-muted-foreground">
        <FileEdit className="h-3 w-3 text-primary" />
        <span className="font-medium text-foreground">{label}</span>
        <span className="ml-auto tabular-nums">
          <span className="text-red-400">−{removed.length}</span> <span className="text-emerald-400">+{added.length}</span>
        </span>
      </div>
      <div className="font-mono text-[11px] leading-relaxed">
        {removed.map((line, i) => (
          <div key={`r${i}`} className="flex gap-2 bg-red-950/40 px-2 py-[1px] text-red-300">
            <span className="select-none text-red-500/70">-</span>
            <span className="whitespace-pre-wrap break-words">{line}</span>
          </div>
        ))}
        {added.map((line, i) => (
          <div key={`a${i}`} className="flex gap-2 bg-emerald-950/40 px-2 py-[1px] text-emerald-300">
            <span className="select-none text-emerald-500/70">+</span>
            <span className="whitespace-pre-wrap break-words">{line}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

const THINKING_STAGES = ["Reading your resume…", "Analyzing your request…", "Checking the job description…", "Drafting edits…"];

function ThinkingIndicator() {
  const [stage, setStage] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setStage((v) => (v + 1 < THINKING_STAGES.length ? v + 1 : v)), 1600);
    return () => clearInterval(t);
  }, []);
  return (
    <div className="flex items-center gap-2 rounded-lg border border-primary/20 bg-primary/5 p-3 text-sm">
      <Loader2 className="h-4 w-4 shrink-0 animate-spin text-primary" />
      <span className="animate-pulse text-muted-foreground">{THINKING_STAGES[stage]}</span>
    </div>
  );
}

interface ChatPaneProps {
  resume: ResumeDocument;
  messages: ChatMessage[];
  atsScore: ATSScore | null;
  coverLetter: CoverLetterDocument | null;
  chatInput: string;
  sending: boolean;
  pendingChanges: PendingChange[];
  onChatInputChange: (val: string) => void;
  onSendChat: () => void;
  onHandleChange: (change: PendingChange, action: "accept" | "reject") => void;
  onHandleBatchChanges: (action: "accept" | "reject") => void;
  onExportCoverLetterPdf: () => void;
}

export function ChatPane({
  resume,
  messages,
  atsScore,
  coverLetter,
  chatInput,
  sending,
  pendingChanges,
  onChatInputChange,
  onSendChat,
  onHandleChange,
  onHandleBatchChanges,
  onExportCoverLetterPdf,
}: ChatPaneProps) {
  const insights = (resume.insights_json || {}) as {
    tailoring_insights?: string[];
    jd_analysis?: Record<string, unknown>;
    company_research?: { summary?: string };
  };

  return (
    <div className="flex min-h-[320px] flex-col border-b border-border xl:min-h-0 xl:border-b-0 xl:border-r">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <div className="rounded-lg bg-primary/10 p-3 text-sm text-foreground">
          <MessageSquare className="mb-2 h-4 w-4 text-primary" />
          I&apos;ve tailored your resume for <strong>{resume.title}</strong>. Ask me to edit bullets, sections, or tone.
        </div>

        {resume.why_this_version && (
          <details open className="rounded-lg border border-primary/20 bg-primary/5 p-3 text-xs text-muted-foreground">
            <summary className="flex cursor-pointer list-none items-center gap-2 font-medium text-primary">
              <Target className="h-3.5 w-3.5" /> Why this resume version
            </summary>
            <div className="mt-3 space-y-2">
              <p>
                <span className="text-muted-foreground">Category:</span>{" "}
                <span className="text-foreground">{resume.resume_category?.replaceAll("_", " ")}</span>
                {resume.why_this_version.fit_score != null ? ` · Fit ${resume.why_this_version.fit_score}` : ""}
              </p>
              {resume.why_this_version.matched_keywords?.length ? (
                <div>
                  <p className="text-muted-foreground">Matched keywords</p>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {resume.why_this_version.matched_keywords.map((keyword) => (
                      <span key={keyword} className="rounded bg-emerald-500/10 px-1.5 py-0.5 text-emerald-300">{keyword}</span>
                    ))}
                  </div>
                </div>
              ) : null}
              {resume.why_this_version.missing_keywords?.length ? (
                <div>
                  <p className="text-muted-foreground">Job-description gaps</p>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {resume.why_this_version.missing_keywords.map((keyword) => (
                      <span key={keyword} className="rounded bg-muted px-1.5 py-0.5 text-muted-foreground">{keyword}</span>
                    ))}
                  </div>
                </div>
              ) : null}
              <p className="flex gap-1.5 border-t border-border pt-2 text-[11px] text-muted-foreground">
                <ShieldCheck className="mt-0.5 h-3 w-3 shrink-0 text-emerald-500" />
                {resume.why_this_version.truthfulness}
              </p>
            </div>
          </details>
        )}

        {insights.tailoring_insights && insights.tailoring_insights.length > 0 && (
          <details className="rounded-lg border border-border p-2 text-xs text-muted-foreground">
            <summary className="cursor-pointer font-medium text-foreground">Resume tailoring insights</summary>
            <ul className="mt-2 list-disc pl-4">{insights.tailoring_insights.map((i, idx) => <li key={idx}>{i}</li>)}</ul>
          </details>
        )}
        {insights.jd_analysis && (
          <details className="rounded-lg border border-border p-2 text-xs text-muted-foreground">
            <summary className="cursor-pointer font-medium text-foreground">JD analysis</summary>
            <pre className="mt-2 whitespace-pre-wrap">{JSON.stringify(insights.jd_analysis, null, 2)}</pre>
          </details>
        )}
        {insights.company_research?.summary && (
          <details className="rounded-lg border border-border p-2 text-xs text-muted-foreground">
            <summary className="cursor-pointer font-medium text-foreground">Company research</summary>
            <p className="mt-2">{insights.company_research.summary}</p>
          </details>
        )}

        {atsScore && (
          <details open className="rounded-lg border border-border bg-card/70 p-3 text-xs text-muted-foreground">
            <summary className="flex cursor-pointer list-none items-center gap-2 font-medium text-foreground">
              <Gauge className="h-3.5 w-3.5 text-primary" /> ATS feedback
            </summary>
            <div className="mt-3 grid grid-cols-2 gap-2 text-center">
              {[
                ["Overall", atsScore.overall_score],
                ["Keywords", atsScore.keyword_match],
                ["Skills", atsScore.skills_coverage ?? 0],
                ["Format", atsScore.formatting_score],
              ].map(([label, value]) => (
                <div key={String(label)} className="rounded border border-border px-2 py-2">
                  <div className="text-base font-semibold text-foreground">{Number(value)}</div>
                  <div>{String(label)}</div>
                </div>
              ))}
            </div>
            {atsScore.matched_keywords?.length ? (
              <div className="mt-3">
                <p>Matched keywords</p>
                <div className="mt-1 flex flex-wrap gap-1">
                  {atsScore.matched_keywords.slice(0, 10).map((keyword) => (
                    <span key={keyword} className="rounded bg-emerald-500/10 px-1.5 py-0.5 text-emerald-300">{keyword}</span>
                  ))}
                </div>
              </div>
            ) : null}
            {atsScore.missing_keywords?.length ? (
              <div className="mt-3">
                <p>Missing keywords</p>
                <div className="mt-1 flex flex-wrap gap-1">
                  {atsScore.missing_keywords.slice(0, 10).map((keyword) => (
                    <span key={keyword} className="rounded bg-muted px-1.5 py-0.5 text-muted-foreground">{keyword}</span>
                  ))}
                </div>
              </div>
            ) : null}
            {atsScore.suggestions.length > 0 && (
              <ul className="mt-3 list-disc space-y-1 pl-4">
                {atsScore.suggestions.slice(0, 3).map((s) => <li key={s}>{s}</li>)}
              </ul>
            )}
          </details>
        )}

        {coverLetter && (
          <details className="rounded-lg border border-border bg-card/70 p-3 text-xs text-muted-foreground">
            <summary className="flex cursor-pointer list-none items-center gap-2 font-medium text-foreground">
              <Mail className="h-3.5 w-3.5 text-primary" /> Cover letter
            </summary>
            <div className="mt-3 space-y-2">
              <p><span className="text-muted-foreground">Status:</span> <span className="text-foreground">{coverLetter.status}</span></p>
              <p className="line-clamp-4">
                {Array.isArray(coverLetter.content_json.paragraphs)
                  ? coverLetter.content_json.paragraphs.join(" ")
                  : "Open the cover letter editor to review the generated draft."}
              </p>
              <div className="flex gap-2 pt-1">
                <Link href={`/cover-letters/${coverLetter.id}`} className="btn-secondary flex-1 justify-center text-xs">Edit</Link>
                <button type="button" onClick={onExportCoverLetterPdf} className="btn-secondary flex-1 justify-center text-xs">
                  <Download className="h-3 w-3" /> PDF
                </button>
              </div>
            </div>
          </details>
        )}

        {pendingChanges.length > 0 && (
          <div className="flex gap-2 rounded-lg border border-border bg-card/80 p-2">
            <button onClick={() => onHandleBatchChanges("reject")} className="btn-secondary flex-1 text-xs">
              <X className="h-3 w-3" /> Reject all ({pendingChanges.length})
            </button>
            <button onClick={() => onHandleBatchChanges("accept")} className="btn-primary flex-1 text-xs">
              <Check className="h-3 w-3" /> Accept all ({pendingChanges.length})
            </button>
          </div>
        )}

        {messages.map((m) => (
          <div key={m.id} className={cn("rounded-lg p-3 text-sm", m.role === "assistant" ? "bg-card text-foreground" : "bg-primary/10 text-foreground")}>
            {m.role === "assistant" && (
              <div className="mb-1.5 flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wide text-primary">
                <Sparkles className="h-3 w-3" /> AI Editor
              </div>
            )}
            {m.content}
            {m.pending_changes.filter((c) => c.status === "pending").map((ch) => (
              <div key={ch.id} className="mt-3">
                <DiffBlock label={ch.path_label || ch.path} oldValue={ch.old_value} newValue={ch.new_value} />
                <div className="mt-2 flex gap-2">
                  <button onClick={() => onHandleChange(ch, "reject")} className="btn-secondary flex-1 text-xs"><X className="h-3 w-3" /> Reject</button>
                  <button onClick={() => onHandleChange(ch, "accept")} className="btn-primary flex-1 text-xs"><Check className="h-3 w-3" /> Accept</button>
                </div>
              </div>
            ))}
          </div>
        ))}

        {sending && <ThinkingIndicator />}
      </div>

      <div className="border-t border-border p-3">
        <textarea
          className="input-field min-h-[60px] text-sm"
          placeholder={pendingChanges.length ? "Approve or reject pending changes first." : "Trim, tailor, sharpen..."}
          value={chatInput}
          onChange={(e) => onChatInputChange(e.target.value)}
          disabled={pendingChanges.length > 0 || sending}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && (e.preventDefault(), onSendChat())}
        />
        <button onClick={onSendChat} disabled={sending || pendingChanges.length > 0} className="btn-primary mt-2 w-full text-xs">
          {sending ? "Thinking..." : "Send"}
        </button>
      </div>
    </div>
  );
}
