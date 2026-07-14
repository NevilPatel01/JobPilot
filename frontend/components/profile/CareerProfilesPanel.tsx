"use client";

import { useCallback, useEffect, useState } from "react";
import { Loader2, Plus, Star, Trash2 } from "lucide-react";
import { candidateApi, type CareerProfile } from "@/lib/api/candidate";
import { cn } from "@/lib/utils";

export function CareerProfilesPanel() {
  const [rows, setRows] = useState<CareerProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [name, setName] = useState("");
  const [positioning, setPositioning] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    try {
      setRows(await candidateApi.listCareerProfiles());
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    reload();
  }, [reload]);

  const create = async () => {
    setBusy(true);
    setError(null);
    try {
      await candidateApi.createCareerProfile({ name, positioning_statement: positioning });
      setName("");
      setPositioning("");
      await reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setBusy(false);
    }
  };

  if (loading) return <div className="flex justify-center py-12"><Loader2 className="h-5 w-5 animate-spin text-muted-foreground" /></div>;

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-border bg-card/40 p-4">
        <p className="text-sm font-medium text-foreground">Add a career profile</p>
        <p className="mt-0.5 text-xs text-muted-foreground">
          A positioning angle, e.g. “Cloud Support Specialist” vs “Full-Stack Developer”. Future phases pick the
          best profile per job.
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Name, e.g. Cloud Support"
            className="w-56 rounded-lg border border-border bg-background/60 px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground"
          />
          <input
            value={positioning}
            onChange={(e) => setPositioning(e.target.value)}
            placeholder="One-sentence positioning statement"
            className="min-w-0 flex-1 rounded-lg border border-border bg-background/60 px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground"
          />
          <button onClick={create} disabled={busy || !name.trim()} className="btn-primary shrink-0">
            {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
            Add
          </button>
        </div>
        {error && <p className="mt-2 text-xs text-destructive">{error}</p>}
      </div>

      <div className="space-y-2">
        {rows.map((row) => (
          <div key={row.id} className={cn("flex items-center gap-3 rounded-lg border p-3", row.is_default ? "border-primary/40 bg-primary/5" : "border-border bg-card/40")}>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-foreground">
                {row.name}
                {row.is_default && <span className="ml-2 text-[10px] uppercase tracking-wide text-primary">default</span>}
              </p>
              {row.positioning_statement && <p className="mt-0.5 text-xs text-muted-foreground">{row.positioning_statement}</p>}
            </div>
            {!row.is_default && (
              <button
                title="Make default"
                onClick={async () => { await candidateApi.setDefaultCareerProfile(row.id); reload(); }}
                className="rounded p-1 text-muted-foreground hover:text-amber-400"
              >
                <Star className="h-4 w-4" />
              </button>
            )}
            <button
              title="Delete"
              onClick={async () => { await candidateApi.deleteCareerProfile(row.id); reload(); }}
              className="rounded p-1 text-muted-foreground hover:text-destructive"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
