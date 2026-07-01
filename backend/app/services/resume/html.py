from __future__ import annotations

import html


def _esc(text: str) -> str:
    return html.escape(text or "")


def _bullets(items: list[str]) -> str:
    if not items:
        return ""
    return "<ul>" + "".join(f"<li>{_esc(b)}</li>" for b in items if b) + "</ul>"


def _html_contact_line(contact: dict, links: list[dict]) -> str:
    parts: list[str] = []
    if contact.get("location"):
        parts.append(_esc(contact["location"]))
    if contact.get("phone"):
        parts.append(_esc(contact["phone"]))
    if contact.get("email"):
        email = _esc(contact["email"])
        parts.append(f'<a href="mailto:{email}">{email}</a>')
    for link in links:
        if link.get("url"):
            parts.append(f'<a href="{_esc(link["url"])}">{_esc(link.get("label") or link["url"])}</a>')
    return " &nbsp;|&nbsp; ".join(parts)


def render_resume_html(content: dict) -> str:
    contact = content.get("contact", {})
    links = content.get("links", [])

    exp_html = ""
    for exp in content.get("experience", []):
        dates = " -- ".join(filter(None, [exp.get("start_date", ""), exp.get("end_date", "")]))
        exp_html += f"""
        <div class="entry">
          <div class="entry-header">
            <strong>{_esc(exp.get("title", ""))}</strong>
            <span class="dates">{_esc(dates)}</span>
          </div>
          <div class="entry-sub">
            <span>{_esc(exp.get("company", ""))}</span>
            <span class="dates">{_esc(exp.get("location", ""))}</span>
          </div>
          {_bullets(exp.get("bullets", []))}
        </div>"""

    edu_html = ""
    for edu in content.get("education", []):
        dates = " -- ".join(filter(None, [edu.get("start_date", ""), edu.get("end_date", "")]))
        degree = _esc(edu.get("degree", ""))
        if edu.get("gpa"):
            degree += f" (GPA: {_esc(edu['gpa'])})"
        edu_html += f"""
        <div class="entry">
          <div class="entry-header">
            <strong>{_esc(edu.get("institution", ""))}</strong>
            <span class="dates">{_esc(dates)}</span>
          </div>
          <div class="entry-sub">
            <span><em>{degree}</em></span>
            <span class="dates">{_esc(edu.get("location", ""))}</span>
          </div>
        </div>"""

    proj_html = ""
    for proj in content.get("projects", []):
        name = _esc(proj.get("name", ""))
        url = (proj.get("url") or "").strip()
        github = (proj.get("github_url") or "").strip()
        primary = url or github
        if primary:
            name = f'<a href="{_esc(primary)}">{name}</a>'
        extra = ""
        if url and github:
            extra = f' <a href="{_esc(github)}">GitHub</a>'
        proj_html += f"""
        <div class="entry">
          <div class="entry-header"><strong>{name}</strong>{extra}</div>
          {_bullets(proj.get("bullets", []))}
        </div>"""

    skills_html = ""
    for cat in content.get("skills", []):
        items = ", ".join(cat.get("skills", []))
        if not items:
            continue
        name = cat.get("name", "")
        if name:
            skills_html += f'<div class="skill-row"><strong>{_esc(name)}:</strong> {_esc(items)}</div>'
        else:
            skills_html += f'<div class="skill-row">{_esc(items)}</div>'

    summary = content.get("summary", "")
    summary_html = ""
    if summary:
        summary_html = f'<div class="section"><h2>Summary</h2><p class="summary">{_esc(summary)}</p></div>'

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
body {{ font-family: Charter, 'Bitstream Charter', 'Times New Roman', Times, serif; max-width: 8.5in; margin: 0 auto; padding: 0.5in; color: #111; font-size: 11pt; line-height: 1.35; }}
h1 {{ text-align: center; font-size: 24pt; margin: 0 0 6px; font-variant: small-caps; letter-spacing: 0.5px; font-weight: 700; }}
.contact {{ text-align: center; font-size: 10pt; margin-bottom: 14px; color: #222; }}
.section {{ margin-top: 12px; }}
.section h2 {{ font-size: 11pt; text-transform: uppercase; font-variant: small-caps; border-bottom: 1px solid #111; margin: 0 0 6px; padding-bottom: 2px; letter-spacing: 0.5px; }}
.entry {{ margin-bottom: 8px; }}
.entry-header {{ display: flex; justify-content: space-between; align-items: baseline; gap: 12px; }}
.entry-sub {{ display: flex; justify-content: space-between; font-style: italic; margin-bottom: 2px; font-size: 10pt; }}
.dates {{ font-size: 10pt; font-style: italic; white-space: nowrap; }}
ul {{ margin: 2px 0 0 18px; padding: 0; }}
li {{ margin-bottom: 2px; font-size: 10pt; }}
.skill-row {{ margin-bottom: 3px; font-size: 10pt; }}
.summary {{ margin: 0; font-size: 10pt; }}
a {{ color: #111; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
</style></head><body>
<h1>{_esc(contact.get("full_name", ""))}</h1>
<div class="contact">{_html_contact_line(contact, links)}</div>
{summary_html}
<div class="section"><h2>Technical Skills</h2>{skills_html or '<p>—</p>'}</div>
<div class="section"><h2>Experience</h2>{exp_html or '<p>—</p>'}</div>
<div class="section"><h2>Projects</h2>{proj_html or '<p>—</p>'}</div>
<div class="section"><h2>Education</h2>{edu_html or '<p>—</p>'}</div>
</body></html>"""


def render_cover_letter_html(content: dict, contact: dict | None = None) -> str:
    contact = contact or {}
    paras = "".join(f"<p>{_esc(p)}</p>" for p in content.get("paragraphs", []) if p)
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
body {{ font-family: 'Times New Roman', Times, serif; max-width: 8.5in; margin: 0 auto; padding: 0.75in; color: #111; font-size: 11pt; line-height: 1.5; }}
.header {{ margin-bottom: 24px; }}
.recipient {{ margin-bottom: 24px; }}
</style></head><body>
<div class="header">
  <div>{_esc(contact.get('full_name', ''))}</div>
  <div>{_esc(contact.get('email', ''))}</div>
  <div>{_esc(contact.get('phone', ''))}</div>
  <div style="margin-top:16px">{_esc(content.get('date', ''))}</div>
</div>
<div class="recipient">
  <div>{_esc(content.get('recipient_name', ''))}</div>
  <div>{_esc(content.get('company_name', ''))}</div>
  <div>{_esc(content.get('company_address', ''))}</div>
</div>
<p>{_esc(content.get('salutation', 'Dear Hiring Manager,'))}</p>
{paras}
<p>{_esc(content.get('closing', 'Sincerely,'))}</p>
<p>{_esc(contact.get('full_name', ''))}</p>
</body></html>"""
