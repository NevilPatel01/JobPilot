"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { RefreshCw } from "lucide-react";
import { api } from "@/lib/api";
import type { ATSScore, ChatMessage, CoverLetterDocument, PendingChange, ResumeContent, ResumeDocument } from "@/types/resume";
import { StructuredProfileEditor } from "@/components/resume/StructuredEditor";
import { PipelineProgressBar, PIPELINE_STEPS, type PipelineStepStatus } from "@/components/resume/PipelineProgressBar";
import { LatexEditor } from "@/components/resume/LatexEditor";
import { PdfPreviewPane } from "@/components/resume/PdfPreviewPane";
import { EditorHeader } from "@/components/resume/editor/EditorHeader";
import { ChatPane } from "@/components/resume/editor/ChatPane";
import { useSidebar } from "@/components/layout/SidebarContext";
import { cn } from "@/lib/utils";
import { io, Socket } from "socket.io-client";

function usePersistentToggle(key: string, initial = true): [boolean, () => void] {
  const [value, setValue] = useState(initial);
  useEffect(() => {
    const stored = localStorage.getItem(key);
    if (stored !== null) setValue(stored === "true");
  }, [key]);
  const toggle = useCallback(() => {
    setValue((v) => {
      const next = !v;
      localStorage.setItem(key, String(next));
      return next;
    });
  }, [key]);
  return [value, toggle];
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function initialPipelineSteps(): Record<string, PipelineStepStatus> {
  return Object.fromEntries(PIPELINE_STEPS.map((step) => [step.id, "pending" as PipelineStepStatus]));
}

export default function ResumeEditorPage() {
  const { id } = useParams<{ id: string }>();
  const searchParams = useSearchParams();
  const [resume, setResume] = useState<ResumeDocument | null>(null);
  const [content, setContent] = useState<ResumeContent | null>(null);
  const [latex, setLatex] = useState("");
  const { isOpen: sidebarOpen } = useSidebar();
  const [showChat, toggleChat] = usePersistentToggle("jobpilot-editor-chat");
  const [showLatex, toggleLatex] = usePersistentToggle("jobpilot-editor-latex");
  const [showDetails, toggleDetails] = usePersistentToggle("jobpilot-editor-details");
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

  useEffect(() => { load().catch(console.error); }, [load]);

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
        if (data.status === "running") next[data.step!] = "running";
        else if (data.status === "failed") next[data.step!] = "failed";
        else if (data.status === "completed") next[data.step!] = data.skipped ? "skipped" : "completed";
        return next;
      });
      if (data.status === "completed" || data.status === "failed") load().catch(console.error);
    };

    socket.on("connect", () => socket.emit("join_room", { room: `resume:${id}` }));
    socket.on("agent_complete", () => { setPipelineSteps(initialPipelineSteps()); load().catch(console.error); });
    socket.on("agent_step", onStep);
    socket.on("agent_error", (data: { step?: string }) => {
      if (data.step) setPipelineSteps((prev) => ({ ...prev, [data.step!]: "failed" }));
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
      try { await api.updateResume(id, { content_json: content }); setContentSaved(true); }
      catch (e) { console.error(e); }
    }, 500);
    return () => clearTimeout(contentSaveTimer.current);
  }, [content, id]);

  useEffect(() => {
    if (!latex || skipLatexSave.current) return;
    setLatexSaved(false);
    clearTimeout(latexSaveTimer.current);
    latexSaveTimer.current = setTimeout(async () => {
      try { await api.updateResume(id, { latex_source: latex }); setLatexSaved(true); }
      catch (e) { console.error(e); }
    }, 800);
    return () => clearTimeout(latexSaveTimer.current);
  }, [latex, id]);

  useEffect(() => { return () => { if (pdfUrl) URL.revokeObjectURL(pdfUrl); }; }, [pdfUrl]);

  const refreshPdfPreview = useCallback(async () => {
    setPdfLoading(true);
    setPdfError(null);
    try {
      const blob = await api.downloadResumePdf(id, { inline: true });
      setPdfUrl((prev) => { if (prev) URL.revokeObjectURL(prev); return URL.createObjectURL(blob); });
    } catch (e: unknown) {
      setPdfError(e instanceof Error ? e.message : "PDF preview failed");
    } finally {
      setPdfLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (!latexSaved || !latex.trim()) return;
    const timer = setTimeout(() => refreshPdfPreview().catch(console.error), 2500);
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
    const result = await api.handleResumeChangesBatch(id, pendingChanges.map((c) => c.id), action);
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
      await refreshPdfPreview();
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

  return (
    <div className="flex h-full flex-col bg-background">
      <EditorHeader
        id={id}
        resume={resume}
        contentSaved={contentSaved}
        latexSaved={latexSaved}
        pipelineBusy={pipelineBusy}
        leftInset={!sidebarOpen}
        showChat={showChat}
        showLatex={showLatex}
        showDetails={showDetails}
        onToggleChat={toggleChat}
        onToggleLatex={toggleLatex}
        onToggleDetails={toggleDetails}
        onRunPipeline={runPipeline}
        onExportPdf={exportPdf}
        onApplyWithResume={applyWithResume}
      />

      {resume.status === "failed" && resume.pipeline_error && (
        <div className="border-b border-red-500/30 bg-red-950/30 px-4 py-2 text-sm text-red-300">
          Pipeline failed{resume.last_step ? ` at ${resume.last_step}` : ""}: {resume.pipeline_error}
        </div>
      )}

      {resume.status === "processing" && (
        <div className="border-b border-amber-500/30 bg-amber-950/20 px-4 py-3 text-sm text-amber-200">
          <p>AI pipeline is running — tailoring resume, scoring ATS, and generating documents.</p>
          <PipelineProgressBar className="mt-3" steps={pipelineSteps} includeCoverLetter={resume.create_cover_letter} />
        </div>
      )}

      <div className="flex flex-1 flex-col overflow-y-auto xl:flex-row xl:overflow-hidden">
        {showChat && (
          <ChatPane
            resume={resume}
            messages={messages}
            atsScore={atsScore}
            coverLetter={coverLetter}
            chatInput={chatInput}
            sending={sending}
            pendingChanges={pendingChanges}
            onChatInputChange={setChatInput}
            onSendChat={sendChat}
            onHandleChange={handleChange}
            onHandleBatchChanges={handleBatchChanges}
            onExportCoverLetterPdf={exportCoverLetterPdf}
          />
        )}

        <div className="flex min-h-[520px] min-w-0 flex-1 flex-col overflow-hidden bg-card p-4 xl:min-h-0">
          <div className="mb-2 rounded-lg border border-primary/30 bg-primary/10 px-3 py-2 text-xs text-primary">
            LaTeX compiles to PDF via Tectonic — preview reflects the exact exported document.
          </div>
          <div className="mb-3 flex items-center justify-between gap-2">
            <p className="text-xs font-medium uppercase tracking-widest text-primary">
              {showLatex ? "LaTeX · PDF Preview" : "PDF Preview"}
            </p>
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
          <div className={cn("grid min-h-0 flex-1 gap-3", showLatex ? "grid-cols-1 xl:grid-cols-2" : "grid-cols-1")}>
            {showLatex && (
              <div className="h-full min-h-0 overflow-hidden rounded-lg border border-border">
                <LatexEditor value={latex} onChange={setLatex} className="h-full text-xs" />
              </div>
            )}
            <PdfPreviewPane pdfUrl={pdfUrl} loading={pdfLoading} error={pdfError} />
          </div>
        </div>

        {showDetails && (
          <div className="min-h-[420px] overflow-y-auto border-t border-border p-4 xl:h-full xl:w-[380px] xl:min-h-0 xl:shrink-0 xl:border-l xl:border-t-0">
            <StructuredProfileEditor content={content} onChange={setContent} />
          </div>
        )}
      </div>
    </div>
  );
}
