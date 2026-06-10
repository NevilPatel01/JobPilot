"use client";

import { useEffect, useState } from "react";
import { Save } from "lucide-react";
import { api } from "@/lib/api";
import type { UserProfile } from "@/types";

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
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Profile</h1>
        <p className="text-sm text-zinc-400">Paste your resume to enable match scoring on job listings</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-5">
          <h2 className="text-sm font-medium text-white">Resume / Skills</h2>
          <textarea
            value={resume}
            onChange={(e) => setResume(e.target.value)}
            placeholder="Paste your resume or list your core skills..."
            className="mt-3 min-h-[300px] w-full rounded-lg border border-zinc-800 bg-zinc-950 p-4 font-mono text-sm text-zinc-300 placeholder:text-zinc-600 focus:border-indigo-600 focus:outline-none"
          />
          <button
            onClick={handleSave}
            disabled={saving}
            className="mt-4 inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50 transition-colors"
          >
            <Save className="h-4 w-4" />
            {saving ? "Saving..." : saved ? "Saved!" : "Save Profile"}
          </button>
        </div>

        <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-5">
          <h2 className="text-sm font-medium text-white">Parsed Skills</h2>
          <p className="mt-1 text-xs text-zinc-500">Auto-extracted from resume. Add or remove manually.</p>
          <div className="mt-4 flex flex-wrap gap-2">
            {skills.map((skill) => (
              <span
                key={skill}
                className="inline-flex items-center gap-1 rounded-full bg-indigo-600/20 px-3 py-1 text-xs text-indigo-400"
              >
                {skill}
                <button onClick={() => removeSkill(skill)} className="hover:text-white">×</button>
              </span>
            ))}
          </div>
          <div className="mt-4 flex gap-2">
            <input
              value={newSkill}
              onChange={(e) => setNewSkill(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && addSkill()}
              placeholder="Add skill..."
              className="flex-1 rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-300 focus:border-indigo-600 focus:outline-none"
            />
            <button
              onClick={addSkill}
              className="rounded-lg border border-zinc-700 px-3 py-2 text-sm text-zinc-300 hover:border-zinc-600"
            >
              Add
            </button>
          </div>

          {profile && (
            <div className="mt-6 border-t border-zinc-800 pt-4 text-sm text-zinc-500">
              <p>{profile.name || "User"}</p>
              <p>{profile.email}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
