"use client";

import { useEffect, useRef, useState } from "react";
import { AlertTriangle, CheckCircle2, ExternalLink, Save, Upload } from "lucide-react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { UserProfile } from "@/types";
import type { ResumeContent as RC } from "@/types/resume";
import { emptyResumeContent } from "@/types/resume";
import { PageHeader } from "@/components/ui/PageHeader";
import { StructuredProfileEditor } from "@/components/resume/StructuredEditor";
import { PdfPreviewPane } from "@/components/resume/PdfPreviewPane";
import { cn } from "@/lib/utils";

export default function ProfilePage() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [content, setContent] = useState<RC>(emptyResumeContent());
  const [loaded, setLoaded] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadConfidence, setUploadConfidence] = useState<number | null>(null);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [pdfError, setPdfError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

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

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setUploadError(null);
    setUploadConfidence(null);
    try {
      const result = await api.uploadResumePdf(file);
      setContent(result.content);
      setUploadConfidence(result.confidence);
      await refreshPdf();
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : "Upload failed — try a different PDF.");
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  return (
    <div>
      <PageHeader
        title="Your Profile"
        description="Your experience, skills, and education — the AI tailors every resume from this."
      />

      {/* PDF import shortcut — always visible */}
      <div className={cn("mb-6 rounded-xl border p-4 transition-all", isEmpty ? "border-primary/30 bg-primary/5" : "border-border bg-card/40")}>
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex-1 min-w-0">
            <p className={cn("text-sm font-medium", isEmpty ? "text-foreground" : "text-muted-foreground")}>
              {isEmpty ? "Quick start: import your existing resume" : "Import from resume PDF"}
            </p>
            <p className="mt-0.5 text-xs text-muted-foreground">
              Drag in a PDF and we&apos;ll auto-fill every section below using AI.
            </p>
          </div>
          <div className="flex items-center gap-3">
            {uploadConfidence !== null && (
              <span className={cn("text-xs font-medium", uploadConfidence >= 0.7 ? "text-green-400" : "text-amber-400")}>
                <CheckCircle2 className="inline h-3.5 w-3.5 mr-1" />
                {Math.round(uploadConfidence * 100)}% parsed — review below
              </span>
            )}
            <button
              type="button"
              onClick={() => fileRef.current?.click()}
              disabled={uploading}
              className={cn("btn-primary shrink-0", isEmpty && "shadow-[0_0_18px_hsl(var(--primary)/0.25)]")}
            >
              <Upload className="h-4 w-4" />
              {uploading ? "Parsing..." : "Upload PDF"}
            </button>
            <input ref={fileRef} type="file" accept="application/pdf,.pdf" className="hidden" onChange={handleUpload} />
          </div>
        </div>
        {uploadError && (
          <p className="mt-2 flex items-center gap-1.5 text-xs text-destructive">
            <AlertTriangle className="h-3.5 w-3.5 shrink-0" /> {uploadError}
          </p>
        )}
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
            <button onClick={handleSave} disabled={saving} className="btn-primary">
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
            Updates when you save. Compiled with your Jake&apos;s Resume template.
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
