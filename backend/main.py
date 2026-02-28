"""
Job Pairing AI - Main Application
=================================
FastAPI backend for intelligent job matching
"""

import os
import io
import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# Import models and database
from models import (
    Base, Job, Candidate, Application, SkillGap,
    get_db, create_tables, SessionLocal
)
from matching_engine import (
    calculate_overall_match,
    ai_enhance_match,
    rank_candidates_for_job,
    get_skill_gaps,
    parse_resume_with_ai,
    calculate_algorithm_metrics
)

# OpenAI for chatbot - use default key or placeholder
import os
from dotenv import load_dotenv
load_dotenv()

# Try to get API key from environment, use placeholder if not available
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
chat_client = None
if OPENAI_API_KEY:
    try:
        from openai import OpenAI
        chat_client = OpenAI(api_key=OPENAI_API_KEY)
    except:
        print("WARNING: Could not initialize OpenAI client. AI features will use fallback mode.")
else:
    print("WARNING: OPENAI_API_KEY not set. AI features will use fallback mode.")

# Create database tables
create_tables()

# Initialize FastAPI app
app = FastAPI(
    title="NexMatch AI - Job Matching Engine",
    description="Intelligent job matching with AI-powered recommendations",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Pydantic Models ====================

class JobCreate(BaseModel):
    title: str
    company: str
    location: str
    location_type: str = "onsite"
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    experience_min: int = 0
    experience_max: int = 10
    job_type: str = "full-time"
    description: Optional[str] = None
    required_skills: List[str] = []
    preferred_skills: List[str] = []


class CandidateCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    current_role: Optional[str] = None
    location: Optional[str] = None
    location_preference: str = "onsite"
    experience_years: int = 0
    expected_salary: Optional[int] = None
    education: Optional[str] = None
    skills: List[str] = []


class MatchRecalculateRequest(BaseModel):
    candidate_id: int
    job_id: int
    skills: Optional[List[str]] = None
    experience_years: Optional[int] = None
    location_preference: Optional[str] = None
    expected_salary: Optional[int] = None


class ApplyRequest(BaseModel):
    candidate_id: int
    job_id: int


# ==================== Routes ====================

@app.get("/")
def root():
    """Serve the frontend application"""
    # Get the path to index.html - it should be in the parent directory
    index_path = Path(__file__).parent.parent / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    # Fallback to JSON if index.html not found
    return {
        "name": "NexMatch AI - Job Matching Engine",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected"
    }


# ==================== AI Chatbot API ====================

class ChatRequest(BaseModel):
    message: str
    candidate_id: Optional[int] = 1


@app.post("/api/v1/chat")
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """AI Chatbot for career guidance"""
    
    # Check if OpenAI client is available
    if chat_client is None:
        # Return a fallback response without AI
        return {
            "response": "I'm currently running in offline mode. To enable AI-powered career guidance, please set the OPENAI_API_KEY environment variable. In the meantime, I can help you with general career advice based on best practices!",
            "success": True,
            "offline_mode": True
        }
    
    candidate = db.query(Candidate).filter(Candidate.id == request.candidate_id).first()
    
    profile_info = ""
    if candidate:
        profile_info = f"""
Current Profile:
- Name: {candidate.name}
- Role: {candidate.current_role}
- Skills: {', '.join(candidate.skills)}
- Experience: {candidate.experience_years} years
- Location: {candidate.location}
- Education: {candidate.education}
"""
    
    system_prompt = f"""You are a helpful career and skills guidance AI assistant for NexMatch AI. 
Your role is to help users learn new skills based on their profile.
{profile_info}
Be concise and provide actionable advice."""

    try:
        response = chat_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.message}
            ],
            temperature=0.7,
            max_tokens=500
        )
        return {"response": response.choices[0].message.content, "success": True}
    except Exception as e:
        return {"response": "Sorry, I'm having trouble responding right now.", "success": False, "error": str(e)}


# ==================== Jobs API ====================

