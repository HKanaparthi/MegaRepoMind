import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.models.user import User
from app.models.repository import Repository, RepositoryFile, RepoStatus
from app.schemas.repository import AddRepositoryRequest, RepositoryOut, FileOut
from app.api.deps import get_current_user
from app.services.github_service import parse_github_url

router = APIRouter(prefix="/repositories", tags=["repositories"])


@router.get("", response_model=list[RepositoryOut])
async def list_repositories(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Repository).where(Repository.user_id == current_user.id).order_by(Repository.created_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=RepositoryOut, status_code=201)
async def add_repository(
    body: AddRepositoryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        _, repo_name = parse_github_url(body.github_url)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid GitHub URL")

    repo = Repository(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        github_url=body.github_url,
        name=repo_name,
        status=RepoStatus.pending,
    )
    db.add(repo)
    await db.commit()
    await db.refresh(repo)

    from app.workers.tasks import index_repository_task
    index_repository_task.delay(repo.id)

    return repo


@router.get("/{repo_id}", response_model=RepositoryOut)
async def get_repository(
    repo_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Repository).where(Repository.id == repo_id, Repository.user_id == current_user.id)
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo


@router.delete("/{repo_id}", status_code=204)
async def delete_repository(
    repo_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Repository).where(Repository.id == repo_id, Repository.user_id == current_user.id)
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    await db.delete(repo)
    await db.commit()


@router.get("/{repo_id}/files", response_model=list[FileOut])
async def list_files(
    repo_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Repository).where(Repository.id == repo_id, Repository.user_id == current_user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Repository not found")

    files_result = await db.execute(
        select(RepositoryFile).where(RepositoryFile.repository_id == repo_id).order_by(RepositoryFile.file_path)
    )
    return files_result.scalars().all()
