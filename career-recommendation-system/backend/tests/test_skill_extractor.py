from app.services.skill_extractor import extract_skills


sample_resume = """
I am a Computer Science student with experience in Python,
Java, SQL, Machine Learning and Data Analysis.

I have developed web applications using React, FastAPI,
HTML, CSS and JavaScript.

I also have experience with Docker, Git, AWS,
MySQL and MongoDB.

My strengths include Problem Solving, Teamwork
and Communication.
"""


result = extract_skills(sample_resume)


print("\nEXTRACTED SKILLS:")
for skill in result["extracted_skills"]:
    print("-", skill)

print("\nSKILL CATEGORIES:")
for category, skills in result["skill_categories"].items():
    print(category, ":", skills)

# ── Verification checks ───────────────────────────────────────────────────
skills_count = len(result["extracted_skills"])
categories_count = len(result["skill_categories"])

assert skills_count > 0, "Expected extracted skills to be non-empty"
assert categories_count > 0, "Expected skill categories to be non-empty"
assert "Python" in result["extracted_skills"]
assert "FastAPI" in result["extracted_skills"]
assert "SQL" in result["extracted_skills"]

print(f"\nTruthful extraction metrics verified: {skills_count} skills across {categories_count} categories.")