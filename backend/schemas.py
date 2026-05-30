from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


# ---- Auth ----

class UserRegister(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=6, max_length=128)
    ui_language: str = "en"


class UserLogin(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(BaseModel):
    id: str
    email: str
    ui_language: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ---- Profile ----

class LanguageSkillIn(BaseModel):
    language: str
    cefr_level: str = "C1"
    order_index: int = 0


class LanguageSkillOut(BaseModel):
    id: str
    language: str
    cefr_level: str
    order_index: int

    model_config = {"from_attributes": True}


class TechSkillIn(BaseModel):
    name: str
    category: str = "tool"
    proficiency: int = 3
    is_highlighted: bool = False


class TechSkillOut(BaseModel):
    id: str
    name: str
    category: str
    proficiency: int
    is_highlighted: bool

    model_config = {"from_attributes": True}


class WorkExperienceIn(BaseModel):
    company: str = ""
    company_location: str = ""
    title: str = ""
    start_date: str = ""
    end_date: str = ""
    is_current: bool = False
    description_md: str = ""
    achievements: list[str] = []
    order_index: int = 0


class WorkExperienceOut(BaseModel):
    id: str
    company: str
    company_location: str
    title: str
    start_date: str
    end_date: str
    is_current: bool
    description_md: str
    achievements: list
    order_index: int

    model_config = {"from_attributes": True}


class EducationIn(BaseModel):
    institution: str = ""
    institution_location: str = ""
    degree: str = ""
    field: str = ""
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    description_md: str = ""
    grade: str = ""


class EducationOut(BaseModel):
    id: str
    institution: str
    institution_location: str
    degree: str
    field: str
    start_year: Optional[int]
    end_year: Optional[int]
    description_md: str
    grade: str

    model_config = {"from_attributes": True}


class CertificateOut(BaseModel):
    id: str
    name: str
    issuer: str
    date_obtained: str
    file_path: str

    model_config = {"from_attributes": True}


class ZeugnisOut(BaseModel):
    id: str
    title: str
    issuer: str
    date: str
    file_path: str
    ai_decoded_grade: str
    ai_decoded_summary: str

    model_config = {"from_attributes": True}


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    headline: Optional[str] = None
    street: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    date_of_birth: Optional[str] = None
    place_of_birth: Optional[str] = None
    nationality: Optional[str] = None
    marital_status: Optional[str] = None
    preferred_language: Optional[str] = None
    target_countries: Optional[list[str]] = None
    preferred_tones: Optional[list[str]] = None
    base_resume_md: Optional[str] = None
    salary_expectation: Optional[str] = None
    notice_period: Optional[str] = None


class ProfileOut(BaseModel):
    id: str
    user_id: str
    full_name: str
    headline: str
    photo_path: str
    street: str
    postal_code: str
    city: str
    country: str
    phone: str
    email: str
    date_of_birth: str
    place_of_birth: str
    nationality: str
    marital_status: str
    preferred_language: str
    target_countries: list
    preferred_tones: list
    base_resume_md: str
    profile_completeness: int
    salary_expectation: str
    notice_period: str
    created_at: datetime
    updated_at: datetime
    work_experiences: list[WorkExperienceOut] = []
    educations: list[EducationOut] = []
    language_skills: list[LanguageSkillOut] = []
    tech_skills: list[TechSkillOut] = []
    certificates: list[CertificateOut] = []
    zeugnisse: list[ZeugnisOut] = []

    model_config = {"from_attributes": True}


# ---- Chat ----

class ChatMessageIn(BaseModel):
    content: str


class ChatSessionOut(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    model_config = {"from_attributes": True}


class ChatMessageOut(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    message_type: str
    metadata_json: dict
    created_at: datetime

    model_config = {"from_attributes": True}


# ---- Jobs ----

class JobScrapeRequest(BaseModel):
    url: str


class JobScrapeResponse(BaseModel):
    id: str
    job_url: str
    job_title: str
    company: str
    company_location: str
    reference_number: str
    job_description_raw: str
    job_requirements: dict


class DocumentGenerateRequest(BaseModel):
    application_id: str
    doc_type: str  # "resume" or "cover_letter"
    language: str = "de"


class DocumentOut(BaseModel):
    id: str
    application_id: str
    doc_type: str
    language: str
    markdown_content: str
    docx_path: str
    pdf_path: str
    version: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ---- DIN 5008 Compliance ----

class ComplianceReport(BaseModel):
    passed: bool
    warnings: list[str] = []
    violations: list[str] = []
