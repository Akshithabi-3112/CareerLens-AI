"""Hybrid Recommendation Weight Ablation Study.

Empirically evaluates 6 distinct hybrid weight configurations:
- Config A: Skill = 1.00, Cluster = 0.00, Ensemble = 0.00 (Pure Rule-Based Baseline)
- Config B: Skill = 0.80, Cluster = 0.20, Ensemble = 0.00 (Skill + Clustering only)
- Config C: Skill = 0.70, Cluster = 0.15, Ensemble = 0.15 (Conservative ML)
- Config D: Skill = 0.60, Cluster = 0.20, Ensemble = 0.20 (Current Production Setting)
- Config E: Skill = 0.50, Cluster = 0.25, Ensemble = 0.25 (Balanced Weighting)
- Config F: Skill = 0.40, Cluster = 0.30, Ensemble = 0.30 (Aggressive ML)

Metrics computed across all configurations:
- Precision@1, Precision@3, Precision@5
- Recall@3
- NDCG@3, NDCG@5
- MRR (Mean Reciprocal Rank)
- Hit Rate@1, Hit Rate@3
- Zero-skill artificial boost check
"""

import os
import math
import json
import csv
from typing import Dict, List
from app.services.career_matcher import recommend_careers
from app.services.clustering_service import analyze_profile_cluster
from app.services.ensemble_service import get_ensemble_predictions
from evaluation.benchmark_datasets import CAREER_RECOMMENDATION_BENCHMARK

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

ABLATION_CONFIGURATIONS = [
    {
        "id": "config_a_baseline",
        "name": "Config A (Skill Only Baseline)",
        "weights": {"skill_match": 1.00, "cluster_relevance": 0.00, "ensemble_prediction": 0.00},
        "description": "Rule-based skill compatibility only, no ML signals",
    },
    {
        "id": "config_b_skill_cluster",
        "name": "Config B (Skill + Cluster)",
        "weights": {"skill_match": 0.80, "cluster_relevance": 0.20, "ensemble_prediction": 0.00},
        "description": "Skill matching augmented by K-Means cluster similarity",
    },
    {
        "id": "config_c_conservative_ml",
        "name": "Config C (Conservative ML)",
        "weights": {"skill_match": 0.70, "cluster_relevance": 0.15, "ensemble_prediction": 0.15},
        "description": "Dominant skill match with conservative ML contributions",
    },
    {
        "id": "config_d_production",
        "name": "Config D (Production Setting)",
        "weights": {"skill_match": 0.60, "cluster_relevance": 0.20, "ensemble_prediction": 0.20},
        "description": "Optimal calibrated production hybrid weighting",
    },
    {
        "id": "config_e_balanced",
        "name": "Config E (Balanced Weights)",
        "weights": {"skill_match": 0.50, "cluster_relevance": 0.25, "ensemble_prediction": 0.25},
        "description": "Equal balance between skill matching and total ML signals",
    },
    {
        "id": "config_f_aggressive_ml",
        "name": "Config F (Aggressive ML)",
        "weights": {"skill_match": 0.40, "cluster_relevance": 0.30, "ensemble_prediction": 0.30},
        "description": "ML-heavy configuration prioritizing cluster & ensemble over exact skills",
    },
]


def _compute_dcg_at_k(relevance_scores: List[float], k: int) -> float:
    dcg = 0.0
    for i, rel in enumerate(relevance_scores[:k]):
        dcg += (2**rel - 1) / math.log2(i + 2)
    return dcg


def _compute_ndcg_at_k(predicted_careers: List[str], ground_truth_dict: Dict[str, int], k: int) -> float:
    actual_rels = [ground_truth_dict.get(c, 0) for c in predicted_careers[:k]]
    dcg = _compute_dcg_at_k(actual_rels, k)
    ideal_rels = sorted(ground_truth_dict.values(), reverse=True)[:k]
    idcg = _compute_dcg_at_k(ideal_rels, k)
    return (dcg / idcg) if idcg > 0 else 0.0


