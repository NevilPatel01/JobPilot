"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Plus, Search, Pencil, Loader2, RefreshCw } from "lucide-react";
import { api } from "@/lib/api";
import type { ResumeDocument } from "@/types/resume";
import { PageHeader } from "@/components/ui/PageHeader";
import { formatDate } from "@/lib/utils";

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    processing: "bg-amber-500/15 text-amber-300 ring-amber-500/30",
    completed: "bg-success/15 text-success ring-success/30",
    failed: "bg-red-500/15 text-red-300 ring-red-500/30",
    draft: "bg-muted text-foreground ring-border",
  };
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ${colors[status] || colors.draft}`}>
      {status === "processing" && <Loader2 className="h-3 w-3 animate-spin" />}
      {status.toUpperCase()}
    </span>
  );
}

export default function ResumesPage() {
  const [resumes, setResumes] = useState<ResumeDocument[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [retryingId, setRetryingId] = useState<string | null>(null);

  const load = useCallback(() => {
    api.getResumes(search || undefined).then((r) => setResumes(r.resumes)).catch(console.error).finally(() => setLoading(false));
  }, [search]);

  const handleRetry = async (id: string) => {
    setRetryingId(id);
    try {
      await api.regenerateResume(id);
      load();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Regenerate failed");
    } finally {
      setRetryingId(null);
    }
  };

  useEffect(() => {
    load();
    const interval = setInterval(load, 5000);
    return () => clearInterval(interval);
  }, [load]);

  return (
    <div>
      <PageHeader
        title="Your Resumes"
        description="Every resume you've created, all in one place. Track progress, edit, or export."
        action={
          <Link href="/resumes/new" className="btn-primary">
            <Plus className="h-4 w-4" /> Create Resume
          </Link>
        }
      />

      <div className="relative mb-4">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <input
          className="input-field w-full pl-10"
          placeholder="Search resumes..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <div className="glass-panel overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-border text-xs uppercase text-muted-foreground">
            <tr>
              <th className="px-4 py-3">Title</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Company</th>
              <th className="px-4 py-3">Updated</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">Loading...</td></tr>
            )}
            {!loading && resumes.length === 0 && (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">No resumes yet. Create your first one!</td></tr>
            )}
            {resumes.map((r) => (
              <tr key={r.id} className="border-b border-border/50 hover:bg-muted/30">
                <td className="px-4 py-3">
                  <div className="font-medium text-foreground">{r.title}</div>
                  {r.status === "processing" && (
                    <div className="text-xs text-muted-foreground">Tailoring resume for this role...</div>
                  )}
                  {r.status === "failed" && r.pipeline_error && (
                    <div className="mt-1 text-xs text-red-400">{r.pipeline_error}</div>
                  )}
                </td>
                <td className="px-4 py-3"><StatusBadge status={r.status} /></td>
                <td className="px-4 py-3 text-muted-foreground">{r.company_name || r.company_url || "—"}</td>
                <td className="px-4 py-3 text-muted-foreground">{formatDate(r.updated_at)}</td>
                <td className="px-4 py-3">
                  <div className="flex gap-2">
                    {r.status === "failed" && (
                      <button
                        type="button"
                        onClick={() => handleRetry(r.id)}
                        disabled={retryingId === r.id}
                        className="btn-secondary text-xs"
                      >
                        <RefreshCw className={`h-3 w-3 ${retryingId === r.id ? "animate-spin" : ""}`} />
                        Retry
                      </button>
                    )}
                    <Link href={`/resumes/${r.id}`} className="btn-secondary text-xs">
                      <Pencil className="h-3 w-3" /> Edit
                    </Link>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
