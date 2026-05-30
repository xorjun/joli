import os
import uuid
import re
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..models import User, UserProfile, Zeugnis
from ..schemas import ZeugnisOut
from ..auth import get_current_user
from ..services.ai_service import zeugnis_decode_completion

router = APIRouter(prefix="/api/zeugnisse", tags=["zeugnisse"])
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs", "zeugnisse")


@router.get("", response_model=list[ZeugnisOut])
async def list_zeugnisse(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        return []

    result = await db.execute(
        select(Zeugnis).where(Zeugnis.profile_id == profile.id).order_by(Zeugnis.date.desc())
    )
    return result.scalars().all()


@router.post("", response_model=ZeugnisOut, status_code=201)
async def upload_zeugnis(
    title: str = "Arbeitszeugnis",
    issuer: str = "",
    date: str = "",
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        profile = UserProfile(user_id=user.id)
        db.add(profile)
        await db.flush()

    os.makedirs(os.path.join(OUTPUT_DIR, user.id), exist_ok=True)
    file_id = str(uuid.uuid4())
    filepath = os.path.join(OUTPUT_DIR, user.id, f"{file_id}.pdf")

    contents = await file.read()
    with open(filepath, "wb") as f:
        f.write(contents)

    zeugnis = Zeugnis(
        profile_id=profile.id,
        title=title,
        issuer=issuer,
        date=date,
        file_path=filepath,
    )
    db.add(zeugnis)
    await db.commit()
    await db.refresh(zeugnis)
    return zeugnis


@router.get("/{zeugnis_id}", response_model=ZeugnisOut)
async def get_zeugnis(
    zeugnis_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    zeugnis = await db.get(Zeugnis, zeugnis_id)
    if not zeugnis:
        raise HTTPException(status_code=404, detail="Zeugnis not found")

    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if not profile or zeugnis.profile_id != profile.id:
        raise HTTPException(status_code=404, detail="Zeugnis not found")

    return zeugnis


@router.get("/{zeugnis_id}/download")
async def download_zeugnis(
    zeugnis_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    zeugnis = await db.get(Zeugnis, zeugnis_id)
    if not zeugnis or not os.path.exists(zeugnis.file_path):
        raise HTTPException(status_code=404, detail="File not found")

    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if not profile or zeugnis.profile_id != profile.id:
        raise HTTPException(status_code=404)

    return FileResponse(zeugnis.file_path, filename=f"{zeugnis.title}.pdf", media_type="application/pdf")


@router.post("/{zeugnis_id}/decode", response_model=ZeugnisOut)
async def decode_zeugnis(
    zeugnis_id: str,
    zeugnis_text: str = "",
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """AI-decode a German Arbeitszeugnis. Provide the text directly or it will use the stored PDF text."""
    zeugnis = await db.get(Zeugnis, zeugnis_id)
    if not zeugnis:
        raise HTTPException(status_code=404, detail="Zeugnis not found")

    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if not profile or zeugnis.profile_id != profile.id:
        raise HTTPException(status_code=404)

    text_to_decode = zeugnis_text.strip()
    if not text_to_decode:
        raise HTTPException(status_code=400, detail="Please provide the Arbeitszeugnis text to decode")

    try:
        decoded = await zeugnis_decode_completion(text_to_decode)
        zeugnis.ai_decoded_summary = decoded

        # Try to extract grade
        grade_match = re.search(r'Gesamtnote[:\s]*([1-5])', decoded)
        if grade_match:
            zeugnis.ai_decoded_grade = grade_match.group(1)

        await db.commit()
        await db.refresh(zeugnis)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Decoding error: {str(e)}")

    return zeugnis
