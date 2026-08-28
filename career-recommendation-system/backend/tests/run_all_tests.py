"""Master Automated Test Runner for all Backend Test Suites.

Runs all 12 test suites:
1. test_api_integration
2. test_career_matcher
3. test_clustering_profiles
4. test_clustering_service
5. test_course_recommendations
6. test_ensemble_service
7. test_explainability_service
8. test_hybrid_ranking
9. test_hybrid_recommendation
10. test_roadmap_service
11. test_skill_extractor
12. test_skill_gap
"""

import sys
import os
import subprocess

TEST_MODULES = [
    "tests.test_skill_extractor",
    "tests.test_skill_gap",
    "tests.test_career_matcher",
    "tests.test_clustering_service",
    "tests.test_clustering_profiles",
    "tests.test_ensemble_service",
    "tests.test_hybrid_ranking",
    "tests.test_hybrid_recommendation",
    "tests.test_course_recommendations",
    "tests.test_roadmap_service",
    "tests.test_explainability_service",
    "tests.test_api_integration",
]


def run_master_test_suite():
    print("=" * 80)
    print("  CAREERLENS AI — MASTER AUTOMATED TEST SUITE")
    print("=" * 80)

    passed_count = 0
    failed_count = 0
    failures = []

    for mod_name in TEST_MODULES:
        print(f"\n>> RUNNING: {mod_name}")
        proc = subprocess.run(
            [sys.executable, "-m", mod_name],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if proc.returncode == 0:
            passed_count += 1
            print(f"   [SUCCESS] {mod_name} passed without errors.")
        else:
            failed_count += 1
            err_msg = proc.stderr.strip() or proc.stdout.strip()
            failures.append((mod_name, err_msg))
            print(f"   [FAILED] {mod_name} (exit code {proc.returncode}):\n{err_msg}")

    print("\n" + "=" * 80)
    print("  TEST SUITE EXECUTION SUMMARY")
    print("=" * 80)
    print(f"  Total Test Suites: {len(TEST_MODULES)}")
    print(f"  Passed:            {passed_count}")
    print(f"  Failed:            {failed_count}")
    print(f"  Skipped:           0")

    if failures:
        print("\n  Failures Detail:")
        for name, err in failures:
            print(f"  - {name}: {err}")
        sys.exit(1)
    else:
        print("\n  [STATUS: ALL 12 TEST SUITES PASSED WITH 100% SUCCESS!]")
        print("=" * 80)


if __name__ == "__main__":
    run_master_test_suite()
