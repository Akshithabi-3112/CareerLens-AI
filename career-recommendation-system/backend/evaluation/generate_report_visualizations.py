"""Publication-Quality Report Visualization Generator using Matplotlib.

Reads structured evaluation result files from `backend/evaluation/results/` and generates
high-resolution PNG figures for academic reports and thesis dissertations:
1. model_comparison.png
2. silhouette_analysis.png
3. ranking_metrics.png
4. ablation_study.png
5. course_gap_coverage.png
6. explainability_metrics.png

Output directory: `backend/evaluation/results/plots/`
"""

import os
import json
import matplotlib
matplotlib.use("Agg")  # Non-interactive headless backend
import matplotlib.pyplot as plt
import numpy as np

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
PLOTS_DIR = os.path.join(RESULTS_DIR, "plots")
os.makedirs(PLOTS_DIR, exist_ok=True)

# Publication styling defaults
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "axes.labelsize": 11,
    "axes.labelweight": "semibold",
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "figure.autolayout": True,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "grid.linestyle": "--",
})

# Academic color palette
COLORS = {
    "primary_blue": "#2563eb",
    "accent_purple": "#7c3aed",
    "teal": "#0d9488",
    "amber": "#d97706",
    "emerald": "#059669",
    "rose": "#e11d48",
    "slate": "#475569",
    "cyan": "#0891b2",
}


def _load_json(filename: str):
    path = os.path.join(RESULTS_DIR, filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


# ── 1. Model Comparison Chart ──────────────────────────────────────────────
def plot_model_comparison():
    summary = _load_json("evaluation_summary.json")
    if not summary or "model_comparison_evaluation" not in summary:
        print("  [SKIP] model_comparison data unavailable.")
        return

    comp = summary["model_comparison_evaluation"]["model_comparison"]
    models = list(comp.keys())
    metrics = ["Accuracy", "Precision", "Recall", "F1-Score"]

    acc = [comp[m]["accuracy"] * 100 for m in models]
    prec = [comp[m]["macro_precision"] * 100 for m in models]
    rec = [comp[m]["macro_recall"] * 100 for m in models]
    f1 = [comp[m]["macro_f1"] * 100 for m in models]

    x = np.arange(len(models))
    width = 0.18

    fig, ax = plt.subplots(figsize=(9, 5.5))
    rects1 = ax.bar(x - 1.5 * width, acc, width, label="Accuracy", color=COLORS["primary_blue"])
    rects2 = ax.bar(x - 0.5 * width, prec, width, label="Precision", color=COLORS["teal"])
    rects3 = ax.bar(x + 0.5 * width, rec, width, label="Recall", color=COLORS["amber"])
    rects4 = ax.bar(x + 1.5 * width, f1, width, label="F1-Score", color=COLORS["accent_purple"])

    ax.set_ylabel("Score (%)")
    ax.set_title("Machine Learning Model Performance Comparison")
    ax.set_xticks(x)
    ax.set_xticklabels(models, fontweight="semibold")
    ax.set_ylim(60, 100)
    ax.legend(loc="lower right", framealpha=0.9)

    for rects in [rects1, rects2, rects3, rects4]:
        for r in rects:
            h = r.get_height()
            ax.annotate(f"{h:.1f}%", xy=(r.get_x() + r.get_width() / 2, h),
                        xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=8)

    save_path = os.path.join(PLOTS_DIR, "model_comparison.png")
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"  [SAVED] {save_path}")


