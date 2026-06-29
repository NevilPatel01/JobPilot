"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { Download, MessageSquare, Check, X, RefreshCw, Loader2, Columns2, FileCode, Target, ShieldCheck, Mail, Gauge } from "lucide-react";
import { api } from "@/lib/api";
import type { ATSScore, ChatMessage, CoverLetterDocument, PendingChange, ResumeContent, ResumeDocument } from "@/types/resume";
import { StructuredProfileEditor } from "@/components/resume/StructuredEditor";
import { PipelineProgressBar, PIPELINE_STEPS, type PipelineStepStatus } from "@/components/resume/PipelineProgressBar";
import { LatexEditor } from "@/components/resume/LatexEditor";
import { PdfPreviewPane } from "@/components/resume/PdfPreviewPane";
import { cn } from "@/lib/utils";
import { io, Socket } from "socket.io-client";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function formatDiffValue(value: string | null): string {
  if (!value) return "";
  try {
    const parsed = JSON.parse(value) as unknown;
    if (Array.isArray(parsed)) {
      return parsed.map((item) => `• ${String(item)}`).join("\n");
    }
    if (parsed && typeof parsed === "object") {
      return JSON.stringify(parsed, null, 2);
    }
  } catch {
    // plain text
  }
  return value;
}

function initialPipelineSteps(): Record<string, PipelineStepStatus> {
  return Object.fromEntries(PIPELINE_STEPS.map((step) => [step.id, "pending" as PipelineStepStatus]));
}

