import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, Enum as SAEnum, JSON
from sqlalchemy.orm import relationship
from .database import Base
import enum


def new_uuid():
    return str(uuid.uuid4())


def now():
    return datetime.utcnow()


class MessageType(str, enum.Enum):
    chat = "chat"
    profile_question = "profile_question"
    document_card = "document_card"
    job_analysis = "job_analysis"
    zeugnis_decode = "zeugnis_decode"


class DocType(str, enum.Enum):
    resume = "resume"
    cover_letter = "cover_letter"
    anlagenverzeichnis = "anlagenverzeichnis"


class CEFRLevel(str, enum.Enum):
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"
    native = "native"


class SkillCategory(str, enum.Enum):
    language_programming = "language_programming"
    framework = "framework"
    tool = "tool"
    platform = "platform"
    soft = "soft"
    domain = "domain"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=new_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    ui_language = Column(String, default="en")  # "en" or "de"
    created_at = Column(DateTime, default=now)

    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    job_applications = relationship("JobApplication", back_populates="user", cascade="all, delete-orphan")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(String, primary_key=True, default=new_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Personal data (German fields)
    full_name = Column(String, default="")
    headline = Column(String, default="")
    photo_path = Column(String, default="")
    street = Column(String, default="")
    postal_code = Column(String, default="")
    city = Column(String, default="")
    country = Column(String, default="Deutschland")
    phone = Column(String, default="")
    email = Column(String, default="")
    date_of_birth = Column(String, default="")  # DD.MM.YYYY
    place_of_birth = Column(String, default="")
    nationality = Column(String, default="")
    marital_status = Column(String, default="")  # optional in modern Germany

    # Preferences
    preferred_language = Column(String, default="de")  # "en" or "de"
    target_countries = Column(JSON, default=list)
    preferred_tones = Column(JSON, default=list)

    # Resume base
    base_resume_md = Column(Text, default="")
    profile_completeness = Column(Integer, default=0)

    # German job market specifics
    salary_expectation = Column(String, default="")
    notice_period = Column(String, default="")

    created_at = Column(DateTime, default=now)
    updated_at = Column(DateTime, default=now, onupdate=now)

    user = relationship("User", back_populates="profile")
    work_experiences = relationship("WorkExperience", back_populates="profile", cascade="all, delete-orphan")
    educations = relationship("Education", back_populates="profile", cascade="all, delete-orphan")
    language_skills = relationship("LanguageSkill", back_populates="profile", cascade="all, delete-orphan")
    tech_skills = relationship("TechSkill", back_populates="profile", cascade="all, delete-orphan")
    certificates = relationship("Certificate", back_populates="profile", cascade="all, delete-orphan")
    zeugnisse = relationship("Zeugnis", back_populates="profile", cascade="all, delete-orphan")


class WorkExperience(Base):
    __tablename__ = "work_experiences"

    id = Column(String, primary_key=True, default=new_uuid)
    profile_id = Column(String, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)
    company = Column(String, default="")
    company_location = Column(String, default="")
    title = Column(String, default="")
    start_date = Column(String, default="")  # MM/YYYY
    end_date = Column(String, default="")    # MM/YYYY or "heute"
    is_current = Column(Boolean, default=False)
    description_md = Column(Text, default="")
    achievements = Column(JSON, default=list)
    order_index = Column(Integer, default=0)

    profile = relationship("UserProfile", back_populates="work_experiences")


class Education(Base):
    __tablename__ = "educations"

    id = Column(String, primary_key=True, default=new_uuid)
    profile_id = Column(String, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)
    institution = Column(String, default="")
    institution_location = Column(String, default="")
    degree = Column(String, default="")
    field = Column(String, default="")
    start_year = Column(Integer, nullable=True)
    end_year = Column(Integer, nullable=True)
    description_md = Column(Text, default="")
    grade = Column(String, default="")  # e.g. "1,3" or "A-"

    profile = relationship("UserProfile", back_populates="educations")


class LanguageSkill(Base):
    __tablename__ = "language_skills"

    id = Column(String, primary_key=True, default=new_uuid)
    profile_id = Column(String, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)
    language = Column(String, default="")
    cefr_level = Column(SAEnum(CEFRLevel), default=CEFRLevel.C1)
    order_index = Column(Integer, default=0)

    profile = relationship("UserProfile", back_populates="language_skills")


class TechSkill(Base):
    __tablename__ = "tech_skills"

    id = Column(String, primary_key=True, default=new_uuid)
    profile_id = Column(String, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, default="")
    category = Column(SAEnum(SkillCategory), default=SkillCategory.tool)
    proficiency = Column(Integer, default=3)  # 1-5
    is_highlighted = Column(Boolean, default=False)

    profile = relationship("UserProfile", back_populates="tech_skills")


class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(String, primary_key=True, default=new_uuid)
    profile_id = Column(String, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, default="")
    issuer = Column(String, default="")
    date_obtained = Column(String, default="")
    file_path = Column(String, default="")

    profile = relationship("UserProfile", back_populates="certificates")


class Zeugnis(Base):
    __tablename__ = "zeugnisse"

    id = Column(String, primary_key=True, default=new_uuid)
    profile_id = Column(String, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, default="")  # e.g. "Arbeitszeugnis ACME GmbH"
    issuer = Column(String, default="")
    date = Column(String, default="")
    file_path = Column(String, default="")  # PDF
    ai_decoded_grade = Column(String, default="")  # Ergebnis der AI-Analyse
    ai_decoded_summary = Column(Text, default="")

    profile = relationship("UserProfile", back_populates="zeugnisse")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, default=new_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, default="Neuer Chat")
    created_at = Column(DateTime, default=now)
    updated_at = Column(DateTime, default=now, onupdate=now)

    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=new_uuid)
    session_id = Column(String, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(String, nullable=False)  # "user", "assistant", "system"
    content = Column(Text, default="")
    message_type = Column(SAEnum(MessageType), default=MessageType.chat)
    metadata_json = Column(JSON, default=dict)  # profile_updates, document_refs, etc.
    created_at = Column(DateTime, default=now)

    session = relationship("ChatSession", back_populates="messages")


class JobApplication(Base):
    __tablename__ = "job_applications"

    id = Column(String, primary_key=True, default=new_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(String, ForeignKey("chat_sessions.id", ondelete="SET NULL"), nullable=True)
    job_url = Column(String, default="")
    job_title = Column(String, default="")
    company = Column(String, default="")
    company_location = Column(String, default="")
    reference_number = Column(String, default="")  # Kennziffer
    job_description_raw = Column(Text, default="")
    job_requirements = Column(JSON, default=dict)
    created_at = Column(DateTime, default=now)

    user = relationship("User", back_populates="job_applications")
    documents = relationship("GeneratedDocument", back_populates="application", cascade="all, delete-orphan")


class GeneratedDocument(Base):
    __tablename__ = "generated_documents"

    id = Column(String, primary_key=True, default=new_uuid)
    application_id = Column(String, ForeignKey("job_applications.id", ondelete="CASCADE"), nullable=False)
    doc_type = Column(SAEnum(DocType), nullable=False)
    language = Column(String, default="de")  # "en" or "de"
    markdown_content = Column(Text, default="")
    docx_path = Column(String, default="")
    pdf_path = Column(String, default="")
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=now)

    application = relationship("JobApplication", back_populates="documents")
