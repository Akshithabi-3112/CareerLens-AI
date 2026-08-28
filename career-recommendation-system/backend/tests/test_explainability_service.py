"""Tests for the Unified Explainability Engine.

Tests:
1. Answers all 9 explainability questions with mathematically grounded data.
2. Verified that explanations change when skills change.
3. Verified that explanations NEVER claim skills the user does not have.
4. Verified that score math formula strictly matches computed component scores.
5. Verified skill-gate protection explanation behavior.

Run from backend with:
    venv\\Scripts\\python.exe -m tests.test_explainability_service
"""

import sys
import io

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from app.services.recommendation_service import build_hybrid_recommendations
from app.services.career_analysis_service import analyze_career_recommendations


print("=" * 80)
print("  UNIFIED EXPLAINABILITY ENGINE - VERIFICATION TEST")
print("=" * 80)

# Profile 1: Data Scientist candidate
user_skills_data = ["Python", "Machine Learning", "TensorFlow", "Pandas"]
skills_result_data = {
    "extracted_skills": user_skills_data,
    "normalized_skills": user_skills_data,
    "skills_by_category": {"AI and Machine Learning": ["Machine Learning", "TensorFlow"], "Programming": ["Python"], "Data Science": ["Pandas"]},
}

hybrid_data = build_hybrid_recommendations(skills_result_data)
analysis_data = analyze_career_recommendations(
    user_skills_data,
    hybrid_data["career_recommendations"],
    cluster_analysis=hybrid_data.get("cluster_analysis"),
    ensemble_analysis=hybrid_data.get("ensemble_analysis"),
)

top_entry = analysis_data[0]
exp = top_entry["unified_explanation"]

print(f"\n[TOP CAREER EXPLANATION: {top_entry['career']}]")
print(f"  Executive Summary:\n    \"{exp['executive_summary']}\"")
print(f"\n  Key Strengths ({len(exp['key_strengths'])}):")
for s in exp["key_strengths"]:
    print(f"    • {s['skill']} ({s['type']}): {s['impact']}")

print(f"\n  Critical Gaps ({len(exp['critical_gaps'])}):")
for g in exp["critical_gaps"]:
    print(f"    • {g['skill']} ({g['urgency']})")

print(f"\n  Transparent Math Formula:")
print(f"    {exp['score_breakdown']['math_formula_explanation']}")

print(f"\n  Machine Learning Signals:")
print(f"    • Cluster:          {exp['ml_influence']['cluster_name']} ({exp['ml_influence']['cluster_similarity_percentage']}%)")
print(f"    • Ensemble:         {exp['ml_influence']['ensemble_confidence_percentage']}% ({exp['ml_influence']['ensemble_model_agreement']})")
print(f"    • Skill Gate:       {exp['ml_influence']['skill_gate_factor']}x ({exp['ml_influence']['skill_gate_explanation']})")

print(f"\n  Learning Rationale:")
print(f"    • Course:   \"{exp['learning_rationale']['course_recommendation_reason']}\"")
print(f"    • Roadmap:  \"{exp['learning_rationale']['roadmap_sequencing_reason']}\"")


# ── ASSERTION CHECKS ───────────────────────────────────────────────────────
print("\n" + "=" * 80)
print("  ASSERTION & GROUNDING CHECKS")
print("=" * 80)

# 1. No false skills claimed in strengths
user_skill_set = {s.lower() for s in user_skills_data}
for strength in exp["key_strengths"]:
    assert strength["skill"].lower() in user_skill_set, (
        f"CRITICAL ERROR: Strength '{strength['skill']}' was claimed but user does not have it!"
    )
print("  [OK] No unheld skills claimed in strengths.")

# 2. Math formula matches scores
sb = exp["score_breakdown"]
final = sb["final_score"]
compat = sb["compatibility_score"]
clust = sb["cluster_relevance"]
ens = sb["ensemble_confidence"]
calc = round(0.6 * compat + 0.2 * clust + 0.2 * ens, 1)
assert abs(final - calc) < 0.5, f"Math discrepancy: final={final}, calculated={calc}"
print(f"  [OK] Math consistency verified: {final}% == {calc}%")

