from fastapi import APIRouter
from pydantic import BaseModel
from app.services.skill_gap_service import analyze_skill_gap


router = APIRouter(
    prefix="/api/skill-gap",
    tags=["Skill Gap"]
)


class SkillGapRequest(BaseModel):
    user_skills: list[str]
    career_name: str
    required_skills: list[str]


@router.post("/analyze")
def analyze(request: SkillGapRequest):

    career = {
        "career": request.career_name,
        "required_skills": request.required_skills
    }

    result = analyze_skill_gap(
        request.user_skills,
        career
    )

    what_to_learn = []

    for skill in result["missing_skills"]:
        what_to_learn.append(
            {
                "skill": skill,
                "recommendation": f"Develop or learn {skill}"
            }
        )

    return {
        "career": result["career"],
        "required_skills": result["required_skills"],
        "matched_skills": result["matched_skills"],
        "missing_skills": result["missing_skills"],
        "matched_skill_count": result["matched_skill_count"],
        "missing_skill_count": result["missing_skill_count"],
        "readiness_score": result["readiness_score"],
        "skill_gap_percentage": result["skill_gap_percentage"],
        "what_to_learn": what_to_learn
    }