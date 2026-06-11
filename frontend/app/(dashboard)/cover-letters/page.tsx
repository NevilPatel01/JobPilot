"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Plus, Pencil } from "lucide-react";
import { api } from "@/lib/api";
import type { CoverLetterDocument } from "@/types/resume";
import { PageHeader } from "@/components/ui/PageHeader";
import { formatDate } from "@/lib/utils";

export default function CoverLettersPage() {
  const [letters, setLetters] = useState<CoverLetterDocument[]>([]);

  useEffect(() => {
    api.getCoverLetters().then((r) => setLetters(r.cover_letters)).catch(console.error);
  }, []);

  return (
    <div>
      <PageHeader
        title="My Cover Letters"
        description="Cover letters generated alongside tailored resumes"
        action={
          <div className="flex gap-2">
            <Link href="/cover-letters/new" className="btn-secondary">
              <Plus className="h-4 w-4" /> From Resume
            </Link>
            <Link href="/resumes/new" className="btn-primary">
              <Plus className="h-4 w-4" /> Create with Resume
            </Link>
          </div>
        }
      />

      <div className="glass-panel overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-zinc-800 text-xs uppercase text-zinc-500">
            <tr>
              <th className="px-4 py-3">Title</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Updated</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {letters.length === 0 && (
              <tr><td colSpan={4} className="px-4 py-8 text-center text-zinc-500">No cover letters yet</td></tr>
            )}
            {letters.map((l) => (
              <tr key={l.id} className="border-b border-zinc-800/50 hover:bg-zinc-800/30">
                <td className="px-4 py-3 font-medium text-white">{l.title}</td>
                <td className="px-4 py-3 text-zinc-400">{l.status}</td>
                <td className="px-4 py-3 text-zinc-500">{formatDate(l.updated_at)}</td>
                <td className="px-4 py-3">
                  <Link href={`/cover-letters/${l.id}`} className="btn-secondary text-xs">
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
