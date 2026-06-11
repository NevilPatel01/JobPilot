import type { ResumeContent } from "@/types/resume";

function esc(text: string) {
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

export function renderResumeHtmlClient(content: ResumeContent): string {
  const c = content.contact;
  const contactLine = [c.email, c.phone, c.location].filter(Boolean).map(esc).join(" · ");
  const exp = content.experience.map((e) => `
    <div class="entry"><strong>${esc(e.title)}</strong> — ${esc(e.company)}
    <ul>${e.bullets.map((b) => `<li>${esc(b)}</li>`).join("")}</ul></div>`).join("");
  const edu = content.education.map((e) => `<div><strong>${esc(e.institution)}</strong> — ${esc(e.degree)}</div>`).join("");
  const proj = content.projects.map((p) => `<div><strong>${esc(p.name)}</strong><ul>${p.bullets.map((b) => `<li>${esc(b)}</li>`).join("")}</ul></div>`).join("");
  const skills = content.skills.map((s) => `<div><strong>${esc(s.name)}:</strong> ${esc(s.skills.join(", "))}</div>`).join("");

  return `<!DOCTYPE html><html><head><style>
  body{font-family:'Times New Roman',serif;max-width:8.5in;margin:0 auto;padding:0.5in;color:#111;font-size:11pt}
  h1{text-align:center;font-size:22pt;margin:0}
  .contact{text-align:center;font-size:10pt;margin-bottom:12px}
  h2{font-size:11pt;text-transform:uppercase;border-bottom:1px solid #111}
  ul{margin:4px 0 0 18px}
  </style></head><body>
  <h1>${esc(c.full_name)}</h1>
  <div class="contact">${contactLine}</div>
  ${content.summary ? `<p>${esc(content.summary)}</p>` : ""}
  <h2>Experience</h2>${exp || "<p>—</p>"}
  <h2>Education</h2>${edu || "<p>—</p>"}
  <h2>Projects</h2>${proj || "<p>—</p>"}
  <h2>Skills</h2>${skills || "<p>—</p>"}
  </body></html>`;
}
