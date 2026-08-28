from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.resume import router as resume_router
from app.api.skill_gap import router as skill_gap_router


app = FastAPI(
    title="Explainable Career Recommendation System",
    version="1.0.0",
    description="AI-powered resume-based career, skill-gap and course recommendation system"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "message": "Career Recommendation System Backend is Running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


app.include_router(
    resume_router,
    prefix="/api/resume",
    tags=["Resume"]
)


app.include_router(skill_gap_router)