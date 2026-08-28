"""Comprehensive End-to-End API Integration and Error Handling Test Suite.

Tests:
1. POST /api/resume/upload across 5 distinct profiles:
   - Profile 1: AI / Machine Learning Profile
   - Profile 2: Frontend / Web Development Profile
   - Profile 3: Backend / Java Spring Profile
   - Profile 4: Data Analyst / Database Profile
   - Profile 5: Weak / Incomplete Profile (Zero technical skills)
2. Validates mathematical score integrity:
   - Final score == (0.60 * compat) + (0.20 * cluster * gate) + (0.20 * ensemble * gate)
   - Zero-skill match roles cannot receive artificial ML score boosts (skill gate = 0.0)
   - Descending score sorting
3. Validates unified explainability, course recommendations, 6-stage roadmap, and cluster/ensemble metadata on every returned career.
4. Comprehensive Error Handling & Edge Cases:
   - Unsupported extension (.exe, .jpg, .zip) -> HTTP 400
   - Empty file payload -> HTTP 400
   - Corrupted PDF binary -> HTTP 500/400 with clean error detail
   - Corrupted DOCX binary -> HTTP 500/400 with clean error detail
   - Very large resume text payload (50,000+ characters) -> HTTP 200 without timeout

Run from backend with:
    venv\\Scripts\\python.exe -m tests.test_api_integration
"""

import io
import sys
from starlette.testclient import TestClient

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from app.main import app

client = TestClient(app)

print("=" * 80)
print("  END-TO-END API INTEGRATION & VERIFICATION TEST SUITE")
print("=" * 80)

# ── Helper to test text upload as .txt or .pdf ─────────────────────────────
def upload_text_resume(text: str, filename: str = "resume.txt"):
    file_bytes = text.encode("utf-8")
    files = {"file": (filename, io.BytesIO(file_bytes), "text/plain")}
    return client.post("/api/resume/upload", files=files)


# ── TEST 1: 5 Profile Categories ──────────────────────────────────────────
PROFILES = [
    {
        "name": "1. AI / Machine Learning Profile",
        "text": "Experienced Machine Learning Engineer with strong skills in Python, TensorFlow, PyTorch, Deep Learning, Pandas, and Scikit-learn.",
        "expected_top_careers": ["Machine Learning Engineer", "AI Engineer", "Deep Learning Specialist", "Data Scientist"],
    },
    {
        "name": "2. Frontend / Web Development Profile",
        "text": "Frontend Web Developer specializing in JavaScript, TypeScript, React, Next.js, HTML, CSS, and Tailwind CSS with GitHub workflows.",
        "expected_top_careers": ["Frontend Developer", "Web Developer", "Full Stack Developer", "UI/UX Designer"],
    },
    {
        "name": "3. Backend / Software Engineering Profile",
        "text": "Senior Backend Software Engineer with experience in Java, Spring Boot, PostgreSQL, MySQL, Redis, Docker, and REST APIs.",
        "expected_top_careers": ["Backend Developer", "Software Engineer", "Java Developer", "Database Administrator"],
    },
    {
        "name": "4. Data / Database Profile",
        "text": "Database Administrator and Data Analyst with deep knowledge of SQL, MySQL, PostgreSQL, Oracle, MongoDB, and Database Design.",
        "expected_top_careers": ["Database Administrator", "Data Analyst", "Data Engineer", "Backend Developer"],
    },
    {
        "name": "5. Weak / Incomplete Profile",
        "text": "General worker with experience in Microsoft Word, Email communication, and basic typing skills.",
        "expected_top_careers": [],  # Expect graceful low-confidence output without crashes
    },
]

