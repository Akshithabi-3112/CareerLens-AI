"""Reproducible checks for the career clustering service.

Run from backend with:
    venv\\Scripts\\python.exe tests\\test_clustering_service.py
"""

from app.services.clustering_service import (
    analyze_profile_cluster,
    get_cluster_model,
)


cluster_model = get_cluster_model()
analysis = analyze_profile_cluster(
    ["Python", "SQL", "Machine Learning", "Pandas"]
)

assert cluster_model["cluster_count"] >= 2
assert len(cluster_model["labels"]) == len(cluster_model["profiles"])
assert analysis["cluster_id"] is not None
assert analysis["cluster_analysis"]["similar_career_group"]
assert "cluster_id" not in analysis["cluster_analysis"]

print("Selected clusters:", cluster_model["cluster_count"])
print("Silhouette scores:", {
    key: round(value, 4)
    for key, value in cluster_model["silhouette_scores"].items()
})
print("Profile cluster analysis:", analysis["cluster_analysis"])
