"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { RefreshCw } from "lucide-react";
import { api } from "@/lib/api";
import type { ATSScore } from "@/types/resume";
import { PageHeader } from "@/components/ui/PageHeader";

function ScoreBar({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <div className="mb-1 flex justify-between text-xs">
        <span className="text-zinc-400">{label}</span>
        <span className="text-zinc-300">{value}%</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-zinc-800">
        <div
          className="h-full rounded-full bg-indigo-500 transition-all"
          style={{ width: `${Math.min(100, value)}%` }}
        />
      </div>
    </div>
  );
}

function scoreColor(score: number): string {
  if (score >= 80) return "text-emerald-400";
  if (score >= 60) return "text-amber-400";
  return "text-red-400";
}

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
            <div className={`text-5xl font-bold ${scoreColor(score.overall_score)}`}>{score.overall_score}</div>
            <div className="mt-2 text-sm text-zinc-500">Overall ATS Score</div>
          </div>
          <div className="glass-panel space-y-4 p-6 lg:col-span-2">
            <ScoreBar label="Keyword match" value={score.keyword_match} />
            <ScoreBar label="Semantic similarity" value={score.semantic_score ?? 0} />
            <ScoreBar label="Skills coverage" value={score.skills_coverage ?? 0} />
            <ScoreBar label="Section completeness" value={score.section_score ?? 0} />
            <ScoreBar label="Formatting" value={score.formatting_score} />

            {score.matched_keywords && score.matched_keywords.length > 0 && (
              <div className="mt-4">
                <h3 className="text-sm font-semibold text-white">Matched Keywords</h3>
                <div className="mt-2 flex flex-wrap gap-2">
                  {score.matched_keywords.map((k) => (
                    <span key={k} className="rounded-full bg-emerald-500/10 px-3 py-1 text-xs text-emerald-300 ring-1 ring-emerald-500/20">{k}</span>
                  ))}
                </div>
              </div>
            )}
            {score.missing_keywords && score.missing_keywords.length > 0 && (
              <div className="mt-4">
                <h3 className="text-sm font-semibold text-white">Missing Keywords</h3>
                <div className="mt-2 flex flex-wrap gap-2">
                  {score.missing_keywords.map((k) => (
                    <span key={k} className="rounded-full bg-red-500/10 px-3 py-1 text-xs text-red-300 ring-1 ring-red-500/20">{k}</span>
                  ))}
                </div>
              </div>
            )}
            {score.suggestions.length > 0 && (
              <div className="mt-4">
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
