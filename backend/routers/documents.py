import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from ..database import get_db
from ..models import User, JobApplication, GeneratedDocument, UserProfile, DocType
from ..schemas import DocumentGenerateRequest, DocumentOut, ComplianceReport
from ..auth import get_current_user
from ..services.ai_service import document_completion
from ..services.document import (
    generate_resume_docx, generate_cover_letter_docx, convert_to_pdf,
)

router = APIRouter(prefix="/api/documents", tags=["documents"])


def _profile_to_dict(profile: UserProfile) -> dict:
    return {
        "full_name": profile.full_name,
        "headline": profile.headline,
        "photo_path": profile.photo_path,
        "street": profile.street,
        "postal_code": profile.postal_code,
        "city": profile.city,
        "country": profile.country,
        "phone": profile.phone,
        "email": profile.email,
        "date_of_birth": profile.date_of_birth,
        "place_of_birth": profile.place_of_birth,
        "nationality": profile.nationality,
        "marital_status": profile.marital_status,
        "preferred_language": profile.preferred_language,
        "base_resume_md": profile.base_resume_md,
        "salary_expectation": profile.salary_expectation,
        "notice_period": profile.notice_period,
        "work_experiences": [
            {
                "company": w.company, "company_location": w.company_location,
                "title": w.title, "start_date": w.start_date,
                "end_date": w.end_date, "is_current": w.is_current,
                "description_md": w.description_md,
                "achievements": w.achievements if isinstance(w.achievements, list) else [],
            }
            for w in (profile.work_experiences or [])
        ],
        "educations": [
            {
                "institution": e.institution, "institution_location": e.institution_location,
                "degree": e.degree, "field": e.field,
                "start_year": e.start_year, "end_year": e.end_year,
                "grade": e.grade,
            }
            for e in (profile.educations or [])
        ],
        "language_skills": [
            {"language": s.language, "cefr_level": s.cefr_level.value if hasattr(s.cefr_level, 'value') else str(s.cefr_level)}
            for s in (profile.language_skills or [])
        ],
        "tech_skills": [
            {"name": s.name, "category": s.category.value if hasattr(s.category, 'value') else str(s.category), "proficiency": s.proficiency}
            for s in (profile.tech_skills or [])
        ],
        "certificates": [
            {"name": c.name, "issuer": c.issuer, "date_obtained": c.date_obtained}
            for c in (profile.certificates or [])
        ],
        "zeugnisse": [
            {"title": z.title, "issuer": z.issuer}
            for z in (profile.zeugnisse or [])
        ],
    }


