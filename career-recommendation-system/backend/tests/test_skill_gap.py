from app.services.skill_gap_service import analyze_skill_gap


user_skills = [
    "Python",
    "Java",
    "SQL",
    "MySQL",
    "Problem Solving"
]


career = {
    "career": "Data Scientist",
    "required_skills": [
        "Python",
        "SQL",
        "Machine Learning",
        "Data Analysis",
        "Statistics"
    ]
}


result = analyze_skill_gap(user_skills, career)


print("\nSKILL GAP ANALYSIS")
print("-" * 50)

print("Career:")
print(result["career"])

print("\nRequired Skills:")
print(result["required_skills"])

print("\nMatched Skills:")
print(result["matched_skills"])

print("\nMissing Skills:")
print(result["missing_skills"])

print("\nMatched Skill Count:")
print(result["matched_skill_count"])

print("\nMissing Skill Count:")
print(result["missing_skill_count"])

print("\nReadiness Score:")
print(result["readiness_score"], "%")

print("\nSkill Gap Percentage:")
print(result["skill_gap_percentage"], "%")