"use client";

import { useCallback, useEffect, useState } from "react";
import { CheckCircle2, Download, Loader2, Pin, PinOff, ShieldAlert, XCircle } from "lucide-react";
import { candidateApi, type CandidateFact, type DraftFact } from "@/lib/api/candidate";
import { ImportReviewModal } from "@/components/profile/ImportReviewModal";
import { cn } from "@/lib/utils";

const TYPE_ORDER = [
  "employment", "education", "certification", "skill", "project",
  "work_authorization", "contact", "target_role", "target_industry", "location", "personal", "metric", "achievement",
];

const BADGE: Record<string, { label: string; cls: string }> = {
  unverified: { label: "Unverified", cls: "bg-amber-500/10 text-amber-400 border-amber-500/30" },
  user_confirmed: { label: "Confirmed", cls: "bg-green-500/10 text-green-400 border-green-500/30" },
  contradicted: { label: "Disputed", cls: "bg-red-500/10 text-red-400 border-red-500/30" },
};

function factTitle(fact: CandidateFact): string {
  const p = fact.payload as Record<string, string | undefined>;
  return p.name || p.employer || p.institution || p.status || p.full_name || Object.values(p).filter((v) => typeof v === "string")[0] || fact.fact_type;
}

function factDetail(fact: CandidateFact): string {
  const p = fact.payload as Record<string, unknown>;
  if (fact.fact_type === "employment")
    return `${p.title ?? ""} · ${p.start_date ?? p.start_date_text ?? "?"} – ${p.end_date ?? p.end_date_text ?? "present"}`;
  if (fact.fact_type === "project") return String(p.one_liner ?? "");
  if (fact.fact_type === "education") return String(p.credential ?? "");
  if (fact.fact_type === "skill") return [p.level, p.years ? `${p.years}y` : ""].filter(Boolean).join(" · ");
  return "";
}

