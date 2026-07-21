"use client";

import { useEffect, useState } from "react";
import { X, Link2, Loader2, FileUp } from "lucide-react";
import type { Application } from "@/types";
import { api } from "@/lib/api";
import type { ResumeDocument } from "@/types/resume";

export type CreateApplicationPayload = Partial<Application> & {
  resumeFile?: File | null;
};

interface AddJobModalProps {
  open: boolean;
  onClose: () => void;
  defaultStatus: string;
  onCreate: (data: CreateApplicationPayload) => Promise<void>;
}

export function AddJobModal({ open, onClose, defaultStatus, onCreate }: AddJobModalProps) {
  const [form, setForm] = useState({
    job_title: "",
    company: "",
    job_url: "",
    salary_range: "",
    notes: "",
    job_description: "",
    resume_id: "",
    status: defaultStatus,
  });
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [resumes, setResumes] = useState<ResumeDocument[]>([]);
  const [importUrl, setImportUrl] = useState("");
  const [importing, setImporting] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!open) return;
    setForm((f) => ({ ...f, status: defaultStatus }));
    api.getResumes().then((r) => setResumes(r.resumes)).catch(console.error);
  }, [open, defaultStatus]);

  if (!open) return null;

  const handleImport = async () => {
    if (!importUrl) return;
    setImporting(true);
    try {
      const job = await api.importJobUrl(importUrl);
      setForm((f) => ({
        ...f,
        job_title: job.title,
        company: job.company,
        job_url: job.url,
        job_description: job.description || f.job_description,
        salary_range:
          job.salary_min || job.salary_max
            ? `$${job.salary_min || "?"}-$${job.salary_max || "?"}`
            : f.salary_range,
      }));
    } catch (e) {
      alert(e instanceof Error ? e.message : "Import failed");
    } finally {
      setImporting(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.job_title || !form.company) return;
    setSaving(true);
    try {
      await onCreate({
        job_title: form.job_title,
        company: form.company,
        job_url: form.job_url || undefined,
        salary_range: form.salary_range || undefined,
        notes: form.notes || undefined,
        job_description: form.job_description || undefined,
        resume_id: form.resume_id || null,
        status: form.status,
        resumeFile,
      });
      setForm({
        job_title: "",
        company: "",
        job_url: "",
        salary_range: "",
        notes: "",
        job_description: "",
        resume_id: "",
        status: defaultStatus,
      });
      setResumeFile(null);
      setImportUrl("");
      onClose();
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/70 backdrop-blur-sm">
      <div className="flex h-full w-full max-w-lg flex-col border-l border-border bg-card/95 backdrop-blur-xl">
        <div className="flex items-center justify-between border-b border-border px-6 py-4">
          <h2 className="text-lg font-semibold text-foreground">Log application</h2>
          <button onClick={onClose} className="rounded-md p-1 text-muted-foreground hover:bg-muted hover:text-foreground">
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex-1 space-y-4 overflow-y-auto p-6">
          <div className="rounded-lg border border-primary/20 bg-primary/5 p-4">
            <label className="text-xs font-medium text-primary">Import any job from its listing URL</label>
            <div className="mt-2 flex gap-2">
              <input
                type="url"
                value={importUrl}
                onChange={(e) => setImportUrl(e.target.value)}
                placeholder="https://company.com/careers/..."
                className="input-field flex-1"
              />
              <button type="button" onClick={handleImport} disabled={importing} className="btn-primary px-3">
                {importing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Link2 className="h-4 w-4" />}
              </button>
            </div>
          </div>

          {[
            { key: "job_title", label: "Job Title *", required: true },
            { key: "company", label: "Company *", required: true },
            { key: "job_url", label: "Job URL", required: false },
            { key: "salary_range", label: "Salary Range", required: false },
          ].map(({ key, label, required }) => (
            <div key={key}>
              <label className="text-xs font-medium text-muted-foreground">{label}</label>
              <input
                required={required}
                value={form[key as keyof typeof form]}
                onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))}
                className="input-field mt-1.5"
              />
            </div>
          ))}

          <div>
            <label className="text-xs font-medium text-muted-foreground">Job description</label>
            <textarea
              value={form.job_description}
              onChange={(e) => setForm((f) => ({ ...f, job_description: e.target.value }))}
              rows={8}
              placeholder="Paste the full job description so you can search and review it later"
              className="input-field mt-1.5 font-mono text-xs"
            />
          </div>

          <div>
            <label className="text-xs font-medium text-muted-foreground">Notes</label>
            <textarea
              value={form.notes}
              onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
              rows={3}
              className="input-field mt-1.5"
            />
          </div>

          <div>
            <label className="text-xs font-medium text-muted-foreground">Link JobPilot resume (optional)</label>
            <select
              value={form.resume_id}
              onChange={(e) => setForm((f) => ({ ...f, resume_id: e.target.value }))}
              className="input-field mt-1.5"
            >
              <option value="">None</option>
              {resumes.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.title}
                  {r.company_name ? ` — ${r.company_name}` : ""}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-xs font-medium text-muted-foreground">Or upload resume PDF (optional)</label>
            <label className="mt-1.5 flex cursor-pointer items-center gap-2 rounded-lg border border-dashed border-border bg-background/50 px-3 py-3 text-sm text-muted-foreground transition hover:border-primary/40 hover:text-foreground">
              <FileUp className="h-4 w-4 shrink-0" />
              <span className="truncate">{resumeFile ? resumeFile.name : "Choose PDF…"}</span>
              <input
                type="file"
                accept="application/pdf,.pdf"
                className="hidden"
                onChange={(e) => setResumeFile(e.target.files?.[0] ?? null)}
              />
            </label>
            {resumeFile && (
              <button type="button" onClick={() => setResumeFile(null)} className="mt-1 text-xs text-muted-foreground hover:text-foreground">
                Clear upload
              </button>
            )}
          </div>

          <button type="submit" disabled={saving} className="btn-primary w-full">
            {saving ? "Saving..." : "Add to Tracker"}
          </button>
        </form>
      </div>
    </div>
  );
}
