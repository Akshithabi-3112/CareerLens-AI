"""Master Experiment & Evaluation Orchestrator.

Runs all 9 evaluation suites:
1. Resume Skill Extraction Evaluation
2. ML Classification Model Comparison (RF vs GB vs VotingClassifier)
3. K-Means Career Clustering Silhouette Sweep
4. Recommendation Ranking Comparison (Compatibility-Only vs Hybrid)
5. Skill-Gap & Readiness Analysis Evaluation
6. Course and Certification Recommendation Evaluation
7. Explainability Faithfulness & Mathematical Grounding Evaluation
8. Hybrid Weight Ablation Study
9. Publication-Quality Matplotlib Visualizations Generator

Generates formatted CSV tables, plots, and JSON results in `backend/evaluation/results/`.
"""

import os
import json
import csv
import sys
import io
import traceback

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from evaluation.eval_skill_extraction import evaluate_skill_extraction
from evaluation.eval_models import evaluate_models
from evaluation.eval_clustering import evaluate_clustering
from evaluation.eval_ranking import evaluate_ranking
from evaluation.eval_skill_gap import evaluate_skill_gap
from evaluation.eval_course_recs import evaluate_course_recommendations
from evaluation.eval_explainability import evaluate_explainability
from evaluation.eval_ablation import evaluate_weight_ablation
from evaluation.generate_report_visualizations import generate_all_visualizations

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)


