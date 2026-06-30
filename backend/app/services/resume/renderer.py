from __future__ import annotations

import html
import json
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.llm.client import LLMConfig

logger = logging.getLogger(__name__)


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
        if proj.get("url"):
            name = f'<a href="{_esc(proj.get("url", ""))}">{name}</a>'
        proj_html += f"""
        <div class="entry">
          <div class="entry-header"><strong>{name}</strong></div>
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


def render_cover_letter_latex(content: dict, contact: dict | None = None) -> str:
    contact = contact or {}
    lines = [
        r"\documentclass[letterpaper,11pt]{article}",
        r"\usepackage[empty]{fullpage}",
        r"\usepackage{parskip}",
        r"\begin{document}",
        r"\noindent " + _latex_esc(contact.get("full_name", "")) + r" \\",
        _latex_esc(contact.get("email", "")) + r" \\",
        _latex_esc(contact.get("phone", "")) + r" \\",
        r"\vspace{12pt}",
        r"\noindent " + _latex_esc(content.get("date", "")) + r" \\",
        r"\vspace{12pt}",
        r"\noindent " + _latex_esc(content.get("recipient_name", "")) + r" \\",
        _latex_esc(content.get("company_name", "")) + r" \\",
        _latex_esc(content.get("company_address", "")) + r" \\",
        r"\vspace{12pt}",
        r"\noindent " + _latex_esc(content.get("salutation", "Dear Hiring Manager,")) + r" \\",
        r"\vspace{6pt}",
    ]
    for para in content.get("paragraphs", []):
        if para:
            lines.append(_latex_esc(para) + r" \\")
            lines.append(r"\vspace{6pt}")
    lines += [
        r"\noindent " + _latex_esc(content.get("closing", "Sincerely,")) + r" \\",
        r"\vspace{24pt}",
        r"\noindent " + _latex_esc(contact.get("full_name", "")),
        r"\end{document}",
    ]
    return "\n".join(lines)


def _latex_esc(text: str) -> str:
    if not text:
        return ""
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text


def _latex_url(url: str) -> str:
    """Escape a URL for use inside \\href{...}{...}."""
    return _latex_esc(url or "")


def _format_dates(start: str, end: str) -> str:
    parts = [p.strip() for p in (start, end) if p and p.strip()]
    return " -- ".join(parts)


def _link_by_kind(links: list[dict], *kinds: str) -> dict | None:
    for link in links:
        label = (link.get("label") or "").lower()
        url = (link.get("url") or "").strip()
        if not url:
            continue
        for kind in kinds:
            if kind in label or kind in url.lower():
                return link
    return None


def _header_contact_line(contact: dict, links: list[dict]) -> str:
    """Build centered header line with plain hyperlinks (no fontawesome)."""
    parts: list[str] = []

    location = (contact.get("location") or "").strip()
    if location:
        parts.append(_latex_esc(location))

    phone = (contact.get("phone") or "").strip()
    if phone:
        parts.append(_latex_esc(phone))

    email = (contact.get("email") or "").strip()
    if email:
        parts.append(
            r"\href{mailto:" + _latex_url(email) + r"}{" + _latex_esc(email) + "}"
        )

    linkedin = _link_by_kind(links, "linkedin", "linked.in")
    if linkedin:
        url = linkedin["url"].strip()
        label = (linkedin.get("label") or "LinkedIn").strip()
        parts.append(r"\href{" + _latex_url(url) + r"}{" + _latex_esc(label) + "}")

    github = _link_by_kind(links, "github")
    if github:
        url = github["url"].strip()
        label = (github.get("label") or "GitHub").strip()
        parts.append(r"\href{" + _latex_url(url) + r"}{" + _latex_esc(label) + "}")

    portfolio = _link_by_kind(links, "portfolio", "website", "personal", "blog")
    if portfolio:
        url = portfolio["url"].strip()
        label = (portfolio.get("label") or "Portfolio").strip()
        parts.append(r"\href{" + _latex_url(url) + r"}{" + _latex_esc(label) + "}")

    used_urls = {
        (linkedin or {}).get("url", ""),
        (github or {}).get("url", ""),
        (portfolio or {}).get("url", ""),
    }
    for link in links:
        url = (link.get("url") or "").strip()
        if not url or url in used_urls:
            continue
        label = (link.get("label") or url).strip()
        parts.append(r"\href{" + _latex_url(url) + r"}{" + _latex_esc(label) + "}")

    return r" $|$ ".join(parts)


def _render_skills_section(skills: list[dict]) -> list[str]:
    if not skills:
        return []
    lines = [r"\section{Technical Skills}", r"\begin{itemize}[leftmargin=0.15in, label={}]"]
    for cat in skills:
        name = (cat.get("name") or "").strip()
        items = [s for s in (cat.get("skills") or []) if s]
        if not items:
            continue
        skill_text = _latex_esc(", ".join(items))
        if name:
            lines.append(r"\small{\item{\textbf{" + _latex_esc(name) + r":} " + skill_text + r"}}")
        else:
            lines.append(r"\small{\item{" + skill_text + r"}}")
    lines.append(r"\end{itemize}")
    return lines


def _render_experience_section(experience: list[dict]) -> list[str]:
    if not experience:
        return []
    lines = [r"\section{Experience}", r"\resumeSubHeadingListStart"]
    for exp in experience:
        dates = _format_dates(exp.get("start_date", ""), exp.get("end_date", ""))
        lines.append(
            r"\resumeSubheading"
            + "{"
            + _latex_esc(exp.get("title", ""))
            + "}{"
            + _latex_esc(exp.get("company", ""))
            + "}{"
            + _latex_esc(exp.get("location", ""))
            + "}{"
            + _latex_esc(dates)
            + "}"
        )
        bullets = [b for b in exp.get("bullets", []) if b]
        if bullets:
            lines.append(r"\resumeItemListStart")
            lines += [r"\resumeItem{" + _latex_esc(b) + "}" for b in bullets]
            lines.append(r"\resumeItemListEnd")
    lines.append(r"\resumeSubHeadingListEnd")
    return lines


def _render_projects_section(projects: list[dict]) -> list[str]:
    if not projects:
        return []
    lines = [r"\section{Projects}", r"\resumeSubHeadingListStart"]
    for proj in projects:
        name = (proj.get("name") or "").strip()
        url = (proj.get("url") or "").strip()
        if url and name:
            heading = r"\textbf{\href{" + _latex_url(url) + r"}{" + _latex_esc(name) + r"}}"
        elif name:
            heading = r"\textbf{" + _latex_esc(name) + r"}"
        else:
            heading = r"\textbf{Project}"
        lines.append(r"\resumeProjectHeading{" + heading + r"}{}")
        bullets = [b for b in proj.get("bullets", []) if b]
        if bullets:
            lines.append(r"\resumeItemListStart")
            lines += [r"\resumeItem{" + _latex_esc(b) + "}" for b in bullets]
            lines.append(r"\resumeItemListEnd")
    lines.append(r"\resumeSubHeadingListEnd")
    return lines


def _render_education_section(education: list[dict]) -> list[str]:
    if not education:
        return []
    lines = [r"\section{Education}", r"\resumeSubHeadingListStart"]
    for edu in education:
        dates = _format_dates(edu.get("start_date", ""), edu.get("end_date", ""))
        degree = edu.get("degree", "")
        gpa = (edu.get("gpa") or "").strip()
        if gpa:
            degree = f"{degree} (GPA: {gpa})" if degree else f"GPA: {gpa}"
        lines.append(
            r"\resumeSubheading"
            + "{"
            + _latex_esc(edu.get("institution", ""))
            + "}{"
            + _latex_esc(degree)
            + "}{"
            + _latex_esc(edu.get("location", ""))
            + "}{"
            + _latex_esc(dates)
            + "}"
        )
    lines.append(r"\resumeSubHeadingListEnd")
    return lines


def _render_summary_section(summary: str) -> list[str]:
    text = (summary or "").strip()
    if not text:
        return []
    return [r"\section{Summary}", _latex_esc(text)]


def render_resume_latex(content: dict) -> str:
    from app.services.resume.latex_preamble import RESUME_LATEX_PREAMBLE

    contact = content.get("contact", {})
    links = content.get("links", [])

    lines = [
        RESUME_LATEX_PREAMBLE.strip(),
        r"\begin{document}",
        r"\begin{center}",
        r"{\Huge \scshape " + _latex_esc(contact.get("full_name", "")) + r"} \\ \vspace{1pt}",
        r"\small " + _header_contact_line(contact, links),
        r"\end{center}",
    ]

    lines += _render_summary_section(content.get("summary", ""))
    lines += _render_skills_section(content.get("skills", []))
    lines += _render_experience_section(content.get("experience", []))
    lines += _render_projects_section(content.get("projects", []))
    lines += _render_education_section(content.get("education", []))

    lines.append(r"\end{document}")
    return "\n".join(lines)


def resolve_export_latex(content: dict, latex_source: str | None = None) -> str:
    """Use stored LaTeX for export when present; otherwise generate from content."""
    if latex_source and latex_source.strip():
        return latex_source
    return render_resume_latex(content)


@dataclass
class PdfParseResult:
    content: dict
    warnings: list[str]
    confidence: float
    section_counts: dict[str, int]


def compute_section_counts(content: dict) -> dict[str, int]:
    contact = content.get("contact") or {}
    return {
        "experience": len(content.get("experience") or []),
        "education": len(content.get("education") or []),
        "projects": len(content.get("projects") or []),
        "skill_categories": len(content.get("skills") or []),
        "links": len(content.get("links") or []),
        "has_summary": 1 if (content.get("summary") or "").strip() else 0,
        "has_contact_name": 1 if (contact.get("full_name") or "").strip() else 0,
    }


def _parse_pdf_stub(raw: str) -> PdfParseResult:
    """Best-effort plain text to minimal structured resume (no LLM)."""
    from app.schemas.resume_content import ResumeContent

    content = ResumeContent()
    warnings: list[str] = []
    if raw.strip():
        content.summary = raw[:2000]
        warnings.append("No API key — only summary text was extracted. Review all sections in your profile.")
        confidence = 0.25
    else:
        warnings.append("Could not extract text from PDF.")
        confidence = 0.0
    dumped = content.model_dump()
    return PdfParseResult(
        content=dumped,
        warnings=warnings,
        confidence=confidence,
        section_counts=compute_section_counts(dumped),
    )


async def parse_pdf_text(raw: str, llm_config: LLMConfig | None = None) -> PdfParseResult:
    """Parse PDF plain text into structured ResumeContent with quality metadata."""
    if not raw.strip():
        return _parse_pdf_stub(raw)

    if not llm_config:
        return _parse_pdf_stub(raw)

    from langchain_core.messages import HumanMessage, SystemMessage

    from app.agents.retry import invoke_llm
    from app.schemas.resume_content import ResumeContent
    from app.services.llm.client import create_chat_model

    prompt = f"""Extract structured resume data from this PDF text. Return JSON with keys:
