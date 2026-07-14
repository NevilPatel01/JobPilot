"use client";

import { useCallback, useEffect, useState } from "react";
import { CheckCircle2, Loader2, Plus, Trash2 } from "lucide-react";
import { candidateApi, type Achievement } from "@/lib/api/candidate";

const EMPTY = { situation: "", task: "", action: "", result: "" };

export function AchievementsPanel() {
  const [rows, setRows] = useState<Achievement[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState(EMPTY);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    try {
      setRows(await candidateApi.listAchievements());
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
      await candidateApi.createAchievement(form);
      setForm(EMPTY);
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
        <p className="text-sm font-medium text-foreground">Add a STAR story</p>
        <p className="mt-0.5 text-xs text-muted-foreground">
          Situation → Task → Action → Result. These power interview prep and evidence-backed resume bullets.
        </p>
        <div className="mt-3 grid gap-2 sm:grid-cols-2">
          {(["situation", "task", "action", "result"] as const).map((field) => (
            <textarea
              key={field}
              value={form[field]}
              onChange={(e) => setForm((f) => ({ ...f, [field]: e.target.value }))}
              rows={2}
              placeholder={field[0].toUpperCase() + field.slice(1)}
              className="rounded-lg border border-border bg-background/60 p-2 text-sm text-foreground placeholder:text-muted-foreground"
            />
          ))}
        </div>
        {error && <p className="mt-2 text-xs text-destructive">{error}</p>}
        <button onClick={create} disabled={busy || !form.result.trim()} className="btn-primary mt-3">
          {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
          Add achievement
        </button>
      </div>

      {rows.length === 0 ? (
        <p className="rounded-lg border border-border bg-background/40 px-4 py-6 text-center text-sm text-muted-foreground">
          No achievements yet — the result field is the one that matters most.
        </p>
      ) : (
        <div className="space-y-2">
          {rows.map((row) => (
            <div key={row.id} className="rounded-lg border border-border bg-card/40 p-3">
              <div className="flex items-start justify-between gap-3">
                <p className="text-sm font-medium text-foreground">{row.result || "(no result)"}</p>
                <div className="flex shrink-0 items-center gap-1">
                  {row.verification_status !== "user_confirmed" && (
                    <button
                      title="Confirm"
                      onClick={async () => { await candidateApi.verifyAchievement(row.id); reload(); }}
                      className="rounded p-1 text-green-400 hover:text-green-300"
                    >
                      <CheckCircle2 className="h-4 w-4" />
                    </button>
                  )}
                  <button
                    title="Delete"
                    onClick={async () => { await candidateApi.deleteAchievement(row.id); reload(); }}
                    className="rounded p-1 text-muted-foreground hover:text-destructive"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
              {(row.situation || row.action) && (
                <p className="mt-1 text-xs text-muted-foreground">
                  {[row.situation, row.task, row.action].filter(Boolean).join(" → ")}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
