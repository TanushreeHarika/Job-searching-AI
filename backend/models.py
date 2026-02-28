import os
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Database URL - using SQLite
DATABASE_URL = "sqlite:///./job_matching.db"

# Create engine
engine = create_engine(DATABASE_URL, echo=False)

# Session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base
Base = declarative_base()


class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    company = Column(String(200), nullable=False)
    location = Column(String(100), nullable=False)
    location_type = Column(String(50), default="onsite")  # onsite, hybrid, remote
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    experience_min = Column(Integer, default=0)
    experience_max = Column(Integer, default=10)
    job_type = Column(String(50), default="full-time")  # full-time, part-time, contract
    description = Column(Text, nullable=True)
    required_skills = Column(JSON, default=list)
    preferred_skills = Column(JSON, default=list)
    posted_date = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    applicant_count = Column(Integer, default=0)
    
    def to_dict(self):
        # Map companies to logos
        company_logos = {
            "google deepmind": {"logo": "🤖", "bg": "rgba(66,133,244,.08)"},
            "nvidia india": {"logo": "⚡", "bg": "rgba(118,185,0,.08)"},
            "flipkart": {"logo": "🛒", "bg": "rgba(255,153,0,.08)"},
            "microsoft research": {"logo": "🪟", "bg": "rgba(0,120,212,.08)"},
            "cred": {"logo": "💳", "bg": "rgba(143,0,255,.08)"},
        }
        
        company_key = self.company.lower().strip() if self.company else ""
        logo_info = company_logos.get(company_key, {"logo": "📋", "bg": "rgba(66,133,244,.08)"})
        
        return {
            "id": self.id,
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "location_type": self.location_type,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "experience_min": self.experience_min,
            "experience_max": self.experience_max,
            "job_type": self.job_type,
            "description": self.description,
            "required_skills": self.required_skills or [],
            "preferred_skills": self.preferred_skills or [],
            "posted_date": self.posted_date.isoformat() if self.posted_date else None,
            "is_active": self.is_active,
            "applicant_count": self.applicant_count,
            "logo": logo_info["logo"],
            "bg": logo_info["bg"],
        }


class Candidate(Base):
    __tablename__ = "candidates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200), nullable=True)
    phone = Column(String(50), nullable=True)
    current_role = Column(String(200), nullable=True)
    location = Column(String(100), nullable=True)
    location_preference = Column(String(50), default="onsite")
    experience_years = Column(Integer, default=0)
    expected_salary = Column(Integer, nullable=True)
    education = Column(String(200), nullable=True)
    skills = Column(JSON, default=list)
    resume_text = Column(Text, nullable=True)
    ai_score = Column(Float, default=0.0)
    profile_views = Column(Integer, default=0)
    applications_sent = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "current_role": self.current_role,
            "location": self.location,
            "location_preference": self.location_preference,
            "experience_years": self.experience_years,
            "expected_salary": self.expected_salary,
            "education": self.education,
            "skills": self.skills or [],
            "ai_score": self.ai_score,
            "profile_views": self.profile_views,
            "applications_sent": self.applications_sent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_active": self.is_active,
        }


class Application(Base):
    __tablename__ = "applications"
    
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, nullable=False)
    job_id = Column(Integer, nullable=False)
    match_score = Column(Float, default=0.0)
    status = Column(String(50), default="pending")  # pending, viewed, shortlisted, rejected, accepted
    applied_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "candidate_id": self.candidate_id,
            "job_id": self.job_id,
            "match_score": self.match_score,
            "status": self.status,
            "applied_at": self.applied_at.isoformat() if self.applied_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class SkillGap(Base):
    __tablename__ = "skill_gaps"
    
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, nullable=False)
    job_id = Column(Integer, nullable=False)
    skill = Column(String(100), nullable=False)
    current_level = Column(Integer, default=0)  # 0-100
    required_level = Column(Integer, default=0)  # 0-100
    gap_percentage = Column(Integer, default=0)
    suggested_resources = Column(JSON, default=list)
    estimated_time_hours = Column(Float, default=0.0)
    
    def to_dict(self):
        return {
            "id": self.id,
            "candidate_id": self.candidate_id,
            "job_id": self.job_id,
            "skill": self.skill,
            "current_level": self.current_level,
            "required_level": self.required_level,
            "gap_percentage": self.gap_percentage,
            "suggested_resources": self.suggested_resources or [],
            "estimated_time_hours": self.estimated_time_hours,
        }


# Create tables
def create_tables():
    Base.metadata.create_all(bind=engine)


# Get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



