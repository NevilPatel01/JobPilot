"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  ArrowUpRight,
  FileUp,
  Loader2,
  Save,
  Trash2,
} from "lucide-react";
import { api } from "@/lib/api";
import type { Application } from "@/types";
import { KANBAN_COLUMNS } from "@/types";
import type { ResumeDocument } from "@/types/resume";
import { PdfPreviewPane } from "@/components/resume/PdfPreviewPane";
import { PageHeader } from "@/components/ui/PageHeader";

function formatDate(value: string | null | undefined) {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

export default function ApplicationDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [app, setApp] = useState<Application | null>(null);
  const [resumes, setResumes] = useState<ResumeDocument[]>([]);
  const [notes, setNotes] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [status, setStatus] = useState("to_apply");
  const [resumeId, setResumeId] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [pdfError, setPdfError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  const loadPdf = useCallback(async (application: Application) => {
    if (!application.resume_id && !application.has_uploaded_resume) {
      setPdfUrl((prev) => {
        if (prev) URL.revokeObjectURL(prev);
        return null;
      });
      setPdfError(null);
      return;
    }
    setPdfLoading(true);
    setPdfError(null);
    try {
      const blob = await api.downloadApplicationResumePdf(application.id);
      setPdfUrl((prev) => {
        if (prev) URL.revokeObjectURL(prev);
        return URL.createObjectURL(blob);
      });
    } catch (e) {
      setPdfError(e instanceof Error ? e.message : "Could not load resume PDF");
      setPdfUrl((prev) => {
        if (prev) URL.revokeObjectURL(prev);
        return null;
      });
    } finally {
      setPdfLoading(false);
    }
  }, []);

  const load = useCallback(async () => {
    const [application, resumeList] = await Promise.all([
      api.getApplication(id),
      api.getResumes().catch(() => ({ resumes: [] as ResumeDocument[], total: 0 })),
    ]);
    setApp(application);
    setNotes(application.notes || "");
    setJobDescription(application.job_description || "");
    setStatus(application.status);
    setResumeId(application.resume_id || "");
    setResumes(resumeList.resumes);
    await loadPdf(application);
  }, [id, loadPdf]);

  useEffect(() => {
    load().catch((e) => {
      console.error(e);
      alert(e instanceof Error ? e.message : "Application not found");
      router.push("/tracker");
    });
  }, [load, router]);

  useEffect(() => {
    return () => {
      if (pdfUrl) URL.revokeObjectURL(pdfUrl);
    };
  }, [pdfUrl]);

  const save = async () => {
    if (!app) return;
    setSaving(true);
    try {
      const updated = await api.updateApplication(app.id, {
        notes: notes || null,
        job_description: jobDescription || null,
        status,
        resume_id: resumeId || null,
      } as Partial<Application>);
      setApp(updated);
      setSaved(true);
      window.setTimeout(() => setSaved(false), 2000);
      await loadPdf(updated);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  const onUpload = async (file: File | null) => {
    if (!app || !file) return;
    setUploading(true);
    try {
      const updated = await api.uploadApplicationResume(app.id, file);
      setApp(updated);
      await loadPdf(updated);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const removeUpload = async () => {
    if (!app) return;
    const updated = await api.deleteApplicationUploadedResume(app.id);
    setApp(updated);
    await loadPdf(updated);
  };

  const remove = async () => {
    if (!app || !confirm("Delete this application?")) return;
    await api.deleteApplication(app.id);
    router.push("/tracker");
  };

  if (!app) {
    return (
      <div className="flex h-64 items-center justify-center text-muted-foreground">
        <Loader2 className="h-5 w-5 animate-spin" />
      </div>
    );
  }

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <Link
          href="/tracker"
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground transition hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" /> Back to Tracker
        </Link>
        <div className="flex items-center gap-2">
          <button onClick={save} disabled={saving} className="btn-primary">
            <Save className="h-4 w-4" /> {saving ? "Saving…" : saved ? "Saved" : "Save"}
          </button>
          <button onClick={remove} className="btn-secondary text-red-400 hover:text-red-300">
            <Trash2 className="h-4 w-4" /> Delete
          </button>
        </div>
      </div>

      <PageHeader
        title={app.job_title || "Application"}
        description={`${app.company || "Unknown company"} · Saved ${formatDate(app.created_at)}${
          app.date_applied ? ` · Applied ${formatDate(app.date_applied)}` : ""
        }`}
      />

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(320px,420px)]">
        <div className="space-y-6">
          <div className="glass-panel space-y-4 p-5">
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="text-xs font-medium text-muted-foreground">
                Status
                <select
                  className="input-field mt-1.5"
                  value={status}
                  onChange={(e) => setStatus(e.target.value)}
                >
                  {KANBAN_COLUMNS.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.label}
                    </option>
                  ))}
                </select>
              </label>
              <div className="text-xs font-medium text-muted-foreground">
                Job listing
                {app.job_url ? (
                  <a
                    href={app.job_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-1.5 flex items-center gap-1 text-sm text-primary hover:underline"
                  >
                    Open original <ArrowUpRight className="h-3.5 w-3.5" />
                  </a>
                ) : (
                  <p className="mt-1.5 text-sm text-muted-foreground">No URL saved</p>
                )}
              </div>
              {app.salary_range && (
                <div className="text-xs font-medium text-muted-foreground sm:col-span-2">
                  Salary
                  <p className="mt-1.5 text-sm text-foreground">{app.salary_range}</p>
                </div>
              )}
            </div>

            <div>
              <label className="text-xs font-medium text-muted-foreground">Notes</label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={4}
                className="input-field mt-1.5"
                placeholder="Interview notes, contacts, follow-ups…"
              />
            </div>

            <div>
              <label className="text-xs font-medium text-muted-foreground">Job description</label>
              <textarea
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                rows={16}
                className="input-field mt-1.5 font-mono text-xs leading-relaxed"
                placeholder="Paste or edit the job description"
              />
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div className="glass-panel space-y-3 p-5">
            <h2 className="text-sm font-semibold text-foreground">Resume</h2>
            <label className="block text-xs font-medium text-muted-foreground">
              Link JobPilot resume
              <select
                className="input-field mt-1.5"
                value={resumeId}
                onChange={(e) => setResumeId(e.target.value)}
              >
                <option value="">None</option>
                {resumes.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.title}
                    {r.company_name ? ` — ${r.company_name}` : ""}
                  </option>
                ))}
              </select>
            </label>
            {app.resume_id && (
              <Link href={`/resumes/${app.resume_id}`} className="text-xs text-primary hover:underline">
                Open in resume editor
              </Link>
            )}

            <div>
              <p className="text-xs font-medium text-muted-foreground">Or upload PDF</p>
              <label className="mt-1.5 flex cursor-pointer items-center gap-2 rounded-lg border border-dashed border-border bg-background/50 px-3 py-3 text-sm text-muted-foreground transition hover:border-primary/40 hover:text-foreground">
                {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileUp className="h-4 w-4" />}
                <span className="truncate">
                  {app.uploaded_resume_filename || "Choose PDF…"}
                </span>
                <input
                  type="file"
                  accept="application/pdf,.pdf"
                  className="hidden"
                  onChange={(e) => onUpload(e.target.files?.[0] ?? null)}
                />
              </label>
              {app.has_uploaded_resume && (
                <button type="button" onClick={removeUpload} className="mt-1 text-xs text-muted-foreground hover:text-foreground">
                  Remove uploaded PDF
                </button>
              )}
            </div>
          </div>

          <div className="h-[min(70vh,720px)]">
            <PdfPreviewPane pdfUrl={pdfUrl} loading={pdfLoading} error={pdfError} className="h-full" />
          </div>
        </div>
      </div>
    </div>
  );
}
