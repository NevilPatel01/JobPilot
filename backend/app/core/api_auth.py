import hashlib
import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.api_key import UserApiToken
from app.models.user import User

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_user_from_api_token(
    api_key: str | None = Depends(api_key_header),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key required")

    token_hash = hashlib.sha256(api_key.encode()).hexdigest()
    result = await db.execute(select(UserApiToken).where(UserApiToken.token_hash == token_hash))
    token_row = result.scalar_one_or_none()
    if not token_row:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

    user_result = await db.execute(select(User).where(User.id == token_row.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    from datetime import datetime, timezone

    token_row.last_used_at = datetime.now(timezone.utc)
    await db.commit()
    return user


def generate_api_token() -> tuple[str, str, str]:
    raw = f"jp_{secrets.token_urlsafe(32)}"
    return raw, hashlib.sha256(raw.encode()).hexdigest(), raw[:12]
