"use client";

import { useCallback, useEffect, useState } from "react";
import { Loader2, Lock, Plus, Trash2 } from "lucide-react";
import { candidateApi, type AnswerBankEntry } from "@/lib/api/candidate";

const CATEGORIES = ["behavioral", "logistics", "salary", "work_authorization", "demographic", "legal_declaration", "other"];
const SENSITIVE = new Set(["salary", "work_authorization", "demographic", "legal_declaration"]);

export function AnswerBankPanel() {
  const [rows, setRows] = useState<AnswerBankEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [question, setQuestion] = useState("");
  const [category, setCategory] = useState("behavioral");
  const [answer, setAnswer] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    try {
      setRows(await candidateApi.listAnswers());
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
      await candidateApi.createAnswer({ question_text: question, question_category: category, answer_text: answer });
      setQuestion("");
      setAnswer("");
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
        <p className="text-sm font-medium text-foreground">Add an application answer</p>
        <p className="mt-0.5 text-xs text-muted-foreground">
          Reusable answers for application forms. Salary, work-authorization, demographic, and legal answers are
          locked as sensitive — they always require your explicit review before use.
        </p>
        <div className="mt-3 space-y-2">
          <input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Question, e.g. “Why do you want to work here?”"
            className="w-full rounded-lg border border-border bg-background/60 px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground"
          />
          <div className="flex gap-2">
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="rounded-lg border border-border bg-background/60 px-3 py-2 text-sm text-foreground"
            >
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>
                  {c.replace(/_/g, " ")}{SENSITIVE.has(c) ? " 🔒" : ""}
                </option>
              ))}
            </select>
            <textarea
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              rows={2}
              placeholder="Your answer"
              className="flex-1 rounded-lg border border-border bg-background/60 p-2 text-sm text-foreground placeholder:text-muted-foreground"
            />
          </div>
        </div>
        {error && <p className="mt-2 text-xs text-destructive">{error}</p>}
        <button onClick={create} disabled={busy || !question.trim()} className="btn-primary mt-3">
          {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
          Save answer
        </button>
      </div>

      <div className="space-y-2">
        {rows.map((row) => (
          <div key={row.id} className="rounded-lg border border-border bg-card/40 p-3">
            <div className="flex items-start justify-between gap-3">
              <p className="text-sm font-medium text-foreground">
                {row.is_sensitive && <Lock className="mr-1.5 inline h-3.5 w-3.5 text-amber-400" />}
                {row.question_text}
              </p>
              <div className="flex shrink-0 items-center gap-2">
                <span className="rounded bg-muted px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-muted-foreground">
                  {row.question_category.replace(/_/g, " ")}
                </span>
                <button
                  title="Delete"
                  onClick={async () => { await candidateApi.deleteAnswer(row.id); reload(); }}
                  className="rounded p-1 text-muted-foreground hover:text-destructive"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
            {row.answer_text && <p className="mt-1 text-xs text-muted-foreground">{row.answer_text}</p>}
            {row.is_sensitive && (
              <p className="mt-1 text-[10px] text-amber-400">Sensitive — always requires review before any use.</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
