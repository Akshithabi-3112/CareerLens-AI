"""Hybrid recommendation orchestration with safe, explainable fallbacks."""

import logging

from app.services.career_matcher import MAX_RECOMMENDATIONS, recommend_careers
from app.services.clustering_service import analyze_profile_cluster
from app.services.ensemble_service import get_ensemble_predictions


logger = logging.getLogger(__name__)
MIN_SKILLS_FOR_ML_SIGNALS = 2


def build_user_feature_profile(skills_result):
    """Build a transparent profile from already-normalized extracted skills."""
    extracted_skills = skills_result.get("extracted_skills", [])
    skill_categories = skills_result.get("skill_categories", {})
    evidence = skills_result.get("evidence", {})

    return {
        "skills": extracted_skills,
        "skill_count": len(extracted_skills),
        "category_count": len([
            category for category, skills in skill_categories.items() if skills
        ]),
        "evidence_count": len(evidence),
        "is_sparse": len(extracted_skills) < MIN_SKILLS_FOR_ML_SIGNALS,
    }


def _cluster_fallback(explanation):
    return {
        "cluster_id": None,
        "cluster_analysis": {
            "status": "fallback",
            "cluster_name": "No career group identified",
            "similar_career_group": [],
            "profile_cluster_similarity": 0.0,
            "dominant_skills": [],
            "matched_cluster_skills": [],
            "cluster_count": 0,
            "explanation": explanation,
        },
    }


def _ensemble_fallback(explanation):
    return {
        "career_probabilities": {},
        "ensemble_analysis": {
            "status": "fallback",
            "training_data": "No production supervised training data is available.",
            "model_metrics": {},
            "top_features": [],
            "per_class_sample": {},
            "sample_count": 0,
            "top_predictions": [],
            "contributing_skills": [],
            "explanation": explanation,
        },
    }


def build_hybrid_recommendations(
    skills_result,
    top_n=MAX_RECOMMENDATIONS,
):
    """Run cluster, ensemble, and skill matching as one resilient pipeline."""
    feature_profile = build_user_feature_profile(skills_result)
    extracted_skills = feature_profile["skills"]

    if feature_profile["is_sparse"]:
        logger.info(
            "Using rule-based fallback for sparse skill profile (%s skills).",
            feature_profile["skill_count"],
        )
        cluster_result = _cluster_fallback(
            "At least two extracted skills are required for a reliable "
            "cluster assignment."
        )
        ensemble_result = _ensemble_fallback(
            "At least two extracted skills are required for the experimental "
            "ensemble signal."
        )
    else:
        try:
            cluster_result = analyze_profile_cluster(extracted_skills)
        except Exception:
            logger.exception("Career clustering was unavailable; using fallback.")
            cluster_result = _cluster_fallback(
                "Career clustering is temporarily unavailable."
            )

        try:
            ensemble_result = get_ensemble_predictions(extracted_skills)
        except Exception:
            logger.exception("Ensemble prediction was unavailable; using fallback.")
            ensemble_result = _ensemble_fallback(
                "The experimental ensemble is temporarily unavailable."
            )

    recommendations = recommend_careers(
        skills_result,
        top_n=top_n,
        profile_cluster=cluster_result.get("cluster_id"),
        profile_cluster_similarity=cluster_result["cluster_analysis"].get(
            "profile_cluster_similarity",
            0.0,
        ),
        profile_cluster_name=cluster_result["cluster_analysis"].get(
            "cluster_name",
        ),
        ensemble_predictions=ensemble_result,
    )

    return {
        "career_recommendations": recommendations,
        "cluster_analysis": cluster_result["cluster_analysis"],
        "ensemble_analysis": ensemble_result["ensemble_analysis"],
        "recommendation_metadata": {
            "pipeline": "hybrid",
            "user_feature_profile": feature_profile,
            "active_signals": {
                "skill_matching": True,
                "clustering": cluster_result.get("cluster_id") is not None,
                "ensemble": (
                    ensemble_result["ensemble_analysis"].get("status")
                    == "experimental"
                ),
            },
        },
    }
