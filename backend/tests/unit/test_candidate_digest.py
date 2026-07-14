import uuid

from app.models.candidate import CandidateFact
from app.services.candidate.digest import DIGEST_TOKEN_CAP, build_projects_digest, estimate_tokens


def _project_fact(name, *, confirmed=True, pinned=False, stars=0, prohibited=False, highlights=None):
    return CandidateFact(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        fact_type="project",
        payload={
            "name": name,
            "url": f"https://github.com/u/{name}",
            "one_liner": f"{name} does things",
            "tech_stack": ["Python"],
            "highlights": highlights if highlights is not None else ["fast", "tested"],
            "stars": stars,
            "pinned": pinned,
            "origin": "github",
        },
        source="github_import",
        verification_status="user_confirmed" if confirmed else "unverified",
        is_prohibited=prohibited,
        superseded_by_id=None,
    )


def test_digest_includes_only_confirmed_non_prohibited_projects():
    facts = [
        _project_fact("keeper"),
        _project_fact("unconfirmed", confirmed=False),
        _project_fact("banned", prohibited=True),
    ]
    content, _ = build_projects_digest(facts)
    assert "keeper" in content
    assert "unconfirmed" not in content
    assert "banned" not in content


def test_digest_blocks_carry_fact_id_tags():
    fact = _project_fact("jobpilot")
    content, _ = build_projects_digest([fact])
    assert f"[fact:{fact.id}]" in content


def test_digest_is_deterministic():
    facts = [_project_fact("a", stars=5), _project_fact("b", stars=1)]
    assert build_projects_digest(facts) == build_projects_digest(facts)


def test_digest_orders_pinned_first():
    low = _project_fact("popular", stars=500)
    pinned = _project_fact("pet-project", stars=0, pinned=True)
    content, _ = build_projects_digest([low, pinned])
    assert content.index("pet-project") < content.index("popular")


def test_digest_respects_token_cap_and_keeps_pinned():
    facts = [_project_fact(f"proj-{i}", highlights=["x" * 300] * 5) for i in range(30)]
    pinned = _project_fact("must-stay", pinned=True)
    content, tokens = build_projects_digest(facts + [pinned])
    assert tokens <= DIGEST_TOKEN_CAP
    assert "must-stay" in content
    assert "+ " in content or "more" in content  # truncation marker for dropped projects


def test_estimate_tokens_roughly_chars_over_four():
    assert estimate_tokens("x" * 400) == 100
