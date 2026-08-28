"""Evaluation script for Career Recommendation Ranking.

Compares:
1. Baseline: Compatibility-Only Matcher
2. Proposed System: Explainable Hybrid Recommendation Engine (Skill + Cluster + Ensemble + Gate)

Metrics:
- Precision@K (K = 1, 3, 5)
- Recall@K (K = 1, 3, 5)
- NDCG@K (Normalized Discounted Cumulative Gain at K = 1, 3, 5)
- Mean Reciprocal Rank (MRR)
- Hit Rate@K (Hit@1, Hit@3, Hit@5)
"""

import math
from typing import Dict, List
from app.services.career_matcher import recommend_careers
from app.services.recommendation_service import build_hybrid_recommendations
from evaluation.benchmark_datasets import CAREER_RECOMMENDATION_BENCHMARK


def _compute_dcg_at_k(relevance_scores: List[float], k: int) -> float:
    dcg = 0.0
    for i, rel in enumerate(relevance_scores[:k]):
        dcg += (2**rel - 1) / math.log2(i + 2)
    return dcg


def _compute_ndcg_at_k(predicted_careers: List[str], ground_truth_dict: Dict[str, int], k: int) -> float:
    actual_rels = [ground_truth_dict.get(c, 0) for c in predicted_careers[:k]]
    dcg = _compute_dcg_at_k(actual_rels, k)

    # Ideal DCG
    ideal_rels = sorted(ground_truth_dict.values(), reverse=True)[:k]
    idcg = _compute_dcg_at_k(ideal_rels, k)

    return (dcg / idcg) if idcg > 0 else 0.0


def evaluate_ranking() -> Dict:
    baseline_metrics = {"p@1": [], "p@3": [], "p@5": [], "r@1": [], "r@3": [], "r@5": [], "ndcg@1": [], "ndcg@3": [], "ndcg@5": [], "mrr": [], "hit@1": [], "hit@3": [], "hit@5": []}
    hybrid_metrics = {"p@1": [], "p@3": [], "p@5": [], "r@1": [], "r@3": [], "r@5": [], "ndcg@1": [], "ndcg@3": [], "ndcg@5": [], "mrr": [], "hit@1": [], "hit@3": [], "hit@5": []}

    for test_case in CAREER_RECOMMENDATION_BENCHMARK:
        skills = test_case["skills"]
        gt_dict = test_case["ground_truth_careers"]
        total_relevant = len([c for c, rel in gt_dict.items() if rel >= 2])  # Primary/high relevant

        skills_input = {
            "extracted_skills": skills,
            "normalized_skills": skills,
            "skill_categories": {},
            "evidence": {},
        }

        # 1. Baseline Predictions (Pure Skill Compatibility Only, ML disabled)
        base_recs = recommend_careers(
            skills_input,
            top_n=10,
            profile_cluster=None,
            profile_cluster_similarity=0.0,
            ensemble_predictions={"career_probabilities": {}, "ensemble_analysis": {"status": "disabled"}},
        )
        base_preds = [r["career"] for r in base_recs]

        # 2. Hybrid Predictions (Skill Compatibility + Cluster + Voting Ensemble + Gate)
        hybrid_res = build_hybrid_recommendations(skills_input)
        hybrid_preds = [r["career"] for r in hybrid_res["career_recommendations"][:10]]

        # Compute for Baseline
        _evaluate_single_system(base_preds, gt_dict, total_relevant, baseline_metrics)

        # Compute for Hybrid
        _evaluate_single_system(hybrid_preds, gt_dict, total_relevant, hybrid_metrics)


    # Aggregate Means
    def _agg(m_dict):
        return {k: round(sum(v) / len(v), 4) if v else 0.0 for k, v in m_dict.items()}

    base_summary = _agg(baseline_metrics)
    hybrid_summary = _agg(hybrid_metrics)

    # Compute percentage improvements
    improvements = {}
    for k in base_summary:
        b = base_summary[k]
        h = hybrid_summary[k]
        imp = ((h - b) / b * 100) if b > 0 else 0.0
        improvements[k] = round(imp, 2)

    return {
        "num_test_profiles": len(CAREER_RECOMMENDATION_BENCHMARK),
        "baseline_compatibility_only": base_summary,
        "proposed_hybrid_system": hybrid_summary,
        "percentage_improvement": improvements,
    }


def _evaluate_single_system(preds: List[str], gt_dict: Dict[str, int], total_relevant: int, accum: Dict):
    for k in [1, 3, 5]:
        top_k = preds[:k]
        rel_in_k = [c for c in top_k if gt_dict.get(c, 0) >= 2]
        p_k = len(rel_in_k) / k
        r_k = len(rel_in_k) / total_relevant if total_relevant > 0 else 0.0
        ndcg_k = _compute_ndcg_at_k(preds, gt_dict, k)
        hit_k = 1.0 if len(rel_in_k) > 0 else 0.0

        accum[f"p@{k}"].append(p_k)
        accum[f"r@{k}"].append(r_k)
        accum[f"ndcg@{k}"].append(ndcg_k)
        accum[f"hit@{k}"].append(hit_k)

    # MRR (first relevant item rank)
    rr = 0.0
    for idx, c in enumerate(preds):
        if gt_dict.get(c, 0) >= 2:
            rr = 1.0 / (idx + 1)
            break
    accum["mrr"].append(rr)


if __name__ == "__main__":
    import json
    res = evaluate_ranking()
    print("=== RECOMMENDATION RANKING EVALUATION ===")
    print(json.dumps(res, indent=2))