# ── 2. Silhouette Analysis Chart ───────────────────────────────────────────
def plot_silhouette_analysis():
    summary = _load_json("evaluation_summary.json")
    if not summary or "clustering_evaluation" not in summary:
        print("  [SKIP] clustering data unavailable.")
        return

    k_sweep = summary["clustering_evaluation"]["k_sweep"]
    k_vals = [item["k"] for item in k_sweep]
    scores = [item["silhouette_score"] for item in k_sweep]
    opt_k = summary["clustering_evaluation"].get("optimal_k_by_silhouette", 7)
    opt_score = summary["clustering_evaluation"].get("max_silhouette_score", max(scores))

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(k_vals, scores, marker="o", linewidth=2.5, color=COLORS["accent_purple"], label="Cosine Silhouette Score")

    # Highlight Optimal K
    ax.scatter([opt_k], [opt_score], color=COLORS["rose"], s=130, zorder=5, label=f"Optimal K = {opt_k} (Score: {opt_score:.4f})")
    ax.annotate(f"Optimal K={opt_k}\n({opt_score:.4f})",
                xy=(opt_k, opt_score), xytext=(opt_k - 0.7, opt_score + 0.018),
                arrowprops=dict(arrowstyle="->", color=COLORS["rose"], lw=1.5),
                fontweight="bold", color=COLORS["rose"])

    ax.set_xlabel("Number of Clusters (K)")
    ax.set_ylabel("Cosine Silhouette Score")
    ax.set_title("K-Means Career Clustering: Silhouette Score vs. Number of Clusters (K)")
    ax.set_xticks(k_vals)
    ax.legend(loc="lower right", framealpha=0.9)

    save_path = os.path.join(PLOTS_DIR, "silhouette_analysis.png")
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"  [SAVED] {save_path}")


# ── 3. Ranking Comparison Chart ────────────────────────────────────────────
def plot_ranking_metrics():
    summary = _load_json("evaluation_summary.json")
    if not summary or "ranking_evaluation" not in summary:
        print("  [SKIP] ranking data unavailable.")
        return

    base = summary["ranking_evaluation"]["baseline_compatibility_only"]
    hyb = summary["ranking_evaluation"]["proposed_hybrid_system"]

    metrics = ["Precision@1", "Precision@3", "Recall@3", "NDCG@3", "MRR"]
    keys = ["p@1", "p@3", "r@3", "ndcg@3", "mrr"]

    base_scores = [base[k] * 100 for k in keys]
    hyb_scores = [hyb[k] * 100 for k in keys]

    x = np.arange(len(metrics))
    width = 0.35

    fig, ax = plt.subplots(figsize=(9, 5.5))
    rects1 = ax.bar(x - width / 2, base_scores, width, label="Baseline (Compatibility-Only)", color=COLORS["slate"])
    rects2 = ax.bar(x + width / 2, hyb_scores, width, label="Proposed Hybrid System", color=COLORS["emerald"])

    ax.set_ylabel("Score (%)")
    ax.set_title("Recommendation Ranking: Baseline vs. Proposed Hybrid Engine")
    ax.set_xticks(x)
    ax.set_xticklabels(metrics, fontweight="semibold")
    ax.set_ylim(0, 105)
    ax.legend(loc="lower right", framealpha=0.9)

    for r in rects1:
        h = r.get_height()
        ax.annotate(f"{h:.1f}%", xy=(r.get_x() + r.get_width() / 2, h),
                    xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=8.5)

    for r in rects2:
        h = r.get_height()
        ax.annotate(f"{h:.1f}%", xy=(r.get_x() + r.get_width() / 2, h),
                    xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=8.5, fontweight="bold")

    save_path = os.path.join(PLOTS_DIR, "ranking_metrics.png")
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"  [SAVED] {save_path}")


# ── 4. Ablation Study Chart ────────────────────────────────────────────────
def plot_ablation_study():
    ablation = _load_json("ablation_study.json")
    if not ablation:
        print("  [SKIP] ablation_study.json unavailable.")
        return

    config_names = [data["name"].split(" (")[0] for data in ablation.values()]
    p1 = [data["metrics"]["p@1"] for data in ablation.values()]
    ndcg3 = [data["metrics"]["ndcg@3"] for data in ablation.values()]
    mrr = [data["metrics"]["mrr"] for data in ablation.values()]

    x = np.arange(len(config_names))
    width = 0.25

    fig, ax = plt.subplots(figsize=(10, 5.5))
    rects1 = ax.bar(x - width, p1, width, label="Precision@1 (%)", color=COLORS["primary_blue"])
    rects2 = ax.bar(x, ndcg3, width, label="NDCG@3 (%)", color=COLORS["teal"])
    rects3 = ax.bar(x + width, mrr, width, label="MRR (%)", color=COLORS["accent_purple"])

    ax.set_ylabel("Score (%)")
    ax.set_title("Hybrid Weight Ablation Study: Impact of Weighting on Ranking Metrics")
    ax.set_xticks(x)
    ax.set_xticklabels(config_names, fontweight="semibold")
    ax.set_ylim(40, 100)
    ax.legend(loc="lower right", framealpha=0.9)

    # Highlight Config D (Production)
    ax.axvspan(2.6, 3.4, color="yellow", alpha=0.15, label="Production (0.60 / 0.20 / 0.20)")

    for rects in [rects1, rects2, rects3]:
        for r in rects:
            h = r.get_height()
            ax.annotate(f"{h:.1f}", xy=(r.get_x() + r.get_width() / 2, h),
                        xytext=(0, 2), textcoords="offset points", ha="center", va="bottom", fontsize=8)

    save_path = os.path.join(PLOTS_DIR, "ablation_study.png")
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"  [SAVED] {save_path}")


