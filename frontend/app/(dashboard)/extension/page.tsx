"use client";

import { useState } from "react";
import Link from "next/link";
import { Check, Copy, Globe2, KeyRound, LockKeyhole, Puzzle, Server, ShieldCheck } from "lucide-react";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/ui/PageHeader";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function ExtensionSetupPage() {
  const [token, setToken] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [copied, setCopied] = useState<string | null>(null);

  const appUrl = typeof window === "undefined" ? "http://localhost:3000" : window.location.origin;

  const createToken = async () => {
    setCreating(true);
    try {
      const result = await api.createApiToken("JobPilot Capture");
      setToken(result.token);
    } finally {
      setCreating(false);
    }
  };

  const copy = async (label: string, value: string) => {
    await navigator.clipboard.writeText(value);
    setCopied(label);
    window.setTimeout(() => setCopied(null), 1800);
  };

  return (
    <div>
      <PageHeader
        title="JobPilot Capture"
        description="Save a job from Chrome to your private Inbox, score it, or mark it applied without retyping the listing."
      />

      <section className="relative overflow-hidden rounded-2xl border border-border bg-card p-7 shadow-sm">
        <div className="absolute -right-20 -top-24 h-64 w-64 rounded-full bg-primary/10 blur-3xl" />
        <div className="relative grid gap-7 lg:grid-cols-[1.25fr_0.75fr] lg:items-center">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/8 px-3 py-1 text-xs font-medium text-primary">
              <Globe2 className="h-3.5 w-3.5" /> Manifest V3 · local install
            </div>
            <h2 className="mt-5 max-w-xl text-2xl font-semibold tracking-tight text-foreground">
              Capture the opportunity while you are reading it.
            </h2>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-muted-foreground">
              The extension reads only the active job page. Your resume and profile stay in JobPilot; Chrome stores only the connection URL and a revocable API token.
            </p>
            <div className="mt-5 flex flex-wrap gap-2 text-xs text-muted-foreground">
              {["LinkedIn", "Indeed", "Job Bank", "Greenhouse", "Lever", "Workday", "Generic pages"].map((source) => (
                <span key={source} className="rounded-md border border-border bg-background/70 px-2.5 py-1.5">{source}</span>
              ))}
            </div>
          </div>
          <div className="rounded-xl border border-border bg-background/70 p-5 backdrop-blur">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary"><Puzzle className="h-5 w-5" /></div>
              <div><p className="text-sm font-semibold text-foreground">Private by design</p><p className="mt-0.5 text-xs text-muted-foreground">No resume data stored locally</p></div>
            </div>
            <div className="mt-4 space-y-2 text-xs text-muted-foreground">
              <p className="flex items-center gap-2"><ShieldCheck className="h-3.5 w-3.5 text-success" /> Token is hashed in JobPilot</p>
              <p className="flex items-center gap-2"><LockKeyhole className="h-3.5 w-3.5 text-success" /> Revoke access at any time</p>
            </div>
          </div>
        </div>
      </section>

      <div className="mt-6 grid gap-5 lg:grid-cols-3">
        <SetupCard number="01" icon={Puzzle} title="Load the extension">
          <p>Open <code>chrome://extensions</code>, enable Developer mode, then choose <strong>Load unpacked</strong>.</p>
          <div className="mt-4 rounded-lg border border-border bg-muted/50 px-3 py-2 font-mono text-xs text-foreground">JobPilot/extension</div>
        </SetupCard>

        <SetupCard number="02" icon={KeyRound} title="Create a capture token">
          <p>Generate a dedicated token. It is shown once and can be deleted from API Settings.</p>
          {token ? (
            <div className="mt-4 rounded-lg border border-success/25 bg-success/8 p-3">
              <p className="break-all font-mono text-xs text-foreground">{token}</p>
              <button onClick={() => copy("token", token)} className="btn-secondary mt-3 w-full text-xs">
                {copied === "token" ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                {copied === "token" ? "Copied" : "Copy token"}
              </button>
            </div>
          ) : (
            <button onClick={createToken} disabled={creating} className="btn-primary mt-4 w-full">
              <KeyRound className="h-4 w-4" /> {creating ? "Creating…" : "Generate extension token"}
            </button>
          )}
        </SetupCard>

        <SetupCard number="03" icon={Server} title="Connect once">
          <p>Open the extension settings and enter these URLs with the token from step two.</p>
          <CopyValue label="API URL" value={API_URL} copied={copied} onCopy={copy} />
          <CopyValue label="App URL" value={appUrl} copied={copied} onCopy={copy} />
        </SetupCard>
      </div>

      <div className="mt-6 flex flex-wrap items-center justify-between gap-4 rounded-xl border border-border bg-card px-5 py-4 text-sm">
        <div><p className="font-medium text-foreground">Need to revoke or replace a token?</p><p className="mt-1 text-xs text-muted-foreground">Manage every extension token from the existing API Settings page.</p></div>
        <Link href="/settings" className="btn-secondary"><KeyRound className="h-4 w-4" /> Open API Settings</Link>
      </div>
    </div>
  );
}

function SetupCard({ number, icon: Icon, title, children }: { number: string; icon: typeof Puzzle; title: string; children: React.ReactNode }) {
  return (
    <section className="glass-panel p-5">
      <div className="flex items-center justify-between"><div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary"><Icon className="h-4 w-4" /></div><span className="font-mono text-xs text-muted-foreground">{number}</span></div>
      <h3 className="mt-5 text-sm font-semibold text-foreground">{title}</h3>
      <div className="mt-2 text-xs leading-5 text-muted-foreground">{children}</div>
    </section>
  );
}

function CopyValue({ label, value, copied, onCopy }: { label: string; value: string; copied: string | null; onCopy: (label: string, value: string) => void }) {
  return (
    <button onClick={() => onCopy(label, value)} className="mt-3 flex w-full items-center justify-between gap-3 rounded-lg border border-border bg-muted/40 px-3 py-2 text-left">
      <span className="min-w-0"><span className="block text-[10px] uppercase tracking-wider text-muted-foreground">{label}</span><span className="block truncate font-mono text-xs text-foreground">{value}</span></span>
      {copied === label ? <Check className="h-3.5 w-3.5 shrink-0 text-success" /> : <Copy className="h-3.5 w-3.5 shrink-0" />}
    </button>
  );
}
