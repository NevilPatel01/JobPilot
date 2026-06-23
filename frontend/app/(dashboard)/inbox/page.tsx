"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Archive,
  ArrowUpRight,
  BriefcaseBusiness,
  Check,
  ChevronDown,
  Inbox as InboxIcon,
  Link2,
  Loader2,
  MapPin,
  Plus,
  Search,
  Sparkles,
  X,
  ShieldAlert,
  Target,
  RefreshCw,
  FileText,
  Info,
  ListPlus,
  SlidersHorizontal,
} from "lucide-react";
import { api } from "@/lib/api";
import type { InboxJob, InboxManualCreate, InboxStatus } from "@/types";
import { PageHeader } from "@/components/ui/PageHeader";

const STATUS_OPTIONS: { value: InboxStatus | ""; label: string }[] = [
  { value: "", label: "All inbox" },
  { value: "new", label: "New" },
  { value: "ai_reviewed", label: "AI reviewed" },
  { value: "shortlisted", label: "Shortlisted" },
  { value: "resume_ready", label: "Resume ready" },
  { value: "applied", label: "Applied" },
  { value: "archived", label: "Archived" },
  { value: "duplicate", label: "Duplicates" },
];

const STATUS_LABELS: Record<InboxStatus, string> = {
  new: "New",
  ai_reviewed: "AI reviewed",
  shortlisted: "Shortlisted",
  resume_ready: "Resume ready",
  applied: "Applied",
  archived: "Archived",
  duplicate: "Duplicate",
};

const CATEGORY_LABELS: Record<string, string> = {
  it_support: "IT Support",
  cloud_junior_devops: "Cloud / Junior DevOps",
  fullstack_web: "Full-stack / Web",
  app_support_analyst: "Application Support",
  automation_scada: "Automation / SCADA",
};

const FIT_STYLES: Record<string, string> = {
  low: "bg-muted/80 text-muted-foreground ring-border",
  stretch: "bg-amber-500/10 text-amber-300 ring-amber-500/20",
  reviewed: "bg-sky-500/10 text-sky-300 ring-sky-500/20",
  recommended: "bg-primary/10 text-primary ring-primary/20",
  priority: "bg-success/10 text-success ring-success/20",
};

const EMPTY_FORM: InboxManualCreate = {
  title: "",
  company: "",
  apply_url: "",
  location: "",
  description: "",
  skills: [],
};

