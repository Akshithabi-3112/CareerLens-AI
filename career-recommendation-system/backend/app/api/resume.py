from fastapi import APIRouter, UploadFile, File

from app.services.career_analysis_service import analyze_career_recommendations
from app.services.recommendation_service import build_hybrid_recommendations
from app.services.resume_parser import parse_resume
from app.services.skill_extractor import extract_skills
from app.services.skill_gap_service import analyze_skill_gap
from app.services.skill_normalizer import normalize_skills_result


router = APIRouter()


@router.get("/health")
def resume_health():
    return {
        "status": "Resume API is working"
    }


@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...)
):
    # Step 1: Parse uploaded resume
    resume_data = await parse_resume(file)

    # Step 2: Get extracted text
    extracted_text = resume_data.get(
        "extracted_text",
        ""
    )

    # Step 3: Extract skills
    skills_result = extract_skills(
        extracted_text
    )

    # Normalize aliases after extraction so scoring and API output use a
    # consistent set of canonical names without changing extraction logic.
    skills_result = normalize_skills_result(
        skills_result
    )

    # Get extracted skills list
    extracted_skills = skills_result.get(
        "extracted_skills",
        []
    )

    # Step 4: Run the hybrid recommendation pipeline. It safely falls back
    # to the existing rule-based matcher if ML signals are unavailable.
    hybrid_result = build_hybrid_recommendations(skills_result)
    career_recommendations = hybrid_result["career_recommendations"]

    # Step 5: Analyze skill gap, learning resources, and unified explainability for every recommended career
    career_analysis = analyze_career_recommendations(
        extracted_skills,
        career_recommendations,
        cluster_analysis=hybrid_result.get("cluster_analysis"),
        ensemble_analysis=hybrid_result.get("ensemble_analysis"),
    )

    # Step 6: Return complete analysis
    return {
        "resume": resume_data,
        "skills": skills_result,
        "career_recommendations": career_recommendations,
        "career_analysis": career_analysis,
        "cluster_analysis": hybrid_result["cluster_analysis"],
        "ensemble_analysis": hybrid_result["ensemble_analysis"],
        "recommendation_metadata": hybrid_result[
            "recommendation_metadata"
        ],
    }
