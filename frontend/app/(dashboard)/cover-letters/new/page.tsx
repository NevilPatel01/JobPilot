"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import type { ResumeDocument } from "@/types/resume";
import { PageHeader } from "@/components/ui/PageHeader";

export default function CreateCoverLetterPage() {
  const router = useRouter();
  const [resumes, setResumes] = useState<ResumeDocument[]>([]);
  const [resumeId, setResumeId] = useState("");
  const [hiringManager, setHiringManager] = useState("");
  const [additionalContext, setAdditionalContext] = useState("");
  const [letterDate, setLetterDate] = useState(new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" }));
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.getResumes().then((r) => {
      const eligible = r.resumes.filter((res) => res.status === "completed" && !res.cover_letter_id);
      setResumes(eligible);
      if (eligible.length === 1) setResumeId(eligible[0].id);
    }).catch(console.error);
  }, []);

  const selected = resumes.find((r) => r.id === resumeId);

  const handleCreate = async () => {
    if (!resumeId) {
      setError("Select a resume first.");
      return;
    }
    setCreating(true);
    setError("");
    try {
      const letter = await api.createCoverLetter({
        resume_id: resumeId,
        title: selected ? `${selected.title} — Cover Letter` : undefined,
        hiring_manager_name: hiringManager || undefined,
        letter_date: letterDate || undefined,
        additional_context: additionalContext || undefined,
      });
      router.push(`/cover-letters/${letter.id}`);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to create cover letter");
      setCreating(false);
    }
  };

  return (
    <div>
      <Link href="/cover-letters" className="mb-4 inline-flex items-center gap-1 text-xs text-zinc-500 hover:text-white">
        <ArrowLeft className="h-3 w-3" /> Back to cover letters
      </Link>

      <PageHeader
        title="Create Cover Letter"
        description="Generate a tailored cover letter from an existing resume"
      />

      <div className="glass-panel mx-auto max-w-xl space-y-5 p-6">
        {resumes.length === 0 ? (
          <div className="text-center text-sm text-zinc-400">
            <p>No eligible resumes found.</p>
            <p className="mt-2">Create and complete a resume first, or use one that doesn&apos;t already have a cover letter.</p>
            <Link href="/resumes/new" className="btn-primary mt-4 inline-flex">Create Resume</Link>
          </div>
        ) : (
          <>
            <div>
              <label className="text-xs text-zinc-400">Resume</label>
              <select
                className="input-field mt-1 w-full text-sm"
                value={resumeId}
                onChange={(e) => setResumeId(e.target.value)}
              >
                <option value="">Select a resume...</option>
                {resumes.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.title} {r.company_name ? `— ${r.company_name}` : ""}
                  </option>
                ))}
              </select>
            </div>

            {selected?.job_description && (
              <div className="rounded-lg border border-zinc-800 p-3">
                <p className="text-xs font-medium text-zinc-400">Job description preview</p>
                <p className="mt-1 line-clamp-4 text-xs text-zinc-500">{selected.job_description}</p>
              </div>
            )}

            <div>
              <label className="text-xs text-zinc-400">Hiring manager (optional)</label>
              <input
                className="input-field mt-1 text-sm"
                value={hiringManager}
                onChange={(e) => setHiringManager(e.target.value)}
                placeholder="Jane Smith"
              />
            </div>

            <div>
              <label className="text-xs text-zinc-400">Letter date</label>
              <input
                className="input-field mt-1 text-sm"
                value={letterDate}
                onChange={(e) => setLetterDate(e.target.value)}
              />
            </div>

            <div>
              <label className="text-xs text-zinc-400">Additional context (optional)</label>
              <textarea
                className="input-field mt-1 min-h-[80px] text-sm"
                value={additionalContext}
                onChange={(e) => setAdditionalContext(e.target.value)}
                placeholder="Referral, relocation, why this company..."
              />
            </div>

            {error && <p className="text-sm text-red-400">{error}</p>}

            <button
              type="button"
              onClick={handleCreate}
              disabled={creating || !resumeId}
              className="btn-primary w-full"
            >
              {creating ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" /> Generating...
                </>
              ) : (
                "Generate Cover Letter"
              )}
            </button>
          </>
        )}
      </div>
    </div>
  );
}