export default function InboxPage() {
  const router = useRouter();
  const [items, setItems] = useState<InboxJob[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<InboxStatus | "">("");
  const [province, setProvince] = useState("");
  const [minScore, setMinScore] = useState("");
  const [resumeCategory, setResumeCategory] = useState("");
  const [search, setSearch] = useState("");
  const [addOpen, setAddOpen] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const [generatingId, setGeneratingId] = useState<string | null>(null);
  const [trackingId, setTrackingId] = useState<string | null>(null);
  const [filtersOpen, setFiltersOpen] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = { limit: "100" };
      if (status) params.status = status;
      if (province) params.province = province;
      if (minScore) params.min_score = minScore;
      if (resumeCategory) params.resume_category = resumeCategory;
      if (search.trim()) params.q = search.trim();
      const response = await api.getInbox(params);
      setItems(response.items);
      setTotal(response.total);
    } catch (error) {
      setToast(error instanceof Error ? error.message : "Could not load inbox");
    } finally {
      setLoading(false);
    }
  }, [minScore, province, resumeCategory, search, status]);

  useEffect(() => {
    const timer = setTimeout(load, 200);
    return () => clearTimeout(timer);
  }, [load]);

  const counts = useMemo(
    () => ({
      recommended: items.filter((item) => (item.fit_score?.score || 0) >= 75).length,
      priority: items.filter((item) => (item.fit_score?.score || 0) >= 85).length,
      profileMissing: items.length > 0 && items.every((item) => !item.fit_score),
    }),
    [items]
  );

  const showToast = (message: string) => {
    setToast(message);
    window.setTimeout(() => setToast(null), 3500);
  };

  const updateStatus = async (item: InboxJob, nextStatus: InboxStatus) => {
    try {
      const updated = await api.updateInboxStatus(item.id, nextStatus);
      if (status && status !== nextStatus) {
        setItems((current) => current.filter((entry) => entry.id !== item.id));
      } else {
        setItems((current) => current.map((entry) => (entry.id === item.id ? updated : entry)));
      }
      showToast(nextStatus === "applied" ? "Added to your application tracker" : `Moved to ${STATUS_LABELS[nextStatus]}`);
    } catch (error) {
      showToast(error instanceof Error ? error.message : "Could not update job");
    }
  };

  const updateCategory = async (item: InboxJob, category: string) => {
    try {
      const updated = await api.updateInboxResumeCategory(item.id, category);
      setItems((current) => current.map((entry) => (entry.id === item.id ? updated : entry)));
    } catch (error) {
      showToast(error instanceof Error ? error.message : "Could not update resume category");
    }
  };

  const generateResume = async (item: InboxJob) => {
    setGeneratingId(item.id);
    try {
      const result = await api.generateInboxResume(item.id, {
        category: item.user_selected_category || undefined,
      });
      router.push(`/resumes/${result.resume_id}`);
    } catch (error) {
      showToast(error instanceof Error ? error.message : "Could not generate resume");
      setGeneratingId(null);
    }
  };

  const addToTracker = async (item: InboxJob) => {
    setTrackingId(item.id);
    try {
      const application = await api.quickSaveJob(item.job.id);
      setItems((current) =>
        current.map((entry) =>
          entry.id === item.id
            ? { ...entry, application_id: application.id, tracker_summary: "To apply" }
            : entry
        )
      );
      showToast("Added to Tracker · To Apply");
    } catch (error) {
      showToast(error instanceof Error ? error.message : "Could not add job to tracker");
    } finally {
      setTrackingId(null);
    }
  };

  const rescore = async () => {
    setLoading(true);
    try {
      const result = await api.rescoreInbox();
      showToast(`Updated fit scores for ${result.scored} jobs`);
      await load();
    } catch (error) {
      showToast(error instanceof Error ? error.message : "Could not update scores");
      setLoading(false);
    }
  };

  return (
    <div>
      <PageHeader
        title="Job Inbox"
        description="Review opportunities before they enter your application pipeline."
        action={
          <div className="flex gap-2">
            <button className="btn-secondary" onClick={rescore} disabled={loading}><RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} /> Rescore</button>
            <button className="btn-primary" onClick={() => setAddOpen(true)}><Plus className="h-4 w-4" /> Add job</button>
          </div>
        }
      />

      <div className="mb-6 grid gap-3 sm:grid-cols-3">
        <InboxMetric label="Showing" value={total} detail="matching opportunities" />
        <InboxMetric label="Recommended" value={counts.recommended} detail="score 75 or higher" />
        <InboxMetric label="Priority" value={counts.priority} detail="score 85 or higher" />
      </div>

      <div className="mb-5 flex flex-wrap gap-3 rounded-xl border border-border bg-card/60 p-3">
        <div className="relative min-w-[240px] flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            className="input-field pl-10"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search title, company, or skill"
          />
        </div>
        <FilterSelect value={status} onChange={(value) => setStatus(value as InboxStatus | "")}>
          {STATUS_OPTIONS.map((option) => (
            <option key={option.value || "active"} value={option.value}>{option.label}</option>
          ))}
        </FilterSelect>
        <button type="button" className="btn-secondary" onClick={() => setFiltersOpen((open) => !open)}>
          <SlidersHorizontal className="h-4 w-4" /> Filters
        </button>
        {filtersOpen && <>
          <FilterSelect value={province} onChange={setProvince}>
            <option value="">All target provinces</option>
            <option value="AB">Alberta</option>
            <option value="BC">British Columbia</option>
            <option value="ON">Ontario</option>
            <option value="SK">Saskatchewan</option>
          </FilterSelect>
          <FilterSelect value={minScore} onChange={setMinScore}>
            <option value="">Any fit score</option>
            <option value="60">60+ Reviewed</option>
            <option value="75">75+ Recommended</option>
            <option value="85">85+ Priority</option>
          </FilterSelect>
          <FilterSelect value={resumeCategory} onChange={setResumeCategory}>
            <option value="">Any resume category</option>
            {Object.entries(CATEGORY_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </FilterSelect>
        </>}
      </div>

      {toast && <div className="mb-4 rounded-lg border border-primary/30 bg-primary/10 px-4 py-3 text-sm text-primary">{toast}</div>}

      {counts.profileMissing && (
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border bg-card/70 px-4 py-3 text-sm">
          <span className="text-muted-foreground">Fit scores appear after you add real skills or experience to your profile.</span>
          <Link href="/profile" className="font-semibold text-primary hover:underline">Complete profile</Link>
        </div>
      )}

      {loading ? (
        <div className="glass-panel flex items-center justify-center py-20 text-sm text-muted-foreground">
          <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Loading inbox
        </div>
      ) : items.length === 0 ? (
        <div className="glass-panel flex flex-col items-center px-6 py-20 text-center">
          <div className="rounded-2xl bg-primary/10 p-4 ring-1 ring-primary/20">
            <InboxIcon className="h-7 w-7 text-primary" />
          </div>
          <h2 className="mt-5 font-medium text-foreground">Your inbox is clear</h2>
          <p className="mt-1 max-w-sm text-sm text-muted-foreground">Paste a job or import a listing URL. It will be normalized and checked for duplicates automatically.</p>
          <button className="btn-secondary mt-5" onClick={() => setAddOpen(true)}><Plus className="h-4 w-4" /> Add first job</button>
        </div>
      ) : (
        <div className="space-y-3">
          {items.map((item) => <InboxCard key={item.id} item={item} onStatus={updateStatus} onCategory={updateCategory} onGenerate={generateResume} onTrack={addToTracker} generating={generatingId === item.id} tracking={trackingId === item.id} />)}
        </div>
      )}

      {addOpen && <AddJobDialog onClose={() => setAddOpen(false)} onAdded={(item) => { setItems((current) => [item, ...current]); setTotal((value) => value + 1); setAddOpen(false); showToast("Job added to inbox"); }} />}
    </div>
  );
}