export function FactsPanel() {
  const [facts, setFacts] = useState<CandidateFact[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [importBusy, setImportBusy] = useState<string | null>(null);
  const [drafts, setDrafts] = useState<DraftFact[] | null>(null);
  const [draftsTitle, setDraftsTitle] = useState("");
  const [notice, setNotice] = useState<string | null>(null);

  const reload = useCallback(async () => {
    try {
      setFacts(await candidateApi.listFacts());
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    reload();
  }, [reload]);

  const act = async (id: string, fn: () => Promise<unknown>) => {
    setBusyId(id);
    try {
      await fn();
      await reload();
    } catch (e) {
      setNotice(e instanceof Error ? e.message : "Action failed");
    } finally {
      setBusyId(null);
    }
  };

  const runLegacyImport = async () => {
    setImportBusy("legacy");
    setNotice(null);
    try {
      const result = await candidateApi.importLegacyProfile();
      setNotice(`Imported ${result.created} facts from your profile (${result.skipped} already present).`);
      await reload();
    } catch (e) {
      setNotice(e instanceof Error ? e.message : "Import failed");
    } finally {
      setImportBusy(null);
    }
  };

  const grouped = TYPE_ORDER.map((type) => ({ type, items: facts.filter((f) => f.fact_type === type) })).filter(
    (g) => g.items.length > 0,
  );

  if (loading) return <div className="flex justify-center py-12"><Loader2 className="h-5 w-5 animate-spin text-muted-foreground" /></div>;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-3 rounded-xl border border-border bg-card/40 p-4">
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-foreground">Verified candidate facts</p>
          <p className="mt-0.5 text-xs text-muted-foreground">
            Every resume claim traces back to a confirmed fact. Import, then confirm each one.
          </p>
        </div>
        <button onClick={runLegacyImport} disabled={importBusy !== null} className="btn-secondary shrink-0">
          {importBusy === "legacy" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
          Import from profile
        </button>
      </div>

      {notice && <p className="text-xs text-muted-foreground">{notice}</p>}

      {grouped.length === 0 && (
        <p className="rounded-lg border border-border bg-background/40 px-4 py-6 text-center text-sm text-muted-foreground">
          No facts yet — import from your profile or sync GitHub projects below.
        </p>
      )}

      {grouped.map(({ type, items }) => (
        <div key={type}>
          <p className="mb-2 text-xs font-medium uppercase tracking-widest text-primary">{type.replace(/_/g, " ")}</p>
          <div className="space-y-2">
            {items.map((fact) => {
              const badge = BADGE[fact.verification_status] ?? BADGE.unverified;
              const pinned = Boolean((fact.payload as Record<string, unknown>).pinned);
              return (
                <div key={fact.id} className="flex items-start gap-3 rounded-lg border border-border bg-card/40 p-3">
                  <div className="min-w-0 flex-1">
                    <p className={cn("text-sm text-foreground", fact.is_prohibited && "line-through opacity-60")}>
                      {factTitle(fact)}
                      {fact.is_prohibited && (
                        <span className="ml-2 inline-flex items-center gap-1 text-[10px] text-destructive">
                          <ShieldAlert className="h-3 w-3" /> prohibited
                        </span>
                      )}
                    </p>
                    {factDetail(fact) && <p className="mt-0.5 truncate text-xs text-muted-foreground">{factDetail(fact)}</p>}
                  </div>
                  <span className={cn("shrink-0 rounded-full border px-2 py-0.5 text-[10px]", badge.cls)}>{badge.label}</span>
                  <div className="flex shrink-0 items-center gap-1">
                    {fact.fact_type === "project" && (
                      <button
                        title={pinned ? "Unpin from resume selection" : "Pin: always eligible for resumes"}
                        onClick={() => act(fact.id, () => (pinned ? candidateApi.unpinFact(fact.id) : candidateApi.pinFact(fact.id)))}
                        className="rounded p-1 text-muted-foreground hover:text-foreground"
                      >
                        {pinned ? <PinOff className="h-4 w-4" /> : <Pin className="h-4 w-4" />}
                      </button>
                    )}
                    {fact.verification_status !== "user_confirmed" && fact.verification_status !== "contradicted" && (
                      <button
                        title="Confirm this fact is accurate"
                        onClick={() => act(fact.id, () => candidateApi.verifyFact(fact.id))}
                        className="rounded p-1 text-green-400 hover:text-green-300"
                      >
                        {busyId === fact.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />}
                      </button>
                    )}
                    {fact.verification_status !== "contradicted" && (
                      <button
                        title="Dispute: mark as inaccurate"
                        onClick={() => act(fact.id, () => candidateApi.disputeFact(fact.id))}
                        className="rounded p-1 text-muted-foreground hover:text-destructive"
                      >
                        <XCircle className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ))}

      {drafts && (
        <ImportReviewModal
          drafts={drafts}
          title={draftsTitle}
          onClose={() => setDrafts(null)}
          onConfirmed={async (result) => {
            setDrafts(null);
            setNotice(`Imported ${result.created} new, updated ${result.superseded}.`);
            await reload();
          }}
        />
      )}
      {/* GitHub sync + resume-text import mount their own modal via this panel's setters */}
      <FactsPanelImports
        onDrafts={(d, t) => {
          setDrafts(d);
          setDraftsTitle(t);
        }}
        onNotice={setNotice}
      />
    </div>
  );
}

function FactsPanelImports({
  onDrafts,
  onNotice,
}: {
  onDrafts: (drafts: DraftFact[], title: string) => void;
  onNotice: (msg: string) => void;
}) {
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);

  const run = async () => {
    setBusy(true);
    try {
      const result = await candidateApi.importResumeText(text);
      if (result.warning) onNotice(result.warning);
      onDrafts(result.draft_facts, `Review ${result.draft_facts.length} facts extracted from your resume`);
    } catch (e) {
      onNotice(e instanceof Error ? e.message : "Extraction failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="rounded-xl border border-border bg-card/40 p-4">
      <p className="text-sm font-medium text-foreground">Import from resume text</p>
      <p className="mt-0.5 text-xs text-muted-foreground">
        Paste your resume — AI extracts facts with verbatim evidence; you review before anything is saved.
      </p>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        rows={4}
        placeholder="Paste resume text…"
        className="mt-3 w-full rounded-lg border border-border bg-background/60 p-3 text-sm text-foreground placeholder:text-muted-foreground"
      />
      <button onClick={run} disabled={busy || text.trim().length < 20} className="btn-secondary mt-2">
        {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
        Extract facts
      </button>
    </div>
  );
}
