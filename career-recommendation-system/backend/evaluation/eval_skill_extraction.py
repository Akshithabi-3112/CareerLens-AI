"""Evaluation script for Resume Skill Extraction.

Computes:
- Per-sample Precision, Recall, F1
- Micro & Macro Precision, Recall, F1 across all evaluation profiles.
"""

from typing import Dict, List
from app.services.skill_extractor import extract_skills
from evaluation.benchmark_datasets import RESUME_EXTRACTION_BENCHMARK


def evaluate_skill_extraction() -> Dict:
    results = []
    total_tp = 0
    total_fp = 0
    total_fn = 0

    for sample in RESUME_EXTRACTION_BENCHMARK:
        raw_text = sample["text"]
        gt_skills = {s.lower() for s in sample["ground_truth_skills"]}

        extracted_res = extract_skills(raw_text)
        pred_skills = {s.lower() for s in extracted_res.get("extracted_skills", [])}

        tp = len(pred_skills & gt_skills)
        fp = len(pred_skills - gt_skills)
        fn = len(gt_skills - pred_skills)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        total_tp += tp
        total_fp += fp
        total_fn += fn

        results.append({
            "id": sample["id"],
            "ground_truth_count": len(gt_skills),
            "extracted_count": len(pred_skills),
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
        })

    # Macro metrics
    macro_p = sum(r["precision"] for r in results) / len(results) if results else 0.0
    macro_r = sum(r["recall"] for r in results) / len(results) if results else 0.0
    macro_f1 = (2 * macro_p * macro_r) / (macro_p + macro_r) if (macro_p + macro_r) > 0 else 0.0

    # Micro metrics
    micro_p = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    micro_r = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    micro_f1 = (2 * micro_p * micro_r) / (micro_p + micro_r) if (micro_p + micro_r) > 0 else 0.0

    return {
        "sample_count": len(results),
        "total_ground_truth_skills": total_tp + total_fn,
        "total_extracted_skills": total_tp + total_fp,
        "micro_metrics": {
            "precision": round(micro_p, 4),
            "recall": round(micro_r, 4),
            "f1_score": round(micro_f1, 4),
        },
        "macro_metrics": {
            "precision": round(macro_p, 4),
            "recall": round(macro_r, 4),
            "f1_score": round(macro_f1, 4),
        },
        "per_sample_results": results,
    }


if __name__ == "__main__":
    import json
    res = evaluate_skill_extraction()
    print("=== SKILL EXTRACTION EVALUATION RESULTS ===")
    print(f"Sample Count: {res['sample_count']}")
    print(f"Macro Precision: {res['macro_metrics']['precision'] * 100:.2f}%")
    print(f"Macro Recall:    {res['macro_metrics']['recall'] * 100:.2f}%")
    print(f"Macro F1-Score:  {res['macro_metrics']['f1_score'] * 100:.2f}%")