function InboxMetric({ label, value, detail }: { label: string; value: number; detail: string }) {
  return <div className="glass-panel px-5 py-4"><p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">{label}</p><div className="mt-1 flex items-baseline gap-2"><span className="text-2xl font-semibold text-foreground">{value}</span><span className="text-xs text-muted-foreground">{detail}</span></div></div>;
}

function FilterSelect({ value, onChange, children }: { value: string; onChange: (value: string) => void; children: React.ReactNode }) {
  return <div className="relative"><select className="input-field min-w-[170px] appearance-none pr-9" value={value} onChange={(event) => onChange(event.target.value)}>{children}</select><ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" /></div>;
}

function InboxCard({ item, onStatus, onCategory, onGenerate, onTrack, generating, tracking }: { item: InboxJob; onStatus: (item: InboxJob, status: InboxStatus) => void; onCategory: (item: InboxJob, category: string) => void; onGenerate: (item: InboxJob) => void; onTrack: (item: InboxJob) => void; generating: boolean; tracking: boolean }) {
  const { job } = item;
  const fit = item.fit_score;
  const [fitOpen, setFitOpen] = useState(false);
  return (
    <article className="glass-panel-hover p-5">
      <div className="flex flex-wrap items-start gap-4">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-muted/70 ring-1 ring-border/70"><BriefcaseBusiness className="h-5 w-5 text-primary" /></div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="font-semibold text-foreground">
              <a
                href={job.apply_url || job.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 underline-offset-4 transition-colors hover:text-primary hover:underline"
                title="Open original job listing"
              >
                {job.title}
                <ArrowUpRight className="h-3.5 w-3.5 shrink-0" />
              </a>
            </h2>
            <span className="rounded-full bg-primary/10 px-2 py-0.5 text-[11px] font-medium text-primary ring-1 ring-inset ring-primary/20">{STATUS_LABELS[item.status]}</span>
          </div>
          <p className="mt-0.5 text-sm text-muted-foreground">{job.company}</p>
          <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-muted-foreground">
            {(job.city || job.province || job.location) && <span className="flex items-center gap-1.5"><MapPin className="h-3.5 w-3.5" />{[job.city, job.province].filter(Boolean).join(", ") || job.location}</span>}
            <span className="capitalize">{job.remote_type || (job.is_remote ? "remote" : "onsite")}</span>
            <span className="capitalize">via {item.captured_via.replace("_", " ")}</span>
          </div>
          {job.skills?.length ? <div className="mt-3 flex flex-wrap gap-1.5">{job.skills.slice(0, 6).map((skill) => <span key={skill} className="rounded-md bg-muted/70 px-2 py-1 text-[11px] text-muted-foreground">{skill}</span>)}</div> : null}
          {fit ? (
            <div className="mt-4 rounded-lg border border-border bg-background/40 p-3">
              <div className="flex flex-wrap items-center gap-2">
                <span className={`rounded-full px-2.5 py-1 text-xs font-semibold capitalize ring-1 ring-inset ${FIT_STYLES[fit.label]}`}>{fit.score} · {fit.label}</span>
                {fit.recommended_category && <span className="flex items-center gap-1.5 text-xs text-muted-foreground"><Target className="h-3.5 w-3.5 text-primary" />{CATEGORY_LABELS[fit.recommended_category] || fit.recommended_category}</span>}
                {fit.risk_flags.length > 0 && <span className="flex items-center gap-1.5 text-xs text-amber-300"><ShieldAlert className="h-3.5 w-3.5" />{fit.risk_flags.map((flag) => flag.replaceAll("_", " ")).join(", ")}</span>}
                <button type="button" onClick={() => setFitOpen((open) => !open)} className="ml-auto flex items-center gap-1 text-xs font-medium text-primary hover:underline">
                  <Info className="h-3.5 w-3.5" /> {fitOpen ? "Hide details" : "Why this score"}
                </button>
              </div>
              {fitOpen && (
                <div className="mt-3 border-t border-border/70 pt-3">
                  <p className="text-xs leading-relaxed text-muted-foreground">{fit.explanation}</p>
                  {(fit.matched_skills.length > 0 || fit.missing_skills.length > 0) && <div className="mt-2 flex flex-wrap gap-1.5">{fit.matched_skills.slice(0, 5).map((skill) => <span key={`matched-${skill}`} className="rounded bg-success/10 px-1.5 py-0.5 text-[10px] text-success">✓ {skill}</span>)}{fit.missing_skills.slice(0, 4).map((skill) => <span key={`missing-${skill}`} className="rounded bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground">gap: {skill}</span>)}</div>}
                </div>
              )}
            </div>
          ) : null}
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => onTrack(item)} disabled={tracking || Boolean(item.application_id)} className="btn-primary whitespace-nowrap">
            <ListPlus className="h-4 w-4" /> {item.application_id ? item.tracker_summary || "In Tracker" : tracking ? "Adding…" : "To Apply"}
          </button>
          {item.status !== "shortlisted" && item.status !== "applied" && <button className="btn-secondary" onClick={() => onStatus(item, "shortlisted")}><Sparkles className="h-4 w-4" /> Shortlist</button>}
          {item.status === "shortlisted" && <button className="btn-primary" onClick={() => onStatus(item, "applied")}><Check className="h-4 w-4" /> Mark applied</button>}
          {item.status !== "archived" && <button onClick={() => onStatus(item, "archived")} className="rounded-lg p-2 text-muted-foreground transition hover:bg-muted hover:text-foreground" title="Archive"><Archive className="h-4 w-4" /></button>}
        </div>
      </div>
      {(item.status === "shortlisted" || item.status === "resume_ready") && (
        <div className="mt-4 flex flex-wrap items-center gap-3 border-t border-border/70 pt-4">
          <div className="min-w-[220px] flex-1">
            <label className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">Resume category</label>
            <div className="relative mt-1">
              <select className="input-field appearance-none pr-9" value={item.user_selected_category || item.ai_recommended_category || "it_support"} onChange={(event) => onCategory(item, event.target.value)} disabled={Boolean(item.resume_id)}>
                {Object.entries(CATEGORY_LABELS).map(([value, label]) => <option key={value} value={value}>{label}{value === item.ai_recommended_category ? " · recommended" : ""}</option>)}
              </select>
              <ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            </div>
          </div>
          {item.resume_id ? (
            <Link href={`/resumes/${item.resume_id}`} className="btn-primary self-end"><FileText className="h-4 w-4" /> Open tailored resume</Link>
          ) : (
            <button onClick={() => onGenerate(item)} disabled={generating} className="btn-primary self-end">{generating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}{generating ? "Generating..." : "Generate tailored resume"}</button>
          )}
        </div>
      )}
    </article>
  );
}

