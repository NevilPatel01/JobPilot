"use client";

import { useEffect, useRef, useState } from "react";
import { AlertTriangle, CheckCircle2, ExternalLink, FileText, Loader2, Save, Upload, XCircle } from "lucide-react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { UserProfile } from "@/types";
import type { ResumeContent as RC } from "@/types/resume";
import { emptyResumeContent } from "@/types/resume";
import { PageHeader } from "@/components/ui/PageHeader";
import { StructuredProfileEditor } from "@/components/resume/StructuredEditor";
import { PdfPreviewPane } from "@/components/resume/PdfPreviewPane";
import { cn } from "@/lib/utils";

// ─── PDF parsing overlay ──────────────────────────────────────────────────────

const PARSE_STAGES = [
  { label: "Reading your PDF",              detail: "Checking file and extracting raw text" },
  { label: "Extracting text and layout",    detail: "Detecting columns, headers, and formatting" },
  { label: "Identifying sections and dates", detail: "Finding experience, education, skills…" },
  { label: "Building your profile with AI", detail: "Structuring data into your profile" },
] as const;

type ParseOverlayProps = {
  stage: number;        // 0-3 active, 4 done, -1 error
  confidence: number | null;
  fileName: string;
  error: string | null;
  onDismiss: () => void;
};

