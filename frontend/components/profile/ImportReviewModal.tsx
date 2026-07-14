"use client";

import { useState } from "react";
import { CheckCircle2, Loader2, X } from "lucide-react";
import { candidateApi, type DraftFact } from "@/lib/api/candidate";
import { cn } from "@/lib/utils";

function draftTitle(draft: DraftFact): string {
  const p = draft.payload as Record<string, string | undefined>;
  return (
    p.name || p.employer || p.institution || p.status || p.full_name || JSON.stringify(draft.payload).slice(0, 60)
  );
}

function draftDetail(draft: DraftFact): string {
  const p = draft.payload as Record<string, unknown>;
  if (draft.fact_type === "employment") return `${p.title ?? ""} · ${p.start_date ?? p.start_date_text ?? ""}–${p.end_date ?? p.end_date_text ?? "present"}`;
  if (draft.fact_type === "project") return String(p.one_liner ?? p.url ?? "");
  if (draft.fact_type === "education") return String(p.credential ?? "");
  return "";
}

export function ImportReviewModal({
  drafts,
  title,
  onClose,
  onConfirmed,
}: {
  drafts: DraftFact[];
  title: string;
  onClose: () => void;
  onConfirmed: (result: { created: number; superseded: number }) => void;
}) {
  const [selected, setSelected] = useState<boolean[]>(drafts.map(() => true));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const confirm = async () => {
    setBusy(true);
    setError(null);
    try {
      const accepted = drafts.filter((_, i) => selected[i]);
      const result = await candidateApi.confirmImport(accepted);
      onConfirmed(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Import failed");
    } finally {
      setBusy(false);
    }
  };

  const count = selected.filter(Boolean).length;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
      <div className="mx-4 flex max-h-[80vh] w-full max-w-lg flex-col rounded-2xl border border-border bg-card shadow-2xl">
        <div className="flex items-center justify-between border-b border-border px-5 py-4">
          <p className="text-sm font-semibold text-foreground">{title}</p>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground"><X className="h-4 w-4" /></button>
        </div>
        <div className="flex-1 space-y-2 overflow-y-auto px-5 py-4">
          {drafts.length === 0 && <p className="text-sm text-muted-foreground">Nothing new to import.</p>}
          {drafts.map((draft, i) => (
            <label
              key={i}
              className={cn(
                "flex cursor-pointer items-start gap-3 rounded-lg border p-3 transition-colors",
                selected[i] ? "border-primary/40 bg-primary/5" : "border-border bg-background/40",
              )}
            >
              <input
                type="checkbox"
                checked={selected[i]}
                onChange={() => setSelected((s) => s.map((v, j) => (j === i ? !v : v)))}
                className="mt-1"
              />
              <div className="min-w-0">
                <p className="text-sm text-foreground">
                  <span className="mr-2 rounded bg-muted px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-muted-foreground">
                    {draft.fact_type}
                  </span>
                  {draftTitle(draft)}
                </p>
                {draftDetail(draft) && <p className="mt-0.5 truncate text-xs text-muted-foreground">{draftDetail(draft)}</p>}
              </div>
            </label>
          ))}
          {error && <p className="text-xs text-destructive">{error}</p>}
        </div>
        <div className="flex items-center justify-between gap-3 border-t border-border px-5 py-4">
          <p className="text-xs text-muted-foreground">Imported facts arrive as “unverified” — confirm them in the Facts tab.</p>
          <button onClick={confirm} disabled={busy || count === 0} className="btn-primary shrink-0">
            {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />}
            Import {count}
          </button>
        </div>
      </div>
    </div>
  );
}
