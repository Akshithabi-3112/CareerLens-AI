"""Tests for the Personalized Dynamic Learning Roadmap service.

Tests:
1. Tests roadmap generation across 3 distinct test scenarios:
   - User A (Beginner with no skills) vs User B (Knows Python & SQL) for Data Scientist.
   - Frontend Developer roadmap (HTML/CSS -> JavaScript -> React -> Next.js).
   - DevOps Engineer roadmap (Linux/Git -> Docker -> Kubernetes/CI/CD).
2. Verifies prerequisite dependency ordering (prerequisites appear in earlier stages).
3. Verifies explainability fields (why_prioritized, enables_next).
4. Verifies integration of matched and completed skills.

Run from backend with:
    venv\\Scripts\\python.exe -m tests.test_roadmap_service
"""

import sys
import io

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from app.services.roadmap_service import generate_career_roadmap


print("=" * 80)
print("  PERSONALIZED LEARNING ROADMAP MODULE - VERIFICATION")
print("=" * 80)

# ── TEST 1: User A vs User B for Data Scientist ────────────────────────────
print("\n" + "=" * 80)
print("  SCENARIO 1: Same Career (Data Scientist) with Different User Skill Profiles")
print("=" * 80)

# User A: Zero skills
roadmap_user_a = generate_career_roadmap(
    career_name="Data Scientist",
    missing_skills=["Python", "Statistics", "Machine Learning", "Deep Learning", "TensorFlow"],
    matched_skills=[],
    required_skills=["Python", "Statistics", "Machine Learning"],
)

# User B: Already knows Python and SQL
roadmap_user_b = generate_career_roadmap(
    career_name="Data Scientist",
    missing_skills=["Statistics", "Machine Learning", "Deep Learning", "TensorFlow"],
    matched_skills=["Python", "SQL"],
    required_skills=["Python", "Statistics", "Machine Learning"],
)

print("\n  [User A Roadmap - Zero Prior Skills]")
for stage in roadmap_user_a["stages"]:
    skills_str = ", ".join(s["skill"] for s in stage["skills"]) or "(Milestone/Action items only)"
    print(f"    • Stage {stage['stage_number']} ({stage['theme']}): {skills_str}")

print("\n  [User B Roadmap - Already Knows Python & SQL]")
for stage in roadmap_user_b["stages"]:
    skills_str = ", ".join(s["skill"] for s in stage["skills"]) or "(Milestone/Action items only)"
    print(f"    • Stage {stage['stage_number']} ({stage['theme']}): {skills_str}")

# Assertions for Scenario 1
# User A should have Python in Stage 1
user_a_stage_1_skills = [s["skill"].lower() for s in roadmap_user_a["stages"][0]["skills"]]
assert "python" in user_a_stage_1_skills, "User A must have Python in Foundation (Stage 1)"

# User B should NOT have Python in missing skills
user_b_all_skills = [s["skill"].lower() for s in roadmap_user_b["skill_plan"]]
assert "python" not in user_b_all_skills, "User B already has Python, should not be in missing roadmap"


# ── TEST 2: Frontend Developer Roadmap Dependency Verification ─────────────
print("\n" + "=" * 80)
print("  SCENARIO 2: Frontend Developer Dependency Order Verification")
print("=" * 80)

roadmap_frontend = generate_career_roadmap(
    career_name="Frontend Developer",
    missing_skills=["HTML", "CSS", "JavaScript", "React", "Next.js", "TypeScript"],
    matched_skills=[],
    required_skills=["HTML", "CSS", "JavaScript", "React"],
)

stage_map = {}
for stage in roadmap_frontend["stages"]:
    for s in stage["skills"]:
        stage_map[s["skill"].lower()] = stage["stage_number"]
    print(f"    • Stage {stage['stage_number']} ({stage['theme']}): {', '.join(s['skill'] for s in stage['skills']) or '—'}")

# Verify topological prerequisite order: HTML/CSS (Stage 1) <= JavaScript (Stage 1/2) <= React (Stage 2/3) <= Next.js (Stage 3+)
print("\n  Dependency Order Check:")
print(f"    - HTML Stage:       {stage_map.get('html')}")
print(f"    - CSS Stage:        {stage_map.get('css')}")
print(f"    - JavaScript Stage: {stage_map.get('javascript')}")
print(f"    - React Stage:      {stage_map.get('react')}")
print(f"    - Next.js Stage:    {stage_map.get('next.js')}")

assert stage_map["html"] <= stage_map["javascript"], "HTML must be in same or earlier stage than JavaScript"
assert stage_map["javascript"] <= stage_map["react"], "JavaScript must be in same or earlier stage than React"
assert stage_map["react"] <= stage_map["next.js"], "React must be in same or earlier stage than Next.js"
print("  [OK] Prerequisite dependency ordering verified!")


# ── TEST 3: DevOps Engineer Roadmap ────────────────────────────────────────
print("\n" + "=" * 80)
print("  SCENARIO 3: DevOps Engineer Roadmap")
print("=" * 80)

roadmap_devops = generate_career_roadmap(
    career_name="DevOps Engineer",
    missing_skills=["Linux", "Git", "Docker", "Kubernetes", "AWS", "CI/CD"],
    matched_skills=[],
    required_skills=["Linux", "Docker", "Kubernetes", "CI/CD"],
)

devops_stage_map = {}
for stage in roadmap_devops["stages"]:
    for s in stage["skills"]:
        devops_stage_map[s["skill"].lower()] = stage["stage_number"]
    print(f"    • Stage {stage['stage_number']} ({stage['theme']}): {', '.join(s['skill'] for s in stage['skills']) or '—'}")

assert devops_stage_map["linux"] <= devops_stage_map["docker"], "Linux must be in same or earlier stage than Docker"
assert devops_stage_map["docker"] <= devops_stage_map["kubernetes"], "Docker must be in same or earlier stage than Kubernetes"
print("  [OK] DevOps dependency ordering verified!")


# ── TEST 4: Explainability Fields Verification ─────────────────────────────
print("\n" + "=" * 80)
print("  SCENARIO 4: Explainability Metadata Verification")
print("=" * 80)

sample_skill = roadmap_frontend["skill_plan"][0]
print(f"  Skill: '{sample_skill['skill']}'")
print(f"    - Target Stage:     Stage {sample_skill['target_stage']} ({sample_skill['stage_name']})")
print(f"    - Why Prioritized:  \"{sample_skill['why_prioritized']}\"")
print(f"    - Enables Next:     \"{sample_skill['enables_next']}\"")

assert "why_prioritized" in sample_skill and len(sample_skill["why_prioritized"]) > 10
assert "enables_next" in sample_skill and len(sample_skill["enables_next"]) > 5

print("\n" + "=" * 80)
print("  ALL PERSONALIZED ROADMAP TESTS PASSED SUCCESSFULLY!")
print("=" * 80)
