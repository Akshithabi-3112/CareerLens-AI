"""Reproducible checks for the hybrid recommendation pipeline.

Run from backend with:
    venv\\Scripts\\python.exe -m tests.test_hybrid_recommendation
"""

from app.services.recommendation_service import build_hybrid_recommendations


full_profile = {
    "extracted_skills": ["Python", "SQL", "Machine Learning", "Pandas"],
    "skill_categories": {
        "Programming": ["Python"],
        "Database": ["SQL"],
        "AI and Machine Learning": ["Machine Learning"],
        "Data Science": ["Pandas"],
    },
    "evidence": {
        "Python": "Python",
        "SQL": "SQL",
        "Machine Learning": "Machine Learning",
        "Pandas": "Pandas",
    },
}
sparse_profile = {
    "extracted_skills": ["Python"],
    "skill_categories": {"Programming": ["Python"]},
    "evidence": {"Python": "Python"},
}

full_result = build_hybrid_recommendations(full_profile, top_n=3)
sparse_result = build_hybrid_recommendations(sparse_profile, top_n=3)
required_components = {
    "compatibility_score",
    "skill_match_score",
    "cluster_relevance_score",
    "ensemble_prediction_score",
    "matched_required_skills",
    "matched_preferred_skills",
    "missing_skills",
}

assert full_result["recommendation_metadata"]["active_signals"]["skill_matching"]
assert required_components.issubset(
    full_result["career_recommendations"][0]
)
assert sparse_result["cluster_analysis"]["status"] == "fallback"
assert sparse_result["ensemble_analysis"]["status"] == "fallback"
assert sparse_result["career_recommendations"][0]["score_components"][
    "weights"
] == {
    "skill_match": 1.0,
    "cluster_relevance": 0.0,
    "ensemble_prediction": 0.0,
}

print("Full-profile signals:", full_result["recommendation_metadata"]["active_signals"])
print("Top hybrid recommendation:", full_result["career_recommendations"][0])
print("Sparse-profile fallback: OK")
