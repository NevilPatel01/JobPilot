"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  Check,
  Download,
  ExternalLink,
  Loader2,
  MessageSquare,
  RefreshCw,
  X,
} from "lucide-react";
import { api } from "@/lib/api";
import type {
  ChatMessage,
  CoverLetterContent,
  CoverLetterDocument,
  PendingChange,
  ResumeDocument,
} from "@/types/resume";
import { parseCoverLetterContent } from "@/types/resume";
import { CoverLetterStructuredEditor } from "@/components/cover-letter/CoverLetterStructuredEditor";
import { ResumePreviewFrame } from "@/components/resume/ResumePreviewFrame";
import { cn } from "@/lib/utils";

export default function CoverLetterEditorPage() {
  const { id } = useParams<{ id: string }>();
  const [letter, setLetter] = useState<CoverLetterDocument | null>(null);
  const [content, setContent] = useState<CoverLetterContent | null>(null);
  const [linkedResume, setLinkedResume] = useState<ResumeDocument | null>(null);
  const [previewHtml, setPreviewHtml] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [sending, setSending] = useState(false);
  const [saved, setSaved] = useState(true);
  const [regenerating, setRegenerating] = useState(false);
  const saveTimer = useRef<ReturnType<typeof setTimeout>>();

  const pendingChanges = messages.flatMap((m) => m.pending_changes.filter((c) => c.status === "pending"));

  const load = useCallback(async () => {
    const l = await api.getCoverLetter(id);
    setLetter(l);
    setContent(parseCoverLetterContent(l.content_json));
    const msgs = await api.getCoverLetterMessages(id);
    setMessages(msgs);
    if (l.resume_id) {
      const resume = await api.getResume(l.resume_id).catch(() => null);
      setLinkedResume(resume);
    }
    const html = await api.getCoverLetterPreviewHtml(id).catch(() => "");
    setPreviewHtml(html);
  }, [id]);

  useEffect(() => {
    load().catch(console.error);
  }, [load]);

  useEffect(() => {
    if (!letter || !content) return;
    setSaved(false);
    clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(async () => {
      try {
        const updated = await api.updateCoverLetter(id, {
          content_json: content as unknown as Record<string, unknown>,
          hiring_manager_name: letter.hiring_manager_name || undefined,
          street_address: letter.street_address || undefined,
          city: letter.city || undefined,
          state_province: letter.state_province || undefined,
          postal_code: letter.postal_code || undefined,
          letter_date: letter.letter_date || undefined,
          additional_context: letter.additional_context || undefined,
        });
        setLetter(updated);
        setSaved(true);
        const html = await api.getCoverLetterPreviewHtml(id).catch(() => "");
        setPreviewHtml(html);
      } catch (e) {
        console.error(e);
      }
    }, 600);
    return () => clearTimeout(saveTimer.current);
  }, [content, letter, id]);

  const sendChat = async () => {
    if (!chatInput.trim() || pendingChanges.length > 0) return;
    setSending(true);
    try {
      const exchange = await api.sendCoverLetterChat(id, chatInput);
      setMessages((prev) => [...prev, exchange.user_message, exchange.assistant_message]);
      setChatInput("");
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Chat failed");
    } finally {
      setSending(false);
    }
  };

  const handleChange = async (change: PendingChange, action: "accept" | "reject") => {
    const result = await api.handleCoverLetterChange(id, change.id, action);
    if (action === "accept") setContent(parseCoverLetterContent(result.content_json));
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

  const exportPdf = async () => {
    try {
      const blob = await api.downloadCoverLetterPdf(id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${letter?.title || "cover-letter"}.pdf`;
      a.click();
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "PDF export failed — is Tectonic installed?");
    }
  };

  const regenerate = async () => {
    setRegenerating(true);
    try {
      await api.regenerateCoverLetter(id);
      const poll = setInterval(async () => {
        const l = await api.getCoverLetter(id);
        if (l.status !== "processing") {
          clearInterval(poll);
          setRegenerating(false);
          load();
        }
      }, 2000);
    } catch (e: unknown) {
      setRegenerating(false);
      alert(e instanceof Error ? e.message : "Regeneration failed");
    }
  };

  const onMetaChange = (updates: Partial<CoverLetterDocument>) => {
    setLetter((prev) => (prev ? { ...prev, ...updates } : prev));
  };

  if (!letter || !content) {
    return <div className="flex h-full items-center justify-center text-muted-foreground">Loading editor...</div>;
  }

  const jdAnalysis = (linkedResume?.insights_json?.jd_analysis || {}) as Record<string, unknown>;
  const companyResearch = (linkedResume?.insights_json?.company_research || {}) as { summary?: string };

  return (
    <div className="flex h-full flex-col bg-background">
      <header className="flex items-center justify-between border-b border-border px-4 py-2">
        <div className="flex items-center gap-3">
          <Link href="/cover-letters" className="text-xs text-muted-foreground hover:text-foreground">
            ← Cover Letters
          </Link>
          <h1 className="truncate text-sm font-medium text-foreground">{letter.title}</h1>
          <span className={cn("text-xs", saved ? "text-emerald-400" : "text-amber-400")}>
            {saved ? "Saved" : "Saving..."}
          </span>
          {letter.status === "processing" && (
            <span className="flex items-center gap-1 text-xs text-amber-400">
              <Loader2 className="h-3 w-3 animate-spin" /> Generating
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {linkedResume && (
            <Link href={`/resumes/${linkedResume.id}`} className="btn-secondary text-xs">
              <ExternalLink className="h-3 w-3" /> Resume
            </Link>
          )}
          <button
            type="button"
            disabled={regenerating || letter.status === "processing"}
            onClick={regenerate}
            className="btn-secondary text-xs"
          >
            <RefreshCw className={cn("h-3 w-3", regenerating && "animate-spin")} /> Regenerate
          </button>
          <button onClick={exportPdf} className="btn-primary text-xs">
            <Download className="h-3 w-3" /> PDF
          </button>
        </div>
      </header>

      {letter.status === "failed" && (
        <div className="border-b border-red-500/30 bg-red-950/30 px-4 py-2 text-sm text-red-300">
          Generation failed. Try Regenerate or edit manually.
        </div>
      )}

      <div className="grid flex-1 grid-cols-[300px_1fr_340px] overflow-hidden">
        {/* Chat */}
        <div className="flex flex-col border-r border-border">
          <div className="flex-1 space-y-4 overflow-y-auto p-4">
            <div className="rounded-lg bg-primary/10 p-3 text-sm text-foreground">
              <MessageSquare className="mb-2 h-4 w-4 text-primary" />
              Ask me to adjust tone, shorten paragraphs, or highlight specific achievements.
            </div>
            {messages.map((m) => (
              <div
                key={m.id}
                className={cn(
                  "rounded-lg p-3 text-sm",
                  m.role === "assistant" ? "bg-card text-foreground" : "bg-primary/10 text-foreground"
                )}
              >
                {m.content}
                {m.pending_changes
                  .filter((c) => c.status === "pending")
                  .map((ch) => (
                    <div key={ch.id} className="mt-3 overflow-hidden rounded border border-border font-mono text-xs">
                      <div className="bg-red-950/50 p-2 text-red-300 line-through">{ch.old_value}</div>
                      <div className="bg-emerald-950/50 p-2 text-emerald-300">{ch.new_value}</div>
                      <div className="flex gap-2 border-t border-border p-2">
                        <button onClick={() => handleChange(ch, "reject")} className="btn-secondary flex-1 text-xs">
                          <X className="h-3 w-3" /> Reject
                        </button>
                        <button onClick={() => handleChange(ch, "accept")} className="btn-primary flex-1 text-xs">
                          <Check className="h-3 w-3" /> Accept
                        </button>
                      </div>
                    </div>
                  ))}
              </div>
            ))}
          </div>
          <div className="border-t border-border p-3">
            <textarea
              className="input-field min-h-[60px] text-sm"
              placeholder={
                pendingChanges.length ? "Approve or reject pending changes first." : "Make it more concise..."
              }
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              disabled={pendingChanges.length > 0 || sending}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && (e.preventDefault(), sendChat())}
            />
            <button
              onClick={sendChat}
              disabled={sending || pendingChanges.length > 0}
              className="btn-primary mt-2 w-full text-xs"
            >
              {sending ? "Thinking..." : "Send"}
            </button>
          </div>
        </div>

        {/* Preview */}
        <div className="overflow-hidden bg-card p-4">
          <ResumePreviewFrame html={previewHtml} className="h-full w-full rounded-lg border border-border bg-white" />
        </div>

        {/* Editor + JD sidebar */}
        <div className="flex flex-col overflow-hidden border-l border-border">
          <div className="flex-1 overflow-y-auto p-4">
            <CoverLetterStructuredEditor
              letter={letter}
              content={content}
              onContentChange={setContent}
              onMetaChange={onMetaChange}
            />
          </div>
          {linkedResume?.job_description && (
            <div className="max-h-[240px] overflow-y-auto border-t border-border p-4">
              <h3 className="text-xs font-medium uppercase tracking-widest text-muted-foreground">Job Description</h3>
              <p className="mt-2 whitespace-pre-wrap text-xs text-muted-foreground">{linkedResume.job_description}</p>
              {companyResearch.summary && (
                <p className="mt-3 text-xs text-muted-foreground">
                  <span className="font-medium text-muted-foreground">Company: </span>
                  {companyResearch.summary}
                </p>
              )}
              {Object.keys(jdAnalysis).length > 0 && (
                <details className="mt-2 text-xs text-muted-foreground">
                  <summary className="cursor-pointer text-muted-foreground">JD analysis</summary>
                  <pre className="mt-1 whitespace-pre-wrap">{JSON.stringify(jdAnalysis, null, 2)}</pre>
                </details>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
