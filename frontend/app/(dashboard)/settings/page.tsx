"use client";

import { useCallback, useEffect, useState } from "react";
import { Save, Key, Trash2, Copy, Sparkles, MapPinned, Radar } from "lucide-react";
import { api } from "@/lib/api";
import type { ApiKeyConfig, ApiToken } from "@/types/resume";
import { PageHeader } from "@/components/ui/PageHeader";
import { AUTO_MODEL, LLM_PRESETS, getProviderPreset } from "@/lib/llmPresets";
import type { ScoringPreferences } from "@/types";

const TARGET_PROVINCES = [
  { code: "AB", label: "Alberta" },
  { code: "BC", label: "British Columbia" },
  { code: "ON", label: "Ontario" },
  { code: "SK", label: "Saskatchewan" },
];

export default function SettingsPage() {
  const [keys, setKeys] = useState<ApiKeyConfig[]>([]);
  const [tokens, setTokens] = useState<ApiToken[]>([]);
  const [provider, setProvider] = useState("openai");
  const [apiKey, setApiKey] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [modelName, setModelName] = useState(AUTO_MODEL);
  const [embeddingModel, setEmbeddingModel] = useState(AUTO_MODEL);
  const [fetchedChatModels, setFetchedChatModels] = useState<string[]>([]);
  const [fetchedEmbedModels, setFetchedEmbedModels] = useState<string[]>([]);
  const [autoReason, setAutoReason] = useState<string | null>(null);
  const [tokenName, setTokenName] = useState("");
  const [newToken, setNewToken] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [probing, setProbing] = useState(false);
  const [scoringPrefs, setScoringPrefs] = useState<ScoringPreferences | null>(null);
  const [savingPrefs, setSavingPrefs] = useState(false);
  const [prefsSaved, setPrefsSaved] = useState(false);
  const [jobBankEnabled, setJobBankEnabled] = useState<boolean | null>(null);
  const [togglingJobBank, setTogglingJobBank] = useState(false);

  const preset = getProviderPreset(provider);

  const load = () => {
    api.getApiKeys().then(setKeys).catch(console.error);
    api.getApiTokens().then(setTokens).catch(console.error);
    api.getScoringPreferences().then(setScoringPrefs).catch(console.error);
    api
      .getScraperSources()
      .then((data) => {
        const jobBank = data.sources.find((s) => s.source === "job_bank");
        setJobBankEnabled(jobBank ? jobBank.enabled : true);
      })
      .catch(console.error);
  };

  useEffect(() => { load(); }, []);

  useEffect(() => {
    if (apiKey.startsWith("sk-ant-")) setProvider("anthropic");
    else if (apiKey.startsWith("sk-or-v1-")) setProvider("custom");
    else if (apiKey.startsWith("sk-")) setProvider("openai");
  }, [apiKey]);

  useEffect(() => {
    setModelName(AUTO_MODEL);
    setEmbeddingModel(AUTO_MODEL);
    setFetchedChatModels([]);
    setFetchedEmbedModels([]);
    setAutoReason(null);
  }, [provider]);

  const probeModels = useCallback(async () => {
    if (!apiKey) return;
    setProbing(true);
    try {
      const models = await api.probeApiKeyModels({ provider, api_key: apiKey, base_url: baseUrl || undefined });
      setFetchedChatModels(models.chat_models);
      setFetchedEmbedModels(models.embedding_models);
      const auto = await api.autoSelectApiKeyModels({ provider, api_key: apiKey, base_url: baseUrl || undefined });
      setAutoReason(auto.reason);
    } catch {
      setFetchedChatModels([]);
      setFetchedEmbedModels([]);
      setAutoReason(null);
    } finally {
      setProbing(false);
    }
  }, [apiKey, baseUrl, provider]);

  useEffect(() => {
    if (!apiKey || apiKey.length < 8) return;
    const timer = setTimeout(() => { probeModels().catch(console.error); }, 600);
    return () => clearTimeout(timer);
  }, [apiKey, baseUrl, provider, probeModels]);

  const chatOptions = [
    ...preset.models,
    ...fetchedChatModels
      .filter((m) => !preset.models.some((p) => p.id === m))
      .map((m) => ({ id: m, label: m })),
  ];

  const embedOptions = [
    ...preset.embeddings,
    ...fetchedEmbedModels
      .filter((m) => !preset.embeddings.some((p) => p.id === m))
      .map((m) => ({ id: m, label: m })),
  ];

  const saveKey = async () => {
    if (!apiKey) return;
    setSaving(true);
    try {
      await api.upsertApiKey({
        provider,
        api_key: apiKey,
        base_url: baseUrl || undefined,
        model_name: modelName,
        embedding_model: embeddingModel,
        is_default: true,
      });
      setApiKey("");
      setAutoReason(null);
      load();
    } finally {
      setSaving(false);
    }
  };

  const testKey = async () => {
    if (!apiKey) return;
    setTesting(true);
    try {
      await api.testApiKey({
        provider,
        api_key: apiKey,
        base_url: baseUrl || undefined,
        model_name: modelName,
        embedding_model: embeddingModel,
      });
      alert("API key is valid!");
    } catch {
      alert("API key validation failed");
    } finally {
      setTesting(false);
    }
  };

  const createToken = async () => {
    if (!tokenName) return;
    const result = await api.createApiToken(tokenName);
    setNewToken(result.token);
    setTokenName("");
    load();
  };

  const toggleProvince = (code: string) => {
    if (!scoringPrefs) return;
    const selected = scoringPrefs.target_provinces.includes(code);
    setScoringPrefs({
      ...scoringPrefs,
      target_provinces: selected
        ? scoringPrefs.target_provinces.filter((province) => province !== code)
        : [...scoringPrefs.target_provinces, code],
    });
  };

  const saveScoringPreferences = async () => {
    if (!scoringPrefs || scoringPrefs.target_provinces.length === 0) return;
    setSavingPrefs(true);
    try {
      const saved = await api.updateScoringPreferences({
        work_authorization: scoringPrefs.work_authorization,
        target_provinces: scoringPrefs.target_provinces,
        relocation_open: scoringPrefs.relocation_open,
        threshold_overrides: scoringPrefs.threshold_overrides,
      });
      setScoringPrefs(saved);
      setPrefsSaved(true);
      window.setTimeout(() => setPrefsSaved(false), 2500);
    } finally {
      setSavingPrefs(false);
    }
  };

  const toggleJobBank = async (enabled: boolean) => {
    setTogglingJobBank(true);
    try {
      const result = await api.updateScraperSource("job_bank", enabled);
      setJobBankEnabled(result.enabled);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Could not update Job Bank source");
    } finally {
      setTogglingJobBank(false);
    }
  };

  const thresholdValue = (key: string, fallback: number) => scoringPrefs?.threshold_overrides?.[key] ?? fallback;

  const updateThreshold = (key: string, value: number) => {
    if (!scoringPrefs) return;
    setScoringPrefs({
      ...scoringPrefs,
      threshold_overrides: {
        low_max: thresholdValue("low_max", 39),
        stretch_max: thresholdValue("stretch_max", 59),
        reviewed_max: thresholdValue("reviewed_max", 74),
        recommended_max: thresholdValue("recommended_max", 84),
        [key]: value,
      },
    });
  };

  return (
    <div>
      <PageHeader
        title="API Settings"
        description="Configure your LLM API keys (BYOK) and generate API tokens for external integrations"
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="glass-panel p-6 lg:col-span-2">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="flex gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 ring-1 ring-primary/20">
                <MapPinned className="h-4 w-4 text-primary" />
              </div>
              <div>
                <h2 className="text-sm font-semibold text-foreground">Job fit preferences</h2>
                <p className="mt-1 text-xs text-muted-foreground">Used to prioritize Canadian opportunities with the strongest hiring and PR fit.</p>
              </div>
            </div>
            <button onClick={saveScoringPreferences} disabled={savingPrefs || !scoringPrefs || scoringPrefs.target_provinces.length === 0} className="btn-primary">
              <Save className="h-4 w-4" /> {savingPrefs ? "Saving..." : prefsSaved ? "Saved" : "Save preferences"}
            </button>
          </div>

          {scoringPrefs ? (
            <div className="mt-5 grid gap-5 md:grid-cols-[220px_1fr_auto]">
              <label className="text-xs font-medium text-muted-foreground">
                Work authorization
                <select className="input-field mt-2" value={scoringPrefs.work_authorization} onChange={(event) => setScoringPrefs({ ...scoringPrefs, work_authorization: event.target.value })}>
                  <option value="work_permit">Work permit</option>
                  <option value="permanent_resident">Permanent resident</option>
                  <option value="citizen">Canadian citizen</option>
                  <option value="requires_sponsorship">Requires sponsorship</option>
                </select>
              </label>
              <div>
                <p className="text-xs font-medium text-muted-foreground">Target provinces</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {TARGET_PROVINCES.map((province) => {
                    const selected = scoringPrefs.target_provinces.includes(province.code);
                    return <button key={province.code} type="button" onClick={() => toggleProvince(province.code)} className={`rounded-lg border px-3 py-2 text-sm transition ${selected ? "border-primary/40 bg-primary/10 text-primary" : "border-border bg-background/50 text-muted-foreground hover:border-border"}`}><span className="font-semibold">{province.code}</span><span className="ml-1.5 text-xs opacity-70">{province.label}</span></button>;
                  })}
                </div>
              </div>
              <label className="flex items-center gap-3 self-end rounded-lg border border-border bg-background/50 px-4 py-2.5 text-sm text-muted-foreground">
                <input type="checkbox" checked={scoringPrefs.relocation_open} onChange={(event) => setScoringPrefs({ ...scoringPrefs, relocation_open: event.target.checked })} className="h-4 w-4 accent-primary" />
                Open to relocation
              </label>
              <div className="md:col-span-3">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-xs font-medium text-muted-foreground">Fit score upper bounds</p>
                  <button type="button" className="text-xs text-muted-foreground transition hover:text-foreground" onClick={() => setScoringPrefs({ ...scoringPrefs, threshold_overrides: null })}>Reset defaults</button>
                </div>
                <div className="mt-2 grid grid-cols-2 gap-3 md:grid-cols-4">
                  {[
                    ["low_max", "Low", 39],
                    ["stretch_max", "Stretch", 59],
                    ["reviewed_max", "Reviewed", 74],
                    ["recommended_max", "Recommended", 84],
                  ].map(([key, label, fallback]) => (
                    <label key={String(key)} className="rounded-lg border border-border bg-background/50 px-3 py-2 text-xs text-muted-foreground">
                      {label}
                      <input type="number" min="0" max="99" className="mt-1 w-full bg-transparent text-base font-semibold text-foreground outline-none" value={thresholdValue(String(key), Number(fallback))} onChange={(event) => updateThreshold(String(key), Number(event.target.value))} />
                    </label>
                  ))}
                </div>
              </div>
            </div>
          ) : <p className="mt-5 text-sm text-muted-foreground">Loading preferences...</p>}
        </div>

        <div className="glass-panel p-6 lg:col-span-2">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="flex gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 ring-1 ring-primary/20">
                <Radar className="h-4 w-4 text-primary" />
              </div>
              <div>
                <h2 className="text-sm font-semibold text-foreground">Job sources</h2>
                <p className="mt-1 text-xs text-muted-foreground">
                  Disable Job Bank Canada scraping if those postings rarely lead to interviews.
                </p>
              </div>
            </div>
            <label className="flex items-center gap-3 rounded-lg border border-border bg-background/50 px-4 py-2.5 text-sm text-muted-foreground">
              <input
                type="checkbox"
                checked={jobBankEnabled === true}
                disabled={jobBankEnabled === null || togglingJobBank}
                onChange={(event) => toggleJobBank(event.target.checked)}
                className="h-4 w-4 accent-primary"
              />
              {togglingJobBank
                ? "Updating…"
                : jobBankEnabled
                  ? "Job Bank scraping on"
                  : "Job Bank scraping off"}
            </label>
          </div>
        </div>

        <div className="glass-panel p-6">
          <div className="flex items-center gap-2">
            <Key className="h-4 w-4 text-primary" />
            <h2 className="text-sm font-semibold text-foreground">LLM API Keys</h2>
          </div>
          <p className="mt-1 text-xs text-muted-foreground">Your keys are encrypted at rest. JobPilot never shares them.</p>

          <div className="mt-4 space-y-3">
            <select className="input-field" value={provider} onChange={(e) => setProvider(e.target.value)}>
              {LLM_PRESETS.map((p) => <option key={p.id} value={p.id}>{p.label}</option>)}
            </select>
            <input className="input-field" type="password" placeholder="API Key" value={apiKey} onChange={(e) => setApiKey(e.target.value)} />
            {provider === "custom" && (
              <input className="input-field" placeholder="Base URL (e.g. https://api.groq.com/openai/v1)" value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)} />
            )}
            <div>
              <label className="mb-1 block text-xs text-muted-foreground">Chat model</label>
              <select className="input-field" value={modelName} onChange={(e) => setModelName(e.target.value)} disabled={probing}>
                {chatOptions.map((m) => <option key={m.id} value={m.id}>{m.label}</option>)}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-xs text-muted-foreground">Embedding model</label>
              <select className="input-field" value={embeddingModel} onChange={(e) => setEmbeddingModel(e.target.value)} disabled={probing}>
                {embedOptions.map((m) => <option key={m.id} value={m.id}>{m.label}</option>)}
              </select>
            </div>
            {probing && (
              <p className="text-xs text-muted-foreground">Detecting available models...</p>
            )}
            {autoReason && (modelName === AUTO_MODEL || embeddingModel === AUTO_MODEL) && (
              <p className="flex items-start gap-1.5 text-xs text-primary">
                <Sparkles className="mt-0.5 h-3 w-3 shrink-0" />
                {autoReason}
              </p>
            )}
            <div className="flex gap-2">
              <button onClick={testKey} disabled={testing || !apiKey} className="btn-secondary flex-1">{testing ? "Testing..." : "Test Key"}</button>
              <button onClick={saveKey} disabled={saving || !apiKey} className="btn-primary flex-1">
                <Save className="h-4 w-4" /> Save
              </button>
            </div>
          </div>

          {keys.length > 0 && (
            <div className="mt-6 space-y-2">
              <h3 className="text-xs font-medium text-muted-foreground">Saved keys</h3>
              {keys.map((k) => (
                <div key={k.id} className="flex items-center justify-between rounded-lg bg-muted/40 px-3 py-2 text-sm">
                  <div>
                    <span className="text-foreground">{k.provider}</span>
                    <span className="ml-2 text-muted-foreground">{k.model_name}</span>
                    {k.is_default && <span className="ml-2 text-xs text-primary">default</span>}
                  </div>
                  <button onClick={() => api.deleteApiKey(k.id).then(load)} className="text-muted-foreground hover:text-red-400">
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="glass-panel p-6">
          <h2 className="text-sm font-semibold text-foreground">Public API Tokens</h2>
          <p className="mt-1 text-xs text-muted-foreground">Use with X-API-Key header on /api/v1/documents/* endpoints</p>

          <div className="mt-4 flex gap-2">
            <input className="input-field flex-1" placeholder="Token name" value={tokenName} onChange={(e) => setTokenName(e.target.value)} />
            <button onClick={createToken} className="btn-primary">Create</button>
          </div>

          {newToken && (
            <div className="mt-3 rounded-lg bg-emerald-500/10 p-3 text-sm text-emerald-300">
              <p className="font-medium">Copy your token now — it won&apos;t be shown again:</p>
              <code className="mt-1 block break-all text-xs">{newToken}</code>
              <button onClick={() => navigator.clipboard.writeText(newToken)} className="btn-secondary mt-2 text-xs">
                <Copy className="h-3 w-3" /> Copy
              </button>
            </div>
          )}

          <div className="mt-4 space-y-2">
            {tokens.map((t) => (
              <div key={t.id} className="flex items-center justify-between rounded-lg bg-muted/40 px-3 py-2 text-sm">
                <div>
                  <span className="text-foreground">{t.name}</span>
                  <span className="ml-2 font-mono text-xs text-muted-foreground">{t.token_prefix}...</span>
                </div>
                <button onClick={() => api.deleteApiToken(t.id).then(load)} className="text-muted-foreground hover:text-red-400">
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
