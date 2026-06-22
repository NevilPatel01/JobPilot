import re

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rag_chunk import DocumentChunk
from app.services.llm.client import LLMConfig, create_embeddings, resolve_embeddings_config
from app.services.rag.chunker import chunk_resume_content, chunk_text

_TERM_RE = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9._+#/-]{2,}")


def _query_terms(query: str) -> list[str]:
    terms = [t.lower() for t in _TERM_RE.findall(query)]
    if terms:
        return terms[:24]
    return [t for t in query.lower().split() if t][:12]


def _keyword_score(text: str, terms: list[str]) -> int:
    lower = text.lower()
    return sum(lower.count(term) for term in terms)


async def delete_chunks(db: AsyncSession, user_id, source_type: str, source_id: str | None = None) -> None:
    q = delete(DocumentChunk).where(
        DocumentChunk.user_id == user_id,
        DocumentChunk.source_type == source_type,
    )
    if source_id is not None:
        q = q.where(DocumentChunk.source_id == source_id)
    await db.execute(q)


async def _search_chunks_keyword(
    db: AsyncSession,
    user_id,
    query: str,
    limit: int = 8,
    source_types: list[str] | None = None,
) -> list[DocumentChunk]:
    terms = _query_terms(query)
    stmt = select(DocumentChunk).where(DocumentChunk.user_id == user_id)
    if source_types:
        stmt = stmt.where(DocumentChunk.source_type.in_(source_types))
    result = await db.execute(stmt.limit(400))
    chunks = list(result.scalars().all())
    if not chunks:
        return []
    ranked = sorted(chunks, key=lambda c: _keyword_score(c.chunk_text, terms), reverse=True)
    return ranked[:limit]


async def ingest_text(
    db: AsyncSession,
    user_id,
    source_type: str,
    source_id: str | None,
    text_content: str,
    llm_config: LLMConfig,
) -> int:
    await delete_chunks(db, user_id, source_type, source_id)
    chunks = chunk_text(text_content)
    if not chunks:
        return 0

    embed_config = await resolve_embeddings_config(db, user_id, llm_config)
    if embed_config:
        embeddings = create_embeddings(embed_config)
        vectors = await embeddings.aembed_documents(chunks)
    else:
        vectors = [None] * len(chunks)

    for chunk, vector in zip(chunks, vectors):
        db.add(
            DocumentChunk(
                user_id=user_id,
                source_type=source_type,
                source_id=source_id,
                chunk_text=chunk,
                embedding=vector,
            )
        )
    await db.flush()
    return len(chunks)


async def ingest_resume_content(
    db: AsyncSession,
    user_id,
    content: dict,
    llm_config: LLMConfig,
    source_id: str = "profile",
) -> int:
    await delete_chunks(db, user_id, "profile", source_id)
    labeled = chunk_resume_content(content)
    if not labeled:
        return 0

    texts = [t for _, t in labeled]
    embed_config = await resolve_embeddings_config(db, user_id, llm_config)
    if embed_config:
        embeddings = create_embeddings(embed_config)
        vectors = await embeddings.aembed_documents(texts)
    else:
        vectors = [None] * len(texts)

    for (_, chunk), vector in zip(labeled, vectors):
        db.add(
            DocumentChunk(
                user_id=user_id,
                source_type="profile",
                source_id=source_id,
                chunk_text=chunk,
                embedding=vector,
            )
        )
    await db.flush()
    return len(labeled)


async def search_chunks(
    db: AsyncSession,
    user_id,
    query: str,
    llm_config: LLMConfig,
    limit: int = 8,
    source_types: list[str] | None = None,
) -> list[DocumentChunk]:
    embed_config = await resolve_embeddings_config(db, user_id, llm_config)
    if not embed_config:
        return await _search_chunks_keyword(db, user_id, query, limit, source_types)

    embeddings = create_embeddings(embed_config)
    query_vector = (await embeddings.aembed_query(query))[0]

    type_filter = ""
    params: dict = {"user_id": str(user_id), "limit": limit, "query_vec": str(query_vector)}
    if source_types:
        type_filter = "AND source_type = ANY(:source_types)"
        params["source_types"] = source_types

    sql = text(
        f"""
        SELECT id, user_id, source_type, source_id, chunk_text, created_at
        FROM document_chunks
        WHERE user_id = :user_id
          AND embedding IS NOT NULL
          {type_filter}
        ORDER BY embedding <=> :query_vec::vector
        LIMIT :limit
        """
    )
    result = await db.execute(sql, params)
    rows = result.fetchall()
    if rows:
        return [
            DocumentChunk(
                id=r[0],
                user_id=r[1],
                source_type=r[2],
                source_id=r[3],
                chunk_text=r[4],
            )
            for r in rows
        ]

    return await _search_chunks_keyword(db, user_id, query, limit, source_types)
