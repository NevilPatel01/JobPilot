"use client";

import { useState } from "react";
import { X, Link2, Loader2 } from "lucide-react";
import type { Application } from "@/types";
import { api } from "@/lib/api";

interface AddJobModalProps {
  open: boolean;
  onClose: () => void;
  defaultStatus: string;
  onCreate: (data: Partial<Application>) => Promise<void>;
}

export function AddJobModal({ open, onClose, defaultStatus, onCreate }: AddJobModalProps) {
  const [form, setForm] = useState({
    job_title: "",
    company: "",
    job_url: "",
    salary_range: "",
    notes: "",
    status: defaultStatus,
  });
  const [importUrl, setImportUrl] = useState("");
  const [importing, setImporting] = useState(false);
  const [saving, setSaving] = useState(false);

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
      await onCreate(form);
      setForm({ job_title: "", company: "", job_url: "", salary_range: "", notes: "", status: defaultStatus });
      onClose();
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60">
      <div className="flex h-full w-full max-w-md flex-col border-l border-zinc-800 bg-zinc-900">
        <div className="flex items-center justify-between border-b border-zinc-800 px-6 py-4">
          <h2 className="text-lg font-semibold text-white">Add Job</h2>
          <button onClick={onClose} className="text-zinc-500 hover:text-zinc-300">
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-4">
          <div className="rounded-lg border border-zinc-800 bg-zinc-950 p-3">
            <label className="text-xs text-zinc-500">Import from URL</label>
            <div className="mt-1 flex gap-2">
              <input
                type="url"
                value={importUrl}
                onChange={(e) => setImportUrl(e.target.value)}
                placeholder="https://company.com/careers/..."
                className="flex-1 rounded border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-zinc-300 focus:border-indigo-600 focus:outline-none"
              />
              <button
                type="button"
                onClick={handleImport}
                disabled={importing}
                className="inline-flex items-center gap-1 rounded bg-indigo-600 px-3 py-2 text-sm text-white hover:bg-indigo-500 disabled:opacity-50"
              >
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
              <label className="text-xs text-zinc-500">{label}</label>
              <input
                required={required}
                value={form[key as keyof typeof form]}
                onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))}
                className="mt-1 w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-300 focus:border-indigo-600 focus:outline-none"
              />
            </div>
          ))}

          <div>
            <label className="text-xs text-zinc-500">Notes</label>
            <textarea
              value={form.notes}
              onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
              rows={3}
              className="mt-1 w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-300 focus:border-indigo-600 focus:outline-none"
            />
          </div>

          <button
            type="submit"
            disabled={saving}
            className="w-full rounded-lg bg-indigo-600 py-2.5 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50 transition-colors"
          >
            {saving ? "Saving..." : "Add to Tracker"}
          </button>
        </form>
      </div>
    </div>
  );
}
