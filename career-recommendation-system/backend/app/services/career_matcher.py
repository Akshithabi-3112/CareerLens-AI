import os
import csv
import logging

from app.services.clustering_service import (
    analyze_profile_cluster,
    get_career_cluster_ids,
)
from app.services.ensemble_service import get_ensemble_predictions


MAX_RECOMMENDATIONS = 10
logger = logging.getLogger(__name__)

DEFAULT_RECOMMENDATION_WEIGHTS = {
    "skill_match": 0.60,
    "cluster_relevance": 0.20,
    "ensemble_prediction": 0.20,
}


BASE_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        ".."
    )
)

CAREERS_FILE = os.path.join(
    BASE_DIR,
    "data",
    "careers.csv"
)


def load_careers():
    careers = []

    if not os.path.exists(CAREERS_FILE):
        raise FileNotFoundError(
            f"Career dataset not found: {CAREERS_FILE}"
        )

    with open(
        CAREERS_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            required_skills = [
                skill.strip()
                for skill in row["required_skills"].split("|")
                if skill.strip()
            ]

            preferred_skills = [
                skill.strip()
                for skill in row["preferred_skills"].split("|")
                if skill.strip()
            ]

            careers.append({
                "career": row["career"].strip(),
                "required_skills": required_skills,
                "preferred_skills": preferred_skills,
                "description": row["description"].strip()
            })

    return careers


def normalize_skills(skills):
    return {
        skill.strip().lower()
        for skill in skills
        if skill and skill.strip()
    }


def get_recommendation_weights():
    """Read final-ranking weights from the environment with safe defaults."""
    environment_names = {
        "skill_match": "CAREER_SKILL_MATCH_WEIGHT",
        "cluster_relevance": "CAREER_CLUSTER_RELEVANCE_WEIGHT",
        "ensemble_prediction": "CAREER_ENSEMBLE_PREDICTION_WEIGHT",
    }
    weights = {}

    for name, default_value in DEFAULT_RECOMMENDATION_WEIGHTS.items():
        try:
            value = float(os.getenv(environment_names[name], default_value))
        except ValueError:
            value = default_value

        weights[name] = max(value, 0.0)

    total_weight = sum(weights.values())

    if total_weight == 0:
        return DEFAULT_RECOMMENDATION_WEIGHTS.copy()

    return {
        name: value / total_weight
        for name, value in weights.items()
    }


def calculate_required_match(
    user_skills,
    required_skills
):

    if not required_skills:
        return 0.0, []

    matched_skills = []

    for skill in required_skills:

        if skill.lower() in user_skills:
            matched_skills.append(skill)

    score = (
        len(matched_skills)
        / len(required_skills)
    )

    return score, matched_skills


def calculate_preferred_match(
    user_skills,
    preferred_skills
):

    if not preferred_skills:
        return 0.0, []

    matched_skills = []

    for skill in preferred_skills:

        if skill.lower() in user_skills:
            matched_skills.append(skill)

    score = (
        len(matched_skills)
        / len(preferred_skills)
    )

    return score, matched_skills


def calculate_category_diversity(
    skill_categories
):

    if not skill_categories:
        return 0.0

    category_count = len(
        [
            category
            for category, skills
            in skill_categories.items()
            if skills
        ]
    )

    maximum_categories = 8

    return min(
        category_count / maximum_categories,
        1.0
    )


def calculate_evidence_quality(
    extracted_skills,
    evidence
):

    if not extracted_skills:
        return 0.0

    skills_with_evidence = 0

    for skill in extracted_skills:

        if skill in evidence:
            skills_with_evidence += 1

    return (
        skills_with_evidence
        / len(extracted_skills)
    )


def calculate_missing_skills(
    user_skills,
    required_skills
):

    missing_skills = []

    for skill in required_skills:

        if skill.lower() not in user_skills:
            missing_skills.append(skill)

    return missing_skills


def calculate_career_score(
    user_skills,
    skill_categories,
    extracted_skills,
    evidence,
    career
):

    required_score, matched_required = (
        calculate_required_match(
            user_skills,
            career["required_skills"]
        )
    )

    preferred_score, matched_preferred = (
        calculate_preferred_match(
            user_skills,
            career["preferred_skills"]
        )
    )

    category_score = (
        calculate_category_diversity(
            skill_categories
        )
    )

    evidence_score = (
        calculate_evidence_quality(
            extracted_skills,
            evidence
        )
    )

    career_compatibility_score = (
        required_score * 0.60
        + preferred_score * 0.20
        + category_score * 0.10
        + evidence_score * 0.10
    )

    missing_skills = calculate_missing_skills(
        user_skills,
        career["required_skills"]
    )

    return {
        "career": career["career"],
        "description": career["description"],
        "compatibility_score": round(
            career_compatibility_score * 100,
            2
        ),
        "required_skill_match": round(
            required_score * 100,
            2
        ),
        "preferred_skill_match": round(
            preferred_score * 100,
            2
        ),
        "matched_required_skills": matched_required,
        "matched_preferred_skills": matched_preferred,
        "missing_skills": missing_skills
    }


def _generate_recommendation_explanation(
    career_name,
    matched_required,
    total_required,
    matched_preferred,
    compatibility_score,
    cluster_alignment,
    cluster_similarity,
    cluster_name,
    ensemble_confidence,
    final_score,
):
    """Generate a transparent, human-readable explanation for a career recommendation."""
    parts = []
    req_count = len(matched_required)
    if total_required > 0:
        req_pct = round((req_count / total_required) * 100)
        if req_count > 0:
            skills_preview = ", ".join(matched_required[:3])
            if req_count > 3:
                skills_preview += f" (+{req_count - 3} more)"
            parts.append(
                f"Matches {req_count} of {total_required} required skills ({req_pct}%): {skills_preview}."
            )
        else:
            parts.append(f"Matches 0 of {total_required} required skills.")

    if matched_preferred:
        pref_preview = ", ".join(matched_preferred[:2])
        parts.append(f"Preferred skills matched: {pref_preview}.")

    if cluster_alignment and cluster_similarity > 0:
        c_label = f" '{cluster_name}'" if cluster_name else ""
        parts.append(
            f"Your profile belongs to the matching{c_label} cluster with {round(cluster_similarity, 1)}% similarity."
        )

    if ensemble_confidence >= 15.0:
        parts.append(
            f"VotingClassifier ensemble model indicates strong role affinity ({round(ensemble_confidence, 1)}%)."
        )
    elif ensemble_confidence > 0.0:
        parts.append(
            f"Ensemble model assigns {round(ensemble_confidence, 1)}% supporting probability."
        )

    if not parts:
        return f"Evaluated role with hybrid recommendation score of {final_score}%."

    return " ".join(parts)


def recommend_careers(
    skills_result,
    top_n=MAX_RECOMMENDATIONS,
    profile_cluster=None,
    profile_cluster_similarity=None,
    profile_cluster_name=None,
    ensemble_predictions=None,
):
    """Compute explainable hybrid career recommendations combining skills, clustering, and ensemble."""
    extracted_skills = (
        skills_result.get(
            "extracted_skills",
            []
        )
    )

    skill_categories = (
        skills_result.get(
            "skill_categories",
            {}
        )
    )

    evidence = (
        skills_result.get(
            "evidence",
            {}
        )
    )

    user_skills = normalize_skills(
        extracted_skills
    )

    careers = load_careers()

    if profile_cluster_similarity is None:
        try:
            cluster_result = analyze_profile_cluster(extracted_skills)
            profile_cluster = cluster_result.get("cluster_id")
            profile_cluster_similarity = cluster_result[
                "cluster_analysis"
            ]["profile_cluster_similarity"]
            profile_cluster_name = cluster_result[
                "cluster_analysis"
            ].get("cluster_name")
        except Exception:
            logger.exception("Career clustering was unavailable during ranking.")
            profile_cluster = None
            profile_cluster_similarity = 0.0
            profile_cluster_name = None

    if ensemble_predictions is None:
        ensemble_predictions = get_ensemble_predictions(extracted_skills)

    if profile_cluster is None:
        career_cluster_ids = {}
    else:
        try:
            career_cluster_ids = get_career_cluster_ids()
        except Exception:
            logger.exception(
                "Career cluster mappings were unavailable during ranking."
            )
            career_cluster_ids = {}
    ensemble_probabilities = ensemble_predictions.get(
        "career_probabilities",
        {},
    )
    ranking_weights = get_recommendation_weights()

    active_signals = {
        "skill_match": True,
        "cluster_relevance": (
            profile_cluster is not None and bool(career_cluster_ids)
        ),
        "ensemble_prediction": (
            ensemble_predictions.get("ensemble_analysis", {}).get("status")
            == "experimental"
        ),
    }
    active_weight_total = sum(
        ranking_weights[name]
        for name, is_active in active_signals.items()
        if is_active
    )

    if active_weight_total == 0:
        active_signals = {
            "skill_match": True,
            "cluster_relevance": False,
            "ensemble_prediction": False,
        }
        active_weight_total = 1.0
        ranking_weights["skill_match"] = 1.0

    ranking_weights = {
        name: (
            round(ranking_weights[name] / active_weight_total, 4)
            if active_signals[name] else 0.0
        )
        for name in ranking_weights
    }

    recommendations = []

    for career in careers:

        result = calculate_career_score(
            user_skills,
            skill_categories,
            extracted_skills,
            evidence,
            career
        )

        cluster_alignment = (
            profile_cluster is not None
            and career_cluster_ids.get(career["career"]) == profile_cluster
        )
        cluster_relevance = (
            profile_cluster_similarity if cluster_alignment else 0.0
        )
        ensemble_scores = ensemble_probabilities.get(career["career"], {})
        ensemble_prediction = ensemble_scores.get(
            "ensemble_probability",
            0.0,
        )

        # ── Safety Guardrail / Skill Gate ────────────────────────────
        # Prevent ML signals from artificially inflating careers when
        # the resume has zero or almost zero required skill matches.
        if result["matched_required_skills"]:
            skill_gate = 1.0
        elif result["matched_preferred_skills"]:
            skill_gate = 0.5
        else:
            skill_gate = 0.0

        effective_cluster = cluster_relevance * skill_gate
        effective_ensemble = ensemble_prediction * skill_gate

        final_score = round(
            (ranking_weights["skill_match"] * result["compatibility_score"])
            + (ranking_weights["cluster_relevance"] * effective_cluster)
            + (ranking_weights["ensemble_prediction"] * effective_ensemble),
            2,
        )

        all_matched = sorted(
            list(set(result["matched_required_skills"] + result["matched_preferred_skills"]))
        )

        explanation = _generate_recommendation_explanation(
            career_name=career["career"],
            matched_required=result["matched_required_skills"],
            total_required=len(career["required_skills"]),
            matched_preferred=result["matched_preferred_skills"],
            compatibility_score=result["compatibility_score"],
            cluster_alignment=cluster_alignment,
            cluster_similarity=cluster_relevance,
            cluster_name=profile_cluster_name,
            ensemble_confidence=ensemble_prediction,
            final_score=final_score,
        )

        w_skill = ranking_weights.get("skill_match", 0.60)
        w_clust = ranking_weights.get("cluster_relevance", 0.20)
        w_ens = ranking_weights.get("ensemble_prediction", 0.20)

        contrib_skill = round(w_skill * result["compatibility_score"], 2)
        contrib_clust = round(w_clust * effective_cluster, 2)
        contrib_ens = round(w_ens * effective_ensemble, 2)

        result["matched_skills"] = all_matched
        result["cluster_alignment"] = cluster_alignment
        result["ensemble_probabilities"] = ensemble_scores
        result["skill_match_score"] = result["compatibility_score"]
        result["cluster_relevance"] = round(cluster_relevance, 2)
        result["cluster_relevance_score"] = round(cluster_relevance, 2)
        result["ensemble_confidence"] = ensemble_prediction
        result["ensemble_prediction_score"] = ensemble_prediction
        result["final_score"] = final_score
        result["final_recommendation_score"] = final_score
        result["explanation"] = explanation
        result["skill_weight"] = round(w_skill * 100)
        result["cluster_weight"] = round(w_clust * 100)
        result["ensemble_weight"] = round(w_ens * 100)
        result["skill_contribution"] = contrib_skill
        result["cluster_contribution"] = contrib_clust
        result["ensemble_contribution"] = contrib_ens
        result["score_components"] = {
            "skill_match_score": result["skill_match_score"],
            "cluster_relevance_score": result["cluster_relevance_score"],
            "ensemble_prediction_score": result["ensemble_prediction_score"],
            "skill_gate_factor": skill_gate,
            "weights": ranking_weights,
            "skill_weight": round(w_skill * 100),
            "cluster_weight": round(w_clust * 100),
            "ensemble_weight": round(w_ens * 100),
            "skill_contribution": contrib_skill,
            "cluster_contribution": contrib_clust,
            "ensemble_contribution": contrib_ens,
            "weighted_contributions": {
                "skill_match": contrib_skill,
                "cluster_relevance": contrib_clust,
                "ensemble_prediction": contrib_ens,
            },
        }

        recommendations.append(result)

    recommendations.sort(
        key=lambda item: (
            item["final_recommendation_score"],
            item["compatibility_score"],
        ),
        reverse=True
    )

    return recommendations[:top_n]

