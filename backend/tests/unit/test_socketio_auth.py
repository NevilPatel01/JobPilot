import uuid

import pytest
import socketio

from app.core.auth import create_access_token
from app.sockets import chat as chat_module


@pytest.mark.asyncio
async def test_connect_without_token_is_rejected(monkeypatch):
    calls = []

    async def _reject(*a, **kw):
        calls.append(a)
        raise socketio.exceptions.ConnectionRefusedError("unauthenticated")

    # connect() should raise ConnectionRefusedError when no token is present in auth
    with pytest.raises(socketio.exceptions.ConnectionRefusedError):
        await chat_module.connect("sid-1", {}, auth=None)


@pytest.mark.asyncio
async def test_connect_with_valid_token_is_accepted():
    user_id = str(uuid.uuid4())
    token = create_access_token({"sub": user_id})
    # should not raise
    await chat_module.connect("sid-2", {}, auth={"token": token})
    assert chat_module._SESSION_USERS.get("sid-2") == user_id


@pytest.mark.asyncio
async def test_join_room_rejects_room_for_other_user():
    user_id = str(uuid.uuid4())
    other_user_id = str(uuid.uuid4())
    token = create_access_token({"sub": user_id})
    await chat_module.connect("sid-3", {}, auth={"token": token})

    with pytest.raises(PermissionError):
        await chat_module.join_room("sid-3", {"room": f"user:{other_user_id}"})


@pytest.mark.asyncio
async def test_join_room_allows_own_resume_room_format():
    # resume:{uuid} rooms are allowed for any authenticated connection today
    # (ownership of the specific resume is checked at the HTTP layer when the
    # resume was created; Socket.IO only verifies the connection is authenticated,
    # not per-resume ownership, since resume_id ownership isn't known to the
    # socket layer without an extra DB round trip — tracked as a follow-up,
    # not blocking this task, which fixes the "zero auth at all" gap first).
    user_id = str(uuid.uuid4())
    token = create_access_token({"sub": user_id})
    await chat_module.connect("sid-4", {}, auth={"token": token})
    # The real python-socketio AsyncServer registers the sid with its internal
    # room-tracking manager during the handshake (before the connect handler
    # runs), which sio.enter_room() relies on. Calling chat_module.connect()
    # directly bypasses that handshake step, so we register the sid with the
    # manager here to faithfully simulate a real connection. AsyncManager.connect()
    # normally assigns a server-generated sid, but this test (like the app code
    # under test) treats "sid-4" as the app-level sid throughout, so we register
    # that exact sid using the same two basic_enter_room calls BaseManager.connect
    # performs internally.
    chat_module.sio.manager.basic_enter_room("sid-4", "/", None, eio_sid="sid-4")
    chat_module.sio.manager.basic_enter_room("sid-4", "/", "sid-4", eio_sid="sid-4")
    await chat_module.join_room("sid-4", {"room": "resume:11111111-1111-1111-1111-111111111111"})
