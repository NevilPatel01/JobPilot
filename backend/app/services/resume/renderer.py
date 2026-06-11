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


def render_resume_html(content: dict) -> str:
    contact = content.get("contact", {})
    links = content.get("links", [])
    link_html = " · ".join(
        f'<a href="{_esc(l.get("url", ""))}">{_esc(l.get("label", ""))}</a>'
        for l in links
        if l.get("url")
    )
    contact_line = " · ".join(
        filter(None, [_esc(contact.get("email", "")), _esc(contact.get("phone", "")), _esc(contact.get("location", ""))])
    )

    exp_html = ""
    for exp in content.get("experience", []):
        dates = " – ".join(filter(None, [exp.get("start_date", ""), exp.get("end_date", "")]))
        exp_html += f"""
        <div class="entry">
          <div class="entry-header">
            <strong>{_esc(exp.get("title", ""))}</strong>
            <span class="dates">{_esc(dates)}</span>
          </div>
          <div class="entry-sub">{_esc(exp.get("company", ""))}{', ' + _esc(exp.get('location', '')) if exp.get('location') else ''}</div>
          {_bullets(exp.get("bullets", []))}
        </div>"""

    edu_html = ""
    for edu in content.get("education", []):
        dates = " – ".join(filter(None, [edu.get("start_date", ""), edu.get("end_date", "")]))
        edu_html += f"""
        <div class="entry">
          <div class="entry-header">
            <strong>{_esc(edu.get("institution", ""))}</strong>
            <span class="dates">{_esc(dates)}</span>
          </div>
          <div class="entry-sub">{_esc(edu.get("degree", ""))}{(' · GPA: ' + _esc(edu.get('gpa', ''))) if edu.get('gpa') else ''}</div>
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
        skills_html += f'<div class="skill-row"><strong>{_esc(cat.get("name", ""))}:</strong> {_esc(", ".join(cat.get("skills", [])))}</div>'

    summary = content.get("summary", "")
    summary_html = f'<p class="summary">{_esc(summary)}</p>' if summary else ""

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
body {{ font-family: 'Times New Roman', Times, serif; max-width: 8.5in; margin: 0 auto; padding: 0.5in; color: #111; font-size: 11pt; line-height: 1.35; }}
h1 {{ text-align: center; font-size: 22pt; margin: 0 0 4px; letter-spacing: 1px; }}
.contact {{ text-align: center; font-size: 10pt; margin-bottom: 12px; }}
.section {{ margin-top: 14px; }}
.section h2 {{ font-size: 11pt; text-transform: uppercase; border-bottom: 1px solid #111; margin: 0 0 6px; padding-bottom: 2px; }}
.entry {{ margin-bottom: 8px; }}
.entry-header {{ display: flex; justify-content: space-between; }}
.entry-sub {{ font-style: italic; margin-bottom: 2px; }}
.dates {{ font-size: 10pt; }}
ul {{ margin: 2px 0 0 18px; padding: 0; }}
li {{ margin-bottom: 1px; }}
.skill-row {{ margin-bottom: 2px; }}
.summary {{ margin: 0 0 8px; }}
a {{ color: #111; text-decoration: none; }}
</style></head><body>
<h1>{_esc(contact.get("full_name", ""))}</h1>
<div class="contact">{contact_line}{(' · ' + link_html) if link_html else ''}</div>
{summary_html}
<div class="section"><h2>Experience</h2>{exp_html or '<p>—</p>'}</div>
<div class="section"><h2>Education</h2>{edu_html or '<p>—</p>'}</div>
<div class="section"><h2>Projects</h2>{proj_html or '<p>—</p>'}</div>
<div class="section"><h2>Skills</h2>{skills_html or '<p>—</p>'}</div>
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


def render_resume_latex(content: dict) -> str:
    contact = content.get("contact", {})
    lines = [
        r"\documentclass[letterpaper,11pt]{article}",
        r"\usepackage[empty]{fullpage}",
        r"\usepackage{enumitem}",
        r"\begin{document}",
        r"\begin{center}",
        r"{\Large \textbf{" + _latex_esc(contact.get("full_name", "")) + r"}} \\",
        r"\small " + _latex_esc(" · ".join(filter(None, [contact.get("email"), contact.get("phone"), contact.get("location")]))) + r" \\",
        r"\end{center}",
    ]
    if content.get("summary"):
        lines += [r"\section*{Summary}", _latex_esc(content["summary"])]

    lines.append(r"\section*{Experience}")
    for exp in content.get("experience", []):
        lines.append(r"\textbf{" + _latex_esc(exp.get("title", "")) + r"} \hfill " + _latex_esc(exp.get("end_date", "")))
        lines.append(r"\textit{" + _latex_esc(exp.get("company", "")) + r"}")
        bullets = [b for b in exp.get("bullets", []) if b]
        if bullets:
            lines.append(r"\begin{itemize}[leftmargin=*]")
            lines += [r"\item " + _latex_esc(b) for b in bullets]
            lines.append(r"\end{itemize}")

    lines.append(r"\section*{Education}")
    for edu in content.get("education", []):
        lines.append(r"\textbf{" + _latex_esc(edu.get("institution", "")) + r"} \hfill " + _latex_esc(edu.get("end_date", "")))
        lines.append(r"\textit{" + _latex_esc(edu.get("degree", "")) + r"}")

    lines.append(r"\section*{Projects}")
    for proj in content.get("projects", []):
        lines.append(r"\textbf{" + _latex_esc(proj.get("name", "")) + r"}")
        bullets = [b for b in proj.get("bullets", []) if b]
        if bullets:
            lines.append(r"\begin{itemize}[leftmargin=*]")
            lines += [r"\item " + _latex_esc(b) for b in bullets]
            lines.append(r"\end{itemize}")

    lines.append(r"\section*{Skills}")
    for cat in content.get("skills", []):
        lines.append(r"\textbf{" + _latex_esc(cat.get("name", "")) + r":} " + _latex_esc(", ".join(cat.get("skills", []))))

    lines.append(r"\end{document}")
    return "\n".join(lines)


def resolve_export_latex(content: dict, latex_source: str | None = None) -> str:
    """Always derive export LaTeX from structured content (latex_source is ignored)."""
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
