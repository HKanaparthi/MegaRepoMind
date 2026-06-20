import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.models.user import User
from app.models.repository import Repository, RepoStatus
from app.models.chat import ChatSession, Message, MessageRole
from app.schemas.chat import CreateSessionRequest, SessionOut, SendMessageRequest, MessageOut
from app.api.deps import get_current_user
from app.services.chat_service import answer_question

router = APIRouter(tags=["chat"])


@router.get("/repositories/{repo_id}/sessions", response_model=list[SessionOut])
async def list_sessions(
    repo_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Repository).where(Repository.id == repo_id, Repository.user_id == current_user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Repository not found")

    sessions = await db.execute(
        select(ChatSession)
        .where(ChatSession.repository_id == repo_id, ChatSession.user_id == current_user.id)
        .order_by(ChatSession.created_at.desc())
    )
    return sessions.scalars().all()


@router.post("/repositories/{repo_id}/sessions", response_model=SessionOut, status_code=201)
async def create_session(
    repo_id: str,
    body: CreateSessionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Repository).where(Repository.id == repo_id, Repository.user_id == current_user.id)
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    if repo.status != RepoStatus.ready:
        raise HTTPException(status_code=400, detail=f"Repository is not ready (status: {repo.status})")

    session = ChatSession(
        id=str(uuid.uuid4()),
        repository_id=repo_id,
        user_id=current_user.id,
        title=body.title,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.get("/sessions/{session_id}/messages", response_model=list[MessageOut])
async def get_messages(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == current_user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Session not found")

    msgs = await db.execute(
        select(Message).where(Message.session_id == session_id).order_by(Message.created_at)
    )
    return msgs.scalars().all()


@router.post("/sessions/{session_id}/messages", response_model=MessageOut, status_code=201)
async def send_message(
    session_id: str,
    body: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == current_user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Store user message
    user_msg = Message(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role=MessageRole.user,
        content=body.content,
    )
    db.add(user_msg)
    await db.flush()

    # Get conversation history for context
    history_result = await db.execute(
        select(Message).where(Message.session_id == session_id).order_by(Message.created_at)
    )
    history = [{"role": m.role, "content": m.content} for m in history_result.scalars().all()]

    # Get AI answer with citations
    answer, citations = await answer_question(db, session.repository_id, body.content, history[:-1])

    # Update session title from first question
    if len(history) == 1:
        from sqlalchemy import update
        short_title = body.content[:60] + ("..." if len(body.content) > 60 else "")
        await db.execute(update(ChatSession).where(ChatSession.id == session_id).values(title=short_title))

    ai_msg = Message(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role=MessageRole.assistant,
        content=answer,
        citations=citations,
    )
    db.add(ai_msg)
    await db.commit()
    await db.refresh(ai_msg)
    return ai_msg
