"use client";

import { ExternalLink, BookmarkPlus } from "lucide-react";
import type { Job } from "@/types";
import { MatchBadge } from "./MatchBadge";
import { formatDate, daysSince } from "@/lib/utils";

interface JobCardProps {
  job: Job;
  matchScore?: number;
  matchedKeywords?: string[];
  onTrack: (jobId: string) => void;
  tracking?: boolean;
}

const sourceColors: Record<string, string> = {
  remoteok: "bg-green-500/20 text-green-500",
  weworkremotely: "bg-blue-500/20 text-blue-400",
  hackernews: "bg-orange-500/20 text-orange-400",
  custom: "bg-zinc-500/20 text-zinc-400",
};

export function JobCard({ job, matchScore, matchedKeywords, onTrack, tracking }: JobCardProps) {
  const verifiedDays = daysSince(job.last_verified);

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-4 transition-all duration-200 hover:border-zinc-700 hover:-translate-y-0.5">
      <div className="flex gap-4">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-zinc-800 text-xs font-bold text-zinc-400">
          {job.company.charAt(0).toUpperCase()}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div>
              <h3 className="font-semibold text-white">{job.title}</h3>
              <p className="text-sm text-zinc-400">{job.company}</p>
            </div>
            <div className="flex flex-wrap gap-2">
              {matchScore !== undefined && <MatchBadge score={matchScore} keywords={matchedKeywords} />}
              <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${sourceColors[job.source] || sourceColors.custom}`}>
                {job.source}
              </span>
            </div>
          </div>

          {job.tech_stack && job.tech_stack.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {job.tech_stack.slice(0, 5).map((tag) => (
                <span key={tag} className="rounded-md bg-zinc-800 px-2 py-0.5 text-xs text-zinc-400">
                  {tag}
                </span>
              ))}
            </div>
          )}

          <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-zinc-500">
            <span>Posted {formatDate(job.first_seen)}</span>
            <span className="text-green-500">✓ Verified {verifiedDays === 0 ? "today" : `${verifiedDays}d ago`}</span>
            {job.location && <span>{job.location}</span>}
          </div>

          <div className="mt-4 flex gap-2">
            <a
              href={job.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 rounded-lg border border-zinc-700 px-3 py-1.5 text-sm text-zinc-300 hover:border-zinc-600 hover:text-white transition-colors"
            >
              <ExternalLink className="h-3.5 w-3.5" />
              View Job
            </a>
            <button
              onClick={() => onTrack(job.id)}
              disabled={tracking}
              className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50 transition-colors"
            >
              <BookmarkPlus className="h-3.5 w-3.5" />
              Track This Job
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
