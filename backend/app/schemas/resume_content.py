import uuid

from pydantic import BaseModel, Field


def new_id() -> str:
    return str(uuid.uuid4())


class ContactInfo(BaseModel):
    full_name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""


class LinkItem(BaseModel):
    id: str = Field(default_factory=new_id)
    label: str = ""
    url: str = ""


class ExperienceEntry(BaseModel):
    id: str = Field(default_factory=new_id)
    company: str = ""
    title: str = ""
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    bullets: list[str] = Field(default_factory=list)


class EducationEntry(BaseModel):
    id: str = Field(default_factory=new_id)
    institution: str = ""
    degree: str = ""
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    gpa: str = ""


class ProjectEntry(BaseModel):
    id: str = Field(default_factory=new_id)
    name: str = ""
    url: str = ""
    bullets: list[str] = Field(default_factory=list)


class SkillCategory(BaseModel):
    id: str = Field(default_factory=new_id)
    name: str = ""
    skills: list[str] = Field(default_factory=list)


class ResumeContent(BaseModel):
    contact: ContactInfo = Field(default_factory=ContactInfo)
    links: list[LinkItem] = Field(default_factory=list)
    summary: str = ""
    experience: list[ExperienceEntry] = Field(default_factory=list)
    education: list[EducationEntry] = Field(default_factory=list)
    projects: list[ProjectEntry] = Field(default_factory=list)
    skills: list[SkillCategory] = Field(default_factory=list)


class CoverLetterContent(BaseModel):
    recipient_name: str = ""
    recipient_title: str = ""
    company_name: str = ""
    company_address: str = ""
    date: str = ""
    salutation: str = ""
    paragraphs: list[str] = Field(default_factory=list)
    closing: str = "Sincerely,"


def empty_resume_content() -> ResumeContent:
    return ResumeContent()


def resume_to_text(content: ResumeContent) -> str:
    parts: list[str] = []
    c = content.contact
    if c.full_name:
        parts.append(c.full_name)
    if c.email:
        parts.append(c.email)
    if content.summary:
        parts.append(content.summary)
    for exp in content.experience:
        parts.append(f"{exp.title} at {exp.company}")
        parts.extend(exp.bullets)
    for edu in content.education:
        parts.append(f"{edu.degree} {edu.institution}")
    for proj in content.projects:
        parts.append(proj.name)
        parts.extend(proj.bullets)
    for cat in content.skills:
        parts.append(f"{cat.name}: {', '.join(cat.skills)}")
    return "\n".join(parts)
