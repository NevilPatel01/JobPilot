"use client";

import { useCallback, useEffect, useState } from "react";
import { RefreshCw, Search } from "lucide-react";
import { api } from "@/lib/api";
import type { Job, MatchScore } from "@/types";
import { JobCard } from "@/components/scraper/JobCard";
import { SkeletonLoader } from "@/components/scraper/SkeletonLoader";

export default function ScraperPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [matchScores, setMatchScores] = useState<Record<string, MatchScore>>({});
  const [loading, setLoading] = useState(true);
  const [scraping, setScraping] = useState(false);
  const [search, setSearch] = useState("");
  const [source, setSource] = useState("");
  const [toast, setToast] = useState<string | null>(null);
  const [trackingId, setTrackingId] = useState<string | null>(null);

  const loadJobs = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = { limit: "100" };
      if (search) params.q = search;
      if (source) params.source = source;
      const data = await api.getJobs(params);
      setJobs(data.jobs);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [search, source]);

  const loadMatchScores = useCallback(async () => {
    try {
      const scores = await api.getMatchScores();
      const map: Record<string, MatchScore> = {};
      scores.forEach((s) => (map[s.job_id] = s));
      setMatchScores(map);
    } catch {
      /* no resume yet */
    }
  }, []);

  useEffect(() => {
    loadJobs();
    loadMatchScores();
  }, [loadJobs, loadMatchScores]);

  const handleScrape = async () => {
    setScraping(true);
    try {
      const result = await api.triggerScraper();
      setToast(result.message);
      await loadJobs();
      await loadMatchScores();
    } catch (e) {
      setToast(e instanceof Error ? e.message : "Scrape failed");
    } finally {
      setScraping(false);
      setTimeout(() => setToast(null), 4000);
    }
  };

  const handleTrack = async (jobId: string) => {
    setTrackingId(jobId);
    try {
      await api.quickSaveJob(jobId);
      setToast("Job added to tracker!");
    } catch (e) {
      setToast(e instanceof Error ? e.message : "Failed to track job");
    } finally {
      setTrackingId(null);
      setTimeout(() => setToast(null), 3000);
    }
  };

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Remote Jobs</h1>
          <p className="text-sm text-zinc-400">{jobs.length} listings</p>
        </div>
        <button
          onClick={handleScrape}
          disabled={scraping}
          className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50 transition-colors"
        >
          <RefreshCw className={`h-4 w-4 ${scraping ? "animate-spin" : ""}`} />
          Scrape Now
        </button>
      </div>

      <div className="mb-6 flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500" />
          <input
            type="text"
            placeholder="Search by title or company..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && loadJobs()}
            className="w-full rounded-lg border border-zinc-800 bg-zinc-900 py-2 pl-10 pr-4 text-sm text-zinc-300 placeholder:text-zinc-500 focus:border-indigo-600 focus:outline-none"
          />
        </div>
        <select
          value={source}
          onChange={(e) => setSource(e.target.value)}
          className="rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-zinc-300 focus:border-indigo-600 focus:outline-none"
        >
          <option value="">All sources</option>
          <option value="remoteok">RemoteOK</option>
          <option value="weworkremotely">WeWorkRemotely</option>
          <option value="hackernews">Hacker News</option>
        </select>
        <button
          onClick={loadJobs}
          className="rounded-lg border border-zinc-700 px-4 py-2 text-sm text-zinc-300 hover:border-zinc-600 transition-colors"
        >
          Filter
        </button>
      </div>

      {toast && (
        <div className="mb-4 rounded-lg border border-indigo-600/50 bg-indigo-600/10 px-4 py-2 text-sm text-indigo-400">
          {toast}
        </div>
      )}

      {loading || scraping ? (
        <SkeletonLoader />
      ) : jobs.length === 0 ? (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-12 text-center">
          <p className="text-zinc-400">No jobs yet. Click &quot;Scrape Now&quot; to fetch listings.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {jobs.map((job) => {
            const match = matchScores[job.id];
            return (
              <JobCard
                key={job.id}
                job={job}
                matchScore={match?.score}
                matchedKeywords={match?.matched_keywords}
                onTrack={handleTrack}
                tracking={trackingId === job.id}
              />
            );
          })}
        </div>
      )}
    </div>
  );
}
