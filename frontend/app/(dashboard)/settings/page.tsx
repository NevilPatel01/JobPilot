"use client";

import { useEffect, useState } from "react";
import { Save, Key, Trash2, Copy } from "lucide-react";
import { api } from "@/lib/api";
import type { ApiKeyConfig, ApiToken } from "@/types/resume";
import { PageHeader } from "@/components/ui/PageHeader";

const PROVIDERS = [
  { id: "openai", label: "OpenAI", defaultModel: "gpt-4o-mini", defaultEmbedding: "text-embedding-3-small" },
  { id: "custom", label: "Custom (OpenAI-compatible)", defaultModel: "gpt-4o-mini", defaultEmbedding: "text-embedding-3-small" },
];

export default function SettingsPage() {
  const [keys, setKeys] = useState<ApiKeyConfig[]>([]);
  const [tokens, setTokens] = useState<ApiToken[]>([]);
  const [provider, setProvider] = useState("openai");
  const [apiKey, setApiKey] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [modelName, setModelName] = useState("gpt-4o-mini");
  const [embeddingModel, setEmbeddingModel] = useState("text-embedding-3-small");
  const [tokenName, setTokenName] = useState("");
  const [newToken, setNewToken] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);

  const load = () => {
    api.getApiKeys().then(setKeys).catch(console.error);
    api.getApiTokens().then(setTokens).catch(console.error);
  };

  useEffect(() => { load(); }, []);

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
      load();
    } finally {
      setSaving(false);
    }
  };

  const testKey = async () => {
    if (!apiKey) return;
    setTesting(true);
    try {
      await api.testApiKey({ provider, api_key: apiKey, base_url: baseUrl || undefined, model_name: modelName, embedding_model: embeddingModel });
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

  return (
    <div>
      <PageHeader
        title="API Settings"
        description="Configure your LLM API keys (BYOK) and generate API tokens for external integrations"
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="glass-panel p-6">
          <div className="flex items-center gap-2">
            <Key className="h-4 w-4 text-indigo-400" />
            <h2 className="text-sm font-semibold text-white">LLM API Keys</h2>
          </div>
          <p className="mt-1 text-xs text-zinc-500">Your keys are encrypted at rest. JobPilot never shares them.</p>

          <div className="mt-4 space-y-3">
            <select className="input-field" value={provider} onChange={(e) => setProvider(e.target.value)}>
              {PROVIDERS.map((p) => <option key={p.id} value={p.id}>{p.label}</option>)}
            </select>
            <input className="input-field" type="password" placeholder="API Key" value={apiKey} onChange={(e) => setApiKey(e.target.value)} />
            {provider === "custom" && (
              <input className="input-field" placeholder="Base URL (e.g. https://api.groq.com/openai/v1)" value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)} />
            )}
            <input className="input-field" placeholder="Model name" value={modelName} onChange={(e) => setModelName(e.target.value)} />
            <input className="input-field" placeholder="Embedding model" value={embeddingModel} onChange={(e) => setEmbeddingModel(e.target.value)} />
            <div className="flex gap-2">
              <button onClick={testKey} disabled={testing || !apiKey} className="btn-secondary flex-1">{testing ? "Testing..." : "Test Key"}</button>
              <button onClick={saveKey} disabled={saving || !apiKey} className="btn-primary flex-1">
                <Save className="h-4 w-4" /> Save
              </button>
            </div>
          </div>

          {keys.length > 0 && (
            <div className="mt-6 space-y-2">
              <h3 className="text-xs font-medium text-zinc-400">Saved keys</h3>
              {keys.map((k) => (
                <div key={k.id} className="flex items-center justify-between rounded-lg bg-zinc-800/40 px-3 py-2 text-sm">
                  <div>
                    <span className="text-white">{k.provider}</span>
                    <span className="ml-2 text-zinc-500">{k.model_name}</span>
                    {k.is_default && <span className="ml-2 text-xs text-indigo-400">default</span>}
                  </div>
                  <button onClick={() => api.deleteApiKey(k.id).then(load)} className="text-zinc-500 hover:text-red-400">
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="glass-panel p-6">
          <h2 className="text-sm font-semibold text-white">Public API Tokens</h2>
          <p className="mt-1 text-xs text-zinc-500">Use with X-API-Key header on /api/v1/documents/* endpoints</p>

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
              <div key={t.id} className="flex items-center justify-between rounded-lg bg-zinc-800/40 px-3 py-2 text-sm">
                <div>
                  <span className="text-white">{t.name}</span>
                  <span className="ml-2 font-mono text-xs text-zinc-500">{t.token_prefix}...</span>
                </div>
                <button onClick={() => api.deleteApiToken(t.id).then(load)} className="text-zinc-500 hover:text-red-400">
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
