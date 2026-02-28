# NexMatch AI - Job Matching Platform

## 🔍 What is This Project? (Simple Explanation)

**NexMatch AI** is a smart job matching platform that helps:
1. **Job Seekers** find jobs that match their skills
2. **Companies** find the best candidates for their job openings

---

### 🧩 How It Works (Simple Terms)

**1. The Problem It Solves:**
- Job hunting is hard - candidates don't know which jobs they're qualified for
- Companies get hundreds of applications - hard to find the right person
- This AI matches the RIGHT candidate to the RIGHT job automatically

**2. What It Does:**

| Feature | What It Does |
|---------|-------------|
| **Job Listings** | Shows available jobs with company, salary, location, required skills |
| **Candidate Profiles** | Stores candidate info: skills, experience, education |
| **AI Matching** | Calculates a "match score" (0-100%) based on skills, experience, salary, location |
| **Resume Parser** | Upload a PDF resume → AI extracts skills & experience automatically |
| **Skill Gap Analysis** | Shows which skills you're missing for a job + learning roadmap |
| **Live Recalculator** | Adjust your profile (skills, experience, salary) and see how your match score changes |
| **Analytics** | Shows algorithm performance metrics |

**3. The Matching Algorithm:**
```
Match Score = Skills (40%) + Experience (25%) + Location (20%) + Salary Fit (15%)
```

**4. Sample Data Included:**
- 5 Jobs: ML Engineer at Google DeepMind, NVIDIA, Flipkart, Microsoft Research, CRED
- 6 Candidates: Arjun, Priya, Rohan, Anika, Vikram, Sneha

---

### 🚀 How to Use It

1. Open **http://localhost:8000** in your browser
2. You'll see the job matching dashboard
3. Click on any job to see:
   - Your match score
   - Which skills match/missing
   - AI tips on how to improve
4. Use the **Resume Parser** to upload your resume
5. Use **Skill Gap Roadmap** to see what skills to learn
6. Use **Live Match Recalculator** to optimize your profile

The app is fully functional with sample data ready to test!

---

## 🛠️ Tech Stack Explained

### **Frontend**
| Technology | Purpose |
|------------|---------|
| **HTML5** | Structure of the web pages |
| **CSS3** | Styling, animations, responsive design |
| **JavaScript** | Interactive features, API calls, UI logic |
| **Vanilla JS** | No framework needed - lightweight & fast |

### **Backend**
| Technology | Purpose |
|------------|---------|
| **FastAPI** | Modern Python web framework for building APIs |
| **Uvicorn** | ASGI server to run the FastAPI app |
| **Python 3.9+** | Programming language |

### **Database**
| Technology | Purpose |
|------------|---------|
| **SQLAlchemy** | Python ORM for database operations |
| **SQLite** | Lightweight database (file-based, no setup needed) |
| **aiosqlite** | Async SQLite support |

### **AI/ML Features**
| Technology | Purpose |
|------------|---------|
| **OpenAI API** | AI-powered chatbot & resume parsing (optional) |
| **Custom Matching Algorithm** | Skills, experience, location, salary scoring |

### **Utilities**
| Technology | Purpose |
|------------|---------|
| **python-dotenv** | Load environment variables |
| **python-multipart** | Handle file uploads (resumes) |
| **pypdf2** | Read PDF resumes |
| **python-docx** | Read DOCX resumes |
| **Pydantic** | Data validation for API requests |

---

### 📊 Architecture Overview

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   Browser       │ ──▶  │   FastAPI       │ ──▶  │    SQLite       │
│   (HTML/CSS/JS) │ ◀──  │   (Python)      │ ◀──  │   Database      │
└─────────────────┘      └─────────────────┘      └─────────────────┘
```

**Flow:**
1. User opens frontend (index.html)
2. JavaScript calls backend APIs
3. FastAPI processes requests
4. SQLAlchemy interacts with SQLite database
5. Response sent back to browser

---

## 📁 Project Structure

```
job pairing ai/
├── index.html              # Frontend UI
├── README.md               # This file
├── TODO.md                 # Project tasks
├── .gitignore              # Git ignore rules
├── backend/
│   ├── main.py             # FastAPI application
│   ├── models.py           # Database models
│   ├── matching_engine.py  # AI matching logic
│   ├── requirements.txt    # Python dependencies
│   ├── .env                # Environment variables
│   ├── job_matching.db     # SQLite database
│   └── venv/               # Virtual environment
```

---

## ⚙️ Setup & Run

### Prerequisites
- Python 3.9+
- Terminal/Command Line

### Installation

```bash
# Navigate to backend folder
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Mac/Linux
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### Run the Server

```bash
# From backend folder
python main.py
```

### Access the App
- **Frontend:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

---

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serve frontend |
| `/api/v1/health` | GET | Health check |
| `/api/v1/jobs` | GET | List all jobs |
| `/api/v1/jobs/{id}` | GET | Get job details |
| `/api/v1/candidates` | GET | List all candidates |
| `/api/v1/candidates/{id}` | GET | Get candidate details |
| `/api/v1/match/{candidate_id}/{job_id}` | GET | Get match score |
| `/api/v1/match/recalculate` | POST | Recalculate match |
| `/api/v1/skillgap/{job_id}` | GET | Skill gap analysis |
| `/api/v1/resume/parse` | POST | Parse resume |
| `/api/v1/apply` | POST | Apply to job |
| `/api/v1/chat` | POST | AI chatbot |
| `/api/v1/analytics` | GET | Algorithm metrics |

---

## 📝 Environment Variables

Create a `.env` file in the `backend/` folder:

```env
# OpenAI API Key - Leave empty to use fallback mode (no AI features)
OPENAI_API_KEY=
```

**Note:** The AI features (chatbot, resume parsing) work in "fallback mode" without an API key. Set `OPENAI_API_KEY` to enable full AI features.

---

## 🎯 Features

1. **Job Search** - Browse jobs with filters
2. **Candidate Ranking** - AI ranks candidates for jobs
3. **Match Scoring** - Multi-factor matching algorithm
4. **Resume Parsing** - Extract info from PDF/DOCX resumes
5. **Skill Gap Analysis** - See what skills to learn
6. **Live Recalculator** - Adjust profile and see score changes
7. **AI Chatbot** - Career guidance assistant
8. **Analytics Dashboard** - View algorithm performance

---

Built for Hackathon 2025 ✦

