"""GitHub public-repo sync → draft project facts.

Public API only (no token; ~60 req/h unauthenticated is plenty for ≤25 repos).
Per-repo README summaries are cached in candidate_digests.sync_state_json keyed
by README sha, so an unchanged repo costs zero LLM calls on re-sync. Drafts are
returned for review — nothing persists until /candidate/import/confirm."""

import base64
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from uuid import UUID

import httpx
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field, ValidationError

from app.agents.json_utils import extract_json_object
from app.agents.retry import invoke_llm
from app.schemas.candidate import CandidateFactCreate
from app.services.audit import record_audit_event
from app.services.candidate.digest import DIGEST_KIND_GITHUB_PROJECTS, get_or_create_digest_row
from app.services.llm.client import create_chat_model, get_user_llm_config

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"
GITHUB_MAX_REPOS = 25
GITHUB_STALE_YEARS = 4
GITHUB_SUMMARY_PROMPT_VERSION = "gh-v1"
_README_CHAR_CAP = 4000

_SUMMARY_SYSTEM_PROMPT = (
    "Summarize this GitHub repository README for a resume project brief. Return JSON: "
    '{"one_liner": str, "what_it_does": str, "tech_stack": [str], '
    '"notable_features": [str, max 3], "metrics_from_readme": [str]}. '
    "Only include claims present in the README or metadata. Do not infer impact numbers."
)


class ProjectSummary(BaseModel):
    one_liner: str = Field("", max_length=300)
    what_it_does: str = Field("", max_length=1000)
    tech_stack: list[str] = Field(default_factory=list, max_length=20)
    notable_features: list[str] = Field(default_factory=list, max_length=3)
    metrics_from_readme: list[str] = Field(default_factory=list, max_length=5)


@dataclass
class GitHubSyncResult:
    draft_facts: list[CandidateFactCreate] = field(default_factory=list)
    skipped_unchanged: int = 0
    rate_limited: bool = False
    warning: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0


