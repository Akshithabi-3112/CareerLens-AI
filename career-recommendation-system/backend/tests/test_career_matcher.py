from app.services.skill_extractor import extract_skills
from app.services.career_matcher import recommend_careers


sample_resume = """
I am a Computer Science student.

I have experience with Python, Java,
JavaScript, HTML and CSS.

I have worked with SQL, MySQL and MongoDB.

My projects include Machine Learning,
Data Analysis and web development using
React and FastAPI.

I also use Docker, Git and AWS.

My strengths are Problem Solving,
Teamwork and Communication.
"""


skills_result = extract_skills(
    sample_resume
)

recommendations = recommend_careers(
    skills_result,
    top_n=5
)


print("\nTOP CAREER RECOMMENDATIONS\n")


for index, career in enumerate(
    recommendations,
    start=1
):

    print(
        f"{index}. {career['career']}"
    )

    print(
        "Compatibility Score:",
        career["compatibility_score"],
        "%"
    )

    print(
        "Matched Required Skills:",
        career["matched_required_skills"]
    )

    print(
        "Missing Skills:",
        career["missing_skills"]
    )

    print("-" * 50)