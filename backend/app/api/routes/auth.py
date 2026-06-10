from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import AuthCallbackRequest, TokenResponse, UserResponse
from app.core.auth import create_access_token
from app.core.database import get_db
from app.models.user import User

router = APIRouter()


@router.post("/callback", response_model=TokenResponse)
async def auth_callback(body: AuthCallbackRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).where(User.oauth_provider == body.oauth_provider, User.oauth_id == body.oauth_id)
    )
    user = result.scalar_one_or_none()

    if user:
        user.email = body.email
        user.name = body.name
        user.avatar_url = body.avatar_url
    else:
        user = User(
            oauth_provider=body.oauth_provider,
            oauth_id=body.oauth_id,
            email=body.email,
            name=body.name,
            avatar_url=body.avatar_url,
        )
        db.add(user)

    await db.commit()
    await db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))