def filter_repos(repos: list[dict]) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=365 * GITHUB_STALE_YEARS)
    kept = []
    for repo in repos:
        if repo.get("fork") or repo.get("archived") or not repo.get("size"):
            continue
        pushed_raw = repo.get("pushed_at") or ""
        try:
            pushed = datetime.strptime(pushed_raw, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if pushed < cutoff:
            continue
        kept.append(repo)
    kept.sort(key=lambda r: r.get("pushed_at") or "", reverse=True)
    return kept[:GITHUB_MAX_REPOS]


def _strip_readme(markdown: str) -> str:
    text = re.sub(r"\[!\[[^\]]*\]\([^)]*\)\]\([^)]*\)|!\[[^\]]*\]\([^)]*\)", "", markdown)  # badges/images
    text = re.sub(r"<[^>]+>", "", text)  # html
    return text.strip()[:_README_CHAR_CAP]


def _is_rate_limited(response) -> bool:
    return response.status_code == 403 and response.headers.get("X-RateLimit-Remaining") == "0"


def _fallback_summary(repo: dict) -> dict:
    return ProjectSummary(one_liner=repo.get("description") or "").model_dump()


def _build_payload(repo: dict, summary: dict, languages: list[str]) -> dict:
    tech = list(dict.fromkeys(languages + (repo.get("topics") or []) + (summary.get("tech_stack") or [])))
    pushed = (repo.get("pushed_at") or "")[:10] or None
    return {
        "name": repo.get("name") or repo.get("full_name", "unnamed"),
        "url": repo.get("html_url") or "",
        "one_liner": summary.get("one_liner") or (repo.get("description") or ""),
        "description": summary.get("what_it_does") or "",
        "tech_stack": tech,
        "highlights": (summary.get("notable_features") or []) + (summary.get("metrics_from_readme") or []),
        "stars": int(repo.get("stargazers_count") or 0),
        "last_pushed": pushed,
        "origin": "github",
    }


async def _summarize_readme(chat_model, repo: dict, readme_text: str, result: GitHubSyncResult) -> dict:
    if not readme_text or chat_model is None:
        return _fallback_summary(repo)
    prompt = f"Repository: {repo.get('full_name')}\nDescription: {repo.get('description') or ''}\n\nREADME:\n{readme_text}"
    try:
        response = await invoke_llm(chat_model, [SystemMessage(content=_SUMMARY_SYSTEM_PROMPT), HumanMessage(content=prompt)])
        usage = getattr(response, "usage_metadata", None) or {}
        result.input_tokens += int(usage.get("input_tokens") or 0)
        result.output_tokens += int(usage.get("output_tokens") or 0)
        return ProjectSummary.model_validate(extract_json_object(response.content)).model_dump()
    except (ValueError, ValidationError, json.JSONDecodeError) as exc:
        logger.warning("github summary failed for %s: %s — metadata fallback", repo.get("full_name"), exc)
        return _fallback_summary(repo)


async def resolve_github_username(user, http_client) -> str | None:
    if user.oauth_provider == "github" and user.oauth_id:
        response = await http_client.get(f"{GITHUB_API}/user/{user.oauth_id}")
        if response.status_code == 200:
            return response.json().get("login")
    return None


async def sync_github_projects(
    db,
    user_id: UUID,
    username: str,
    *,
    http_client=None,
    chat_model=None,
    model_name: str | None = None,
) -> GitHubSyncResult:
    result = GitHubSyncResult()
    owns_client = http_client is None
    if owns_client:
        http_client = httpx.AsyncClient(timeout=20, headers={"Accept": "application/vnd.github+json"})

    if chat_model is None:
        llm_config = await get_user_llm_config(db, user_id)
        if llm_config:
            chat_model = create_chat_model(llm_config, temperature=0.0)
            model_name = model_name or llm_config.model_name

    digest_row = await get_or_create_digest_row(db, user_id, DIGEST_KIND_GITHUB_PROJECTS)
    sync_state: dict = dict(digest_row.sync_state_json or {})

    try:
        repos_response = await http_client.get(
            f"{GITHUB_API}/users/{username}/repos", params={"per_page": 100, "sort": "pushed", "type": "owner"}
        )
        if _is_rate_limited(repos_response):
            result.rate_limited = True
            result.warning = "GitHub rate limit reached — try again later."
            return result
        if repos_response.status_code != 200:
            result.warning = f"GitHub returned {repos_response.status_code} for user '{username}'."
            return result

        for repo in filter_repos(repos_response.json()):
            full_name = repo["full_name"]
            readme_response = await http_client.get(f"{GITHUB_API}/repos/{full_name}/readme")
            if _is_rate_limited(readme_response):
                result.rate_limited = True
                result.warning = "GitHub rate limit reached mid-sync — partial results."
                break
            readme_sha = ""
            readme_text = ""
            if readme_response.status_code == 200:
                body = readme_response.json()
                readme_sha = body.get("sha") or ""
                try:
                    readme_text = _strip_readme(base64.b64decode(body.get("content") or "").decode("utf-8", "ignore"))
                except Exception:  # malformed base64 — treat as no readme
                    readme_text = ""
            elif not repo.get("description"):
                continue  # no readme and no description: nothing truthful to say

            cached = sync_state.get(full_name) or {}
            if cached.get("sha") == readme_sha and cached.get("summary") is not None:
                summary = cached["summary"]
                result.skipped_unchanged += 1
            else:
                lang_response = await http_client.get(f"{GITHUB_API}/repos/{full_name}/languages")
                languages = list(lang_response.json().keys()) if lang_response.status_code == 200 else []
                summary = await _summarize_readme(chat_model, repo, readme_text, result)
                summary["_languages"] = languages
                sync_state[full_name] = {"sha": readme_sha, "summary": summary}

            payload = _build_payload(repo, summary, summary.get("_languages") or [])
            result.draft_facts.append(
                CandidateFactCreate(fact_type="project", payload=payload, source="github_import")
            )

        digest_row.sync_state_json = sync_state
        await db.flush()
        await record_audit_event(
            db,
            user_id=user_id,
            action="candidate_fact.github_sync",
            entity_type="users",
            entity_id=str(user_id),
            model_name=model_name,
            prompt_version=GITHUB_SUMMARY_PROMPT_VERSION,
            after={
                "username": username,
                "drafts": len(result.draft_facts),
                "skipped_unchanged": result.skipped_unchanged,
                "rate_limited": result.rate_limited,
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
            },
        )
        return result
    finally:
        if owns_client:
            await http_client.aclose()
