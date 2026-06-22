"use client";

import { useCallback, useEffect, useState } from "react";
import { RefreshCw, Search, Inbox } from "lucide-react";
import { api } from "@/lib/api";
import type { Job, MatchScore } from "@/types";
import { JobCard } from "@/components/scraper/JobCard";
import { SkeletonLoader } from "@/components/scraper/SkeletonLoader";
import { PageHeader } from "@/components/ui/PageHeader";

export default function ScraperPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [matchScores, setMatchScores] = useState<Record<string, MatchScore>>({});
  const [loading, setLoading] = useState(true);
  const [scraping, setScraping] = useState(false);
  const [search, setSearch] = useState("");
  const [source, setSource] = useState("");
  const [toast, setToast] = useState<string | null>(null);
  const [savingId, setSavingId] = useState<string | null>(null);

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

  const handleSave = async (jobId: string) => {
    setSavingId(jobId);
    try {
      await api.saveJobToInbox(jobId);
      setToast("Added to Job Inbox");
    } catch (e) {
      setToast(e instanceof Error ? e.message : "Failed to save job");
    } finally {
      setSavingId(null);
      setTimeout(() => setToast(null), 3000);
    }
  };

  return (
    <div>
      <PageHeader
        title="Canadian Jobs"
        description={`${jobs.length} Canada-eligible listings`}
        action={
          <button onClick={handleScrape} disabled={scraping} className="btn-primary">
            <RefreshCw className={`h-4 w-4 ${scraping ? "animate-spin" : ""}`} />
            Scrape Now
          </button>
        }
      />

      <div className="mb-6 flex flex-wrap gap-3">
        <div className="relative min-w-[200px] flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search title or company..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && loadJobs()}
            className="input-field pl-10"
          />
        </div>
        <select value={source} onChange={(e) => setSource(e.target.value)} className="input-field w-auto min-w-[140px]">
          <option value="">All sources</option>
          <option value="remoteok">RemoteOK</option>
          <option value="weworkremotely">WeWorkRemotely</option>
          <option value="hackernews">Hacker News</option>
        </select>
        <button onClick={loadJobs} className="btn-secondary">
          Filter
        </button>
      </div>

      {toast && (
        <div className="mb-4 rounded-lg border border-primary/30 bg-primary/10 px-4 py-2.5 text-sm text-primary">
          {toast}
        </div>
      )}

      {loading || scraping ? (
        <SkeletonLoader />
      ) : jobs.length === 0 ? (
        <div className="glass-panel flex flex-col items-center py-16 text-center">
          <Inbox className="h-10 w-10 text-muted-foreground/60" />
          <p className="mt-4 font-medium text-muted-foreground">No jobs yet</p>
          <p className="mt-1 text-sm text-muted-foreground">Click Scrape Now to pull Canada-eligible listings</p>
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
                onSave={handleSave}
                saving={savingId === job.id}
              />
            );
          })}
        </div>
      )}
    </div>
  );
}
