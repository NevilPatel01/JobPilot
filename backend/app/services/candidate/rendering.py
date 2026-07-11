"""Derive a ResumeContent rendering from candidate_facts — the single write
path for user_profiles_structured.content_json going forward (see
docs/product/TARGET_DATA_MODEL.md §9b)."""

from app.models.candidate import CandidateFact
from app.schemas.resume_content import (
    ContactInfo, EducationEntry, ExperienceEntry, ProjectEntry, ResumeContent, SkillCategory,
)


def render_content_json(facts: list[CandidateFact]) -> ResumeContent:
    visible = [f for f in facts if not f.is_prohibited]

    contact = ContactInfo()
    for f in visible:
        if f.fact_type == "personal":
            contact.full_name = f.payload.get("full_name", contact.full_name)
            contact.location = f.payload.get("location", contact.location)
        elif f.fact_type == "contact":
            contact.email = f.payload.get("email", contact.email)
            contact.phone = f.payload.get("phone", contact.phone)

    summary = ""
    experience: list[ExperienceEntry] = []
    education: list[EducationEntry] = []
    projects: list[ProjectEntry] = []
    skills: list[SkillCategory] = []

    for f in visible:
        p = f.payload
        if f.fact_type == "employment":
            experience.append(ExperienceEntry(
                id=str(f.id), company=p.get("company", ""), title=p.get("title", ""),
                location=p.get("location", ""), start_date=p.get("start_date", ""),
                end_date=p.get("end_date", ""), bullets=p.get("bullets", []),
            ))
        elif f.fact_type == "education":
            education.append(EducationEntry(
                id=str(f.id), institution=p.get("institution", ""), degree=p.get("degree", ""),
                location=p.get("location", ""), start_date=p.get("start_date", ""),
                end_date=p.get("end_date", ""), gpa=p.get("gpa", ""),
            ))
        elif f.fact_type == "project":
            projects.append(ProjectEntry(
                id=str(f.id), name=p.get("name", ""), url=p.get("url", ""),
                github_url=p.get("github_url", ""), bullets=p.get("bullets", []),
            ))
        elif f.fact_type == "skill":
            skills.append(SkillCategory(
                id=str(f.id), name=p.get("category", p.get("name", "")), skills=p.get("skills", []),
            ))
        elif f.fact_type == "target_role" and not summary:
            summary = p.get("summary", "")

    return ResumeContent(
        contact=contact, summary=summary, experience=experience,
        education=education, projects=projects, skills=skills,
    )
