# Job Pairing AI - Smart Matching Engine
FastAPI backend with OpenAI-powered intelligent job matching

## Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set environment variable:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

4. Run the server:
```bash
uvicorn main:app --reload
```

5. Open http://localhost:8000/docs for API documentation

## API Endpoints

- `GET /api/v1/jobs` - Get all jobs with match scores
- `GET /api/v1/jobs/{job_id}` - Get job details
- `GET /api/v1/candidates` - Get all candidates (for employer view)
- `GET /api/v1/candidates/{candidate_id}` - Get candidate details
- `POST /api/v1/match/recalculate` - Recalculate match score
- `POST /api/v1/resume/parse` - Parse resume and extract profile
- `GET /api/v1/skillgap/{job_id}` - Get skill gap analysis
- `POST /api/v1/apply` - Apply to a job
- `GET /api/v1/analytics` - Get algorithm performance metrics

## Features

- Skill-based matching algorithm
- Experience and qualification filtering
- Location-based recommendations
- Salary compatibility assessment
- AI-powered candidate ranking
- Resume parsing with OpenAI
- Real-time match score recalculation

