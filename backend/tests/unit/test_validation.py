from app.agents.validation import guard_tailored_content


def test_guard_removes_invented_employer(sample_resume):
    tailored = {**sample_resume, "experience": [
        *sample_resume["experience"],
        {
            "id": "fake",
            "company": "Evil Corp Industries",
            "title": "CEO",
            "location": "",
            "start_date": "2020",
            "end_date": "2021",
            "bullets": ["Did bad things"],
        },
    ]}
    cleaned, warnings = guard_tailored_content(sample_resume, tailored)
    companies = [e["company"] for e in cleaned["experience"]]
    assert "Evil Corp Industries" not in companies
    assert any("Removed invented employer" in w for w in warnings)


def test_guard_keeps_valid_tailored_company(sample_resume):
    cleaned, warnings = guard_tailored_content(sample_resume, sample_resume)
    assert len(cleaned["experience"]) == len(sample_resume["experience"])
    assert not warnings


def test_guard_removes_invented_institution(sample_resume):
    tailored = {
        **sample_resume,
        "education": [
            {
                "id": "fake-edu",
                "institution": "Fake University",
                "degree": "PhD Astrology",
                "location": "",
                "start_date": "",
                "end_date": "",
                "gpa": "",
            }
        ],
    }
    cleaned, warnings = guard_tailored_content(sample_resume, tailored)
    institutions = [e["institution"] for e in cleaned["education"]]
    assert "Fake University" not in institutions
    assert any("Removed invented institution" in w for w in warnings)


def test_guard_keeps_added_skills_but_removes_invented_projects(sample_resume):
    tailored = {
        **sample_resume,
        # Added skill "Kubernetes" is now ALLOWED (ATS keyword coverage).
        "skills": [{"id": "new", "name": "Cloud", "skills": ["Python", "Kubernetes"]}],
        "projects": [
            *sample_resume["projects"],
            {"id": "fake", "name": "Global Banking Platform", "url": "", "bullets": ["Built it."]},
        ],
    }

    cleaned, warnings = guard_tailored_content(sample_resume, tailored)

    all_skills = {skill for group in cleaned["skills"] for skill in group["skills"]}
    assert "Kubernetes" in all_skills  # added skills are kept
    assert "Global Banking Platform" not in {project["name"] for project in cleaned["projects"]}
    assert any("Removed invented project" in warning for warning in warnings)


def test_guard_reverts_invented_numeric_claims(sample_resume):
    tailored = {
        **sample_resume,
        "summary": "Senior backend engineer with 20 years of experience.",
        "experience": [
            {
                **sample_resume["experience"][0],
                "bullets": ["Scaled the platform to 500M users and cut costs by 90%."],
            }
        ],
    }

    cleaned, warnings = guard_tailored_content(sample_resume, tailored)

    assert cleaned["summary"] == sample_resume["summary"]
    # Fabricated numbers (500M users, 90%) must not survive.
    bullets_text = " ".join(cleaned["experience"][0]["bullets"])
    assert "500" not in bullets_text
    assert "90%" not in bullets_text
    assert any("unsupported number" in warning for warning in warnings)
