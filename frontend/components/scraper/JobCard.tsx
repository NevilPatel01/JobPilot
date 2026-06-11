"use client";

import { ExternalLink, BookmarkPlus } from "lucide-react";
import type { Job } from "@/types";
import { MatchBadge } from "./MatchBadge";
import { formatDate, daysSince, stripHtml } from "@/lib/utils";

interface JobCardProps {
  job: Job;
  matchScore?: number;
  matchedKeywords?: string[];
  onTrack: (jobId: string) => void;
  tracking?: boolean;
}

const sourceColors: Record<string, string> = {
  remoteok: "bg-emerald-500/10 text-emerald-400 ring-emerald-500/20",
  weworkremotely: "bg-sky-500/10 text-sky-400 ring-sky-500/20",
  hackernews: "bg-orange-500/10 text-orange-400 ring-orange-500/20",
  custom: "bg-zinc-500/10 text-zinc-400 ring-zinc-500/20",
};

export function JobCard({ job, matchScore, matchedKeywords, onTrack, tracking }: JobCardProps) {
  const verifiedDays = daysSince(job.last_verified);
  const preview = job.description ? stripHtml(job.description).slice(0, 160) : null;

  return (
    <div className="glass-panel-hover group p-5">
      <div className="flex gap-4">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-zinc-800 to-zinc-900 text-sm font-bold text-zinc-300 ring-1 ring-zinc-700/50">
          {job.company.charAt(0).toUpperCase()}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="min-w-0">
              <h3 className="font-semibold tracking-tight text-white group-hover:text-indigo-100">{job.title}</h3>
              <p className="mt-0.5 text-sm text-zinc-500">{job.company}</p>
            </div>
            <div className="flex flex-wrap gap-2">
              {matchScore !== undefined && <MatchBadge score={matchScore} keywords={matchedKeywords} />}
              <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ${sourceColors[job.source] || sourceColors.custom}`}>
                {job.source}
              </span>
            </div>
          </div>

          {preview && (
            <p className="mt-2.5 line-clamp-2 text-sm leading-relaxed text-zinc-500">{preview}...</p>
          )}

          {job.tech_stack && job.tech_stack.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {job.tech_stack.slice(0, 6).map((tag) => (
                <span key={tag} className="rounded-md bg-zinc-800/80 px-2 py-0.5 text-xs text-zinc-400 ring-1 ring-zinc-700/50">
                  {tag}
                </span>
              ))}
            </div>
          )}

          <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-zinc-600">
            <span>Posted {formatDate(job.first_seen)}</span>
            <span className="text-emerald-500/80">
              Verified {verifiedDays === 0 ? "today" : `${verifiedDays}d ago`}
            </span>
            {job.location && <span>{job.location}</span>}
            {job.country === "CA" && <span className="text-red-400/80">🇨🇦 Canada</span>}
            {job.is_remote && <span className="text-indigo-400/70">Remote</span>}
          </div>

          <div className="mt-4 flex gap-2">
            <a href={job.url} target="_blank" rel="noopener noreferrer" className="btn-secondary py-1.5 text-xs">
              <ExternalLink className="h-3.5 w-3.5" />
              View Job
            </a>
            <button onClick={() => onTrack(job.id)} disabled={tracking} className="btn-primary py-1.5 text-xs">
              <BookmarkPlus className="h-3.5 w-3.5" />
              Track
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