export default function ResumeEditorPage() {
  const { id } = useParams<{ id: string }>();
  const searchParams = useSearchParams();
  const [resume, setResume] = useState<ResumeDocument | null>(null);
  const [content, setContent] = useState<ResumeContent | null>(null);
  const [latex, setLatex] = useState("");
  const [previewMode, setPreviewMode] = useState<"split" | "source" | "preview">("split");
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [pdfError, setPdfError] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [atsScore, setAtsScore] = useState<ATSScore | null>(null);
  const [coverLetter, setCoverLetter] = useState<CoverLetterDocument | null>(null);
  const [chatInput, setChatInput] = useState("");
  const [sending, setSending] = useState(false);
  const [contentSaved, setContentSaved] = useState(true);
  const [latexSaved, setLatexSaved] = useState(true);
  const [regeneratingLatex, setRegeneratingLatex] = useState(false);
  const [pipelineBusy, setPipelineBusy] = useState(false);
  const [pipelineSteps, setPipelineSteps] = useState<Record<string, PipelineStepStatus>>(initialPipelineSteps);
  const contentSaveTimer = useRef<ReturnType<typeof setTimeout>>();
  const latexSaveTimer = useRef<ReturnType<typeof setTimeout>>();
  const skipLatexSave = useRef(true);
  const socketRef = useRef<Socket | null>(null);
  const prevResumeStatus = useRef<string | null>(null);

  const pendingChanges = messages.flatMap((m) => m.pending_changes.filter((c) => c.status === "pending"));

  const load = useCallback(async () => {
    const r = await api.getResume(id);
    setResume(r);
    setContent(r.content_json);
    skipLatexSave.current = true;
    if (r.latex_source?.trim()) {
      setLatex(r.latex_source);
    } else {
      const { latex: generated } = await api.getResumeLatex(id);
      setLatex(generated);
    }
    const msgs = await api.getResumeMessages(id);
    setMessages(msgs);
    const latestAts = await api.getATSScore(id).catch(() => null);
    setAtsScore(latestAts);
    if (r.cover_letter_id) {
      const letter = await api.getCoverLetter(r.cover_letter_id).catch(() => null);
      setCoverLetter(letter);
    } else {
      setCoverLetter(null);
    }
    setContentSaved(true);
    setLatexSaved(true);
    skipLatexSave.current = false;
  }, [id]);

  useEffect(() => {
    load().catch(console.error);
  }, [load]);

  useEffect(() => {
    const chat = searchParams.get("chat");
    if (chat) setChatInput(chat);
  }, [searchParams]);

  useEffect(() => {
    const socket = io(API_URL, { path: "/socket.io", transports: ["websocket", "polling"] });
    socketRef.current = socket;

    const onStep = (data: { step?: string; status?: string; cached?: boolean; skipped?: boolean }) => {
      if (!data.step || !data.status) return;
      setPipelineSteps((prev) => {
        const next = { ...prev };
        if (data.status === "running") {
          next[data.step!] = "running";
        } else if (data.status === "failed") {
          next[data.step!] = "failed";
        } else if (data.status === "completed") {
          next[data.step!] = data.skipped ? "skipped" : "completed";
        }
        return next;
      });
      if (data.status === "completed" || data.status === "failed") {
        load().catch(console.error);
      }
    };

    socket.on("connect", () => socket.emit("join_room", { room: `resume:${id}` }));
    socket.on("agent_complete", () => {
      setPipelineSteps(initialPipelineSteps());
      load().catch(console.error);
    });
    socket.on("agent_step", onStep);
    socket.on("agent_error", (data: { step?: string }) => {
      if (data.step) {
        setPipelineSteps((prev) => ({ ...prev, [data.step!]: "failed" }));
      }
      load().catch(console.error);
    });
    return () => { socket.disconnect(); };
  }, [id, load]);

  useEffect(() => {
    if (resume?.status === "processing" && prevResumeStatus.current !== "processing") {
      setPipelineSteps(initialPipelineSteps());
    }
    prevResumeStatus.current = resume?.status ?? null;
  }, [resume?.status]);

  useEffect(() => {
    if (!content) return;
    setContentSaved(false);
    clearTimeout(contentSaveTimer.current);
    contentSaveTimer.current = setTimeout(async () => {
      try {
        await api.updateResume(id, { content_json: content });
        setContentSaved(true);
      } catch (e) {
        console.error(e);
      }
    }, 500);
    return () => clearTimeout(contentSaveTimer.current);
  }, [content, id]);

  useEffect(() => {
    if (!latex || skipLatexSave.current) return;
    setLatexSaved(false);
    clearTimeout(latexSaveTimer.current);
    latexSaveTimer.current = setTimeout(async () => {
      try {
        await api.updateResume(id, { latex_source: latex });
        setLatexSaved(true);
      } catch (e) {
        console.error(e);
      }
    }, 800);
    return () => clearTimeout(latexSaveTimer.current);
  }, [latex, id]);

  useEffect(() => {
    return () => {
      if (pdfUrl) URL.revokeObjectURL(pdfUrl);
    };
  }, [pdfUrl]);

  const refreshPdfPreview = useCallback(async () => {
    setPdfLoading(true);
    setPdfError(null);
    try {
      const blob = await api.downloadResumePdf(id, { inline: true });
      setPdfUrl((prev) => {
        if (prev) URL.revokeObjectURL(prev);
        return URL.createObjectURL(blob);
      });
    } catch (e: unknown) {
      setPdfError(e instanceof Error ? e.message : "PDF preview failed");
    } finally {
      setPdfLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (!latexSaved || !latex.trim()) return;
    const timer = setTimeout(() => {
      refreshPdfPreview().catch(console.error);
    }, 2500);
    return () => clearTimeout(timer);
  }, [latexSaved, latex, refreshPdfPreview]);

  const sendChat = async () => {
    if (!chatInput.trim() || pendingChanges.length > 0) return;
    setSending(true);
    try {
      const exchange = await api.sendResumeChat(id, chatInput);
      setMessages((prev) => [...prev, exchange.user_message, exchange.assistant_message]);
      setChatInput("");
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Chat failed");
    } finally {
      setSending(false);
    }
  };

  const handleChange = async (change: PendingChange, action: "accept" | "reject") => {
    const result = await api.handleResumeChange(id, change.id, action);
    if (action === "accept") setContent(result.content_json);
    setMessages((prev) =>
      prev.map((m) => ({
        ...m,
        pending_changes: m.pending_changes.map((c) =>
          c.id === change.id ? { ...c, status: action === "accept" ? "accepted" : "rejected" } : c
        ),
      }))
    );
    load();
  };

  const handleBatchChanges = async (action: "accept" | "reject") => {
    if (pendingChanges.length === 0) return;
    const result = await api.handleResumeChangesBatch(
      id,
      pendingChanges.map((c) => c.id),
      action
    );
    if (action === "accept") setContent(result.content_json);
    const ids = new Set(pendingChanges.map((c) => c.id));
    setMessages((prev) =>
      prev.map((m) => ({
        ...m,
        pending_changes: m.pending_changes.map((c) =>
          ids.has(c.id) ? { ...c, status: action === "accept" ? "accepted" : "rejected" } : c
        ),
      }))
    );
    load();
  };

  const regenerateLatexFromContent = async () => {
    setRegeneratingLatex(true);
    try {
      skipLatexSave.current = true;
      const updated = await api.regenerateResumeLatex(id);
      setLatex(updated.latex_source || "");
      setLatexSaved(true);
      skipLatexSave.current = false;
      if (previewMode !== "source") await refreshPdfPreview();
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "LaTeX regeneration failed");
    } finally {
      setRegeneratingLatex(false);
    }
  };

  const exportPdf = async () => {
    try {
      const blob = await api.downloadResumePdf(id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${resume?.title || "resume"}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "PDF export failed");
    }
  };

  const exportCoverLetterPdf = async () => {
    if (!coverLetter) return;
    try {
      const blob = await api.downloadCoverLetterPdf(coverLetter.id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${coverLetter.title || "cover-letter"}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Cover letter export failed");
    }
  };

  const runPipeline = async (mode: "full" | "tailor") => {
    setPipelineBusy(true);
    try {
      if (mode === "full") await api.regenerateResume(id);
      else await api.regenerateTailoredResume(id);
      await load();
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Pipeline failed to start");
    } finally {
      setPipelineBusy(false);
    }
  };

  const applyWithResume = async () => {
    try {
      if (resume?.inbox_job_id) {
        await api.updateInboxStatus(resume.inbox_job_id, "applied");
      } else {
        const app = await api.createApplication({
          job_title: resume?.title,
          company: resume?.company_name || "Unknown",
          job_url: resume?.company_url || undefined,
          status: "to_apply",
          notes: `Resume: ${resume?.id}`,
        });
        await api.updateResume(id, { application_id: app.id });
      }
      window.location.href = "/tracker";
    } catch (error) {
      alert(error instanceof Error ? error.message : "Could not add application to Tracker");
    }
  };

  if (!resume || !content) {
    return <div className="flex h-full items-center justify-center text-muted-foreground">Loading editor...</div>;
  }

  const insights = (resume.insights_json || {}) as {
    tailoring_insights?: string[];
    jd_analysis?: Record<string, unknown>;
    company_research?: { summary?: string };
  };

  const saveLabel = !contentSaved || !latexSaved ? "Saving..." : "Saved";

  return (
    <div className="flex h-full flex-col bg-background">
      <header className="flex items-center justify-between border-b border-border px-4 py-2">
        <div className="flex items-center gap-3">
          <Link href="/resumes" className="text-xs text-muted-foreground hover:text-foreground">← Resumes</Link>
          <h1 className="truncate text-sm font-medium text-foreground">{resume.title}</h1>
          <span className={cn("text-xs", contentSaved && latexSaved ? "text-emerald-400" : "text-amber-400")}>{saveLabel}</span>
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
                onClick={() => runPipeline("tailor")}
                className="btn-secondary text-xs"
              >
                <RefreshCw className={cn("h-3 w-3", pipelineBusy && "animate-spin")} /> Re-tailor
              </button>
              {resume.status === "failed" && (
                <button
                  type="button"
                  disabled={pipelineBusy}
                  onClick={() => runPipeline("full")}
                  className="btn-secondary text-xs"
                >
                  Regenerate all
                </button>
              )}
            </>
          )}
          <Link href={`/resumes/${id}/review`} className="btn-secondary text-xs">ATS Review</Link>
          <button
            onClick={applyWithResume}
            className="btn-secondary text-xs"
          >
            Apply with Resume
          </button>
          <button
            type="button"
            onClick={() => setPreviewMode("source")}
            className={cn("btn-secondary text-xs", previewMode === "source" && "ring-1 ring-primary/40")}
          >
            <FileCode className="h-3 w-3" /> Source
          </button>
          <button
            type="button"
            onClick={() => setPreviewMode("split")}
            className={cn("btn-secondary text-xs", previewMode === "split" && "ring-1 ring-primary/40")}
          >
            <Columns2 className="h-3 w-3" /> Split
          </button>
          <button
            type="button"
            onClick={() => setPreviewMode("preview")}
            className={cn("btn-secondary text-xs", previewMode === "preview" && "ring-1 ring-primary/40")}
          >
            PDF
          </button>
          <button onClick={exportPdf} className="btn-primary text-xs">
            <Download className="h-3 w-3" /> PDF
          </button>
        </div>
      </header>

      {resume.status === "failed" && resume.pipeline_error && (
        <div className="border-b border-red-500/30 bg-red-950/30 px-4 py-2 text-sm text-red-300">
          Pipeline failed{resume.last_step ? ` at ${resume.last_step}` : ""}: {resume.pipeline_error}
        </div>
      )}

      {resume.status === "processing" && (
        <div className="border-b border-amber-500/30 bg-amber-950/20 px-4 py-3 text-sm text-amber-200">
          <p>AI pipeline is running — tailoring resume, scoring ATS, and generating documents.</p>
          <PipelineProgressBar
            className="mt-3"
            steps={pipelineSteps}
            includeCoverLetter={resume.create_cover_letter}
          />
        </div>
      )}

      <div className="grid flex-1 grid-rows-[minmax(320px,0.65fr)_minmax(520px,1.4fr)_minmax(420px,1fr)] overflow-y-auto xl:grid-cols-[320px_1fr_360px] xl:grid-rows-none xl:overflow-hidden">
        {/* Chat pane */}
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
                  <p><span className="text-muted-foreground">Category:</span> <span className="text-foreground">{resume.resume_category?.replaceAll("_", " ")}</span>{resume.why_this_version.fit_score != null ? ` · Fit ${resume.why_this_version.fit_score}` : ""}</p>
                  {resume.why_this_version.matched_keywords?.length ? <div><p className="text-muted-foreground">Matched keywords</p><div className="mt-1 flex flex-wrap gap-1">{resume.why_this_version.matched_keywords.map((keyword) => <span key={keyword} className="rounded bg-emerald-500/10 px-1.5 py-0.5 text-emerald-300">{keyword}</span>)}</div></div> : null}
                  {resume.why_this_version.missing_keywords?.length ? <div><p className="text-muted-foreground">Job-description gaps</p><div className="mt-1 flex flex-wrap gap-1">{resume.why_this_version.missing_keywords.map((keyword) => <span key={keyword} className="rounded bg-muted px-1.5 py-0.5 text-muted-foreground">{keyword}</span>)}</div></div> : null}
                  <p className="flex gap-1.5 border-t border-border pt-2 text-[11px] text-muted-foreground"><ShieldCheck className="mt-0.5 h-3 w-3 shrink-0 text-emerald-500" />{resume.why_this_version.truthfulness}</p>
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
                    {atsScore.suggestions.slice(0, 3).map((suggestion) => <li key={suggestion}>{suggestion}</li>)}
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
                  <p className="line-clamp-4">{Array.isArray(coverLetter.content_json.paragraphs) ? coverLetter.content_json.paragraphs.join(" ") : "Open the cover letter editor to review the generated draft."}</p>
                  <div className="flex gap-2 pt-1">
                    <Link href={`/cover-letters/${coverLetter.id}`} className="btn-secondary flex-1 justify-center text-xs">Edit</Link>
                    <button type="button" onClick={exportCoverLetterPdf} className="btn-secondary flex-1 justify-center text-xs">
                      <Download className="h-3 w-3" /> PDF
                    </button>
                  </div>
                </div>
              </details>
            )}

            {pendingChanges.length > 0 && (
              <div className="flex gap-2 rounded-lg border border-border bg-card/80 p-2">
                <button onClick={() => handleBatchChanges("reject")} className="btn-secondary flex-1 text-xs">
                  <X className="h-3 w-3" /> Reject all ({pendingChanges.length})
                </button>
                <button onClick={() => handleBatchChanges("accept")} className="btn-primary flex-1 text-xs">
                  <Check className="h-3 w-3" /> Accept all ({pendingChanges.length})
                </button>
              </div>
            )}

            {messages.map((m) => (
              <div key={m.id} className={cn("rounded-lg p-3 text-sm", m.role === "assistant" ? "bg-card text-foreground" : "bg-primary/10 text-foreground")}>
                {m.content}
                {m.pending_changes.filter((c) => c.status === "pending").map((ch) => (
                  <div key={ch.id} className="mt-3 overflow-hidden rounded border border-border font-mono text-xs">
                    <div className="border-b border-border bg-muted/80 px-2 py-1 text-[11px] font-sans text-muted-foreground">
                      {ch.path_label || ch.path}
                    </div>
                    <div className="whitespace-pre-wrap bg-red-950/50 p-2 text-red-300 line-through">{formatDiffValue(ch.old_value)}</div>
                    <div className="whitespace-pre-wrap bg-emerald-950/50 p-2 text-emerald-300">{formatDiffValue(ch.new_value)}</div>
                    <div className="flex gap-2 border-t border-border p-2">
                      <button onClick={() => handleChange(ch, "reject")} className="btn-secondary flex-1 text-xs"><X className="h-3 w-3" /> Reject</button>
                      <button onClick={() => handleChange(ch, "accept")} className="btn-primary flex-1 text-xs"><Check className="h-3 w-3" /> Accept</button>
                    </div>
                  </div>
                ))}
              </div>
            ))}
          </div>
          <div className="border-t border-border p-3">
            <textarea
              className="input-field min-h-[60px] text-sm"
              placeholder={pendingChanges.length ? "Approve or reject pending changes first." : "Trim, tailor, sharpen..."}
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              disabled={pendingChanges.length > 0 || sending}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && (e.preventDefault(), sendChat())}
            />
            <button onClick={sendChat} disabled={sending || pendingChanges.length > 0} className="btn-primary mt-2 w-full text-xs">
              {sending ? "Thinking..." : "Send"}
            </button>
          </div>
        </div>

        {/* LaTeX source + PDF preview */}
        <div className="flex min-h-[520px] flex-col overflow-hidden bg-card p-4 xl:min-h-0">
          <div className="mb-2 rounded-lg border border-primary/30 bg-primary/10 px-3 py-2 text-xs text-primary">
            LaTeX compiles to PDF via Tectonic — preview reflects the exact exported document.
          </div>
          <div className="mb-3 flex items-center justify-between gap-2">
            <p className="text-xs font-medium uppercase tracking-widest text-primary">LaTeX · PDF Preview</p>
            <button
              type="button"
              onClick={regenerateLatexFromContent}
              disabled={regeneratingLatex}
              className="btn-secondary text-xs"
            >
              <RefreshCw className={cn("h-3 w-3", regeneratingLatex && "animate-spin")} />
              Regenerate from content
            </button>
          </div>
          <div
            className={cn(
              "grid min-h-0 flex-1 gap-3",
              previewMode === "split" && "grid-cols-2",
              previewMode === "source" && "grid-cols-1",
              previewMode === "preview" && "grid-cols-1"
            )}
          >
            {previewMode !== "preview" && (
              <div className="h-full min-h-0 overflow-hidden rounded-lg border border-border">
                <LatexEditor value={latex} onChange={setLatex} className="h-full text-xs" />
              </div>
            )}
            {previewMode !== "source" && (
              <PdfPreviewPane pdfUrl={pdfUrl} loading={pdfLoading} error={pdfError} />
            )}
          </div>
        </div>

        {/* Structured editor */}
        <div className="min-h-[420px] overflow-y-auto border-t border-border p-4 xl:min-h-0 xl:border-l xl:border-t-0">
          <StructuredProfileEditor content={content} onChange={setContent} />
        </div>
      </div>
    </div>
  );
}
