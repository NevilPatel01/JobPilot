"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import type { CoverLetterDocument } from "@/types/resume";
import { ResumePreviewFrame } from "@/components/resume/ResumePreviewFrame";

export default function CoverLetterEditorPage() {
  const { id } = useParams<{ id: string }>();
  const [letter, setLetter] = useState<CoverLetterDocument | null>(null);
  const [previewHtml, setPreviewHtml] = useState("");
  const [paragraphs, setParagraphs] = useState("");

  useEffect(() => {
    api.getCoverLetter(id).then((l) => {
      setLetter(l);
      const paras = (l.content_json.paragraphs as string[] | undefined) || [];
      setParagraphs(paras.join("\n\n"));
    }).catch(console.error);
  }, [id]);

  useEffect(() => {
    if (letter) {
      api.getCoverLetterPreviewHtml(id).then(setPreviewHtml).catch(console.error);
    }
  }, [letter, id, paragraphs]);

  const save = async () => {
    if (!letter) return;
    const updated = await api.updateCoverLetter(id, {
      content_json: {
        ...letter.content_json,
        paragraphs: paragraphs.split("\n\n").filter(Boolean),
      },
    });
    setLetter(updated);
  };

  if (!letter) return <div className="text-zinc-500">Loading...</div>;

  return (
    <div>
      <div className="mb-4 flex items-center gap-3">
        <Link href="/cover-letters" className="text-xs text-zinc-500 hover:text-white">← Cover Letters</Link>
        <h1 className="text-lg font-semibold text-white">{letter.title}</h1>
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="glass-panel p-4">
          <label className="text-xs text-zinc-400">Letter body (paragraphs separated by blank line)</label>
          <textarea
            className="input-field mt-2 min-h-[400px]"
            value={paragraphs}
            onChange={(e) => setParagraphs(e.target.value)}
            onBlur={save}
          />
        </div>
        <div className="glass-panel p-4">
          <p className="text-xs uppercase tracking-widest text-indigo-400">Cover Letter Preview</p>
          <div className="mt-3 h-[500px]">
            <ResumePreviewFrame html={previewHtml} />
          </div>
        </div>
      </div>
    </div>
  );
}
