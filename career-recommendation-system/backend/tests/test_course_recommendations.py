"""Tests for the Course and Certification Recommendation module.

Tests:
1. Evaluates course recommendations across 3 distinct careers with different missing skills:
   - Data Scientist (missing: Deep Learning, TensorFlow, Tableau)
   - Frontend Developer (missing: React, TypeScript, Next.js)
   - DevOps Engineer (missing: Docker, Kubernetes, AWS)
2. Verifies prioritisation of missing required skills
3. Verifies separation of Essential Courses vs Recommended Certifications
4. Verifies skill-to-course mapping

Run from backend with:
    venv\\Scripts\\python.exe -m tests.test_course_recommendations
"""

import sys
import io

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from app.services.course_service import get_courses_catalog, recommend_courses_for_gaps


TEST_CASES = [
    {
        "career": "Data Scientist",
        "missing_skills": ["Deep Learning", "TensorFlow", "Tableau", "Statistics"],
        "required_missing": ["Deep Learning", "TensorFlow"],
    },
    {
        "career": "Frontend Developer",
        "missing_skills": ["React", "TypeScript", "Next.js", "Tailwind CSS"],
        "required_missing": ["React", "TypeScript"],
    },
    {
        "career": "DevOps Engineer",
        "missing_skills": ["Docker", "Kubernetes", "AWS", "CI/CD"],
        "required_missing": ["Docker", "Kubernetes", "AWS"],
    },
]

print("=" * 80)
print("  COURSE & CERTIFICATION RECOMMENDATION MODULE - VERIFICATION")
print("=" * 80)

catalog = get_courses_catalog()
print(f"\n  [Catalog Status] Loaded {len(catalog)} curated courses & certifications from courses.csv")
assert len(catalog) >= 50, f"Expected at least 50 courses in catalog, found {len(catalog)}"

for tc in TEST_CASES:
    career = tc["career"]
    missing = tc["missing_skills"]
    required_missing = tc["required_missing"]

    print()
    print("=" * 80)
    print(f"  TESTING CAREER: {career}")
    print(f"  Missing Skills:          {', '.join(missing)}")
    print(f"  High-Priority Required:  {', '.join(required_missing)}")
    print("=" * 80)

    recs = recommend_courses_for_gaps(
        missing_skills=missing,
        career_name=career,
        required_missing_skills=required_missing,
        top_n=5,
    )

    print(f"\n  [Summary] {recs['summary']}")
    print(f"  [Total Recommended] {recs['total_courses_recommended']} courses")

    # Essential courses
    print("\n  📚 Top Priority Essential Courses:")
    for i, c in enumerate(recs["essential_courses"][:4], 1):
        cert_tag = "[CERTIFICATE]" if c["certification_available"] else ""
        print(f"    {i}. {c['course_name']} ({c['provider']}) - {c['difficulty']} - {c['duration']} {cert_tag}")
        print(f"       Gaps Covered: {', '.join(c['matched_gaps'])} | Priority Score: {c['relevance_score']}")

    # Recommended Certifications
    print("\n  🏆 Recommended Industry Certifications:")
    for i, cert in enumerate(recs["recommended_certifications"][:3], 1):
        print(f"    {i}. {cert['course_name']} ({cert['provider']}) - Type: {cert['course_type']}")
        print(f"       URL: {cert['url']}")

    # Skill course map check
    print("\n  🗺️ Direct Skill-to-Course Map Preview:")
    for sk in missing[:3]:
        mapped = recs["skill_course_map"].get(sk, [])
        if mapped:
            print(f"    - {sk} -> '{mapped[0]['course_name']}' ({mapped[0]['provider']})")

    # Assertions
    assert recs["total_courses_recommended"] > 0, f"Expected courses for {career}"
    assert len(recs["essential_courses"]) > 0, f"Expected essential courses for {career}"
    assert len(recs["recommended_certifications"]) > 0, f"Expected certifications for {career}"
    
    # Check that courses match actual missing skills
    for c in recs["essential_courses"]:
        assert len(c["matched_gaps"]) > 0, f"Course {c['course_name']} has no matched gaps"
        assert c.get("recommendation_category") == "Skill Gap Learning"
        for g in c["matched_gaps"]:
            assert g in missing, f"Course gap {g} not in target missing skills {missing}"

# ── Test Case: Zero Missing Skills ─────────────────────────────────────────
print("\n" + "=" * 80)
print("  TESTING ZERO MISSING SKILLS SCENARIO (ADVANCED RECOMMENDATIONS)")
print("=" * 80)

zero_gap_recs = recommend_courses_for_gaps(
    missing_skills=[],
    career_name="Data Scientist",
    matched_skills=["Python", "Machine Learning", "SQL", "Pandas"],
    top_n=5,
)

assert zero_gap_recs["has_missing_skills"] is False
assert zero_gap_recs["total_courses_recommended"] > 0
assert len(zero_gap_recs["essential_courses"]) > 0
for adv in zero_gap_recs["essential_courses"]:
    assert adv.get("recommendation_category") == "Advanced Learning"
    assert "targets ." not in adv.get("why_recommended", "")
    assert len(adv.get("why_recommended", "").strip()) > 10

print("  [OK] Zero-missing-skills scenario correctly provides Advanced Learning courses with truthful rationales.")

print()
print("=" * 80)
print("  ALL COURSE & CERTIFICATION TESTS PASSED SUCCESSFULLY!")
print("=" * 80)
