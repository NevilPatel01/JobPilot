import logging

import socketio
from jose import JWTError, jwt

from app.core.config import settings

logger = logging.getLogger(__name__)

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins=settings.cors_origins)

# sid -> user_id (str). In-memory only; acceptable because Socket.IO sessions
# are themselves in-memory per-worker state, same lifetime as this map.
_SESSION_USERS: dict[str, str] = {}


def _user_id_from_token(token: str | None) -> str | None:
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None
    return payload.get("sub")


@sio.event
async def connect(sid, environ, auth=None):
    user_id = _user_id_from_token((auth or {}).get("token"))
    if not user_id:
        logger.info("[Socket] Rejected unauthenticated connection: %s", sid)
        raise socketio.exceptions.ConnectionRefusedError("unauthenticated")
    _SESSION_USERS[sid] = user_id
    logger.info("[Socket] Client connected: %s (user %s)", sid, user_id)


@sio.event
async def disconnect(sid):
    _SESSION_USERS.pop(sid, None)
    logger.info("[Socket] Client disconnected: %s", sid)


@sio.event
async def join_room(sid, data):
    room = data.get("room")
    if not room:
        return
    user_id = _SESSION_USERS.get(sid)
    if not user_id:
        raise PermissionError("not authenticated")
    # user:{id} rooms may only be joined by that same user.
    if room.startswith("user:") and room != f"user:{user_id}":
        raise PermissionError("cannot join another user's room")
    await sio.enter_room(sid, room)


@sio.event
async def send_message(sid, data):
    room = data.get("room")
    if room:
        await sio.emit("receive_message", data, room=room)


async def emit_to_room(event: str, data: dict, room: str) -> None:
    await sio.emit(event, data, room=room)
