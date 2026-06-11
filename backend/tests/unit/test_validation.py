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
