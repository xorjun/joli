import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from ..database import get_db
from ..models import (
    User, UserProfile, WorkExperience, Education, LanguageSkill, TechSkill, Certificate
)
from ..schemas import (
    ProfileOut, ProfileUpdate,
    WorkExperienceIn, WorkExperienceOut,
    EducationIn, EducationOut,
    LanguageSkillIn, LanguageSkillOut,
    TechSkillIn, TechSkillOut,
)
from ..auth import get_current_user

router = APIRouter(prefix="/api/profile", tags=["profile"])
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")


@router.get("/me", response_model=ProfileOut)
async def get_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserProfile)
        .where(UserProfile.user_id == user.id)
        .options(
            selectinload(UserProfile.work_experiences),
            selectinload(UserProfile.educations),
            selectinload(UserProfile.language_skills),
            selectinload(UserProfile.tech_skills),
            selectinload(UserProfile.certificates),
            selectinload(UserProfile.zeugnisse),
        )
    )
    profile = result.scalar_one_or_none()
    if not profile:
        profile = UserProfile(user_id=user.id)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
    return profile


@router.put("/me", response_model=ProfileOut)
async def update_profile(
    body: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserProfile)
        .where(UserProfile.user_id == user.id)
        .options(
            selectinload(UserProfile.work_experiences),
            selectinload(UserProfile.educations),
            selectinload(UserProfile.language_skills),
            selectinload(UserProfile.tech_skills),
            selectinload(UserProfile.certificates),
            selectinload(UserProfile.zeugnisse),
        )
    )
    profile = result.scalar_one_or_none()
    if not profile:
        profile = UserProfile(user_id=user.id)
        db.add(profile)

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    await db.commit()
    await db.refresh(profile)
    return profile


@router.post("/photo")
async def upload_photo(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files allowed")

    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        profile = UserProfile(user_id=user.id)
        db.add(profile)

    photos_dir = os.path.join(OUTPUT_DIR, "photos")
    os.makedirs(photos_dir, exist_ok=True)
    ext = os.path.splitext(file.filename or "photo.jpg")[1] or ".jpg"
    filename = f"{user.id}{ext}"
    filepath = os.path.join(photos_dir, filename)

    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Photo too large (max 5MB)")

    with open(filepath, "wb") as f:
        f.write(contents)

    profile.photo_path = filepath
    await db.commit()

    return {"photo_path": filepath}


@router.get("/photo")
async def get_photo(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if not profile or not profile.photo_path or not os.path.exists(profile.photo_path):
        raise HTTPException(status_code=404, detail="No photo")

    from fastapi.responses import FileResponse
    return FileResponse(profile.photo_path)


# ---- Experience CRUD ----

@router.post("/experience", response_model=WorkExperienceOut, status_code=201)
async def add_experience(body: WorkExperienceIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        profile = UserProfile(user_id=user.id)
        db.add(profile)
        await db.flush()

    exp = WorkExperience(profile_id=profile.id, **body.model_dump())
    db.add(exp)
    await db.commit()
    await db.refresh(exp)
    return exp


@router.delete("/experience/{exp_id}", status_code=204)
async def delete_experience(exp_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404)
    exp = await db.get(WorkExperience, exp_id)
    if not exp or exp.profile_id != profile.id:
        raise HTTPException(status_code=404)
    await db.delete(exp)
    await db.commit()


# ---- Education CRUD ----

@router.post("/education", response_model=EducationOut, status_code=201)
async def add_education(body: EducationIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        profile = UserProfile(user_id=user.id)
        db.add(profile)
        await db.flush()

    edu = Education(profile_id=profile.id, **body.model_dump())
    db.add(edu)
    await db.commit()
    await db.refresh(edu)
    return edu


@router.delete("/education/{edu_id}", status_code=204)
async def delete_education(edu_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404)
    edu = await db.get(Education, edu_id)
    if not edu or edu.profile_id != profile.id:
        raise HTTPException(status_code=404)
    await db.delete(edu)
    await db.commit()


# ---- Language Skills CRUD ----

@router.post("/languages", response_model=LanguageSkillOut, status_code=201)
async def add_language_skill(body: LanguageSkillIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        profile = UserProfile(user_id=user.id)
        db.add(profile)
        await db.flush()

    skill = LanguageSkill(profile_id=profile.id, **body.model_dump())
    db.add(skill)
    await db.commit()
    await db.refresh(skill)
    return skill


@router.delete("/languages/{skill_id}", status_code=204)
async def delete_language_skill(skill_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404)
    skill = await db.get(LanguageSkill, skill_id)
    if not skill or skill.profile_id != profile.id:
        raise HTTPException(status_code=404)
    await db.delete(skill)
    await db.commit()


# ---- Tech Skills CRUD ----

@router.post("/tech-skills", response_model=TechSkillOut, status_code=201)
async def add_tech_skill(body: TechSkillIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        profile = UserProfile(user_id=user.id)
        db.add(profile)
        await db.flush()

    skill = TechSkill(profile_id=profile.id, **body.model_dump())
    db.add(skill)
    await db.commit()
    await db.refresh(skill)
    return skill


@router.delete("/tech-skills/{skill_id}", status_code=204)
async def delete_tech_skill(skill_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404)
    skill = await db.get(TechSkill, skill_id)
    if not skill or skill.profile_id != profile.id:
        raise HTTPException(status_code=404)
    await db.delete(skill)
    await db.commit()
