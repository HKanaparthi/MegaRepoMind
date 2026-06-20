import uuid
from pathlib import Path
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.repository import Repository, RepositoryFile, Chunk, RepoStatus
from app.services.github_service import clone_repository, cleanup_clone, walk_files, parse_github_url
from app.services.chunking_service import chunk_code, get_language
from app.services.embedding_service import embed_texts
from app.core.config import settings


async def ingest_repository(db: AsyncSession, repository_id: str):
    result = await db.execute(select(Repository).where(Repository.id == repository_id))
    repo = result.scalar_one_or_none()
    if not repo:
        return

    await db.execute(
        update(Repository).where(Repository.id == repository_id).values(status=RepoStatus.indexing)
    )
    await db.commit()

    try:
        clone_dir = clone_repository(repo.github_url, repository_id)
        files = walk_files(clone_dir)

        file_count = 0
        chunk_count = 0
        BATCH_SIZE = 50

        for i, file_path in enumerate(files):
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore").replace("\x00", "")
                if not content.strip():
                    continue

                relative_path = str(file_path.relative_to(clone_dir))
                language = get_language(relative_path)
                lines = content.splitlines()

                db_file = RepositoryFile(
                    id=str(uuid.uuid4()),
                    repository_id=repository_id,
                    file_path=relative_path,
                    language=language,
                    size=file_path.stat().st_size,
                    line_count=len(lines),
                )
                db.add(db_file)

                text_chunks = chunk_code(content, language)
                if not text_chunks:
                    continue

                texts = [
                    f"File: {relative_path}\n\n{chunk.content}"
                    for chunk in text_chunks
                ]
                embeddings = embed_texts(texts)

                for chunk, embedding in zip(text_chunks, embeddings):
                    db_chunk = Chunk(
                        id=str(uuid.uuid4()),
                        repository_id=repository_id,
                        file_id=db_file.id,
                        content=f"File: {relative_path}\n\n{chunk.content}",
                        start_line=chunk.start_line,
                        end_line=chunk.end_line,
                        embedding=embedding,
                    )
                    db.add(db_chunk)
                    chunk_count += 1

                file_count += 1

            except Exception:
                continue

            if (i + 1) % BATCH_SIZE == 0:
                await db.commit()

        try:
            summary, tech_stack = await _generate_summary(repo.github_url, files, clone_dir)
        except Exception:
            summary, tech_stack = "Repository indexed successfully.", ""

        await db.execute(
            update(Repository).where(Repository.id == repository_id).values(
                status=RepoStatus.ready,
                file_count=file_count,
                chunk_count=chunk_count,
                indexed_at=datetime.now(timezone.utc),
                summary=summary,
                tech_stack=tech_stack,
            )
        )
        await db.commit()

    except Exception as e:
        await db.execute(
            update(Repository).where(Repository.id == repository_id).values(
                status=RepoStatus.failed,
                error_message=str(e)[:500],
            )
        )
        await db.commit()
    finally:
        cleanup_clone(repository_id)


async def _generate_summary(github_url: str, files: list[Path], clone_dir: str) -> tuple[str, str]:
    import anthropic
    from app.core.config import settings

    # Detect tech stack from file extensions
    ext_counts: dict[str, int] = {}
    for f in files:
        ext = f.suffix.lower()
        ext_counts[ext] = ext_counts.get(ext, 0) + 1

    top_exts = sorted(ext_counts.items(), key=lambda x: -x[1])[:10]
    ext_summary = ", ".join(f"{ext}({count})" for ext, count in top_exts)

    # Read key files for context
    key_files = ["README.md", "readme.md", "package.json", "requirements.txt",
                 "pyproject.toml", "go.mod", "Cargo.toml", "pom.xml"]
    context_parts = []
    for kf in key_files:
        kf_path = Path(clone_dir) / kf
        if kf_path.exists():
            try:
                content = kf_path.read_text(errors="ignore")[:2000]
                context_parts.append(f"=== {kf} ===\n{content}")
            except Exception:
                pass

    context = "\n\n".join(context_parts) or "No key files found."

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=settings.LLM_MODEL,
        max_tokens=600,
        messages=[{
            "role": "user",
            "content": f"""Analyze this repository: {github_url}

File extensions found: {ext_summary}

Key files:
{context}

Provide:
1. SUMMARY: A 2-3 sentence description of what this project does
2. TECH_STACK: A comma-separated list of the main technologies (e.g., React, FastAPI, PostgreSQL)

Format your response exactly as:
SUMMARY: <your summary here>
TECH_STACK: <tech1, tech2, tech3>"""
        }]
    )

    text = response.content[0].text
    summary = ""
    tech_stack = ""
    for line in text.splitlines():
        if line.startswith("SUMMARY:"):
            summary = line.replace("SUMMARY:", "").strip()
        elif line.startswith("TECH_STACK:"):
            tech_stack = line.replace("TECH_STACK:", "").strip()

    return summary or "Repository successfully indexed.", tech_stack or ext_summary
