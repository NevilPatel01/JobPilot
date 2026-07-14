"""Deterministic projects digest — the compact "one file" the resume pipeline reads.

Built purely from user-confirmed, non-prohibited project facts (no LLM).
Each block ends with a [fact:<uuid>] tag so generated resume bullets stay
traceable back to their evidence (validation.py enforces this)."""

from uuid import UUID

from sqlalchemy import select

from app.models.candidate import CandidateDigest, CandidateFact

DIGEST_KIND_GITHUB_PROJECTS = "github_projects"
DIGEST_TOKEN_CAP = 1500
_HIGHLIGHT_CHAR_CAP = 160


def estimate_tokens(text: str) -> int:
    return len(text) // 4


def _rank_key(fact: CandidateFact):
    payload = fact.payload or {}
    pinned = bool(payload.get("pinned"))
    stars = int(payload.get("stars") or 0)
    recency = str(payload.get("last_pushed") or "")
    return (not pinned, -stars, recency, str(payload.get("name") or ""), str(fact.id))


def _block(fact: CandidateFact, *, truncate_highlights: bool) -> str:
    payload = fact.payload or {}
    tech = ", ".join(payload.get("tech_stack") or [])
    stars = int(payload.get("stars") or 0)
    header_bits = [payload.get("name") or "unnamed", tech]
    if stars:
        header_bits.append(f"⭐{stars}")
    if payload.get("last_pushed"):
        header_bits.append(str(payload["last_pushed"]))
    highlights = [h.strip() for h in (payload.get("highlights") or []) if h.strip()]
    if truncate_highlights:
        highlights = [h[:_HIGHLIGHT_CHAR_CAP] for h in highlights[:2]]
    body_bits = [b for b in [payload.get("one_liner", "").strip(), ". ".join(highlights)] if b]
    return f"### {' | '.join(b for b in header_bits if b)}\n{'. '.join(body_bits)} [fact:{fact.id}]"


def build_projects_digest(facts: list[CandidateFact]) -> tuple[str, int]:
    eligible = sorted(
        (
            f
            for f in facts
            if f.fact_type == "project"
            and f.verification_status == "user_confirmed"
            and not f.is_prohibited
            and f.superseded_by_id is None
        ),
        key=_rank_key,
    )
    blocks: list[str] = []
    dropped = 0
    content = ""
    for index, fact in enumerate(eligible):
        block = _block(fact, truncate_highlights=False)
        candidate = "\n\n".join(blocks + [block])
        if estimate_tokens(candidate) > DIGEST_TOKEN_CAP:
            block = _block(fact, truncate_highlights=True)
            candidate = "\n\n".join(blocks + [block])
        if estimate_tokens(candidate) > DIGEST_TOKEN_CAP:
            # pinned projects always survive: evict the last non-pinned block instead
            if bool((fact.payload or {}).get("pinned")) and blocks:
                for i in range(len(blocks) - 1, -1, -1):
                    if "pinned-keep" not in blocks[i]:
                        blocks.pop(i)
                        dropped += 1
                        break
                blocks.append(block)
            else:
                dropped += 1
            continue
        blocks.append(block)
    content = "\n\n".join(blocks)
    if dropped:
        content = f"{content}\n\n+ {dropped} more projects omitted for brevity"
    return content, estimate_tokens(content)


async def get_or_create_digest_row(db, user_id: UUID, kind: str) -> CandidateDigest:
    row = (
        await db.execute(
            select(CandidateDigest).where(CandidateDigest.user_id == user_id, CandidateDigest.kind == kind)
        )
    ).scalar_one_or_none()
    if row is None:
        row = CandidateDigest(user_id=user_id, kind=kind, content_text="", sync_state_json={})
        db.add(row)
        await db.flush()
    return row


async def regenerate_github_projects_digest(db, user_id: UUID) -> CandidateDigest:
    facts = (
        (
            await db.execute(
                select(CandidateFact).where(
                    CandidateFact.user_id == user_id, CandidateFact.fact_type == "project"
                )
            )
        )
        .scalars()
        .all()
    )
    content, tokens = build_projects_digest(list(facts))
    row = await get_or_create_digest_row(db, user_id, DIGEST_KIND_GITHUB_PROJECTS)
    row.content_text = content
    row.token_estimate = tokens
    row.source_fact_ids = [f.id for f in facts if f.verification_status == "user_confirmed" and not f.is_prohibited]
    await db.flush()
    return row
