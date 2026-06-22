"use client";

import { useCallback, useEffect, useState } from "react";
import { Save, Key, Trash2, Copy, Sparkles } from "lucide-react";
import { api } from "@/lib/api";
import type { ApiKeyConfig, ApiToken } from "@/types/resume";
import { PageHeader } from "@/components/ui/PageHeader";
import { AUTO_MODEL, LLM_PRESETS, getProviderPreset } from "@/lib/llmPresets";

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

  const preset = getProviderPreset(provider);

  const load = () => {
    api.getApiKeys().then(setKeys).catch(console.error);
    api.getApiTokens().then(setTokens).catch(console.error);
  };

  useEffect(() => { load(); }, []);

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
              {LLM_PRESETS.map((p) => <option key={p.id} value={p.id}>{p.label}</option>)}
            </select>
            <input className="input-field" type="password" placeholder="API Key" value={apiKey} onChange={(e) => setApiKey(e.target.value)} />
            {provider === "custom" && (
              <input className="input-field" placeholder="Base URL (e.g. https://api.groq.com/openai/v1)" value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)} />
            )}
            <div>
              <label className="mb-1 block text-xs text-zinc-500">Chat model</label>
              <select className="input-field" value={modelName} onChange={(e) => setModelName(e.target.value)} disabled={probing}>
                {chatOptions.map((m) => <option key={m.id} value={m.id}>{m.label}</option>)}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-xs text-zinc-500">Embedding model</label>
              <select className="input-field" value={embeddingModel} onChange={(e) => setEmbeddingModel(e.target.value)} disabled={probing}>
                {embedOptions.map((m) => <option key={m.id} value={m.id}>{m.label}</option>)}
              </select>
            </div>
            {probing && (
              <p className="text-xs text-zinc-500">Detecting available models...</p>
            )}
            {autoReason && (modelName === AUTO_MODEL || embeddingModel === AUTO_MODEL) && (
              <p className="flex items-start gap-1.5 text-xs text-indigo-300">
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