function AddJobDialog({ onClose, onAdded }: { onClose: () => void; onAdded: (item: InboxJob) => void }) {
  const [mode, setMode] = useState<"paste" | "url">("paste");
  const [form, setForm] = useState<InboxManualCreate>(EMPTY_FORM);
  const [url, setUrl] = useState("");
  const [skills, setSkills] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const item = mode === "url" ? await api.importInboxUrl(url) : await api.addInboxJob({ ...form, skills: skills.split(",").map((item) => item.trim()).filter(Boolean) });
      onAdded(item);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not add job");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <div className="w-full max-w-xl rounded-2xl border border-border bg-card p-6 shadow-2xl shadow-black/50">
        <div className="flex items-center justify-between"><div><h2 className="text-lg font-semibold text-foreground">Add to Job Inbox</h2><p className="mt-1 text-sm text-muted-foreground">Capture now, decide whether to apply later.</p></div><button onClick={onClose} className="rounded-lg p-2 text-muted-foreground hover:bg-muted hover:text-foreground"><X className="h-4 w-4" /></button></div>
        <div className="mt-5 grid grid-cols-2 rounded-lg bg-background/80 p-1">
          <button type="button" onClick={() => setMode("paste")} className={`rounded-md px-3 py-2 text-sm font-medium ${mode === "paste" ? "bg-muted text-foreground" : "text-muted-foreground"}`}><BriefcaseBusiness className="mr-2 inline h-4 w-4" />Paste details</button>
          <button type="button" onClick={() => setMode("url")} className={`rounded-md px-3 py-2 text-sm font-medium ${mode === "url" ? "bg-muted text-foreground" : "text-muted-foreground"}`}><Link2 className="mr-2 inline h-4 w-4" />Import URL</button>
        </div>
        <form className="mt-5 space-y-4" onSubmit={submit}>
          {mode === "url" ? <label className="block text-sm text-muted-foreground">Job listing URL<input autoFocus required type="url" className="input-field mt-2" value={url} onChange={(event) => setUrl(event.target.value)} placeholder="https://company.com/jobs/..." /></label> : <>
            <div className="grid gap-4 sm:grid-cols-2"><TextField label="Job title" value={form.title} required onChange={(title) => setForm({ ...form, title })} /><TextField label="Company" value={form.company} required onChange={(company) => setForm({ ...form, company })} /></div>
            <TextField label="Application URL" type="url" value={form.apply_url} required onChange={(apply_url) => setForm({ ...form, apply_url })} />
            <div className="grid gap-4 sm:grid-cols-2"><TextField label="Location" value={form.location || ""} onChange={(location) => setForm({ ...form, location })} /><TextField label="Skills (comma separated)" value={skills} onChange={setSkills} /></div>
            <label className="block text-sm text-muted-foreground">Description<textarea className="input-field mt-2 min-h-28 resize-y" value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} placeholder="Paste the job description" /></label>
          </>}
          {error && <p className="rounded-lg border border-red-500/20 bg-red-500/10 px-3 py-2 text-sm text-red-300">{error}</p>}
          <div className="flex justify-end gap-3 pt-1"><button type="button" className="btn-secondary" onClick={onClose}>Cancel</button><button className="btn-primary" disabled={saving}>{saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}{saving ? "Adding..." : "Add to inbox"}</button></div>
        </form>
      </div>
    </div>
  );
}

function TextField({ label, value, onChange, required, type = "text" }: { label: string; value: string; onChange: (value: string) => void; required?: boolean; type?: string }) {
  return <label className="block text-sm text-muted-foreground">{label}<input type={type} required={required} className="input-field mt-2" value={value} onChange={(event) => onChange(event.target.value)} /></label>;
}
