"""Comprehensive verification of the Hybrid Recommendation Algorithm.

Tests:
1. 4 distinct profiles (AI/ML, Frontend, Backend, Data/Database)
2. Compares Compatibility-only ranking vs Hybrid ranking
3. Verifies guardrails (unrelated careers not artificially inflated by ML signals)
4. Checks explainability outputs and score breakdowns

Run from backend with:
    venv\\Scripts\\python.exe -m tests.test_hybrid_ranking
"""

import sys
import io

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from app.services.recommendation_service import build_hybrid_recommendations
from app.services.career_matcher import calculate_career_score, load_careers, normalize_skills


PROFILES = {
    "AI / ML Profile": {
        "extracted_skills": ["Python", "Machine Learning", "TensorFlow", "Deep Learning", "PyTorch"],
        "skill_categories": {
            "Programming": ["Python"],
            "AI and Machine Learning": ["Machine Learning", "TensorFlow", "Deep Learning", "PyTorch"],
        },
        "evidence": {s: s for s in ["Python", "Machine Learning", "TensorFlow", "Deep Learning", "PyTorch"]},
        "expected_top_domains": ["Data Scientist", "Machine Learning Engineer", "AI Engineer", "Deep Learning Engineer"],
    },
    "Frontend Profile": {
        "extracted_skills": ["HTML", "CSS", "JavaScript", "React", "TypeScript"],
        "skill_categories": {
            "Frontend": ["HTML", "CSS", "JavaScript", "React", "TypeScript"],
        },
        "evidence": {s: s for s in ["HTML", "CSS", "JavaScript", "React", "TypeScript"]},
        "expected_top_domains": ["Frontend Developer", "React Developer", "Web Developer", "Full Stack Developer"],
    },
    "Backend Profile": {
        "extracted_skills": ["Java", "Spring Boot", "SQL", "Docker", "REST APIs"],
        "skill_categories": {
            "Programming": ["Java"],
            "Backend": ["Spring Boot", "REST APIs"],
            "Database": ["SQL"],
            "DevOps": ["Docker"],
        },
        "evidence": {s: s for s in ["Java", "Spring Boot", "SQL", "Docker", "REST APIs"]},
        "expected_top_domains": ["Backend Developer", "Software Engineer", "Java Developer", "API Engineer"],
    },
    "Database Profile": {
        "extracted_skills": ["SQL", "MySQL", "MongoDB", "Database Design", "PostgreSQL"],
        "skill_categories": {
            "Database": ["SQL", "MySQL", "MongoDB", "Database Design", "PostgreSQL"],
        },
        "evidence": {s: s for s in ["SQL", "MySQL", "MongoDB", "Database Design", "PostgreSQL"]},
        "expected_top_domains": ["Database Developer", "Database Administrator", "Backend Developer", "Data Analyst"],
    },
}


def get_compat_only_ranking(skills_result, top_n=5):
    """Compute pure rule-based compatibility rankings for baseline comparison."""
    careers = load_careers()
    user_skills = normalize_skills(skills_result["extracted_skills"])
    scores = []
    for c in careers:
        res = calculate_career_score(
            user_skills,
            skills_result.get("skill_categories", {}),
            skills_result["extracted_skills"],
            skills_result.get("evidence", {}),
            c,
        )
        scores.append(res)
    scores.sort(key=lambda x: x["compatibility_score"], reverse=True)
    return scores[:top_n]


print("=" * 80)
print("  HYBRID RECOMMENDATION SYSTEM - COMPREHENSIVE VERIFICATION")
print("=" * 80)

careers_db = load_careers()

for name, profile in PROFILES.items():
    print()
    print("=" * 80)
    print(f"  TESTING: {name}")
    print(f"  Skills: {', '.join(profile['extracted_skills'])}")
    print("=" * 80)

    # 1. Run Hybrid Recommendations
    hybrid_res = build_hybrid_recommendations(profile, top_n=5)
    recs = hybrid_res["career_recommendations"]
    cluster = hybrid_res["cluster_analysis"]
    ensemble = hybrid_res["ensemble_analysis"]

    print(f"\n  [Cluster Match] {cluster.get('cluster_name')} (Sim: {cluster.get('profile_cluster_similarity')}%)")
    print(f"  [Ensemble Status] {ensemble.get('status')} | Top CV Acc: {ensemble.get('model_metrics', {}).get('cross_validation_mean_accuracy', 'N/A')}")

    # 2. Compare with Baseline Compatibility-only Ranking
    compat_baseline = get_compat_only_ranking(profile, top_n=5)

    print("\n  Top 5 Hybrid Recommendations vs Baseline Compatibility:")
    print(f"  {'Rank':<5} {'Hybrid Role':<28} {'Hybrid Score':<14} {'Compat Only':<28} {'Compat Score'}")
    print("  " + "-" * 78)

    for i in range(5):
        h_role = recs[i]["career"] if i < len(recs) else "—"
        h_score = f"{recs[i]['final_score']}%" if i < len(recs) else "—"
        c_role = compat_baseline[i]["career"] if i < len(compat_baseline) else "—"
        c_score = f"{compat_baseline[i]['compatibility_score']}%" if i < len(compat_baseline) else "—"
        print(f"  #{i+1:<4} {h_role:<28} {h_score:<14} {c_role:<28} {c_score}")

    # 3. Print Top 1 Score Breakdown and Explanation
    top = recs[0]
    print(f"\n  Top Recommendation Detail: '{top['career']}'")
    print(f"    - Compatibility Score:    {top['compatibility_score']}%")
    print(f"    - Cluster Relevance:       {top['cluster_relevance_score']}% (Aligned: {top['cluster_alignment']})")
    print(f"    - Ensemble Confidence:     {top['ensemble_prediction_score']}%")
    print(f"    - Skill Gate Factor:       {top['score_components'].get('skill_gate_factor', 1.0)}")
    print(f"    - Final Hybrid Score:      {top['final_score']}%")
    print(f"    - Matched Skills:          {', '.join(top['matched_skills'])}")
    print(f"    - Missing Skills:          {', '.join(top['missing_skills'])}")
    print(f"    - Explanation:             \"{top['explanation']}\"")

    # Assertions
    assert len(recs) == 5, f"Expected 5 recommendations, got {len(recs)}"
    assert top["final_score"] > 0, "Top hybrid score must be positive"
    assert "explanation" in top and len(top["explanation"]) > 20, "Explanation missing or too short"
    assert "score_components" in top, "Score components missing"


