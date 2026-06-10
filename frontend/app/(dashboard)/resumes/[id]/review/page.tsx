"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { RefreshCw } from "lucide-react";
import { api } from "@/lib/api";
import type { ATSScore } from "@/types/resume";
import { PageHeader } from "@/components/ui/PageHeader";

export default function ResumeReviewPage() {
  const { id } = useParams<{ id: string }>();
  const [score, setScore] = useState<ATSScore | null>(null);
  const [loading, setLoading] = useState(false);

  const load = () => api.getATSScore(id).then(setScore).catch(console.error);

  useEffect(() => { load(); }, [id]);

  const rescore = async () => {
    setLoading(true);
    try {
      const s = await api.runATSScore(id);
      setScore(s);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <PageHeader
        title="Resume Review"
        description="ATS score and keyword analysis against the job description"
        action={
          <div className="flex gap-2">
            <Link href={`/resumes/${id}`} className="btn-secondary">Back to Editor</Link>
            <button onClick={rescore} disabled={loading} className="btn-primary">
              <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} /> Re-score
            </button>
          </div>
        }
      />

      {score ? (
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="glass-panel flex flex-col items-center justify-center p-8">
            <div className="text-5xl font-bold text-indigo-400">{score.overall_score}</div>
            <div className="mt-2 text-sm text-zinc-500">Overall ATS Score</div>
          </div>
          <div className="glass-panel p-6 lg:col-span-2">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-2xl font-semibold text-white">{score.keyword_match}%</div>
                <div className="text-xs text-zinc-500">Keyword Match</div>
              </div>
              <div>
                <div className="text-2xl font-semibold text-white">{score.formatting_score}%</div>
                <div className="text-xs text-zinc-500">Formatting</div>
              </div>
            </div>
            {score.missing_keywords && score.missing_keywords.length > 0 && (
              <div className="mt-6">
                <h3 className="text-sm font-semibold text-white">Missing Keywords</h3>
                <div className="mt-2 flex flex-wrap gap-2">
                  {score.missing_keywords.map((k) => (
                    <span key={k} className="rounded-full bg-red-500/10 px-3 py-1 text-xs text-red-300 ring-1 ring-red-500/20">{k}</span>
                  ))}
                </div>
              </div>
            )}
            {score.suggestions.length > 0 && (
              <div className="mt-6">
                <h3 className="text-sm font-semibold text-white">Suggestions</h3>
                <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-zinc-400">
                  {score.suggestions.map((s, i) => <li key={i}>{s}</li>)}
                </ul>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="glass-panel p-8 text-center text-zinc-500">
          No ATS score yet.{" "}
          <button onClick={rescore} className="text-indigo-400 hover:underline">Run analysis</button>
        </div>
      )}
    </div>
  );
}