- content: object with contact {{full_name, email, phone, location}}, links[], summary, experience[], education[], projects[], skills[]
  Each list item needs id (uuid string), dates as strings, bullets[] for experience/projects
  skills is list of {{id, name, skills[]}}
- warnings: list of strings noting ambiguities, missing sections, or low-confidence fields
- confidence: float 0-1 for overall extraction quality

Rules:
- Do not invent employers, degrees, dates, or metrics not supported by the text
- Use empty strings and empty lists for missing fields
- Preserve wording in bullets where possible

PDF text:
{raw[:12000]}"""

    try:
        llm = create_chat_model(llm_config, temperature=0.1)
        res = await invoke_llm(
            llm,
            [SystemMessage(content="Return valid JSON only."), HumanMessage(content=prompt)],
        )
        parsed = json.loads(res.content if isinstance(res.content, str) else str(res.content))
        content = ResumeContent.model_validate(parsed.get("content") or {})
        warnings = [str(w) for w in (parsed.get("warnings") or []) if w]
        confidence = float(parsed.get("confidence", 0.7))
        confidence = max(0.0, min(1.0, confidence))

        counts = compute_section_counts(content.model_dump())
        if not counts["has_contact_name"]:
            warnings.append("Contact name was not detected — verify header in profile.")
        if counts["experience"] == 0:
            warnings.append("No experience entries found — add roles manually if missing.")
        if counts["education"] == 0:
            warnings.append("No education entries found — add degrees manually if missing.")

        return PdfParseResult(
            content=content.model_dump(),
            warnings=warnings or ["Review parsed sections for accuracy."],
            confidence=confidence,
            section_counts=counts,
        )
    except Exception as e:
        logger.warning("LLM PDF parse failed, falling back to stub: %s", e)
        stub = _parse_pdf_stub(raw)
        stub.warnings.insert(0, f"Structured parse failed ({e}); using summary-only fallback.")
        stub.confidence = min(stub.confidence, 0.3)
        return stub
