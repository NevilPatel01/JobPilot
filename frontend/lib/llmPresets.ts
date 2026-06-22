export const AUTO_MODEL = "auto";

export type LlmProviderId = "openai" | "anthropic" | "custom";

export interface ModelOption {
  id: string;
  label: string;
}

export interface ProviderPreset {
  id: LlmProviderId;
  label: string;
  models: ModelOption[];
  embeddings: ModelOption[];
}

export const LLM_PRESETS: ProviderPreset[] = [
  {
    id: "openai",
    label: "OpenAI",
    models: [
      { id: AUTO_MODEL, label: "Auto — best cost/quality (recommended)" },
      { id: "gpt-4o-mini", label: "GPT-4o Mini (low cost)" },
      { id: "gpt-4o", label: "GPT-4o (higher quality)" },
      { id: "o1-mini", label: "o1-mini (reasoning)" },
    ],
    embeddings: [
      { id: AUTO_MODEL, label: "Auto — text-embedding-3-small" },
      { id: "text-embedding-3-small", label: "Embedding 3 Small (recommended)" },
      { id: "text-embedding-3-large", label: "Embedding 3 Large" },
    ],
  },
  {
    id: "anthropic",
    label: "Anthropic (Claude)",
    models: [
      { id: AUTO_MODEL, label: "Auto — Claude Haiku (recommended, low cost)" },
      { id: "claude-3-5-haiku-latest", label: "Claude 3.5 Haiku" },
      { id: "claude-3-5-sonnet-latest", label: "Claude 3.5 Sonnet" },
      { id: "claude-3-opus-latest", label: "Claude 3 Opus (premium)" },
    ],
    embeddings: [
      { id: AUTO_MODEL, label: "Auto — keyword search (add OpenAI key for vectors)" },
      { id: "keyword-search", label: "Keyword search (no OpenAI key required)" },
    ],
  },
  {
    id: "custom",
    label: "Custom (OpenAI-compatible)",
    models: [{ id: AUTO_MODEL, label: "Auto — detect from API" }],
    embeddings: [{ id: AUTO_MODEL, label: "Auto — detect from API" }],
  },
];

export function getProviderPreset(id: string): ProviderPreset {
  return LLM_PRESETS.find((p) => p.id === id) ?? LLM_PRESETS[0];
}
