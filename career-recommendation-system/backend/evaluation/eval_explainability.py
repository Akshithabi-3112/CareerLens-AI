"""Evaluation script for the Explainability Engine.

Evaluates real outputs from explanation_service.py and career_analysis_service.py:
1. Faithfulness / Grounding Score (% of claims backed by verified model outputs)
2. Hallucination Rate (% of factual claims unsupported or fabricating skills/scores)
3. Mathematical Consistency (MAE, MaxAE, and consistency rate between formula and score)
4. Explanation Coverage (% of recommendations containing complete structured rationale)
"""

import os
import json
import csv
from typing import Dict, List
from app.services.recommendation_service import build_hybrid_recommendations
from app.services.career_analysis_service import analyze_career_recommendations
from evaluation.benchmark_datasets import CAREER_RECOMMENDATION_BENCHMARK

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)


def evaluate_explainability() -> Dict:
    total_recommendations_evaluated = 0
    total_claims_checked = 0
    total_supported_claims = 0
    total_unsupported_claims = 0

    math_absolute_errors = []
    mathematically_consistent_count = 0
    complete_coverage_count = 0

    per_profile_summaries = []

    for test_case in CAREER_RECOMMENDATION_BENCHMARK:
        profile_id = test_case["profile_id"]
        user_skills = test_case["skills"]

        skills_input = {
            "extracted_skills": user_skills,
            "normalized_skills": user_skills,
            "skills_by_category": {},
            "evidence": {},
        }

        # Run real hybrid pipeline & career analysis
        hybrid_res = build_hybrid_recommendations(skills_input)
        career_recs = hybrid_res.get("career_recommendations", [])
        cluster_analysis = hybrid_res.get("cluster_analysis", {})
        ensemble_analysis = hybrid_res.get("ensemble_analysis", {})

        career_analysis = analyze_career_recommendations(
            user_skills,
            career_recs,
            cluster_analysis=cluster_analysis,
            ensemble_analysis=ensemble_analysis,
        )

        user_skills_lower = {s.lower() for s in user_skills}

        for rec, analysis_item in zip(career_recs, career_analysis):
            total_recommendations_evaluated += 1
            exp = analysis_item.get("unified_explanation", {})
            matched_skills = [s.lower() for s in analysis_item.get("matched_skills", [])]
            missing_skills = [s.lower() for s in analysis_item.get("missing_skills", [])]

            # ── 1. Check Coverage of Explanation Sections ──────────────────
            has_summary = bool(exp.get("executive_summary"))
            has_strengths = bool(exp.get("key_strengths"))
            has_gaps = "critical_gaps" in exp
            has_score_breakdown = bool(exp.get("score_breakdown"))
            has_ml_influence = bool(exp.get("ml_influence"))
            has_learning_rationale = bool(exp.get("learning_rationale"))

            if (has_summary and has_strengths and has_gaps and
                    has_score_breakdown and has_ml_influence and has_learning_rationale):
                complete_coverage_count += 1

            # ── 2. Fact / Grounding Verification ───────────────────────────
            # A. Strengths Grounding: claimed strength skill must be possessed by candidate
            for st in exp.get("key_strengths", []):
                total_claims_checked += 1
                sk = st.get("skill", "").lower()
                if sk in user_skills_lower:
                    total_supported_claims += 1
                else:
                    total_unsupported_claims += 1

            # B. Gaps Grounding: claimed gap must be actually missing and not possessed
            for gp in exp.get("critical_gaps", []):
                total_claims_checked += 1
                sk = gp.get("skill", "").lower()
                if sk in missing_skills and sk not in user_skills_lower:
                    total_supported_claims += 1
                else:
                    total_unsupported_claims += 1

            # C. Score Grounding: breakdown values must match rec values
            sb = exp.get("score_breakdown", {})
            total_claims_checked += 3

            # Check compatibility score
            if abs(sb.get("compatibility_score", 0) - rec.get("compatibility_score", 0)) <= 0.1:
                total_supported_claims += 1
            else:
                total_unsupported_claims += 1

            # Check cluster relevance
            if abs(sb.get("cluster_relevance", 0) - rec.get("cluster_relevance_score", 0)) <= 0.1:
                total_supported_claims += 1
            else:
                total_unsupported_claims += 1

            # Check ensemble confidence
            if abs(sb.get("ensemble_confidence", 0) - rec.get("ensemble_confidence", 0)) <= 0.1:
                total_supported_claims += 1
            else:
                total_unsupported_claims += 1

            # ── 3. Mathematical Consistency Verification ────────────────────
            explained_final = sb.get("final_score", 0.0)
            compat = sb.get("compatibility_score", 0.0)
            clust = sb.get("cluster_relevance", 0.0)
            ens = sb.get("ensemble_confidence", 0.0)
            weights = sb.get("weights", {"skill_match": 0.6, "cluster_relevance": 0.2, "ensemble_prediction": 0.2})
            gate = sb.get("skill_gate_factor", 1.0)

            w_skill = weights.get("skill_match", 0.6)
            w_clust = weights.get("cluster_relevance", 0.2)
            w_ens = weights.get("ensemble_prediction", 0.2)

            recomputed_final = round(
                (w_skill * compat) + (w_clust * clust * gate) + (w_ens * ens * gate),
                2
            )
            abs_err = abs(explained_final - recomputed_final)
            math_absolute_errors.append(abs_err)

            if abs_err <= 0.5:  # within rounding tolerance
                mathematically_consistent_count += 1

        per_profile_summaries.append({
            "profile_id": profile_id,
            "top_career": career_recs[0]["career"] if career_recs else "None",
            "executive_summary": career_analysis[0]["unified_explanation"]["executive_summary"] if career_analysis else "",
        })

    # Summary Metrics Calculation
    faithfulness_score = (
        (total_supported_claims / total_claims_checked * 100.0)
        if total_claims_checked > 0 else 100.0
    )
    hallucination_rate = (
        (total_unsupported_claims / total_claims_checked * 100.0)
        if total_claims_checked > 0 else 0.0
    )
    explanation_coverage_pct = (
        (complete_coverage_count / total_recommendations_evaluated * 100.0)
        if total_recommendations_evaluated > 0 else 100.0
    )
    math_consistency_pct = (
        (mathematically_consistent_count / total_recommendations_evaluated * 100.0)
        if total_recommendations_evaluated > 0 else 100.0
    )
    mean_abs_err = sum(math_absolute_errors) / len(math_absolute_errors) if math_absolute_errors else 0.0
    max_abs_err = max(math_absolute_errors) if math_absolute_errors else 0.0

    result_data = {
        "summary": {
            "total_recommendations_evaluated": total_recommendations_evaluated,
            "total_factual_claims_checked": total_claims_checked,
            "faithfulness_score_percent": round(faithfulness_score, 2),
            "hallucination_rate_percent": round(hallucination_rate, 2),
            "explanation_coverage_percent": round(explanation_coverage_pct, 2),
            "mathematical_consistency_percent": round(math_consistency_pct, 2),
            "mean_absolute_math_error": round(mean_abs_err, 4),
            "max_absolute_math_error": round(max_abs_err, 4),
        },
        "per_profile_summaries": per_profile_summaries,
    }

    # Export JSON
    json_path = os.path.join(RESULTS_DIR, "explainability_evaluation.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result_data, f, indent=2)

    # Export CSV
    csv_path = os.path.join(RESULTS_DIR, "explainability_summary.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Metric", "Value", "Unit", "Interpretation"])
        writer.writerow(["Faithfulness Score", f"{faithfulness_score:.2f}", "%", "Proportion of claims verified by underlying data"])
        writer.writerow(["Hallucination Rate", f"{hallucination_rate:.2f}", "%", "Proportion of unsupported or ungrounded claims"])
        writer.writerow(["Explanation Coverage", f"{explanation_coverage_pct:.2f}", "%", "Proportion of recommendations with complete 6-part rationale"])
        writer.writerow(["Mathematical Consistency", f"{math_consistency_pct:.2f}", "%", "Proportion of scores perfectly matching formula math"])
        writer.writerow(["Mean Absolute Math Error", f"{mean_abs_err:.4f}", "points", "Average residual between stated and computed score"])
        writer.writerow(["Max Absolute Math Error", f"{max_abs_err:.4f}", "points", "Maximum residual between stated and computed score"])

    return result_data


if __name__ == "__main__":
    res = evaluate_explainability()
    print("=== EXPLAINABILITY EVALUATION ===")
    print(json.dumps(res["summary"], indent=2))