function PdfParseOverlay({ stage, confidence, fileName, error, onDismiss }: ParseOverlayProps) {
  const isDone  = stage === 4;
  const isError = stage === -1;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
      <div className="mx-4 w-full max-w-md rounded-2xl border border-border bg-card shadow-2xl">
        {/* Header */}
        <div className="flex items-center gap-3 border-b border-border px-6 py-4">
          <div className={cn(
            "flex h-9 w-9 shrink-0 items-center justify-center rounded-lg",
            isError ? "bg-destructive/10" : "bg-primary/10"
          )}>
            <FileText className={cn("h-4 w-4", isError ? "text-destructive" : "text-primary")} />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-foreground">
              {isDone ? "Profile imported" : isError ? "Import failed" : "Parsing resume…"}
            </p>
            <p className="truncate text-xs text-muted-foreground">{fileName}</p>
          </div>
        </div>

        {/* Stages */}
        <div className="space-y-1 px-6 py-5">
          {PARSE_STAGES.map((s, i) => {
            const done    = !isError && (isDone || i < stage);
            const active  = !isError && !isDone && i === stage;
            const pending = !done && !active;

            return (
              <div
                key={i}
                className={cn(
                  "flex items-start gap-3 rounded-lg px-3 py-2.5 transition-colors duration-300",
                  active && "bg-primary/8"
                )}
              >
                <div className="mt-0.5 shrink-0">
                  {done ? (
                    <CheckCircle2 className="h-4 w-4 text-primary" />
                  ) : active ? (
                    <Loader2 className="h-4 w-4 animate-spin text-primary" />
                  ) : isError && i === stage ? (
                    <XCircle className="h-4 w-4 text-destructive" />
                  ) : (
                    <div className={cn("h-4 w-4 rounded-full border-2", pending ? "border-border" : "border-primary")} />
                  )}
                </div>
                <div>
                  <p className={cn(
                    "text-sm font-medium leading-tight",
                    done ? "text-foreground" : active ? "text-foreground" : "text-muted-foreground/50"
                  )}>
                    {s.label}
                  </p>
                  {active && (
                    <p className="mt-0.5 text-xs text-muted-foreground">{s.detail}</p>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div className="border-t border-border px-6 py-4">
          {isError ? (
            <div className="space-y-3">
              <p className="flex items-start gap-2 text-xs text-destructive">
                <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                {error ?? "Upload failed — try a different PDF."}
              </p>
              <button onClick={onDismiss} className="btn-secondary w-full">Dismiss</button>
            </div>
          ) : isDone ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">Parse confidence</span>
                <span className={cn(
                  "text-sm font-semibold",
                  (confidence ?? 0) >= 0.7 ? "text-green-400" : "text-amber-400"
                )}>
                  {confidence !== null ? `${Math.round(confidence * 100)}%` : "—"}
                </span>
              </div>
              {confidence !== null && (
                <div className="h-1.5 overflow-hidden rounded-full bg-muted">
                  <div
                    className={cn("h-full rounded-full transition-all duration-700", (confidence ?? 0) >= 0.7 ? "bg-green-500" : "bg-amber-500")}
                    style={{ width: `${Math.round((confidence ?? 0) * 100)}%` }}
                  />
                </div>
              )}
              <p className="text-xs text-muted-foreground">
                {(confidence ?? 0) >= 0.7
                  ? "Sections look complete — review and save."
                  : "Some sections may need manual review before saving."}
              </p>
              <button onClick={onDismiss} className="btn-primary w-full">
                <CheckCircle2 className="h-4 w-4" /> Review & Save Profile
              </button>
            </div>
          ) : (
            <p className="text-center text-xs text-muted-foreground">
              Do not close this page while parsing…
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Profile page ─────────────────────────────────────────────────────────────

export default function ProfilePage() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [content, setContent] = useState<RC>(emptyResumeContent());
  const [loaded, setLoaded] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  // Parse overlay state
  const [parseStage, setParseStage]       = useState<number | null>(null); // null = hidden
  const [parseFileName, setParseFileName] = useState("");
  const [parseError, setParseError]       = useState<string | null>(null);
  const [parseConfidence, setParseConfidence] = useState<number | null>(null);

  const [pdfUrl, setPdfUrl]       = useState<string | null>(null);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [pdfError, setPdfError]   = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const stageTimers = useRef<ReturnType<typeof setTimeout>[]>([]);

  const isEmpty = loaded && !content.contact.full_name.trim();

  const refreshPdf = async () => {
    setPdfLoading(true);
    setPdfError(null);
    try {
      const blob = await api.getProfilePreviewPdf();
      setPdfUrl((prev) => {
        if (prev) URL.revokeObjectURL(prev);
        return URL.createObjectURL(blob);
      });
    } catch (e: unknown) {
      setPdfError(e instanceof Error ? e.message : "PDF preview failed");
    } finally {
      setPdfLoading(false);
    }
  };

  useEffect(() => {
    api.getProfile().then((p) => setProfile(p)).catch(console.error);
    api.getStructuredProfile()
      .then((p) => { setContent(p.content); setLoaded(true); })
      .catch(() => setLoaded(true));
  }, []);

  useEffect(() => {
    if (loaded) refreshPdf().catch(console.error);
    return () => { if (pdfUrl) URL.revokeObjectURL(pdfUrl); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loaded]);

  const clearStageTimers = () => {
    stageTimers.current.forEach(clearTimeout);
    stageTimers.current = [];
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (fileRef.current) fileRef.current.value = "";

    setParseFileName(file.name);
    setParseError(null);
    setParseConfidence(null);
    setParseStage(0);

    // Advance through stages on a timer — the last stage waits for the real API
    clearStageTimers();
    const delays = [900, 2200, 3800]; // ms to advance to stages 1, 2, 3
    delays.forEach((delay, i) => {
      stageTimers.current.push(setTimeout(() => setParseStage(i + 1), delay));
    });

    try {
      const result = await api.uploadResumePdf(file);
      clearStageTimers();
      setContent(result.content);
      setParseConfidence(result.confidence);
      setParseStage(4); // done
      refreshPdf().catch(console.error);
    } catch (err) {
      clearStageTimers();
      setParseError(err instanceof Error ? err.message : "Upload failed — try a different PDF.");
      setParseStage(-1); // error
    }
  };

  const dismissOverlay = () => {
    clearStageTimers();
    setParseStage(null);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.updateStructuredProfile(content);
      const p = await api.getProfile();
      setProfile(p);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
      await refreshPdf();
    } catch (e) {
      console.error(e);
    } finally {
      setSaving(false);
    }
  };

  const showingOverlay = parseStage !== null;

  return (
    <div>
      {showingOverlay && (
        <PdfParseOverlay
          stage={parseStage}
          confidence={parseConfidence}
          fileName={parseFileName}
          error={parseError}
          onDismiss={dismissOverlay}
        />
      )}

      <PageHeader
        title="Your Profile"
        description="Your experience, skills, and education — the AI tailors every resume from this."
      />

      {/* PDF import shortcut */}
      <div className={cn("mb-6 rounded-xl border p-4 transition-all", isEmpty ? "border-primary/30 bg-primary/5" : "border-border bg-card/40")}>
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex-1 min-w-0">
            <p className={cn("text-sm font-medium", isEmpty ? "text-foreground" : "text-muted-foreground")}>
              {isEmpty ? "Quick start: import your existing resume" : "Import from resume PDF"}
            </p>
            <p className="mt-0.5 text-xs text-muted-foreground">
              Upload a PDF and we&apos;ll auto-fill every section below using AI.
            </p>
          </div>
          <button
            type="button"
            onClick={() => fileRef.current?.click()}
            disabled={showingOverlay}
            className={cn("btn-primary shrink-0", isEmpty && "shadow-[0_0_18px_hsl(var(--primary)/0.25)]")}
          >
            <Upload className="h-4 w-4" />
            Upload PDF
          </button>
          <input ref={fileRef} type="file" accept="application/pdf,.pdf" className="hidden" onChange={handleUpload} />
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div>
          {isEmpty && (
            <div className="mb-4 rounded-lg border border-border bg-background/40 px-4 py-3 text-sm text-muted-foreground">
              Fill in at least your <strong className="text-foreground">name</strong> and one{" "}
              <strong className="text-foreground">experience entry</strong> so the AI has something to tailor.
              Or upload a PDF above to auto-fill everything.
            </div>
          )}

          <StructuredProfileEditor content={content} onChange={setContent} />

          <div className="mt-4 flex items-center gap-3">
            <button onClick={handleSave} disabled={saving || showingOverlay} className="btn-primary">
              <Save className="h-4 w-4" />
              {saving ? "Saving..." : saved ? "Saved" : "Save Profile"}
            </button>
            {saved && (
              <Link href="/resumes/new" className="inline-flex items-center gap-1.5 text-sm text-primary hover:underline">
                Create a resume now <ExternalLink className="h-3.5 w-3.5" />
              </Link>
            )}
          </div>
        </div>

        <div className="glass-panel flex flex-col p-4">
          <p className="text-xs font-medium uppercase tracking-widest text-primary">Live PDF preview</p>
          <p className="mt-1 text-xs text-muted-foreground">
            Updates when you save. Compiled with your resume template.
          </p>
          <div className="mt-3 flex-1 min-h-[600px]">
            <PdfPreviewPane pdfUrl={pdfUrl} loading={pdfLoading} error={pdfError} />
          </div>
          {!pdfError && !pdfLoading && pdfUrl && (
            <button onClick={refreshPdf} className="btn-secondary mt-2 text-xs">Refresh preview</button>
          )}
        </div>
      </div>

      {profile && (
        <p className="mt-6 text-xs text-muted-foreground">{profile.name} · {profile.email}</p>
      )}
    </div>
  );
}
