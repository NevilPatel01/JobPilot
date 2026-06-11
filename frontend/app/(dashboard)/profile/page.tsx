"use client";

import { useEffect, useState } from "react";
import { Save } from "lucide-react";
import { api } from "@/lib/api";
import type { UserProfile } from "@/types";
import type { ResumeContent as RC } from "@/types/resume";
import { emptyResumeContent } from "@/types/resume";
import { PageHeader } from "@/components/ui/PageHeader";
import { StructuredProfileEditor } from "@/components/resume/StructuredEditor";
import { ResumePreviewFrame } from "@/components/resume/ResumePreviewFrame";
import { renderResumeHtmlClient } from "@/lib/resumePreview";

export default function ProfilePage() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [content, setContent] = useState<RC>(emptyResumeContent());
  const [resumeText, setResumeText] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [tab, setTab] = useState<"structured" | "legacy">("structured");

  useEffect(() => {
    api.getProfile().then((p) => {
      setProfile(p);
      setResumeText(p.resume_text || "");
    }).catch(console.error);
    api.getStructuredProfile().then((p) => setContent(p.content)).catch(console.error);
  }, []);

  const handleSaveStructured = async () => {
    setSaving(true);
    try {
      await api.updateStructuredProfile(content);
      const p = await api.getProfile();
      setProfile(p);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (e) {
      console.error(e);
    } finally {
      setSaving(false);
    }
  };

  const handleSaveLegacy = async () => {
    setSaving(true);
    try {
      const updated = await api.updateProfile({ resume_text: resumeText });
      setProfile(updated);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <PageHeader
        title="User Profile"
        description="Your profile data powers resume tailoring and job match scoring"
      />

      <div className="mb-4 flex gap-2">
        <button onClick={() => setTab("structured")} className={tab === "structured" ? "btn-primary" : "btn-secondary"}>Structured Profile</button>
        <button onClick={() => setTab("legacy")} className={tab === "legacy" ? "btn-primary" : "btn-secondary"}>Plain Text Import</button>
      </div>

      {tab === "structured" ? (
        <div className="grid gap-6 lg:grid-cols-2">
          <div>
            <StructuredProfileEditor content={content} onChange={setContent} />
            <button onClick={handleSaveStructured} disabled={saving} className="btn-primary mt-4">
              <Save className="h-4 w-4" />
              {saving ? "Saving..." : saved ? "Saved" : "Save Profile"}
            </button>
          </div>
          <div className="glass-panel p-4">
            <p className="text-xs uppercase tracking-widest text-indigo-400">Preview</p>
            <div className="mt-3 h-[600px]">
              <ResumePreviewFrame html={renderResumeHtmlClient(content)} />
            </div>
          </div>
        </div>
      ) : (
        <div className="glass-panel p-6">
          <textarea
            value={resumeText}
            onChange={(e) => setResumeText(e.target.value)}
            placeholder="Paste resume text for legacy match scoring..."
            className="min-h-[300px] w-full rounded-lg border border-zinc-800 bg-zinc-950/80 p-4 font-mono text-sm text-zinc-300"
          />
          <button onClick={handleSaveLegacy} disabled={saving} className="btn-primary mt-4">
            <Save className="h-4 w-4" /> Save Plain Text
          </button>
        </div>
      )}

      {profile && (
        <div className="mt-6 text-sm text-zinc-500">{profile.name} · {profile.email}</div>
      )}
    </div>
  );
}