# ── Guardrail Test: Zero-skill match career protection ────────────────────
print()
print("=" * 80)
print("  GUARDRAIL VERIFICATION: Zero-skill Career Inflation Protection")
print("=" * 80)

# With AI/ML skills, an unrelated role like "Graphic Designer" should have 0 required skills matched
ai_profile = PROFILES["AI / ML Profile"]
ai_hybrid = build_hybrid_recommendations(ai_profile, top_n=58) # all careers
all_recs = ai_hybrid["career_recommendations"]

graphic_designer = next((r for r in all_recs if r["career"] == "Graphic Designer"), None)
top_ai_career = all_recs[0]

print(f"  Top AI Career: '{top_ai_career['career']}' -> Final Score: {top_ai_career['final_score']}%")
if graphic_designer:
    print(f"  Unrelated 'Graphic Designer' -> Matched Required: {graphic_designer['matched_required_skills']}, Skill Gate: {graphic_designer['score_components']['skill_gate_factor']}, Final Score: {graphic_designer['final_score']}%")
    assert graphic_designer["score_components"]["skill_gate_factor"] == 0.0, "Skill gate factor for zero-match role must be 0.0"
    assert graphic_designer["final_score"] < top_ai_career["final_score"], "Unrelated role must score significantly lower than relevant roles"
    print("  [OK] Guardrail successfully clamped ML boost for zero-skill match career!")

# ── Score Transparency & Contribution Verification ───────────────────────
print()
print("=" * 80)
print("  SCORE TRANSPARENCY & WEIGHTED CONTRIBUTION VERIFICATION")
print("=" * 80)

for rec in all_recs[:10]:
    sc = rec.get("score_components", {})
    w_contrib = sc.get("weighted_contributions", {})
    weights = sc.get("weights", {})
    gate = sc.get("skill_gate_factor", 1.0)
    final = rec.get("final_score", 0.0)

    c_skill = w_contrib.get("skill_match", 0.0)
    c_clust = w_contrib.get("cluster_relevance", 0.0)
    c_ens = w_contrib.get("ensemble_prediction", 0.0)

    # 1. Verify exact mathematical contribution
    expected_skill = round(weights.get("skill_match", 0.60) * rec["compatibility_score"], 2)
    expected_clust = round(weights.get("cluster_relevance", 0.20) * rec["cluster_relevance_score"] * gate, 2)
    expected_ens = round(weights.get("ensemble_prediction", 0.20) * rec["ensemble_prediction_score"] * gate, 2)

    assert abs(c_skill - expected_skill) <= 0.01, f"Skill contribution mismatch: {c_skill} != {expected_skill}"
    assert abs(c_clust - expected_clust) <= 0.01, f"Cluster contribution mismatch: {c_clust} != {expected_clust}"
    assert abs(c_ens - expected_ens) <= 0.01, f"Ensemble contribution mismatch: {c_ens} != {expected_ens}"

    # 2. Verify sum equals final score
    calc_sum = round(c_skill + c_clust + c_ens, 2)
    assert abs(final - calc_sum) <= 0.05, f"Sum mismatch for '{rec['career']}': final={final}, sum={calc_sum}"

    # 3. Additive helper fields check
    assert "skill_weight" in rec and rec["skill_weight"] == round(weights.get("skill_match", 0.60) * 100)
    assert "cluster_weight" in rec and rec["cluster_weight"] == round(weights.get("cluster_relevance", 0.20) * 100)
    assert "ensemble_weight" in rec and rec["ensemble_weight"] == round(weights.get("ensemble_prediction", 0.20) * 100)
    assert "skill_contribution" in rec and rec["skill_contribution"] == c_skill
    assert "cluster_contribution" in rec and rec["cluster_contribution"] == c_clust
    assert "ensemble_contribution" in rec and rec["ensemble_contribution"] == c_ens

print("  [OK] All 10 recommendations verified: weighted contributions mathematically sum to final score!")

print()
print("=" * 80)
print("  ALL HYBRID RECOMMENDATION TESTS PASSED SUCCESSFULLY!")
print("=" * 80)