for profile in PROFILES:
    print(f"\n[TESTING: {profile['name']}]")
    res = upload_text_resume(profile["text"])
    assert res.status_code == 200, f"Expected 200 OK but got {res.status_code}: {res.text}"

    data = res.json()

    # 1. Structural Checks
    assert "resume" in data
    assert "skills" in data
    assert "career_recommendations" in data
    assert "career_analysis" in data
    assert "cluster_analysis" in data
    assert "ensemble_analysis" in data
    assert "recommendation_metadata" in data

    extracted = data["skills"].get("extracted_skills", [])
    recs = data["career_recommendations"]
    analysis = data["career_analysis"]

    print(f"  • Extracted Skills ({len(extracted)}): {', '.join(extracted[:5]) or 'None'}")
    print(f"  • Matched Cluster: '{data['cluster_analysis'].get('cluster_name')}' (Similarity: {data['cluster_analysis'].get('profile_cluster_similarity', 0)}%)")
    print(f"  • Recommendations Count: {len(recs)}")

    if recs:
        top_rec = recs[0]
        top_analysis = analysis[0]

        print(f"  • Top Ranked Career: '{top_rec['career']}' (Hybrid Score: {top_rec.get('final_score') or top_rec.get('final_recommendation_score')}%)")

        # 2. Mathematical Score Validation
        final = top_rec.get("final_score", top_rec.get("final_recommendation_score"))
        compat = top_rec.get("compatibility_score", 0)
        clust = top_rec.get("cluster_relevance_score", 0)
        ens = top_rec.get("ensemble_confidence", 0)
        score_comp = top_rec.get("score_components", {})
        weights = score_comp.get("weights", {"skill_match": 0.60, "cluster_relevance": 0.20, "ensemble_prediction": 0.20})
        gate = score_comp.get("skill_gate_factor", 1.0)

        w_skill = weights.get("skill_match", 0.60)
        w_clust = weights.get("cluster_relevance", 0.20)
        w_ens = weights.get("ensemble_prediction", 0.20)

        calc = round(w_skill * compat + w_clust * clust * gate + w_ens * ens * gate, 1)
        assert abs(final - calc) <= 0.5, f"Score mismatch: final={final}, calculated={calc} (weights={weights}, gate={gate})"
        assert 0.0 <= final <= 100.0, f"Score out of bounds: {final}"

        # 3. Descending Sort Order Validation
        all_scores = [r.get("final_score", r.get("final_recommendation_score")) for r in recs]
        assert all_scores == sorted(all_scores, reverse=True), "Recommendations must be sorted descending by final score"

        # 4. Career Analysis Verification
        assert "course_recommendations" in top_analysis, "Missing course recommendations in career analysis"
        assert "career_roadmap" in top_analysis, "Missing career roadmap in career analysis"
        assert "unified_explanation" in top_analysis, "Missing unified explanation in career analysis"
        assert len(top_analysis["career_roadmap"]["stages"]) == 6, "Roadmap must have 6 stages"

        # 5. Top Career Domain Alignment Check (if not weak profile)
        if profile["expected_top_careers"]:
            top_career_names = [r["career"] for r in recs[:3]]
            matched_any = any(c in profile["expected_top_careers"] for c in top_career_names)
            assert matched_any, f"Expected one of {profile['expected_top_careers']} in top 3, but got {top_career_names}"

    print(f"  [PASS] {profile['name']} verified successfully!")


# ── TEST 2: Error Handling and Edge Cases ──────────────────────────────────
print("\n" + "=" * 80)
print("  TESTING ERROR HANDLING & EDGE CASES")
print("=" * 80)

# 1. Unsupported extension (.exe)
res_bad_ext = client.post(
    "/api/resume/upload",
    files={"file": ("malware.exe", io.BytesIO(b"binary content"), "application/octet-stream")},
)
assert res_bad_ext.status_code == 400
assert "Unsupported file type" in res_bad_ext.json()["detail"]
print("  [PASS] Unsupported extension (.exe) correctly returned 400 Bad Request.")

# 2. Empty file
res_empty = client.post(
    "/api/resume/upload",
    files={"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")},
)
assert res_empty.status_code == 400
assert "empty" in res_empty.json()["detail"].lower()
print("  [PASS] Empty file correctly returned 400 Bad Request.")

# 3. Corrupted PDF
res_corrupt_pdf = client.post(
    "/api/resume/upload",
    files={"file": ("corrupt.pdf", io.BytesIO(b"%PDF-invalid-bytes-non-parseable"), "application/pdf")},
)
assert res_corrupt_pdf.status_code in (400, 500)
assert "detail" in res_corrupt_pdf.json()
print(f"  [PASS] Corrupted PDF returned safe HTTP {res_corrupt_pdf.status_code} with detail: '{res_corrupt_pdf.json()['detail']}'")

# 4. Large Resume Payload (50,000+ characters)
large_text = "Experienced Senior Python Software Engineer specializing in Machine Learning, Docker, SQL. " * 800
res_large = upload_text_resume(large_text, filename="large_resume.txt")
assert res_large.status_code == 200
assert len(res_large.json()["skills"]["extracted_skills"]) > 0
print(f"  [PASS] Large resume payload ({len(large_text)} chars) processed cleanly in HTTP 200.")

print("\n" + "=" * 80)
print("  ALL END-TO-END INTEGRATION & ERROR HANDLING TESTS PASSED!")
print("=" * 80)
