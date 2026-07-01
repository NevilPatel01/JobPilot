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
        # Show a labeled "Email" link (matches the target design) instead of the raw address.
        parts.append(r"\href{mailto:" + _latex_url(email) + r"}{Email}")

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


def _bold_bullet_join(parts: list[str]) -> str:
    """Bold left-side entry header: 'Title • Company'."""
    items = [p for p in parts if p]
    if not items:
        return ""
    return r"\textbf{" + r" $\bullet$ ".join(items) + "}"


def _pipe_join(parts: list[str]) -> str:
    """Right-side meta: 'Location | Dates'."""
    return r" $|$ ".join([p for p in parts if p])


def _render_summary_section(summary: str) -> list[str]:
    text = (summary or "").strip()
    if not text:
        return []
    return [r"\section{Summary}", _latex_esc(text)]


def _render_skills_section(skills: list[dict]) -> list[str]:
    items: list[str] = []
    for cat in skills or []:
        name = (cat.get("name") or "").strip()
        skill_items = [s for s in (cat.get("skills") or []) if s and s.strip()]
        if not skill_items:
            continue
        skill_text = _latex_esc(", ".join(skill_items))
        if name:
            items.append(r"\item \textbf{" + _latex_esc(name) + r"}: " + skill_text)
        else:
            items.append(r"\item " + skill_text)
    if not items:  # never emit an empty itemize — it crashes Tectonic
        return []
    return [r"\section{Technical Skills}", r"\begin{itemize}", *items, r"\end{itemize}"]


def _render_bullets(bullets: list[str]) -> list[str]:
    items = [b for b in bullets if b and b.strip()]
    if not items:
        return []
    return [r"\begin{itemize}", *[r"\item " + _latex_esc(b) for b in items], r"\end{itemize}"]


def _render_experience_section(experience: list[dict]) -> list[str]:
    entries: list[str] = []
    for exp in experience or []:
        left = _bold_bullet_join([_latex_esc(exp.get("title", "")), _latex_esc(exp.get("company", ""))])
        dates = _latex_esc(_format_dates(exp.get("start_date", ""), exp.get("end_date", "")))
        right = _pipe_join([_latex_esc(exp.get("location", "")), dates])
        bullets = _render_bullets(exp.get("bullets", []))
        if not left and not right and not bullets:  # skip fully-empty entry
            continue
        entries.append(r"\entryrow{" + left + r"}{" + right + r"}")
        entries += bullets
    if not entries:
        return []
    return [r"\section{Work Experience}", *entries]


def _render_projects_section(projects: list[dict]) -> list[str]:
    entries: list[str] = []
    for proj in projects or []:
        name = (proj.get("name") or "").strip()
        url = (proj.get("url") or "").strip()
        github = (proj.get("github_url") or "").strip()
        bullets = _render_bullets(proj.get("bullets", []))
        if not name and not bullets:  # skip fully-empty project
            continue
        primary = url or github  # link the title to the live site, else the repo
        if primary and name:
            left = r"\textbf{\href{" + _latex_url(primary) + r"}{" + _latex_esc(name) + r"}}"
        elif name:
            left = r"\textbf{" + _latex_esc(name) + r"}"
        else:
            left = r"\textbf{Project}"
        # Right side: the GitHub link when a live URL already occupies the title.
        right = r"\href{" + _latex_url(github) + r"}{GitHub}" if (url and github) else ""
        entries.append(r"\entryrow{" + left + r"}{" + right + r"}")
        entries += bullets
    if not entries:
        return []
    return [r"\section{Projects}", *entries]


def _render_education_section(education: list[dict]) -> list[str]:
    entries: list[str] = []
    for edu in education or []:
        degree = edu.get("degree", "")
        gpa = (edu.get("gpa") or "").strip()
        if gpa:
            degree = f"{degree} (GPA: {gpa})" if degree else f"GPA: {gpa}"
        left = _bold_bullet_join([_latex_esc(degree), _latex_esc(edu.get("institution", ""))])
        dates = _latex_esc(_format_dates(edu.get("start_date", ""), edu.get("end_date", "")))
        right = _pipe_join([_latex_esc(edu.get("location", "")), dates])
        if not left and not right:  # skip fully-empty entry
            continue
        entries.append(r"\entryrow{" + left + r"}{" + right + r"}")
    if not entries:
        return []
    return [r"\section{Education}", *entries]


def render_resume_latex(content: dict) -> str:
    from app.services.resume.latex_preamble import RESUME_LATEX_PREAMBLE

    contact = content.get("contact", {})
    links = content.get("links", [])
    name = _latex_esc(contact.get("full_name", "")).strip()
    contact_line = _header_contact_line(contact, links)

    # Use \par (not \\) so an empty name can't trigger "There's no line here to end".
    header = [r"\begin{center}"]
    if name:
        header.append(r"{\LARGE\bfseries " + name + r"}\par\vspace{2pt}")
    if contact_line:
        header.append(r"{\small " + contact_line + r"}")
    header.append(r"\end{center}")
    if not name and not contact_line:
        header = []  # nothing to show — skip the empty centered block entirely

    # Order matches the target design: Experience → Projects → Skills → Education.
    body: list[str] = []
    body += _render_summary_section(content.get("summary", ""))
    body += _render_experience_section(content.get("experience", []))
    body += _render_projects_section(content.get("projects", []))
    body += _render_skills_section(content.get("skills", []))
    body += _render_education_section(content.get("education", []))

    lines = [RESUME_LATEX_PREAMBLE.strip(), r"\begin{document}", *header]
    if body:
        lines += [r"\vspace{2pt}", *body]
    elif not header:
        # Nothing to typeset — emit a blank page instead of a zero-page doc,
        # which Tectonic rejects ("cannot open .xdv") and would fall back on.
        lines.append(r"\null")
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
