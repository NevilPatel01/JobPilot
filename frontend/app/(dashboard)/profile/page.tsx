"use client";

import { useEffect, useState } from "react";
import { Save, Sparkles } from "lucide-react";
import { api } from "@/lib/api";
import type { UserProfile } from "@/types";
import { PageHeader } from "@/components/ui/PageHeader";

export default function ProfilePage() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [resume, setResume] = useState("");
  const [skills, setSkills] = useState<string[]>([]);
  const [newSkill, setNewSkill] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    api.getProfile().then((p) => {
      setProfile(p);
      setResume(p.resume_text || "");
      setSkills(p.skills_keywords || []);
    }).catch(console.error);
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      const updated = await api.updateProfile({ resume_text: resume, skills_keywords: skills });
      setProfile(updated);
      setSkills(updated.skills_keywords || []);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (e) {
      console.error(e);
    } finally {
      setSaving(false);
    }
  };

  const addSkill = () => {
    const s = newSkill.trim().toLowerCase();
    if (s && !skills.includes(s)) {
      setSkills([...skills, s]);
      setNewSkill("");
    }
  };

  const removeSkill = (skill: string) => setSkills(skills.filter((s) => s !== skill));

  return (
    <div>
      <PageHeader
        title="Profile"
        description="Paste your resume to enable match scoring on job listings"
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="glass-panel p-6">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-indigo-400" />
            <h2 className="text-sm font-semibold text-white">Resume / Skills</h2>
          </div>
          <textarea
            value={resume}
            onChange={(e) => setResume(e.target.value)}
            placeholder="Paste your resume or list core skills (React, Python, AWS, etc.)..."
            className="mt-4 min-h-[300px] w-full rounded-lg border border-zinc-800 bg-zinc-950/80 p-4 font-mono text-sm leading-relaxed text-zinc-300 placeholder:text-zinc-600 focus:border-indigo-600/50 focus:outline-none focus:ring-1 focus:ring-indigo-600/20"
          />
          <button onClick={handleSave} disabled={saving} className="btn-primary mt-4">
            <Save className="h-4 w-4" />
            {saving ? "Saving..." : saved ? "Saved" : "Save Profile"}
          </button>
        </div>

        <div className="glass-panel p-6">
          <h2 className="text-sm font-semibold text-white">Parsed Skills</h2>
          <p className="mt-1 text-xs text-zinc-600">Auto-extracted from resume. Add or remove manually.</p>
          <div className="mt-4 flex flex-wrap gap-2">
            {skills.length === 0 && (
              <p className="text-sm text-zinc-600">Save your resume to extract skills</p>
            )}
            {skills.map((skill) => (
              <span
                key={skill}
                className="inline-flex items-center gap-1.5 rounded-full bg-indigo-600/10 px-3 py-1 text-xs font-medium text-indigo-300 ring-1 ring-indigo-500/20"
              >
                {skill}
                <button onClick={() => removeSkill(skill)} className="text-indigo-400/60 hover:text-white">
                  ×
                </button>
              </span>
            ))}
          </div>
          <div className="mt-4 flex gap-2">
            <input
              value={newSkill}
              onChange={(e) => setNewSkill(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && addSkill()}
              placeholder="Add skill..."
              className="input-field flex-1"
            />
            <button onClick={addSkill} className="btn-secondary">
              Add
            </button>
          </div>

          {profile && (
            <div className="mt-6 border-t border-zinc-800/80 pt-4">
              <p className="text-sm font-medium text-zinc-300">{profile.name || "User"}</p>
              <p className="text-xs text-zinc-600">{profile.email}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