@app.get("/api/v1/jobs")
def get_jobs(
    candidate_id: Optional[int] = Query(None, description="Filter jobs by match for candidate"),
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Get all active jobs with match scores
    """
    jobs = db.query(Job).filter(Job.is_active == True).offset(skip).limit(limit).all()
    
    # If candidate_id provided, calculate match scores
    if candidate_id:
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if candidate:
            result = []
            for job in jobs:
                job_dict = job.to_dict()
                candidate_dict = candidate.to_dict()
                match = calculate_overall_match(candidate_dict, job_dict)
                job_dict["match_score"] = match["overall_score"]
                job_dict["match_details"] = match
                result.append(job_dict)
            # Sort by match score
            result.sort(key=lambda x: x.get("match_score", 0), reverse=True)
            return result
    
    return [job.to_dict() for job in jobs]


@app.get("/api/v1/jobs/{job_id}")
def get_job(job_id: int, db: Session = Depends(get_db)):
    """Get job details by ID"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.to_dict()


@app.post("/api/v1/jobs")
def create_job(job: JobCreate, db: Session = Depends(get_db)):
    """Create a new job posting"""
    db_job = Job(
        title=job.title,
        company=job.company,
        location=job.location,
        location_type=job.location_type,
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        experience_min=job.experience_min,
        experience_max=job.experience_max,
        job_type=job.job_type,
        description=job.description,
        required_skills=job.required_skills,
        preferred_skills=job.preferred_skills,
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job.to_dict()


# ==================== Candidates API ====================

@app.get("/api/v1/candidates")
def get_candidates(
    job_id: Optional[int] = Query(None, description="Filter candidates by match for job"),
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get all candidates"""
    candidates = db.query(Candidate).filter(Candidate.is_active == True).offset(skip).limit(limit).all()
    
    # If job_id provided, rank candidates for that job
    if job_id:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            candidate_list = [c.to_dict() for c in candidates]
            import asyncio
            ranked = asyncio.run(rank_candidates_for_job(job.to_dict(), candidate_list))
            return ranked
    
    return [c.to_dict() for c in candidates]


@app.get("/api/v1/candidates/{candidate_id}")
def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    """Get candidate details by ID"""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate.to_dict()


@app.post("/api/v1/candidates")
def create_candidate(candidate: CandidateCreate, db: Session = Depends(get_db)):
    """Create a new candidate profile"""
    db_candidate = Candidate(
        name=candidate.name,
        email=candidate.email,
        phone=candidate.phone,
        current_role=candidate.current_role,
        location=candidate.location,
        location_preference=candidate.location_preference,
        experience_years=candidate.experience_years,
        expected_salary=candidate.expected_salary,
        education=candidate.education,
        skills=candidate.skills,
    )
    db.add(db_candidate)
    db.commit()
    db.refresh(db_candidate)
    return db_candidate.to_dict()


# ==================== Match API ====================

@app.post("/api/v1/match/recalculate")
async def recalculate_match(request: MatchRecalculateRequest, db: Session = Depends(get_db)):
    """Recalculate match score with updated candidate profile"""
    candidate = db.query(Candidate).filter(Candidate.id == request.candidate_id).first()
    job = db.query(Job).filter(Job.id == request.job_id).first()
    
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Create updated candidate dict
    candidate_dict = candidate.to_dict()
    if request.skills:
        candidate_dict["skills"] = request.skills
    if request.experience_years is not None:
        candidate_dict["experience_years"] = request.experience_years
    if request.location_preference:
        candidate_dict["location_preference"] = request.location_preference
    if request.expected_salary is not None:
        candidate_dict["expected_salary"] = request.expected_salary
    
    job_dict = job.to_dict()
    
    # Calculate match
    match = calculate_overall_match(candidate_dict, job_dict)
    
    # Enhance with AI
    enhanced = await ai_enhance_match(candidate_dict, job_dict, match)
    
    return {
        "candidate_id": request.candidate_id,
        "job_id": request.job_id,
        "match_score": enhanced["overall_score"],
        "skill_score": enhanced.get("skill_score"),
        "experience_score": enhanced.get("experience_score"),
        "location_score": enhanced.get("location_score"),
        "salary_score": enhanced.get("salary_score"),
        "match_level": enhanced.get("match_level"),
        "matched_skills": enhanced.get("matched_skills", []),
        "missing_skills": enhanced.get("missing_skills", []),
        "ai_tip": enhanced.get("ai_tip"),
        "skills_to_learn": enhanced.get("skills_to_learn", [])
    }


@app.get("/api/v1/match/{candidate_id}/{job_id}")
async def get_match(candidate_id: int, job_id: int, db: Session = Depends(get_db)):
    """Get match details between candidate and job"""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not candidate or not job:
        raise HTTPException(status_code=404, detail="Candidate or Job not found")
    
    candidate_dict = candidate.to_dict()
    job_dict = job.to_dict()
    
    match = calculate_overall_match(candidate_dict, job_dict)
    enhanced = await ai_enhance_match(candidate_dict, job_dict, match)
    
    return enhanced


# ==================== Skill Gap API ====================

@app.get("/api/v1/skillgap/{job_id}")
async def get_skill_gap_analysis(
    job_id: int,
    candidate_id: int = Query(..., description="Candidate ID"),
    db: Session = Depends(get_db)
):
    """Get skill gap analysis for a candidate-job pair"""
    job = db.query(Job).filter(Job.id == job_id).first()
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    
    if not job or not candidate:
        raise HTTPException(status_code=404, detail="Job or Candidate not found")
    
    gaps = await get_skill_gaps(candidate.to_dict(), job.to_dict())
    
    return {
        "job_id": job_id,
        "job_title": job.title,
        "company": job.company,
        "candidate_id": candidate_id,
        "candidate_name": candidate.name,
        "current_match": calculate_overall_match(candidate.to_dict(), job.to_dict())["overall_score"],
        "projected_match": gaps.get("projected_score", 85),
        "potential_gain": gaps.get("potential_improvement", 0),
        "gaps": gaps.get("gaps", [])
    }


# ==================== Resume Parse API ====================

@app.post("/api/v1/resume/parse")
async def parse_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Parse resume and extract candidate information"""
    # Read file content
    content = await file.read()
    
    # Try to extract text based on file type
    resume_text = ""
    
    if file.filename.endswith('.pdf'):
        try:
            import PyPDF2
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            for page in pdf_reader.pages:
                resume_text += page.extract_text() + "\n"
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error reading PDF: {str(e)}")
    
    elif file.filename.endswith('.docx'):
        try:
            from docx import Document
            doc = Document(io.BytesIO(content))
            for para in doc.paragraphs:
                resume_text += para.text + "\n"
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error reading DOCX: {str(e)}")
    
    elif file.filename.endswith('.txt'):
        resume_text = content.decode('utf-8', errors='ignore')
    
    else:
        raise HTTPException(status_code=400, detail="Unsupported file format. Use PDF, DOCX, or TXT")
    
    # Parse with AI
    parsed = await parse_resume_with_ai(resume_text)
    
    return {
        "success": True,
        "parsed_data": parsed,
        "message": f"Profile extracted successfully! {len(parsed.get('skills_detected', []))} skills detected · {parsed.get('experience_years_detected', 0)} years experience · {parsed.get('roles_found', 0)} roles found"
    }


# ==================== Apply API ====================

@app.post("/api/v1/apply")
def apply_to_job(request: ApplyRequest, db: Session = Depends(get_db)):
    """Apply to a job"""
    candidate = db.query(Candidate).filter(Candidate.id == request.candidate_id).first()
    job = db.query(Job).filter(Job.id == request.job_id).first()
    
    if not candidate or not job:
        raise HTTPException(status_code=404, detail="Candidate or Job not found")
    
    # Check if already applied
    existing = db.query(Application).filter(
        Application.candidate_id == request.candidate_id,
        Application.job_id == request.job_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Already applied to this job")
    
    # Calculate match score
    match = calculate_overall_match(candidate.to_dict(), job.to_dict())
    
    # Create application
    application = Application(
        candidate_id=request.candidate_id,
        job_id=request.job_id,
        match_score=match["overall_score"],
        status="pending"
    )
    
    db.add(application)
    
    # Update job applicant count
    job.applicant_count += 1
    
    # Update candidate applications count
    candidate.applications_sent += 1
    
    db.commit()
    db.refresh(application)
    
    return {
        "success": True,
        "application_id": application.id,
        "match_score": match["overall_score"],
        "message": "Application submitted successfully!"
    }


# ==================== Analytics API ====================

@app.get("/api/v1/analytics")
def get_analytics(db: Session = Depends(get_db)):
    """Get algorithm performance metrics"""
    applications = db.query(Application).all()
    applications_data = [app.to_dict() for app in applications]
    
    metrics = calculate_algorithm_metrics(applications_data)
    
    # Get additional stats
    total_jobs = db.query(Job).filter(Job.is_active == True).count()
    total_candidates = db.query(Candidate).filter(Candidate.is_active == True).count()
    total_applications = db.query(Application).count()
    
    # Get score distribution
    high_matches = db.query(Application).filter(Application.match_score >= 85).count()
    medium_matches = db.query(Application).filter(
        Application.match_score >= 70,
        Application.match_score < 85
    ).count()
    low_matches = db.query(Application).filter(Application.match_score < 70).count()
    
    return {
        "metrics": metrics,
        "stats": {
            "total_jobs": total_jobs,
            "total_candidates": total_candidates,
            "total_applications": total_applications,
            "high_matches": high_matches,
            "medium_matches": medium_matches,
            "low_matches": low_matches
        },
        "distribution": {
            "90_to_100": high_matches,
            "80_to_90": medium_matches,
            "70_to_80": low_matches,
            "60_to_70": 0,
            "below_60": 0
        }
    }


# ==================== Seed Data ====================

def seed_data():
    """Seed initial data for testing"""
    db = SessionLocal()
    
    # Check if data already exists
    if db.query(Job).first():
        print("Data already exists, skipping seed...")
        db.close()
        return
    
    # Create sample jobs
    jobs = [
        Job(
            title="Senior ML Engineer",
            company="Google DeepMind",
            location="Remote",
            location_type="remote",
            salary_min=4000000,
            salary_max=5500000,
            experience_min=5,
            experience_max=10,
            job_type="full-time",
            description="Join our team to work on cutting-edge AI research and products.",
            required_skills=["PyTorch", "TensorFlow", "MLOps", "Python", "Machine Learning"],
            preferred_skills=["Kubernetes", "MLflow", "CUDA", "Deep Learning"],
            applicant_count=347
        ),
        Job(
            title="Deep Learning Engineer",
            company="NVIDIA India",
            location="Pune",
            location_type="hybrid",
            salary_min=4500000,
            salary_max=6500000,
            experience_min=4,
            experience_max=8,
            job_type="full-time",
            description="Work on GPU-accelerated deep learning solutions.",
            required_skills=["CUDA", "PyTorch", "C++", "Python", "Deep Learning"],
            preferred_skills=["Computer Vision", "TensorRT", "Optimization"],
            applicant_count=218
        ),
        Job(
            title="Data Scientist II",
            company="Flipkart",
            location="Bangalore",
            location_type="onsite",
            salary_min=2800000,
            salary_max=3800000,
            experience_min=3,
            experience_max=6,
            job_type="full-time",
            description="Build data-driven products for India's largest e-commerce platform.",
            required_skills=["Python", "SQL", "PySpark", "Machine Learning"],
            preferred_skills=["Kafka", "Spark Streaming", "Tableau"],
            applicant_count=512
        ),
        Job(
            title="ML Research Scientist",
            company="Microsoft Research",
            location="Hyderabad",
            location_type="onsite",
            salary_min=5000000,
            salary_max=7000000,
            experience_min=7,
            experience_max=15,
            job_type="full-time",
            description="Conduct cutting-edge research in machine learning and AI.",
            required_skills=["Research", "NLP", "Python", "Machine Learning"],
            preferred_skills=["CUDA", "Publications", "Deep Learning"],
            applicant_count=189
        ),
        Job(
            title="AI Product Manager",
            company="CRED",
            location="Bangalore",
            location_type="hybrid",
            salary_min=3500000,
            salary_max=5000000,
            experience_min=4,
            experience_max=8,
            job_type="full-time",
            description="Lead AI-powered product initiatives at India's fastest-growing fintech.",
            required_skills=["Roadmapping", "Analytics", "SQL", "Product Management"],
            preferred_skills=["A/B Testing", "Figma", "ML Basics"],
            applicant_count=430
        ),
    ]
    
    for job in jobs:
        db.add(job)
    
    # Create sample candidates
    candidates = [
        Candidate(
            name="Arjun Kumar",
            email="arjun.kumar@email.com",
            phone="+91 9876543210",
            current_role="ML Engineer",
            location="Hyderabad",
            location_preference="hybrid",
            experience_years=4,
            expected_salary=3200000,
            education="B.Tech CSE, NIT",
            skills=["Python", "PyTorch", "TensorFlow", "SQL", "MLOps"],
            ai_score=88,
            profile_views=148,
            applications_sent=12
        ),
        Candidate(
            name="Priya Sharma",
            email="priya.sharma@email.com",
            phone="+91 9876543211",
            current_role="ML Engineer",
            location="Bangalore",
            location_preference="remote",
            experience_years=5,
            expected_salary=4500000,
            education="M.Tech, IIT Delhi",
            skills=["PyTorch", "NLP", "MLOps", "Python", "Computer Vision"],
            ai_score=94,
            profile_views=230,
            applications_sent=18
        ),
        Candidate(
            name="Rohan Mehta",
            email="rohan.mehta@email.com",
            phone="+91 9876543212",
            current_role="Data Scientist",
            location="Pune",
            location_preference="hybrid",
            experience_years=4,
            expected_salary=3500000,
            education="M.Sc. Statistics, DU",
            skills=["Spark", "Sklearn", "TensorFlow", "SQL", "Python"],
            ai_score=88,
            profile_views=156,
            applications_sent=15
        ),
        Candidate(
            name="Anika Patel",
            email="anika.patel@email.com",
            phone="+91 9876543213",
            current_role="AI Researcher",
            location="Hyderabad",
            location_preference="onsite",
            experience_years=6,
            expected_salary=5500000,
            education="PhD AI, CMU",
            skills=["Research", "CUDA", "Python", "Deep Learning", "NLP"],
            ai_score=85,
            profile_views=89,
            applications_sent=8
        ),
        Candidate(
            name="Vikram Singh",
            email="vikram.singh@email.com",
            phone="+91 9876543214",
            current_role="MLOps Engineer",
            location="Bangalore",
            location_preference="remote",
            experience_years=3,
            expected_salary=2800000,
            education="B.E. CSE, RVCE",
            skills=["Kubernetes", "Docker", "Python", "AWS", "MLOps"],
            ai_score=79,
            profile_views=67,
            applications_sent=10
        ),
        Candidate(
            name="Sneha Rao",
            email="sneha.rao@email.com",
            phone="+91 9876543215",
            current_role="Data Engineer",
            location="Bangalore",
            location_preference="onsite",
            experience_years=4,
            expected_salary=3200000,
            education="B.Tech IT, PESIT",
            skills=["Kafka", "Airflow", "SQL", "Python", "Spark"],
            ai_score=73,
            profile_views=45,
            applications_sent=14
        ),
    ]
    
    for candidate in candidates:
        db.add(candidate)
    
    db.commit()
    print("Seed data created successfully!")
    db.close()


# Run seed data on startup
@app.on_event("startup")
async def startup_event():
    seed_data()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

