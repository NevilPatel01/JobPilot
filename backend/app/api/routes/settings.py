from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import ApiKeyCreate, ApiKeyResponse, ApiTokenCreate, ApiTokenCreatedResponse, ApiTokenResponse
from app.core.api_auth import generate_api_token
from app.core.auth import get_current_user
from app.core.crypto import encrypt_value
from app.core.database import get_db
from app.models.api_key import UserApiKey, UserApiToken
from app.models.user import User
from app.services.llm.client import LLMConfig, test_api_key

router = APIRouter()


def _mask_key(key: str) -> str:
    if len(key) <= 8:
        return "****"
    return key[:4] + "..." + key[-4:]


@router.get("/api-keys", response_model=list[ApiKeyResponse])
async def list_api_keys(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserApiKey).where(UserApiKey.user_id == user.id))
    keys = result.scalars().all()
    return [
        ApiKeyResponse(
            id=k.id,
            provider=k.provider,
            api_key_masked=_mask_key("placeholder"),
            base_url=k.base_url,
            model_name=k.model_name,
            embedding_model=k.embedding_model,
            is_default=k.is_default,
        )
        for k in keys
    ]


@router.put("/api-keys", response_model=ApiKeyResponse)
async def upsert_api_key(
    body: ApiKeyCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserApiKey).where(UserApiKey.user_id == user.id, UserApiKey.provider == body.provider)
    )
    existing = result.scalar_one_or_none()

    if body.is_default:
        others = await db.execute(select(UserApiKey).where(UserApiKey.user_id == user.id))
        for k in others.scalars().all():
            k.is_default = False

    if existing:
        existing.api_key_enc = encrypt_value(body.api_key)
        existing.base_url = body.base_url
        existing.model_name = body.model_name
        existing.embedding_model = body.embedding_model
        existing.is_default = body.is_default
        key_row = existing
    else:
        key_row = UserApiKey(
            user_id=user.id,
            provider=body.provider,
            api_key_enc=encrypt_value(body.api_key),
            base_url=body.base_url,
            model_name=body.model_name,
            embedding_model=body.embedding_model,
            is_default=body.is_default,
        )
        db.add(key_row)

    await db.commit()
    await db.refresh(key_row)
    return ApiKeyResponse(
        id=key_row.id,
        provider=key_row.provider,
        api_key_masked=_mask_key(body.api_key),
        base_url=key_row.base_url,
        model_name=key_row.model_name,
        embedding_model=key_row.embedding_model,
        is_default=key_row.is_default,
    )


@router.post("/api-keys/test")
async def test_user_api_key(
    body: ApiKeyCreate,
    user: User = Depends(get_current_user),
):
    config = LLMConfig(
        provider=body.provider,
        api_key=body.api_key,
        base_url=body.base_url,
        model_name=body.model_name or "gpt-4o-mini",
        embedding_model=body.embedding_model or "text-embedding-3-small",
    )
    ok = await test_api_key(config)
    if not ok:
        raise HTTPException(status_code=400, detail="API key validation failed")
    return {"ok": True}


@router.delete("/api-keys/{key_id}")
async def delete_api_key(
    key_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID

    result = await db.execute(select(UserApiKey).where(UserApiKey.id == UUID(key_id), UserApiKey.user_id == user.id))
    key_row = result.scalar_one_or_none()
    if not key_row:
        raise HTTPException(status_code=404, detail="API key not found")
    await db.delete(key_row)
    await db.commit()
    return {"ok": True}


@router.get("/api-tokens", response_model=list[ApiTokenResponse])
async def list_api_tokens(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserApiToken).where(UserApiToken.user_id == user.id))
    return [ApiTokenResponse.model_validate(t) for t in result.scalars().all()]


@router.post("/api-tokens", response_model=ApiTokenCreatedResponse)
async def create_api_token(
    body: ApiTokenCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    raw, token_hash, prefix = generate_api_token()
    row = UserApiToken(user_id=user.id, name=body.name, token_hash=token_hash, token_prefix=prefix)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return ApiTokenCreatedResponse(
        id=row.id,
        name=row.name,
        token_prefix=row.token_prefix,
        created_at=row.created_at,
        last_used_at=row.last_used_at,
        token=raw,
    )


@router.delete("/api-tokens/{token_id}")
async def delete_api_token(
    token_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID

    result = await db.execute(select(UserApiToken).where(UserApiToken.id == UUID(token_id), UserApiToken.user_id == user.id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Token not found")
    await db.delete(row)
    await db.commit()
    return {"ok": True}
