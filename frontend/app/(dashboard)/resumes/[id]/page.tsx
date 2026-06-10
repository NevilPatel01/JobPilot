"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Download, FileText, MessageSquare, Check, X } from "lucide-react";
import { api } from "@/lib/api";
import type { ChatMessage, PendingChange, ResumeContent, ResumeDocument } from "@/types/resume";
import { StructuredProfileEditor } from "@/components/resume/StructuredEditor";
import { ResumePreviewFrame } from "@/components/resume/ResumePreviewFrame";
import { renderResumeHtmlClient } from "@/lib/resumePreview";
import { cn } from "@/lib/utils";
import { io, Socket } from "socket.io-client";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function ResumeEditorPage() {
  const { id } = useParams<{ id: string }>();
  const [resume, setResume] = useState<ResumeDocument | null>(null);
  const [content, setContent] = useState<ResumeContent | null>(null);
  const [previewHtml, setPreviewHtml] = useState("");
  const [showLatex, setShowLatex] = useState(false);
  const [latex, setLatex] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [sending, setSending] = useState(false);
  const [saved, setSaved] = useState(true);
  const saveTimer = useRef<ReturnType<typeof setTimeout>>();
  const socketRef = useRef<Socket | null>(null);

  const pendingChanges = messages.flatMap((m) => m.pending_changes.filter((c) => c.status === "pending"));

  const load = useCallback(async () => {
    const r = await api.getResume(id);
    setResume(r);
    setContent(r.content_json);
    setLatex(r.latex_source || "");
    const html = await api.getResumePreviewHtml(id).catch(() => renderResumeHtmlClient(r.content_json));
    setPreviewHtml(html);
    const msgs = await api.getResumeMessages(id);
    setMessages(msgs);
  }, [id]);

  useEffect(() => {
    load().catch(console.error);
  }, [load]);

  useEffect(() => {
    const socket = io(API_URL, { path: "/socket.io", transports: ["websocket", "polling"] });
    socketRef.current = socket;
    socket.on("connect", () => socket.emit("join_room", { room: `resume:${id}` }));
    socket.on("agent_complete", () => load());
    socket.on("agent_step", () => load());
    return () => { socket.disconnect(); };
  }, [id, load]);

  useEffect(() => {
    if (!content) return;
    setPreviewHtml(renderResumeHtmlClient(content));
    setSaved(false);
    clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(async () => {
      try {
        await api.updateResume(id, { content_json: content });
        setSaved(true);
      } catch (e) {
        console.error(e);
      }
    }, 500);
    return () => clearTimeout(saveTimer.current);
  }, [content, id]);

  const sendChat = async () => {
    if (!chatInput.trim() || pendingChanges.length > 0) return;
    setSending(true);
    try {
      const msg = await api.sendResumeChat(id, chatInput);
      setMessages((prev) => [...prev, msg]);
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

  const exportPdf = async () => {
    try {
      const blob = await api.downloadResumePdf(id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${resume?.title || "resume"}.pdf`;
      a.click();
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "PDF export failed");
    }
  };

  if (!resume || !content) {
    return <div className="flex h-full items-center justify-center text-zinc-500">Loading editor...</div>;
  }

  const insights = (resume.insights_json || {}) as {
    tailoring_insights?: string[];
    jd_analysis?: Record<string, unknown>;
    company_research?: { summary?: string };
  };

  return (
    <div className="flex h-full flex-col bg-zinc-950">
      <header className="flex items-center justify-between border-b border-zinc-800 px-4 py-2">
        <div className="flex items-center gap-3">
          <Link href="/resumes" className="text-xs text-zinc-500 hover:text-white">← Resumes</Link>
          <h1 className="truncate text-sm font-medium text-white">{resume.title}</h1>
          <span className={cn("text-xs", saved ? "text-emerald-400" : "text-amber-400")}>{saved ? "Saved" : "Saving..."}</span>
        </div>
        <div className="flex items-center gap-2">
          <Link href={`/resumes/${id}/review`} className="btn-secondary text-xs">ATS Review</Link>
          <button
            onClick={async () => {
              const app = await api.createApplication({
                job_title: resume.title,
                company: resume.company_name || "Unknown",
                job_url: resume.company_url || undefined,
                status: "to_apply",
                notes: `Resume: ${resume.id}`,
              });
              await api.updateResume(id, { application_id: app.id });
              window.location.href = "/tracker";
            }}
            className="btn-secondary text-xs"
          >
            Apply with Resume
          </button>
          <button onClick={() => setShowLatex(!showLatex)} className="btn-secondary text-xs">
            <FileText className="h-3 w-3" /> {showLatex ? "Preview" : "LaTeX"}
          </button>
          <button onClick={exportPdf} className="btn-primary text-xs">
            <Download className="h-3 w-3" /> PDF
          </button>
        </div>
      </header>

      <div className="grid flex-1 grid-cols-[320px_1fr_360px] overflow-hidden">
        {/* Chat pane */}
        <div className="flex flex-col border-r border-zinc-800">
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            <div className="rounded-lg bg-indigo-600/10 p-3 text-sm text-zinc-300">
              <MessageSquare className="mb-2 h-4 w-4 text-indigo-400" />
              I&apos;ve tailored your resume for <strong>{resume.title}</strong>. Ask me to edit bullets, sections, or tone.
            </div>

            {insights.tailoring_insights && insights.tailoring_insights.length > 0 && (
              <details className="rounded-lg border border-zinc-800 p-2 text-xs text-zinc-400">
                <summary className="cursor-pointer font-medium text-zinc-300">Resume tailoring insights</summary>
                <ul className="mt-2 list-disc pl-4">{insights.tailoring_insights.map((i, idx) => <li key={idx}>{i}</li>)}</ul>
              </details>
            )}
            {insights.jd_analysis && (
              <details className="rounded-lg border border-zinc-800 p-2 text-xs text-zinc-400">
                <summary className="cursor-pointer font-medium text-zinc-300">JD analysis</summary>
                <pre className="mt-2 whitespace-pre-wrap">{JSON.stringify(insights.jd_analysis, null, 2)}</pre>
              </details>
            )}
            {insights.company_research?.summary && (
              <details className="rounded-lg border border-zinc-800 p-2 text-xs text-zinc-400">
                <summary className="cursor-pointer font-medium text-zinc-300">Company research</summary>
                <p className="mt-2">{insights.company_research.summary}</p>
              </details>
            )}

            {messages.map((m) => (
              <div key={m.id} className={cn("rounded-lg p-3 text-sm", m.role === "assistant" ? "bg-zinc-900 text-zinc-300" : "bg-indigo-600/10 text-white")}>
                {m.content}
                {m.pending_changes.filter((c) => c.status === "pending").map((ch) => (
                  <div key={ch.id} className="mt-3 overflow-hidden rounded border border-zinc-700 font-mono text-xs">
                    <div className="bg-red-950/50 p-2 text-red-300 line-through">{ch.old_value}</div>
                    <div className="bg-emerald-950/50 p-2 text-emerald-300">{ch.new_value}</div>
                    <div className="flex gap-2 border-t border-zinc-700 p-2">
                      <button onClick={() => handleChange(ch, "reject")} className="btn-secondary flex-1 text-xs"><X className="h-3 w-3" /> Reject</button>
                      <button onClick={() => handleChange(ch, "accept")} className="btn-primary flex-1 text-xs"><Check className="h-3 w-3" /> Accept</button>
                    </div>
                  </div>
                ))}
              </div>
            ))}
          </div>
          <div className="border-t border-zinc-800 p-3">
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

        {/* Preview pane */}
        <div className="overflow-hidden bg-zinc-900 p-4">
          {showLatex ? (
            <textarea
              className="h-full w-full rounded-lg border border-zinc-800 bg-zinc-950 p-4 font-mono text-xs text-zinc-300"
              value={latex}
              onChange={(e) => setLatex(e.target.value)}
              onBlur={() => api.updateResume(id, { latex_source: latex })}
            />
          ) : (
            <ResumePreviewFrame html={previewHtml} className="h-full w-full rounded-lg border border-zinc-800 bg-white" />
          )}
        </div>

        {/* Structured editor */}
        <div className="overflow-y-auto border-l border-zinc-800 p-4">
          <StructuredProfileEditor content={content} onChange={setContent} />
        </div>
      </div>
    </div>
  );
}
