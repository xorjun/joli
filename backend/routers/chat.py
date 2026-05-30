from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from ..database import get_db
from ..models import User, ChatSession, ChatMessage, MessageType, UserProfile
from ..schemas import ChatMessageIn, ChatSessionOut, ChatMessageOut
from ..auth import get_current_user
from ..services.ai_service import (
    chat_completion, get_chat_prompt, parse_profile_updates, strip_profile_updates_block,
)
from ..services.profile_engine import apply_profile_updates, calculate_profile_completeness

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.get("/sessions", response_model=list[ChatSessionOut])
async def list_sessions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == user.id)
        .order_by(ChatSession.updated_at.desc())
    )
    sessions = result.scalars().all()
    out = []
    for s in sessions:
        count_result = await db.execute(
            select(func.count(ChatMessage.id)).where(ChatMessage.session_id == s.id)
        )
        msg_count = count_result.scalar() or 0
        out.append(ChatSessionOut(
            id=s.id, title=s.title, created_at=s.created_at, updated_at=s.updated_at,
            message_count=msg_count,
        ))
    return out


@router.post("/sessions", response_model=ChatSessionOut, status_code=201)
async def create_session(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = ChatSession(user_id=user.id, title="Neuer Chat")
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return ChatSessionOut(
        id=session.id, title=session.title, created_at=session.created_at,
        updated_at=session.updated_at, message_count=0,
    )


@router.get("/sessions/{session_id}", response_model=list[ChatMessageOut])
async def get_session_messages(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = await db.get(ChatSession, session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    return result.scalars().all()


@router.post("/sessions/{session_id}/messages", response_model=ChatMessageOut)
async def send_message(
    session_id: str,
    body: ChatMessageIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = await db.get(ChatSession, session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get or create profile
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        profile = UserProfile(user_id=user.id, preferred_language=user.ui_language)
        db.add(profile)
        await db.flush()

    language = profile.preferred_language or "de"

    # Save user message
    user_msg = ChatMessage(
        session_id=session_id, role="user", content=body.content,
    )
    db.add(user_msg)

    # Get recent history for context
    history_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .limit(20)
    )
    history = history_result.scalars().all()

    messages_for_ai = []
    for msg in history:
        role = msg.role
        content = msg.content
        if msg.metadata_json and msg.metadata_json.get("visible_content"):
            content = msg.metadata_json["visible_content"]
        messages_for_ai.append({"role": role, "content": content})

    # Add the new user message
    messages_for_ai.append({"role": "user", "content": body.content})

    # Call AI
    system_prompt = get_chat_prompt(language)
    try:
        ai_response = await chat_completion(messages_for_ai, system_prompt=system_prompt)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI service error: {str(e)}")

    # Parse profile updates
    profile_updates = parse_profile_updates(ai_response)
    visible_content = strip_profile_updates_block(ai_response)

    # Auto-detect job URLs in user message
    import re
    url_match = re.search(r'https?://[^\s]+', body.content)
    detected_url = url_match.group(0) if url_match else None

    # Apply profile updates
    changes = []
    if profile_updates:
        changes = await apply_profile_updates(db, profile, profile_updates)

    # Recalculate completeness
    new_completeness = calculate_profile_completeness(profile)
    profile.profile_completeness = new_completeness

    # Update session title with first meaningful topic
    if session.title in ("Neuer Chat", "New Chat") and body.content:
        title = body.content[:80]
        session.title = title + ("..." if len(body.content) > 80 else "")

    # Save AI message
    metadata = {
        "visible_content": visible_content,
        "profile_updates": profile_updates,
        "profile_changes": changes,
        "profile_completeness": new_completeness,
        "detected_job_url": detected_url,
    }

    ai_msg = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=ai_response,
        message_type=MessageType.profile_question if profile_updates else MessageType.chat,
        metadata_json=metadata,
    )
    db.add(ai_msg)
    await db.commit()
    await db.refresh(ai_msg)

    return ChatMessageOut(
        id=ai_msg.id, session_id=ai_msg.session_id, role=ai_msg.role,
        content=ai_msg.content, message_type=ai_msg.message_type.value,
        metadata_json=ai_msg.metadata_json, created_at=ai_msg.created_at,
    )
