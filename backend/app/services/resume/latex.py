from __future__ import annotations


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
    parts: list[str] = []

    location = (contact.get("location") or "").strip()
    if location:
        parts.append(_latex_esc(location))

    phone = (contact.get("phone") or "").strip()
    if phone:
        parts.append(_latex_esc(phone))

    email = (contact.get("email") or "").strip()
    if email:
        parts.append(r"\href{mailto:" + _latex_url(email) + r"}{" + _latex_esc(email) + "}")

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


def _render_summary_section(summary: str) -> list[str]:
    text = (summary or "").strip()
    if not text:
        return []
    return [r"\section{Summary}", _latex_esc(text)]


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
        github = (proj.get("github_url") or "").strip()
        primary = url or github  # link the title to the live site, else the repo
        if primary and name:
            heading = r"\textbf{\href{" + _latex_url(primary) + r"}{" + _latex_esc(name) + r"}}"
        elif name:
            heading = r"\textbf{" + _latex_esc(name) + r"}"
        else:
            heading = r"\textbf{Project}"
        # Right side of the heading: surface any remaining link(s).
        right_parts: list[str] = []
        if url and github:
            right_parts.append(r"\href{" + _latex_url(github) + r"}{GitHub}")
        right = r" $|$ ".join(right_parts)
        lines.append(r"\resumeProjectHeading{" + heading + r"}{" + right + r"}")
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


def resolve_export_latex(content: dict, latex_source: str | None = None) -> str:
    if latex_source and latex_source.strip():
        return latex_source
    return render_resume_latex(content)
