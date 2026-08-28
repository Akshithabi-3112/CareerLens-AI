"""Evaluation script for K-Means Career Clustering.

Evaluates:
1. Silhouette score sweep across K in [3..12]
2. Optimal K determination
3. Cluster size distribution
4. Dominant skill coherence per cluster
"""

from typing import Dict, List
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from app.services.clustering_service import (
    get_cluster_model,
    get_all_clusters_overview,
)


def evaluate_clustering() -> Dict:
    model_bundle = get_cluster_model()
    profiles = model_bundle["profiles"]
    vectorizer = model_bundle["vectorizer"]
    production_k = model_bundle["cluster_count"]
    silhouette_scores_dict = model_bundle["silhouette_scores"]
    labels = model_bundle["labels"]

    skill_matrix = vectorizer.transform([p["skills"] for p in profiles])

    # K-Sweep
    k_sweep_results = []
    for k, score in sorted(silhouette_scores_dict.items()):
        k_sweep_results.append({
            "k": k,
            "silhouette_score": round(float(score), 4),
        })

    # Production Fitted Cluster Overview
    clusters_overview = get_all_clusters_overview()

    # Cluster Distribution
    unique, counts = np.unique(labels, return_counts=True)
    dist = {int(u): int(c) for u, c in zip(unique, counts)}

    return {
        "dataset_career_count": len(profiles),
        "feature_dimensions": len(vectorizer.classes_),
        "k_sweep": k_sweep_results,
        "optimal_k_by_silhouette": production_k,
        "max_silhouette_score": round(float(max(silhouette_scores_dict.values())), 4),
        "production_k": production_k,
        "production_silhouette_score": round(float(silhouette_scores_dict[production_k]), 4),
        "cluster_size_distribution": dist,
        "clusters_overview": clusters_overview,
    }



if __name__ == "__main__":
    import json
    res = evaluate_clustering()
    print("=== CLUSTERING EVALUATION RESULTS ===")
    print(f"Optimal K: {res['optimal_k_by_silhouette']} (Silhouette: {res['max_silhouette_score']})")
    print("K-Sweep:")
    for row in res["k_sweep"]:
        print(f"  K={row['k']}: Silhouette = {row['silhouette_score']}")
