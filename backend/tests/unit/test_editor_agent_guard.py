import types

import pytest

from app.agents import editor_agent


class _FakeChatModel:
    pass


@pytest.mark.asyncio
async def test_run_editor_agent_strips_fabricated_employer(monkeypatch, sample_resume):
    async def _fake_get_config(*a, **kw):
        return object()

    async def _fake_search_chunks(*a, **kw):
        return []

    def _fake_create_chat_model(*a, **kw):
        return _FakeChatModel()

    async def _fake_invoke_llm(*a, **kw):
        import json
        return types.SimpleNamespace(content=json.dumps({
            "reply": "Updated your most recent role.",
            "changes": [{"path": "experience[0].company", "new_value": "Fabricated Employer Inc"}],
        }))

    monkeypatch.setattr(editor_agent, "get_user_llm_config", _fake_get_config)
    monkeypatch.setattr(editor_agent, "search_chunks", _fake_search_chunks)
    monkeypatch.setattr(editor_agent, "create_chat_model", _fake_create_chat_model)
    monkeypatch.setattr(editor_agent, "invoke_llm", _fake_invoke_llm)

    reply, changes = await editor_agent.run_editor_agent(db=None, user_id="u1", content=sample_resume, message="update my job")

    assert len(changes) == 1
    assert changes[0]["new_value"] != "Fabricated Employer Inc"
