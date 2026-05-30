import re
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..models import User, JobApplication
from ..schemas import JobScrapeRequest, JobScrapeResponse
from ..auth import get_current_user
from ..services.scraper import scrape_job_url
from ..services.ai_service import chat_completion

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post("/scrape", response_model=JobScrapeResponse)
async def scrape_job(
    body: JobScrapeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    scraped = await scrape_job_url(body.url)

    # AI-powered requirements extraction
    requirements = {}
    if scraped["job_description_raw"]:
        try:
            prompt = f"""Analyze this job description and extract structured requirements as JSON:
{scraped["job_description_raw"][:4000]}

Return ONLY valid JSON with these keys:
- "required_skills": [list of hard skills]
- "nice_to_have": [list of optional skills]
- "experience_years": number or null
- "education_level": string or null
- "languages": [list of required languages]
- "key_responsibilities": [list of main duties]
- "company_culture": [list of cultural indicators]
"""
            result = await chat_completion(
                [{"role": "user", "content": prompt}],
                model="deepseek/deepseek-chat-v3",
            )
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                requirements = json.loads(json_match.group(0))
        except Exception:
            pass

    # Save to DB
    job_app = JobApplication(
        user_id=user.id,
        job_url=body.url,
        job_title=scraped["job_title"],
        company=scraped["company"],
        company_location=scraped["company_location"],
        reference_number=scraped["reference_number"],
        job_description_raw=scraped["job_description_raw"],
        job_requirements=requirements,
    )
    db.add(job_app)
    await db.commit()
    await db.refresh(job_app)

    return JobScrapeResponse(
        id=job_app.id,
        job_url=job_app.job_url,
        job_title=job_app.job_title,
        company=job_app.company,
        company_location=job_app.company_location,
        reference_number=job_app.reference_number,
        job_description_raw=job_app.job_description_raw,
        job_requirements=job_app.job_requirements,
    )


@router.get("/{job_id}")
async def get_job(
    job_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    job = await db.get(JobApplication, job_id)
    if not job or job.user_id != user.id:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
