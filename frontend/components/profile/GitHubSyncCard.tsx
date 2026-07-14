"use client";

import { useState } from "react";
import { GitBranch, Loader2, RefreshCw } from "lucide-react";
import { candidateApi, type DraftFact } from "@/lib/api/candidate";
import { ImportReviewModal } from "@/components/profile/ImportReviewModal";

export function GitHubSyncCard({ onImported }: { onImported?: () => void }) {
  const [username, setUsername] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [drafts, setDrafts] = useState<DraftFact[] | null>(null);
  const [digest, setDigest] = useState<string | null>(null);

  const sync = async () => {
    setBusy(true);
    setNotice(null);
    try {
      const result = await candidateApi.importGitHub(username.trim() || undefined);
      if (result.rate_limited) setNotice(result.warning ?? "GitHub rate limit reached — try again later.");
      else if (result.warning) setNotice(result.warning);
      setDrafts(result.draft_facts);
    } catch (e) {
      setNotice(e instanceof Error ? e.message : "Sync failed");
    } finally {
      setBusy(false);
    }
  };

  const showDigest = async () => {
    try {
      const d = await candidateApi.getProjectsDigest();
      setDigest(d.content_text || "(empty — confirm some project facts first)");
    } catch (e) {
      setNotice(e instanceof Error ? e.message : "Digest unavailable");
    }
  };

  return (
    <div className="rounded-xl border border-border bg-card/40 p-4">
      <div className="flex flex-wrap items-center gap-3">
        <GitBranch className="h-5 w-5 shrink-0 text-foreground" />
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-foreground">Sync GitHub projects</p>
          <p className="mt-0.5 text-xs text-muted-foreground">
            Public repos only. READMEs are summarized once and cached — re-sync is free until a repo changes.
          </p>
        </div>
        <input
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="GitHub username (optional if you sign in with GitHub)"
          className="w-64 rounded-lg border border-border bg-background/60 px-3 py-1.5 text-sm text-foreground placeholder:text-muted-foreground"
        />
        <button onClick={sync} disabled={busy} className="btn-primary shrink-0">
          {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
          Sync
        </button>
      </div>
      {notice && <p className="mt-2 text-xs text-muted-foreground">{notice}</p>}
      <button onClick={showDigest} className="mt-2 text-xs text-primary hover:underline">
        Preview projects brief (what the resume AI sees)
      </button>
      {digest !== null && (
        <pre className="mt-2 max-h-64 overflow-auto whitespace-pre-wrap rounded-lg border border-border bg-background/60 p-3 text-xs text-muted-foreground">
          {digest}
        </pre>
      )}
      {drafts && (
        <ImportReviewModal
          drafts={drafts}
          title={`Review ${drafts.length} GitHub projects`}
          onClose={() => setDrafts(null)}
          onConfirmed={(result) => {
            setDrafts(null);
            setNotice(`Imported ${result.created} new, updated ${result.superseded}. Confirm them in the Facts tab to use on resumes.`);
            onImported?.();
          }}
        />
      )}
    </div>
  );
}
