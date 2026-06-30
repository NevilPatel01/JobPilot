import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.pipeline_helpers import PipelineState, emit, run_step
from app.agents.retry import invoke_llm
from app.schemas.resume_content import CoverLetterContent, ResumeContent, resume_to_text
from app.services.llm.client import create_chat_model, get_user_llm_config

logger = logging.getLogger(__name__)


async def generate_cover_letter(state: PipelineState, db: AsyncSession) -> PipelineState:
    if not state.get("create_cover_letter"):
        return state

    resume_id = state["resume_id"]
    await emit(resume_id, "agent_step", {"step": "cover_letter", "status": "running"})
    llm_config = await get_user_llm_config(db, state["user_id"])
    meta = state.get("cover_letter_meta") or {}
    company = state.get("company_research") or {}
    content = CoverLetterContent(
        recipient_name=meta.get("hiring_manager_name", ""),
        company_name=company.get("company_name") or state.get("company_name", ""),
        company_address=", ".join(filter(None, [meta.get("street_address"), meta.get("city"), meta.get("state_province"), meta.get("postal_code")])),
        date=meta.get("letter_date", ""),
        salutation=f"Dear {meta.get('hiring_manager_name') or 'Hiring Manager'},",
    )

    if llm_config:
        from app.services.cover_letter.generator import build_cover_letter_prompt, parse_cover_letter_response

        llm = create_chat_model(llm_config, temperature=0.5)
        resume_text = resume_to_text(ResumeContent.model_validate(state["content"]))
        prompt = build_cover_letter_prompt(
            meta=meta,
            company=company,
            jd_analysis=state.get("jd_analysis") or {},
            job_description=state.get("job_description", ""),
            resume_text=resume_text,
        )
        try:
            res = await invoke_llm(
                llm,
                [SystemMessage(content="Return valid JSON only."), HumanMessage(content=prompt)],
            )
            parsed = json.loads(res.content if isinstance(res.content, str) else str(res.content))
            content.paragraphs, content.closing = parse_cover_letter_response(parsed)
        except Exception as e:
            logger.warning("Cover letter generation failed: %s", e)
            content.paragraphs = ["I am excited to apply for this role and believe my experience is a strong fit."]

    state["cover_letter_content"] = content.model_dump()
    await run_step(db, resume_id, "cover_letter", "completed")
    await emit(resume_id, "agent_step", {"step": "cover_letter", "status": "completed"})
    return state