@router.post("/generate", response_model=DocumentOut)
async def generate_document(
    body: DocumentGenerateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Load job application
    job = await db.get(JobApplication, body.application_id)
    if not job or job.user_id != user.id:
        raise HTTPException(status_code=404, detail="Application not found")

    # Load profile with all relations
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

    language = body.language or (profile.preferred_language if profile else "de")
    is_resume = body.doc_type == "resume"

    # Build AI prompt
    if is_resume:
        prompt = _build_resume_prompt(profile, job, language)
    else:
        prompt = _build_cover_letter_prompt(profile, job, language)

    # Generate content via AI
    try:
        markdown_content = await document_completion(prompt, language)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI generation error: {str(e)}")

    # Generate DOCX
    profile_dict = _profile_to_dict(profile) if profile else {}
    if is_resume:
        docx_path = generate_resume_docx(profile_dict, language)
    else:
        docx_path = generate_cover_letter_docx(profile_dict, {
            "job_title": job.job_title,
            "company": job.company,
            "company_location": job.company_location,
            "reference_number": job.reference_number,
        }, markdown_content, language)

    # Convert to PDF
    pdf_path = convert_to_pdf(docx_path) or ""

    # Save to DB
    doc = GeneratedDocument(
        application_id=body.application_id,
        doc_type=DocType.resume if is_resume else DocType.cover_letter,
        language=language,
        markdown_content=markdown_content,
        docx_path=docx_path,
        pdf_path=pdf_path,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    return DocumentOut(
        id=doc.id, application_id=doc.application_id,
        doc_type=doc.doc_type.value, language=doc.language,
        markdown_content=doc.markdown_content,
        docx_path=doc.docx_path, pdf_path=doc.pdf_path,
        version=doc.version, created_at=doc.created_at,
    )


@router.get("/{doc_id}", response_model=DocumentOut)
async def get_document(
    doc_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    doc = await db.get(GeneratedDocument, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    job = await db.get(JobApplication, doc.application_id)
    if not job or job.user_id != user.id:
        raise HTTPException(status_code=404, detail="Document not found")

    return doc


@router.get("/{doc_id}/docx")
async def download_docx(
    doc_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    doc = await db.get(GeneratedDocument, doc_id)
    if not doc or not doc.docx_path or not os.path.exists(doc.docx_path):
        raise HTTPException(status_code=404, detail="DOCX not found")

    return FileResponse(doc.docx_path, filename=f"lebenslauf.docx", media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


@router.get("/{doc_id}/pdf")
async def download_pdf(
    doc_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    doc = await db.get(GeneratedDocument, doc_id)
    if not doc or not doc.pdf_path or not os.path.exists(doc.pdf_path):
        if doc and doc.docx_path and os.path.exists(doc.docx_path):
            pdf_path = convert_to_pdf(doc.docx_path)
            if pdf_path:
                doc.pdf_path = pdf_path
                await db.commit()
        if not doc or not doc.pdf_path or not os.path.exists(doc.pdf_path):
            raise HTTPException(status_code=404, detail="PDF not available")

    return FileResponse(doc.pdf_path, filename=f"lebenslauf.pdf", media_type="application/pdf")


@router.get("/{doc_id}/compliance", response_model=ComplianceReport)
async def check_compliance(
    doc_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    doc = await db.get(GeneratedDocument, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    warnings = []
    violations = []

    # Basic DIN 5008 checks
    if doc.language == "de":
        if doc.doc_type == DocType.cover_letter:
            content = doc.markdown_content
            if len(content) > 3000:
                warnings.append("Cover letter might exceed 1 page (DIN 5008 recommendation)")
            if "Mit freundlichen Grüßen" not in content:
                violations.append("Missing German closing formula")
            if "Bewerbung als" not in content:
                warnings.append("Missing Betreffzeile")
            if "Anlagen" not in content:
                warnings.append("Missing Anlagen section")

        if doc.doc_type == DocType.resume:
            content = doc.markdown_content
            if "Berufserfahrung" not in content and "Work Experience" not in content:
                warnings.append("Missing work experience section")
            if "Ausbildung" not in content and "Education" not in content:
                warnings.append("Missing education section")

    return ComplianceReport(
        passed=len(violations) == 0,
        warnings=warnings,
        violations=violations,
    )


def _build_resume_prompt(profile: UserProfile | None, job: JobApplication, language: str) -> str:
    profile_dict = _profile_to_dict(profile) if profile else {}
    job_info = f"""
Job Title: {job.job_title}
Company: {job.company}
Location: {job.company_location}
Description: {job.job_description_raw[:2000]}
Requirements: {job.job_requirements}
"""
    profile_info = f"""
Profile: {profile_dict}
"""

    if language == "de":
        return f"""Erstelle einen tabellarischen Lebenslauf nach DIN 5008 für folgende Stelle:

{job_info}

Nutzerprofil:
{profile_info}

## Anforderungen
- Tabellarisches Format mit klar getrennten Abschnitten
- Abschnitte: Persönliche Daten, Berufserfahrung, Ausbildung, Weiterbildungen, Kenntnisse & Fähigkeiten
- Sprachkenntnisse mit GER-Niveaus (A1-C2)
- Berufserfahrung mit datierten Einträgen und stichpunktartigen Erfolgen
- Ausbildung mit Abschluss und Note
- Kein Bewerbungsfoto (wird vom Generator eingefügt)
- Output als cleanes Markdown"""
    else:
        return f"""Create a professional resume for this position:

{job_info}

Profile:
{profile_info}

Requirements:
- Clean, modern format with sections: Summary, Skills, Experience, Education, Certifications
- STAR method for achievements
- Reverse chronological order
- No photo or personal data beyond contact info
- Output as clean Markdown"""


def _build_cover_letter_prompt(profile: UserProfile | None, job: JobApplication, language: str) -> str:
    profile_dict = _profile_to_dict(profile) if profile else {}
    job_info = f"""
Job Title: {job.job_title}
Company: {job.company}
Location: {job.company_location}
Description: {job.job_description_raw[:2000]}
"""

    if language == "de":
        return f"""Erstelle ein Anschreiben nach DIN 5008 für diese Stelle:

{job_info}

Nutzerprofil: {profile_dict}

## Anforderungen
- Formelles Anschreiben mit Absender- und Empfängerblock
- Betreffzeile: "Bewerbung als {job.job_title}"
- 3-4 Absätze: Einleitung, Qualifikationen, Unternehmensbezug, Abschluss
- Schlussformel: "Mit freundlichen Grüßen"
- Anlagen erwähnen
- Strikt 1 Seite
- Formelle Sie-Form
- Output als cleanes Markdown"""
    else:
        return f"""Write a professional cover letter for this position:

{job_info}

Profile: {profile_dict}

Requirements:
- 3-4 paragraphs: opening, qualifications, company connection, closing
- Professional business letter format
- Show company research
- Output as clean Markdown"""
