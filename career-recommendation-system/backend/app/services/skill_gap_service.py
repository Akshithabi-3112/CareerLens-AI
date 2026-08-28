def analyze_skill_gap(user_skills, career):
    required_skills = career.get("required_skills", [])

    user_skills_normalized = [
        skill.strip().lower()
        for skill in user_skills
    ]

    matched_skills = []
    missing_skills = []

    for original_skill in required_skills:
        normalized_skill = original_skill.strip().lower()

        if normalized_skill in user_skills_normalized:
            matched_skills.append(original_skill)
        else:
            missing_skills.append(original_skill)

    total_required_skills = len(required_skills)

    if total_required_skills == 0:
        readiness_score = 0
        skill_gap_percentage = 100
    else:
        readiness_score = round(
            (len(matched_skills) / total_required_skills) * 100,
            2
        )

        skill_gap_percentage = round(
            (len(missing_skills) / total_required_skills) * 100,
            2
        )

    return {
        "career": career.get("career"),
        "required_skills": required_skills,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "total_required_skills": total_required_skills,
        "matched_skill_count": len(matched_skills),
        "missing_skill_count": len(missing_skills),
        "readiness_score": readiness_score,
        "skill_gap_percentage": skill_gap_percentage
    }