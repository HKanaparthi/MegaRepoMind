from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.services.embedding_service import embed_query
from app.core.config import settings


async def retrieve_chunks(db: AsyncSession, repository_id: str, question: str) -> list[dict]:
    query_embedding = embed_query(question)
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

    sql = text("""
        SELECT
            c.id,
            c.content,
            c.start_line,
            c.end_line,
            f.file_path,
            f.language,
            1 - (c.embedding <=> CAST(:embedding AS vector)) AS score
        FROM chunks c
        JOIN repository_files f ON f.id = c.file_id
        WHERE c.repository_id = :repo_id
          AND c.embedding IS NOT NULL
        ORDER BY c.embedding <=> CAST(:embedding AS vector)
        LIMIT :top_k
    """)

    result = await db.execute(sql, {
        "embedding": embedding_str,
        "repo_id": repository_id,
        "top_k": settings.TOP_K_CHUNKS,
    })

    rows = result.fetchall()
    return [
        {
            "id": row.id,
            "content": row.content,
            "start_line": row.start_line,
            "end_line": row.end_line,
            "file_path": row.file_path,
            "language": row.language,
            "score": float(row.score),
        }
        for row in rows
        if float(row.score) > 0.3  # filter low-relevance chunks
    ]
