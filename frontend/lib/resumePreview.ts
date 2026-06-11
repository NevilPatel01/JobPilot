import type { ResumeContent } from "@/types/resume";

function esc(text: string) {
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function contactLine(content: ResumeContent): string {
  const c = content.contact;
  const parts: string[] = [];
  if (c.location) parts.push(esc(c.location));
  if (c.phone) parts.push(esc(c.phone));
  if (c.email) {
    const email = esc(c.email);
    parts.push(`<a href="mailto:${email}">${email}</a>`);
  }
  for (const link of content.links) {
    if (link.url) {
      parts.push(`<a href="${esc(link.url)}">${esc(link.label || link.url)}</a>`);
    }
  }
  return parts.join(" &nbsp;|&nbsp; ");
}

export function renderResumeHtmlClient(content: ResumeContent): string {
  const c = content.contact;

  const exp = content.experience
    .map(
      (e) => `
    <div class="entry">
      <div class="entry-header">
        <strong>${esc(e.title)}</strong>
        <span class="dates">${esc([e.start_date, e.end_date].filter(Boolean).join(" -- "))}</span>
      </div>
      <div class="entry-sub">
        <span>${esc(e.company)}</span>
        <span class="dates">${esc(e.location)}</span>
      </div>
      <ul>${e.bullets.map((b) => `<li>${esc(b)}</li>`).join("")}</ul>
    </div>`
    )
    .join("");

  const edu = content.education
    .map((e) => {
      const degree = e.gpa ? `${esc(e.degree)} (GPA: ${esc(e.gpa)})` : esc(e.degree);
      return `
    <div class="entry">
      <div class="entry-header">
        <strong>${esc(e.institution)}</strong>
        <span class="dates">${esc([e.start_date, e.end_date].filter(Boolean).join(" -- "))}</span>
      </div>
      <div class="entry-sub">
        <span><em>${degree}</em></span>
        <span class="dates">${esc(e.location)}</span>
      </div>
    </div>`;
    })
    .join("");

  const proj = content.projects
    .map((p) => {
      const name = p.url
        ? `<a href="${esc(p.url)}">${esc(p.name)}</a>`
        : esc(p.name);
      return `
    <div class="entry">
      <div class="entry-header"><strong>${name}</strong></div>
      <ul>${p.bullets.map((b) => `<li>${esc(b)}</li>`).join("")}</ul>
    </div>`;
    })
    .join("");

  const skills = content.skills
    .map((s) => {
      const items = esc(s.skills.join(", "));
      return s.name
        ? `<div class="skill-row"><strong>${esc(s.name)}:</strong> ${items}</div>`
        : `<div class="skill-row">${items}</div>`;
    })
    .join("");

  const summary = content.summary
    ? `<div class="section"><h2>Summary</h2><p class="summary">${esc(content.summary)}</p></div>`
    : "";

  return `<!DOCTYPE html><html><head><style>
  body{font-family:Charter,'Bitstream Charter','Times New Roman',serif;max-width:8.5in;margin:0 auto;padding:0.5in;color:#111;font-size:11pt;line-height:1.35}
  h1{text-align:center;font-size:24pt;margin:0 0 6px;font-variant:small-caps;letter-spacing:0.5px;font-weight:700}
  .contact{text-align:center;font-size:10pt;margin-bottom:14px;color:#222}
  .section{margin-top:12px}
  h2{font-size:11pt;text-transform:uppercase;font-variant:small-caps;border-bottom:1px solid #111;margin:0 0 6px;padding-bottom:2px;letter-spacing:0.5px}
  .entry{margin-bottom:8px}
  .entry-header{display:flex;justify-content:space-between;align-items:baseline;gap:12px}
  .entry-sub{display:flex;justify-content:space-between;font-style:italic;margin-bottom:2px;font-size:10pt}
  .dates{font-size:10pt;font-style:italic;white-space:nowrap}
  ul{margin:2px 0 0 18px;padding:0}
  li{margin-bottom:2px;font-size:10pt}
  .skill-row{margin-bottom:3px;font-size:10pt}
  .summary{margin:0;font-size:10pt}
  a{color:#111;text-decoration:none}
  </style></head><body>
  <h1>${esc(c.full_name)}</h1>
  <div class="contact">${contactLine(content)}</div>
  ${summary}
  <div class="section"><h2>Technical Skills</h2>${skills || "<p>—</p>"}</div>
  <div class="section"><h2>Experience</h2>${exp || "<p>—</p>"}</div>
  <div class="section"><h2>Projects</h2>${proj || "<p>—</p>"}</div>
  <div class="section"><h2>Education</h2>${edu || "<p>—</p>"}</div>
  </body></html>`;
}