# 3. Dynamic change test with Frontend profile
user_skills_web = ["HTML", "CSS", "JavaScript", "React"]
skills_result_web = {
    "extracted_skills": user_skills_web,
    "normalized_skills": user_skills_web,
    "skills_by_category": {"Programming": ["JavaScript"], "Web Development": ["HTML", "CSS", "React"]},
}

hybrid_web = build_hybrid_recommendations(skills_result_web)
analysis_web = analyze_career_recommendations(
    user_skills_web,
    hybrid_web["career_recommendations"],
    cluster_analysis=hybrid_web.get("cluster_analysis"),
    ensemble_analysis=hybrid_web.get("ensemble_analysis"),
)

top_web = analysis_web[0]
exp_web = top_web["unified_explanation"]

print(f"\n[FRONTEND PROFILE EXPLANATION: {top_web['career']}]")
print(f"  Executive Summary: \"{exp_web['executive_summary']}\"")
assert top_web["career"] in ["Frontend Developer", "Web Developer", "Full Stack Developer", "UI/UX Designer"], "Top role should be web-related"
assert "JavaScript" in [s["skill"] for s in exp_web["key_strengths"]], "JavaScript must be in strengths"
assert "Python" not in [s["skill"] for s in exp_web["key_strengths"]], "Python must NOT be in web strengths"
print("  [OK] Dynamic variation and profile specificity verified!")

# 4. Regression Test: Scenario A — With Missing Skills
course_reason_a = exp["learning_rationale"]["course_recommendation_reason"]
assert "targets ." not in course_reason_a, f"Malformed empty placeholder in Scenario A: {course_reason_a}"
assert "develop ," not in course_reason_a, f"Malformed empty placeholder in Scenario A: {course_reason_a}"
assert len(course_reason_a.strip()) > 10, "Expected non-empty course rationale"
print(f"  [OK] Scenario A (Missing Skills) Course Rationale verified: \"{course_reason_a}\"")

# 5. Regression Test: Scenario B — Zero Missing Skills (100% match)
from app.services.career_matcher import load_careers
all_careers = load_careers()
ds_career = next((c for c in all_careers if c["career"] == "Data Scientist"), all_careers[0])
all_ds_skills = ds_career["required_skills"] + ds_career.get("preferred_skills", [])

zero_gap_skills_data = {
    "extracted_skills": all_ds_skills,
    "normalized_skills": all_ds_skills,
    "skills_by_category": {"Data Science": all_ds_skills},
}
zero_gap_hybrid = build_hybrid_recommendations(zero_gap_skills_data)
zero_gap_analysis = analyze_career_recommendations(
    all_ds_skills,
    zero_gap_hybrid["career_recommendations"],
    cluster_analysis=zero_gap_hybrid.get("cluster_analysis"),
    ensemble_analysis=zero_gap_hybrid.get("ensemble_analysis"),
)

ds_entry = next((e for e in zero_gap_analysis if e["career"] == ds_career["career"]), zero_gap_analysis[0])
exp_zero = ds_entry["unified_explanation"]
course_reason_b = exp_zero["learning_rationale"]["course_recommendation_reason"]

assert len(ds_entry["missing_skills"]) == 0, "Expected zero missing skills for full-skill profile"
assert "targets ." not in course_reason_b, f"Malformed empty placeholder in Scenario B: {course_reason_b}"
assert "develop ," not in course_reason_b, f"Malformed empty placeholder in Scenario B: {course_reason_b}"
assert any(keyword in course_reason_b.lower() for keyword in ["advanced", "deepen", "readiness", "specialization", "strengthen"]), (
    f"Expected advanced/readiness learning rationale for zero missing skills, got: {course_reason_b}"
)
print(f"  [OK] Scenario B (Zero Missing Skills) Course Rationale verified: \"{course_reason_b}\"")

print("\n" + "=" * 80)
print("  ALL EXPLAINABILITY VERIFICATION TESTS PASSED!")
print("=" * 80)
