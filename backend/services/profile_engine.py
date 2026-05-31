from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models import (
    UserProfile, WorkExperience, Education, LanguageSkill, TechSkill, Certificate
)


def _normalize_skill_category(raw_category: str) -> str:
    category = (raw_category or "").strip().lower()
    mapping = {
        "language_programming": "language_programming",
        "programming_language": "language_programming",
        "framework": "framework",
        "tool": "tool",
        "platform": "platform",
        "cloud": "platform",
        "cloud_platform": "platform",
        "soft": "soft",
        "soft_skill": "soft",
        "domain": "domain",
    }
    return mapping.get(category, "tool")


async def apply_profile_updates(db: AsyncSession, profile: UserProfile, updates: dict) -> list[str]:
    """Apply extracted profile_updates from AI response to the database."""
    changes = []

    # Simple string fields on profile
    str_fields = [
        "full_name", "headline", "salary_expectation", "notice_period",
        "preferred_language",
    ]
    for field in str_fields:
        if field in updates and updates[field]:
            setattr(profile, field, updates[field])
            changes.append(field)

    # Work experience
    if "work_experience" in updates:
        existing_experiences = profile.__dict__.get("work_experiences") or []
        base_order_index = len(existing_experiences)
        for exp_data in updates["work_experience"]:
            exp = WorkExperience(
                profile_id=profile.id,
                company=exp_data.get("company", ""),
                company_location=exp_data.get("company_location", ""),
                title=exp_data.get("title", ""),
                start_date=exp_data.get("start_date", ""),
                end_date=exp_data.get("end_date", ""),
                is_current=exp_data.get("is_current", False),
                description_md=exp_data.get("description_md", ""),
                achievements=exp_data.get("achievements", []),
                order_index=base_order_index,
            )
            db.add(exp)
            base_order_index += 1
            changes.append("work_experience")

    # Education
    if "education" in updates:
        for edu_data in updates["education"]:
            edu = Education(
                profile_id=profile.id,
                institution=edu_data.get("institution", ""),
                institution_location=edu_data.get("institution_location", ""),
                degree=edu_data.get("degree", ""),
                field=edu_data.get("field", ""),
                start_year=edu_data.get("start_year"),
                end_year=edu_data.get("end_year"),
            )
            db.add(edu)
            changes.append("education")

    # Tech skills (avoid duplicates by name)
    if "tech_skills" in updates:
        existing_skill_rows = await db.execute(
            select(TechSkill.name).where(TechSkill.profile_id == profile.id)
        )
        existing_names = {
            (name or "").strip().lower()
            for name in existing_skill_rows.scalars().all()
            if name
        }
        for skill_data in updates["tech_skills"]:
            name = skill_data.get("name", "").strip()
            if name and name.lower() not in existing_names:
                skill = TechSkill(
                    profile_id=profile.id,
                    name=name,
                    category=_normalize_skill_category(skill_data.get("category", "tool")),
                    proficiency=skill_data.get("proficiency", 3),
                    is_highlighted=skill_data.get("is_highlighted", False),
                )
                db.add(skill)
                existing_names.add(name.lower())
                changes.append("tech_skill")

    # Language skills
    if "language_skills" in updates:
        existing_lang_rows = await db.execute(
            select(LanguageSkill.language).where(LanguageSkill.profile_id == profile.id)
        )
        existing_langs = {
            (lang or "").strip().lower()
            for lang in existing_lang_rows.scalars().all()
            if lang
        }
        for lang_data in updates["language_skills"]:
            lang = lang_data.get("language", "").strip()
            if lang and lang.lower() not in existing_langs:
                skill = LanguageSkill(
                    profile_id=profile.id,
                    language=lang,
                    cefr_level=lang_data.get("cefr_level", "C1"),
                    order_index=len(existing_langs),
                )
                db.add(skill)
                existing_langs.add(lang.lower())
                changes.append("language_skill")

    # Certificates
    if "certificates" in updates:
        for cert_data in updates["certificates"]:
            cert = Certificate(
                profile_id=profile.id,
                name=cert_data.get("name", ""),
                issuer=cert_data.get("issuer", ""),
                date_obtained=cert_data.get("date_obtained", ""),
            )
            db.add(cert)
            changes.append("certificate")

    await db.flush()
    return changes


def calculate_profile_completeness(profile: UserProfile) -> int:
    """Calculate profile completeness as a percentage."""
    score = 0
    max_score = 0

    work_experiences = profile.__dict__.get("work_experiences") or []
    educations = profile.__dict__.get("educations") or []
    language_skills = profile.__dict__.get("language_skills") or []
    tech_skills = profile.__dict__.get("tech_skills") or []
    certificates = profile.__dict__.get("certificates") or []
    zeugnisse = profile.__dict__.get("zeugnisse") or []

    checks = [
        (bool(profile.full_name), 5),
        (bool(profile.street or profile.city), 3),
        (bool(profile.phone or profile.email), 3),
        (bool(profile.date_of_birth), 2),
        (bool(profile.nationality), 2),
        (len(work_experiences) > 0, 15),
        (len(educations) > 0, 10),
        (len(language_skills) > 0, 5),
        (len(tech_skills) > 0, 15),
        (len(tech_skills) >= 5, 10),
        (len(certificates) > 0, 5),
        (bool(profile.salary_expectation), 5),
        (bool(profile.notice_period), 5),
        (len(zeugnisse) > 0, 5),
        (bool(profile.preferred_language), 5),
        (len(profile.target_countries) > 0, 5),
    ]

    for check, weight in checks:
        max_score += weight
        if check:
            score += weight

    return min(int((score / max_score) * 100) if max_score > 0 else 0, 100)