def run_all_experiments():
    print("=" * 80)
    print("  ACADEMIC EVALUATION & EXPERIMENT SUITE")
    print("  Project: Explainable Resume-Based Career & Skill Recommendation System")
    print("=" * 80)

    results_summary = {}
    experiment_statuses = []

    def _run_step(step_num, title, func):
        print(f"\n[{step_num}/9] {title}...")
        try:
            res = func()
            experiment_statuses.append((title, "PASS", None))
            return res
        except Exception as e:
            tb = traceback.format_exc()
            experiment_statuses.append((title, "FAIL", f"{e}\n{tb}"))
            print(f"  [FAILED] {title}: {e}")
            return None

    # 1. Skill Extraction
    res_extraction = _run_step(1, "Evaluating Resume Skill Extraction", evaluate_skill_extraction)
    if res_extraction:
        macro_ext = res_extraction["macro_metrics"]
        print(f"  • Macro Precision: {macro_ext['precision'] * 100:.2f}%")
        print(f"  • Macro Recall:    {macro_ext['recall'] * 100:.2f}%")
        print(f"  • Macro F1-Score:  {macro_ext['f1_score'] * 100:.2f}%")

        ext_csv = os.path.join(RESULTS_DIR, "skill_extraction_samples.csv")
        with open(ext_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "ground_truth_count", "extracted_count", "true_positives", "false_positives", "false_negatives", "precision", "recall", "f1_score"])
            writer.writeheader()
            writer.writerows(res_extraction["per_sample_results"])

    # 2. Model Comparison
    res_models = _run_step(2, "Evaluating Machine Learning Classifiers", evaluate_models)
    if res_models:
        model_comp = res_models["model_comparison"]
        model_csv = os.path.join(RESULTS_DIR, "model_comparison.csv")
        with open(model_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Model", "Accuracy (%)", "Macro Precision (%)", "Macro Recall (%)", "Macro F1 (%)", "Latency (ms/sample)"])
            for name, metrics in model_comp.items():
                print(f"  • {name:22s} | Acc: {metrics['accuracy']*100:.2f}% | F1: {metrics['macro_f1']*100:.2f}% | Latency: {metrics['avg_latency_ms_per_sample']}ms")
                writer.writerow([
                    name,
                    f"{metrics['accuracy']*100:.2f}",
                    f"{metrics['macro_precision']*100:.2f}",
                    f"{metrics['macro_recall']*100:.2f}",
                    f"{metrics['macro_f1']*100:.2f}",
                    f"{metrics['avg_latency_ms_per_sample']:.3f}",
                ])

    # 3. Clustering Sweep
    res_clustering = _run_step(3, "Evaluating K-Means Career Clustering", evaluate_clustering)
    if res_clustering:
        print(f"  • Optimal K by Silhouette: K = {res_clustering['optimal_k_by_silhouette']} (Silhouette: {res_clustering['max_silhouette_score']:.4f})")
        clust_csv = os.path.join(RESULTS_DIR, "clustering_k_sweep.csv")
        with open(clust_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["k", "silhouette_score"])
            writer.writeheader()
            writer.writerows(res_clustering["k_sweep"])

    # 4. Recommendation Ranking Comparison
    res_ranking = _run_step(4, "Evaluating Career Ranking (Baseline vs Hybrid)", evaluate_ranking)
    if res_ranking:
        base_r = res_ranking["baseline_compatibility_only"]
        hyb_r = res_ranking["proposed_hybrid_system"]
        imp_r = res_ranking["percentage_improvement"]
        print("  Metric        | Baseline (Compat-Only) | Proposed (Hybrid) | Relative Improvement")
        print("  " + "-" * 72)
        for m in ["p@1", "p@3", "p@5", "r@1", "r@3", "r@5", "ndcg@1", "ndcg@3", "ndcg@5", "mrr", "hit@1", "hit@3", "hit@5"]:
            print(f"  {m.upper():13s} | {base_r[m]*100:20.2f}% | {hyb_r[m]*100:15.2f}% | {imp_r[m]:+19.2f}%")

        rank_csv = os.path.join(RESULTS_DIR, "ranking_comparison.csv")
        with open(rank_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Metric", "Baseline_Compatibility_Only", "Proposed_Hybrid_System", "Relative_Improvement_Percent"])
            for m in base_r:
                writer.writerow([m.upper(), f"{base_r[m]*100:.2f}", f"{hyb_r[m]*100:.2f}", f"{imp_r[m]:+.2f}"])

    # 5. Skill Gap Analysis
    res_gap = _run_step(5, "Evaluating Skill-Gap & Readiness Analysis", evaluate_skill_gap)
    if res_gap:
        print(f"  • Controlled Test Cases: {res_gap['num_test_cases']} | All Passed: {res_gap['all_cases_passed']}")

    # 6. Course Recommendation Evaluation
    res_courses = _run_step(6, "Evaluating Course & Certification Recommendations", evaluate_course_recommendations)
    if res_courses:
        c_sum = res_courses["summary"]
        print(f"  • Overall Gap Coverage:       {c_sum['overall_gap_coverage_percent']}%")
        print(f"  • Top-1 Course Coverage:      {c_sum['top1_course_coverage_percent']}%")
        print(f"  • Top-3 Courses Coverage:     {c_sum['top3_course_coverage_percent']}%")
        print(f"  • Course Relevance Rate:      {c_sum['course_relevance_percent']}%")
        print(f"  • Certification Relevance:    {c_sum['certification_relevance_percent']}%")

    # 7. Explainability Evaluation
    res_explain = _run_step(7, "Evaluating Unified Explainability Engine", evaluate_explainability)
    if res_explain:
        e_sum = res_explain["summary"]
        print(f"  • Faithfulness / Grounding:   {e_sum['faithfulness_score_percent']}%")
        print(f"  • Hallucination Rate:         {e_sum['hallucination_rate_percent']}%")
        print(f"  • Explanation Coverage:       {e_sum['explanation_coverage_percent']}%")
        print(f"  • Mathematical Consistency:   {e_sum['mathematical_consistency_percent']}% (Mean Abs Error: {e_sum['mean_absolute_math_error']})")

    # 8. Hybrid Weight Ablation Study
    res_ablation = _run_step(8, "Evaluating Hybrid Weight Ablation Configurations", evaluate_weight_ablation)
    if res_ablation:
        print("  Config ID                     | P@1 (%) | NDCG@3 (%) | MRR (%) | Zero-Skill Boost")
        print("  " + "-" * 72)
        for cfg_id, cdata in res_ablation.items():
            m = cdata["metrics"]
            boost_txt = "Protected (0.0x)" if not cdata["zero_skill_artificial_boost_detected"] else "Detected"
            print(f"  {cdata['name']:30s} | {m['p@1']:7.2f}% | {m['ndcg@3']:10.2f}% | {m['mrr']:7.2f}% | {boost_txt}")

    # Master JSON Summary Export
    master_summary = {
        "metadata": {
            "title": "Explainable Career, Course & Skill-Gap Recommendation System Evaluation",
            "framework_version": "2.0.0",
        },
        "skill_extraction_evaluation": res_extraction,
        "model_comparison_evaluation": res_models,
        "clustering_evaluation": res_clustering,
        "ranking_evaluation": res_ranking,
        "skill_gap_evaluation": res_gap,
        "course_recommendation_evaluation": res_courses,
        "explainability_evaluation": res_explain,
        "ablation_study_evaluation": res_ablation,
    }

    summary_json_path = os.path.join(RESULTS_DIR, "evaluation_summary.json")
    with open(summary_json_path, "w", encoding="utf-8") as f:
        json.dump(master_summary, f, indent=2)

    # 9. Visualizations Generation
    _run_step(9, "Generating Report Visualizations (Matplotlib)", generate_all_visualizations)

    # Final Execution Summary
    passed_total = len([s for s in experiment_statuses if s[1] == "PASS"])
    failed_total = len([s for s in experiment_statuses if s[1] == "FAIL"])

    print("\n" + "=" * 80)
    print("  ACADEMIC EVALUATION SUMMARY")
    print("=" * 80)
    print(f"  Total Evaluations: {len(experiment_statuses)}")
    print(f"  Passed:            {passed_total}")
    print(f"  Failed:            {failed_total}")
    print("")

    for title, status, err in experiment_statuses:
        status_tag = f"[{status}]"
        print(f"  {status_tag:8s} {title}")
        if err:
            print(f"           Error: {err.splitlines()[0]}")

    print("=" * 80)
    print(f"  All Structured Results & Plots Saved in: {RESULTS_DIR}")
    print("=" * 80)


if __name__ == "__main__":
    run_all_experiments()

