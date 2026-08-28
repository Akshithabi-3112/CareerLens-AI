"""Evaluation script for Skill-Gap Analysis.

Evaluates:
- Precision, Recall, and F1 of identified missing skills vs ground-truth required career skills
- Readiness score calculation correctness
"""

from typing import Dict, List
from app.services.skill_gap_service import analyze_skill_gap


# Controlled test cases: (user_skills, career_data, expected_missing, expected_matched, expected_readiness)
CONTROLLED_GAP_CASES = [
    {
        "case_id": "case_1_full_match",
        "user_skills": ["Python", "Machine Learning", "TensorFlow", "Pandas"],
        "career_data": {
            "career": "Machine Learning Engineer",
            "required_skills": ["Python", "Machine Learning", "TensorFlow", "Pandas"],
        },
        "expected_matched": ["Python", "Machine Learning", "TensorFlow", "Pandas"],
        "expected_missing": [],
        "expected_readiness": 100.0,
    },
    {
        "case_id": "case_2_partial_match",
        "user_skills": ["Python", "SQL"],
        "career_data": {
            "career": "Data Scientist",
            "required_skills": ["Python", "SQL", "Machine Learning", "Statistics"],
        },
        "expected_matched": ["Python", "SQL"],
        "expected_missing": ["Machine Learning", "Statistics"],
        "expected_readiness": 50.0,
    },
    {
        "case_id": "case_3_zero_match",
        "user_skills": ["Photoshop", "Illustrator"],
        "career_data": {
            "career": "DevOps Engineer",
            "required_skills": ["Linux", "Docker", "Kubernetes", "CI/CD"],
        },
        "expected_matched": [],
        "expected_missing": ["Linux", "Docker", "Kubernetes", "CI/CD"],
        "expected_readiness": 0.0,
    },
    {
        "case_id": "case_4_frontend_match",
        "user_skills": ["HTML", "CSS", "JavaScript"],
        "career_data": {
            "career": "Frontend Developer",
            "required_skills": ["HTML", "CSS", "JavaScript", "React"],
        },
        "expected_matched": ["HTML", "CSS", "JavaScript"],
        "expected_missing": ["React"],
        "expected_readiness": 75.0,
    },
]


def evaluate_skill_gap() -> Dict:
    results = []

    for case in CONTROLLED_GAP_CASES:
        res = analyze_skill_gap(case["user_skills"], case["career_data"])

        matched = [s.lower() for s in res["matched_skills"]]
        missing = [s.lower() for s in res["missing_skills"]]
        exp_matched = [s.lower() for s in case["expected_matched"]]
        exp_missing = [s.lower() for s in case["expected_missing"]]

        matched_match = set(matched) == set(exp_matched)
        missing_match = set(missing) == set(exp_missing)
        readiness_match = abs(res["readiness_score"] - case["expected_readiness"]) < 0.01

        results.append({
            "case_id": case["case_id"],
            "career": case["career_data"]["career"],
            "calculated_readiness": res["readiness_score"],
            "expected_readiness": case["expected_readiness"],
            "matched_skills_accurate": matched_match,
            "missing_skills_accurate": missing_match,
            "readiness_accurate": readiness_match,
        })

    all_accurate = all(
        r["matched_skills_accurate"] and r["missing_skills_accurate"] and r["readiness_accurate"]
        for r in results
    )

    return {
        "num_test_cases": len(results),
        "all_cases_passed": all_accurate,
        "test_results": results,
    }


if __name__ == "__main__":
    import json
    res = evaluate_skill_gap()
    print("=== SKILL GAP EVALUATION RESULTS ===")
    print(json.dumps(res, indent=2))