def evaluate_weight_ablation() -> Dict:
    results_by_config = {}

    for config in ABLATION_CONFIGURATIONS:
        cfg_id = config["id"]
        cfg_name = config["name"]
        w = config["weights"]

        # Temporarily set environment variables for the ranking service
        os.environ["CAREER_SKILL_MATCH_WEIGHT"] = str(w["skill_match"])
        os.environ["CAREER_CLUSTER_RELEVANCE_WEIGHT"] = str(w["cluster_relevance"])
        os.environ["CAREER_ENSEMBLE_PREDICTION_WEIGHT"] = str(w["ensemble_prediction"])

        metrics_accum = {
            "p@1": [], "p@3": [], "p@5": [],
            "r@3": [],
            "ndcg@3": [], "ndcg@5": [],
            "mrr": [],
            "hit@1": [], "hit@3": [],
        }
        zero_skill_boost_detected = False

        for test_case in CAREER_RECOMMENDATION_BENCHMARK:
            skills = test_case["skills"]
            gt_dict = test_case["ground_truth_careers"]
            total_relevant = len([c for c, rel in gt_dict.items() if rel >= 2])

            skills_input = {
                "extracted_skills": skills,
                "normalized_skills": skills,
                "skill_categories": {},
                "evidence": {},
            }

            cluster_res = analyze_profile_cluster(skills)
            ensemble_res = get_ensemble_predictions(skills)

            recs = recommend_careers(
                skills_input,
                top_n=10,
                profile_cluster=cluster_res.get("cluster_id"),
                profile_cluster_similarity=cluster_res.get("cluster_analysis", {}).get("profile_cluster_similarity", 0.0),
                profile_cluster_name=cluster_res.get("cluster_analysis", {}).get("cluster_name"),
                ensemble_predictions=ensemble_res,
            )

            preds = [r["career"] for r in recs]

            # Check zero-skill guardrail: if matched_required_skills == 0, gate must clamp ML
            for r in recs:
                if not r.get("matched_required_skills") and not r.get("matched_preferred_skills"):
                    if r.get("score_components", {}).get("skill_gate_factor", 1.0) != 0.0:
                        zero_skill_boost_detected = True

            # Calculate metrics
            for k in [1, 3, 5]:
                top_k = preds[:k]
                rel_in_k = [c for c in top_k if gt_dict.get(c, 0) >= 2]
                p_k = len(rel_in_k) / k
                hit_k = 1.0 if len(rel_in_k) > 0 else 0.0

                metrics_accum[f"p@{k}"].append(p_k)
                if k in (1, 3):
                    metrics_accum[f"hit@{k}"].append(hit_k)

            # R@3
            rel_in_3 = [c for c in preds[:3] if gt_dict.get(c, 0) >= 2]
            metrics_accum["r@3"].append(len(rel_in_3) / total_relevant if total_relevant > 0 else 0.0)

            # NDCG@3, NDCG@5
            metrics_accum["ndcg@3"].append(_compute_ndcg_at_k(preds, gt_dict, 3))
            metrics_accum["ndcg@5"].append(_compute_ndcg_at_k(preds, gt_dict, 5))

            # MRR
            rr = 0.0
            for idx, c in enumerate(preds):
                if gt_dict.get(c, 0) >= 2:
                    rr = 1.0 / (idx + 1)
                    break
            metrics_accum["mrr"].append(rr)

        # Compute average metrics
        agg_metrics = {
            k: round(sum(v) / len(v) * 100.0, 2)
            for k, v in metrics_accum.items()
        }

        results_by_config[cfg_id] = {
            "name": cfg_name,
            "weights": w,
            "description": config["description"],
            "metrics": agg_metrics,
            "zero_skill_artificial_boost_detected": zero_skill_boost_detected,
            "skill_gate_active": True,
        }

    # Reset environment variables to default production weights
    os.environ["CAREER_SKILL_MATCH_WEIGHT"] = "0.60"
    os.environ["CAREER_CLUSTER_RELEVANCE_WEIGHT"] = "0.20"
    os.environ["CAREER_ENSEMBLE_PREDICTION_WEIGHT"] = "0.20"

    # Export JSON
    json_path = os.path.join(RESULTS_DIR, "ablation_study.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results_by_config, f, indent=2)

    # Export CSV
    csv_path = os.path.join(RESULTS_DIR, "ablation_study.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Configuration", "Skill Weight", "Cluster Weight", "Ensemble Weight",
            "P@1 (%)", "P@3 (%)", "P@5 (%)", "R@3 (%)", "NDCG@3 (%)", "NDCG@5 (%)",
            "MRR (%)", "Hit@1 (%)", "Hit@3 (%)"
        ])
        for cfg_id, data in results_by_config.items():
            w = data["weights"]
            m = data["metrics"]
            writer.writerow([
                data["name"], w["skill_match"], w["cluster_relevance"], w["ensemble_prediction"],
                m["p@1"], m["p@3"], m["p@5"], m["r@3"], m["ndcg@3"], m["ndcg@5"],
                m["mrr"], m["hit@1"], m["hit@3"]
            ])

    return results_by_config


if __name__ == "__main__":
    res = evaluate_weight_ablation()
    print("=== HYBRID WEIGHT ABLATION STUDY ===")
    print(json.dumps(res, indent=2))
