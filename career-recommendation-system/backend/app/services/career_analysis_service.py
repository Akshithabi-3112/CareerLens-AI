from app.services.skill_gap_service import analyze_skill_gap
from app.services.course_service import recommend_courses_for_gaps
from app.services.roadmap_service import generate_career_roadmap
from app.services.explanation_service import generate_unified_career_explanation


def analyze_career_recommendations(
    user_skills,
    career_recommendations,
    cluster_analysis=None,
    ensemble_analysis=None,
):
    analyzed_careers = []

    for career in career_recommendations:
        career_data = {
            "career": career.get("career"),
            "required_skills": (
                career.get("matched_required_skills", [])
                + career.get("missing_skills", [])
            )
        }

        skill_gap_result = analyze_skill_gap(
            user_skills,
            career_data
        )

        missing_skills = skill_gap_result["missing_skills"]
        matched_skills = skill_gap_result["matched_skills"]

        course_recs = recommend_courses_for_gaps(
            missing_skills=missing_skills,
            career_name=career.get("career"),
            required_missing_skills=career.get("missing_skills", []),
            matched_skills=matched_skills,
            top_n=8,
        )

        roadmap = generate_career_roadmap(
            career_name=career.get("career"),
            missing_skills=missing_skills,
            matched_skills=matched_skills,
            required_skills=career.get("matched_required_skills", []) + career.get("missing_skills", []),
        )

        unified_explanation = generate_unified_career_explanation(
            career_name=career.get("career"),
            career_rec=career,
            skill_gap_result=skill_gap_result,
            cluster_analysis=cluster_analysis,
            ensemble_analysis=ensemble_analysis,
            course_recs=course_recs,
            roadmap=roadmap,
        )

        what_to_learn = []
        for skill in missing_skills:
            matching_courses = course_recs.get("skill_course_map", {}).get(skill, [])
            rec_text = f"Develop or learn {skill}"
            if matching_courses:
                first_course = matching_courses[0]
                rec_text = first_course.get("why_recommended") or (
                    f"Recommended: {first_course['course_name']} on {first_course['provider']}"
                )

            what_to_learn.append({
                "skill": skill,
                "recommendation": rec_text,
                "courses": matching_courses,
            })

        analyzed_careers.append({
            "career": career.get("career"),
            "description": career.get("description"),
            "compatibility_score": career.get(
                "compatibility_score"
            ),
            "matched_skills": skill_gap_result[
                "matched_skills"
            ],
            "missing_skills": skill_gap_result[
                "missing_skills"
            ],
            "matched_skill_count": skill_gap_result[
                "matched_skill_count"
            ],
            "missing_skill_count": skill_gap_result[
                "missing_skill_count"
            ],
            "readiness_score": skill_gap_result[
                "readiness_score"
            ],
            "skill_gap_percentage": skill_gap_result[
                "skill_gap_percentage"
            ],
            "what_to_learn": what_to_learn,
            "course_recommendations": course_recs,
            "career_roadmap": roadmap,
            "unified_explanation": unified_explanation,
        })

    return analyzed_careers