# ── 5. Course Gap Coverage Chart ───────────────────────────────────────────
def plot_course_gap_coverage():
    courses_eval = _load_json("course_recs_evaluation.json")
    if not courses_eval:
        print("  [SKIP] course_recs_evaluation.json unavailable.")
        return

    summary = courses_eval["summary"]
    metrics = [
        "Top-1 Course\nCoverage",
        "Top-3 Courses\nCoverage",
        "Top-5 Courses\nCoverage",
        "Overall Gap\nCoverage",
        "Course\nRelevance",
    ]
    values = [
        summary["top1_course_coverage_percent"],
        summary["top3_course_coverage_percent"],
        summary["top5_course_coverage_percent"],
        summary["overall_gap_coverage_percent"],
        summary["course_relevance_percent"],
    ]

    colors = [COLORS["cyan"], COLORS["primary_blue"], COLORS["accent_purple"], COLORS["emerald"], COLORS["teal"]]

    fig, ax = plt.subplots(figsize=(8.5, 5))
    rects = ax.bar(metrics, values, width=0.5, color=colors)

    ax.set_ylabel("Percentage (%)")
    ax.set_title("Course Recommendation: Skill Gap Coverage and Course Relevance")
    ax.set_ylim(0, 115)

    for r in rects:
        h = r.get_height()
        ax.annotate(f"{h:.1f}%", xy=(r.get_x() + r.get_width() / 2, h),
                    xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=9.5, fontweight="bold")

    save_path = os.path.join(PLOTS_DIR, "course_gap_coverage.png")
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"  [SAVED] {save_path}")


# ── 6. Explainability Metrics Chart ────────────────────────────────────────
def plot_explainability_metrics():
    exp_eval = _load_json("explainability_evaluation.json")
    if not exp_eval:
        print("  [SKIP] explainability_evaluation.json unavailable.")
        return

    summary = exp_eval["summary"]
    metrics = [
        "Faithfulness\nScore",
        "Explanation\nCoverage",
        "Mathematical\nConsistency",
        "Hallucination\nRate (Ideal: 0%)",
    ]
    values = [
        summary["faithfulness_score_percent"],
        summary["explanation_coverage_percent"],
        summary["mathematical_consistency_percent"],
        summary["hallucination_rate_percent"],
    ]

    colors = [COLORS["emerald"], COLORS["primary_blue"], COLORS["accent_purple"], COLORS["rose"]]

    fig, ax = plt.subplots(figsize=(8.5, 5))
    rects = ax.bar(metrics, values, width=0.48, color=colors)

    ax.set_ylabel("Score (%)")
    ax.set_title("Unified Explainability: Quality, Faithfulness, and Grounding Metrics")
    ax.set_ylim(0, 115)

    for r in rects:
        h = r.get_height()
        ax.annotate(f"{h:.1f}%", xy=(r.get_x() + r.get_width() / 2, h),
                    xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=9.5, fontweight="bold")

    save_path = os.path.join(PLOTS_DIR, "explainability_metrics.png")
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"  [SAVED] {save_path}")


def generate_all_visualizations():
    print("=" * 80)
    print("  GENERATING PUBLICATION-QUALITY REPORT VISUALIZATIONS (Matplotlib)")
    print("=" * 80)
    plot_model_comparison()
    plot_silhouette_analysis()
    plot_ranking_metrics()
    plot_ablation_study()
    plot_course_gap_coverage()
    plot_explainability_metrics()
    print("=" * 80)
    print(f"  All Figures Successfully Saved to: {PLOTS_DIR}")
    print("=" * 80)


if __name__ == "__main__":
    generate_all_visualizations()
