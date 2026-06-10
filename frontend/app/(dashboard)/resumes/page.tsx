"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Plus, Search, Pencil, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import type { ResumeDocument } from "@/types/resume";
import { PageHeader } from "@/components/ui/PageHeader";
import { formatDate } from "@/lib/utils";

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    processing: "bg-amber-500/15 text-amber-300 ring-amber-500/30",
    completed: "bg-emerald-500/15 text-emerald-300 ring-emerald-500/30",
    failed: "bg-red-500/15 text-red-300 ring-red-500/30",
    draft: "bg-zinc-500/15 text-zinc-300 ring-zinc-500/30",
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

  const load = () => {
    api.getResumes(search || undefined).then((r) => setResumes(r.resumes)).catch(console.error).finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
    const interval = setInterval(load, 5000);
    return () => clearInterval(interval);
  }, [search]);

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
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500" />
        <input
          className="input-field w-full pl-10"
          placeholder="Search resumes..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <div className="glass-panel overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-zinc-800 text-xs uppercase text-zinc-500">
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
              <tr><td colSpan={5} className="px-4 py-8 text-center text-zinc-500">Loading...</td></tr>
            )}
            {!loading && resumes.length === 0 && (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-zinc-500">No resumes yet. Create your first one!</td></tr>
            )}
            {resumes.map((r) => (
              <tr key={r.id} className="border-b border-zinc-800/50 hover:bg-zinc-800/30">
                <td className="px-4 py-3">
                  <div className="font-medium text-white">{r.title}</div>
                  {r.status === "processing" && (
                    <div className="text-xs text-zinc-500">Tailoring resume for this role...</div>
                  )}
                </td>
                <td className="px-4 py-3"><StatusBadge status={r.status} /></td>
                <td className="px-4 py-3 text-zinc-400">{r.company_name || r.company_url || "—"}</td>
                <td className="px-4 py-3 text-zinc-500">{formatDate(r.updated_at)}</td>
                <td className="px-4 py-3">
                  <Link href={`/resumes/${r.id}`} className="btn-secondary text-xs">
                    <Pencil className="h-3 w-3" /> Edit
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
