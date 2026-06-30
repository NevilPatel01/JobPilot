"use client";

import { useState } from "react";
import { ChevronDown, Plus, Trash2 } from "lucide-react";
import type { ResumeContent } from "@/types/resume";
import { newId } from "@/types/resume";

interface Props {
  content: ResumeContent;
  onChange: (content: ResumeContent) => void;
}

const CONTACT_PLACEHOLDERS: Record<string, string> = {
  full_name: "Your Full Name",
  email: "you@example.com",
  phone: "+1 555-000-0000",
  location: "City, Province",
};

export function StructuredProfileEditor({ content, onChange }: Props) {
  const update = (patch: Partial<ResumeContent>) => onChange({ ...content, ...patch });

  return (
    <div className="space-y-6">
      <section className="glass-panel p-4">
        <h3 className="text-sm font-semibold text-foreground">Contact</h3>
        <div className="mt-3 grid gap-2 sm:grid-cols-2">
          {(["full_name", "email", "phone", "location"] as const).map((field) => (
            <input
              key={field}
              className="input-field"
              placeholder={CONTACT_PLACEHOLDERS[field] ?? field.replace("_", " ")}
              value={content.contact[field]}
              onChange={(e) =>
                update({ contact: { ...content.contact, [field]: e.target.value } })
              }
            />
          ))}
        </div>
      </section>

      <section className="glass-panel p-4">
        <h3 className="text-sm font-semibold text-foreground">Summary</h3>
        <textarea
          className="input-field mt-2 min-h-[80px]"
          value={content.summary}
          onChange={(e) => update({ summary: e.target.value })}
          placeholder="e.g. Full-stack engineer with 4 years building scalable web apps in React and Python. Focused on product impact and clean APIs."
        />
      </section>

      <SectionList
        title="Experience"
        isEmpty={content.experience.length === 0}
        onAdd={() =>
          update({
            experience: [
              ...content.experience,
              { id: newId(), company: "", title: "", location: "", start_date: "", end_date: "", bullets: [""] },
            ],
          })
        }
      >
        {content.experience.map((exp, i) => (
          <div key={exp.id} className="mb-4 rounded-lg border border-border p-3">
            <div className="flex justify-between">
              <span className="text-xs text-muted-foreground">Role {i + 1}</span>
              <button
                onClick={() => update({ experience: content.experience.filter((e) => e.id !== exp.id) })}
                className="text-muted-foreground hover:text-red-400"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
            <div className="mt-2 grid gap-2 sm:grid-cols-2">
              <input className="input-field" placeholder="Title" value={exp.title}
                onChange={(e) => {
                  const experience = [...content.experience];
                  experience[i] = { ...exp, title: e.target.value };
                  update({ experience });
                }} />
              <input className="input-field" placeholder="Company" value={exp.company}
                onChange={(e) => {
                  const experience = [...content.experience];
                  experience[i] = { ...exp, company: e.target.value };
                  update({ experience });
                }} />
            </div>
            {exp.bullets.map((b, bi) => (
              <input key={bi} className="input-field mt-2" placeholder="Bullet point" value={b}
                onChange={(e) => {
                  const experience = [...content.experience];
                  const bullets = [...exp.bullets];
                  bullets[bi] = e.target.value;
                  experience[i] = { ...exp, bullets };
                  update({ experience });
                }} />
            ))}
            <button
              className="btn-secondary mt-2 text-xs"
              onClick={() => {
                const experience = [...content.experience];
                experience[i] = { ...exp, bullets: [...exp.bullets, ""] };
                update({ experience });
              }}
            >
              + Bullet
            </button>
          </div>
        ))}
      </SectionList>

      <SectionList
        title="Education"
        isEmpty={content.education.length === 0}
        onAdd={() =>
          update({
            education: [
              ...content.education,
              { id: newId(), institution: "", degree: "", location: "", start_date: "", end_date: "", gpa: "" },
            ],
          })
        }
      >
        {content.education.map((edu, i) => (
          <div key={edu.id} className="mb-3 grid gap-2 sm:grid-cols-2">
            <input className="input-field" placeholder="Institution" value={edu.institution}
              onChange={(e) => {
                const education = [...content.education];
                education[i] = { ...edu, institution: e.target.value };
                update({ education });
              }} />
            <input className="input-field" placeholder="Degree" value={edu.degree}
              onChange={(e) => {
                const education = [...content.education];
                education[i] = { ...edu, degree: e.target.value };
                update({ education });
              }} />
          </div>
        ))}
      </SectionList>

      <SectionList
        title="Projects"
        isEmpty={content.projects.length === 0}
        onAdd={() =>
          update({
            projects: [...content.projects, { id: newId(), name: "", url: "", bullets: [""] }],
          })
        }
      >
        {content.projects.map((proj, i) => (
          <div key={proj.id} className="mb-3 rounded-lg border border-border p-3">
            <input className="input-field" placeholder="Project name" value={proj.name}
              onChange={(e) => {
                const projects = [...content.projects];
                projects[i] = { ...proj, name: e.target.value };
                update({ projects });
              }} />
            {proj.bullets.map((b, bi) => (
              <input key={bi} className="input-field mt-2" placeholder="Bullet" value={b}
                onChange={(e) => {
                  const projects = [...content.projects];
                  const bullets = [...proj.bullets];
                  bullets[bi] = e.target.value;
                  projects[i] = { ...proj, bullets };
                  update({ projects });
                }} />
            ))}
          </div>
        ))}
      </SectionList>

      <SectionList
        title="Skills"
        isEmpty={content.skills.length === 0}
        onAdd={() =>
          update({ skills: [...content.skills, { id: newId(), name: "Languages", skills: [] }] })
        }
      >
        {content.skills.map((cat, i) => (
          <div key={cat.id} className="mb-3">
            <input className="input-field" placeholder="Category" value={cat.name}
              onChange={(e) => {
                const skills = [...content.skills];
                skills[i] = { ...cat, name: e.target.value };
                update({ skills });
              }} />
            <input
              className="input-field mt-2"
              placeholder="Comma-separated skills"
              value={cat.skills.join(", ")}
              onChange={(e) => {
                const skills = [...content.skills];
                skills[i] = { ...cat, skills: e.target.value.split(",").map((s) => s.trim()).filter(Boolean) };
                update({ skills });
              }}
            />
          </div>
        ))}
      </SectionList>
    </div>
  );
}

function SectionList({
  title,
  onAdd,
  children,
  isEmpty = false,
}: {
  title: string;
  onAdd: () => void;
  children: React.ReactNode;
  isEmpty?: boolean;
}) {
  const [open, setOpen] = useState(isEmpty);
  return (
    <section className="glass-panel p-4">
      <div className="flex items-center justify-between">
        <button type="button" onClick={() => setOpen((v) => !v)} className="flex flex-1 items-center gap-2 text-left text-sm font-semibold text-foreground">
          <ChevronDown className={`h-4 w-4 text-muted-foreground transition-transform ${open ? "rotate-180" : ""}`} />
          {title}
          {isEmpty && <span className="text-xs font-normal text-muted-foreground">(empty)</span>}
        </button>
        {open && (
          <button type="button" onClick={onAdd} className="btn-secondary text-xs">
            <Plus className="h-3 w-3" /> Add
          </button>
        )}
      </div>
      {open && <div className="mt-3">{children}</div>}
    </section>
  );
}
