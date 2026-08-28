"""Test clustering with three distinct skill profiles.

Run from backend with:
    venv\\Scripts\\python.exe -m tests.test_clustering_profiles
"""

import sys
import io

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from app.services.clustering_service import (
    analyze_profile_cluster,
    get_all_clusters_overview,
    get_career_cluster_ids,
)


# -- Profile 1: AI / ML --------------------------------------------------
profile_ai = ["Python", "Machine Learning", "TensorFlow"]
result_ai = analyze_profile_cluster(profile_ai)

# -- Profile 2: Web / Frontend -------------------------------------------
profile_web = ["HTML", "CSS", "JavaScript", "React"]
result_web = analyze_profile_cluster(profile_web)

# -- Profile 3: Database -------------------------------------------------
profile_db = ["SQL", "MySQL", "MongoDB", "Database Design"]
result_db = analyze_profile_cluster(profile_db)


print("=" * 70)
print("  CLUSTERING TEST RESULTS - 3 Distinct Skill Profiles")
print("=" * 70)

for label, skills, result in [
    ("AI / ML Profile", profile_ai, result_ai),
    ("Web / Frontend Profile", profile_web, result_web),
    ("Database Profile", profile_db, result_db),
]:
    ca = result["cluster_analysis"]
    print()
    print("-" * 70)
    print(f"  {label}  (input: {', '.join(skills)})")
    print("-" * 70)
    print(f"  Cluster ID:            {result['cluster_id']}")
    print(f"  Cluster Name:          {ca['cluster_name']}")
    print(f"  Similarity:            {ca['profile_cluster_similarity']}%")
    print(f"  Cluster Count:         {ca.get('cluster_count', 'N/A')}")
    print(f"  Dominant Skills:       {', '.join(ca.get('dominant_skills', []))}")
    print(f"  Matched User Skills:   {', '.join(ca.get('matched_cluster_skills', []))}")
    print(f"  Similar Careers:       {', '.join(ca['similar_career_group'])}")
    print(f"  Explanation:           {ca['explanation']}")


# -- Verify different profiles produce different/relevant clusters --------
ids = [result_ai["cluster_id"], result_web["cluster_id"], result_db["cluster_id"]]
print()
print("=" * 70)
print("  CLUSTER ASSIGNMENT SUMMARY")
print("=" * 70)
print(f"  AI/ML Profile  -> Cluster {ids[0]}")
print(f"  Web Profile    -> Cluster {ids[1]}")
print(f"  DB Profile     -> Cluster {ids[2]}")
unique_count = len(set(ids))
print(f"  Unique clusters used: {unique_count} / 3")
assert unique_count >= 2, f"Expected at least 2 unique clusters, got {unique_count}"
print("  [OK] Profiles map to different clusters")


# -- Full cluster overview ------------------------------------------------
print()
print("=" * 70)
print("  FULL CLUSTER OVERVIEW")
print("=" * 70)
overview = get_all_clusters_overview()
print(f"  Total clusters:     {overview['cluster_count']}")
print(f"  Best silhouette:    {overview['best_silhouette_score']}")
print(f"  Silhouette scores:  {overview['silhouette_scores']}")

for c in overview["clusters"]:
    print()
    print(f"  [{c['cluster_id']}] {c['cluster_name']}")
    print(f"      Careers ({c['career_count']}): {', '.join(c['careers'][:8])}")
    if c["career_count"] > 8:
        print(f"      ... and {c['career_count'] - 8} more")
    print(f"      Top skills: {', '.join(c['dominant_skills'])}")


# -- Verify integration with recommendation pipeline ---------------------
print()
print("=" * 70)
print("  RECOMMENDATION PIPELINE INTEGRATION")
print("=" * 70)

from app.services.recommendation_service import build_hybrid_recommendations

skills_result = {
    "extracted_skills": ["Python", "SQL", "Machine Learning", "Pandas"],
    "skill_categories": {
        "Programming": ["Python"],
        "Database": ["SQL"],
        "AI and Machine Learning": ["Machine Learning"],
        "Data Science": ["Pandas"],
    },
    "evidence": {
        "Python": "Python",
        "SQL": "SQL",
        "Machine Learning": "Machine Learning",
        "Pandas": "Pandas",
    },
}

result = build_hybrid_recommendations(skills_result, top_n=3)

assert "career_recommendations" in result
assert len(result["career_recommendations"]) > 0
assert "cluster_analysis" in result
ca = result["cluster_analysis"]
assert ca.get("cluster_name"), "cluster_name is missing"
assert ca.get("dominant_skills") is not None, "dominant_skills is missing"
assert ca.get("matched_cluster_skills") is not None, "matched_cluster_skills is missing"
assert ca.get("cluster_count") is not None, "cluster_count is missing"

print(f"  Recommendations returned:  {len(result['career_recommendations'])}")
print(f"  Cluster name:              {ca['cluster_name']}")
print(f"  Cluster similarity:        {ca['profile_cluster_similarity']}%")
print(f"  Cluster count:             {ca['cluster_count']}")
print(f"  Dominant skills:           {', '.join(ca.get('dominant_skills', []))}")
print(f"  Matched cluster skills:    {', '.join(ca.get('matched_cluster_skills', []))}")

top_rec = result["career_recommendations"][0]
assert "compatibility_score" in top_rec, "compatibility_score missing from rec"
assert "missing_skills" in top_rec, "missing_skills missing from rec"
assert "cluster_alignment" in top_rec, "cluster_alignment missing from rec"
assert "score_components" in top_rec, "score_components missing from rec"

print(f"  Top career:                {top_rec['career']}")
print(f"  Compatibility:             {top_rec['compatibility_score']}%")
print(f"  Cluster alignment:         {top_rec['cluster_alignment']}")
print(f"  Final recommendation:      {top_rec['final_recommendation_score']}%")
print(f"  Score components:          Present [OK]")


# -- Verify skill-gap analysis still works --------------------------------
print()
print("=" * 70)
print("  SKILL-GAP ANALYSIS VERIFICATION")
print("=" * 70)

from app.services.skill_gap_service import analyze_skill_gap

gap_result = analyze_skill_gap(
    ["Python", "SQL", "Machine Learning"],
    {"career": "Data Scientist", "required_skills": ["Python", "SQL", "Machine Learning", "Data Analysis", "Statistics"]}
)

assert gap_result["matched_skills"] == ["Python", "SQL", "Machine Learning"]
assert "Data Analysis" in gap_result["missing_skills"]
assert "Statistics" in gap_result["missing_skills"]
assert gap_result["readiness_score"] == 60.0
assert gap_result["skill_gap_percentage"] == 40.0

print(f"  Career:             {gap_result['career']}")
print(f"  Matched skills:     {', '.join(gap_result['matched_skills'])}")
print(f"  Missing skills:     {', '.join(gap_result['missing_skills'])}")
print(f"  Readiness score:    {gap_result['readiness_score']}%")
print(f"  Skill gap:          {gap_result['skill_gap_percentage']}%")
print(f"  Skill-gap analysis: [OK] Working correctly")


# -- Final verdict --------------------------------------------------------
print()
print("=" * 70)
print("  ALL TESTS PASSED")
print("=" * 70)
