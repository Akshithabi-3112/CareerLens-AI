"""Evaluation script for Course and Certification Recommendations.

Evaluates the real production course recommendation service (course_service.py) on:
1. Skill Gap Coverage Rate (% of missing skills covered by recommended courses)
2. Top-K Course Coverage (Top 1, Top 3, Top 5 courses)
3. Course Relevance (% of recommended courses teaching verified missing skills)
4. Certification Relevance & Availability
"""

import os
import json
import csv
from typing import Dict, List
from app.services.course_service import recommend_courses_for_gaps
from app.services.skill_gap_service import analyze_skill_gap
from app.services.career_matcher import load_careers
from evaluation.benchmark_datasets import CAREER_RECOMMENDATION_BENCHMARK

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)


def evaluate_course_recommendations() -> Dict:
    all_careers = {c["career"]: c for c in load_careers()}
    eval_records = []

    total_missing_skills_count = 0
    total_covered_skills_count = 0
    total_courses_recommended = 0
    total_relevant_courses = 0
    total_certs_recommended = 0
    total_relevant_certs = 0

    top1_covered_count = 0
    top3_covered_count = 0
    top5_covered_count = 0

    for test_case in CAREER_RECOMMENDATION_BENCHMARK:
        profile_id = test_case["profile_id"]
        user_skills = test_case["skills"]
        gt_careers = test_case["ground_truth_careers"]

        # Evaluate against the primary target career (relevance == 3)
        primary_careers = [c for c, rel in gt_careers.items() if rel == 3 and c in all_careers]
        if not primary_careers:
            primary_careers = [list(gt_careers.keys())[0]]

        target_career_name = primary_careers[0]
        career_data = all_careers.get(target_career_name, {
            "career": target_career_name,
            "required_skills": ["Python"],
        })

        # Calculate real skill gaps
        gap_res = analyze_skill_gap(user_skills, career_data)
        missing_skills = gap_res.get("missing_skills", [])
        matched_skills = gap_res.get("matched_skills", [])

        # Call real course service
        course_res = recommend_courses_for_gaps(
            missing_skills=missing_skills,
            career_name=target_career_name,
            required_missing_skills=missing_skills,
            top_n=6,
        )

        essential_courses = course_res.get("essential_courses", [])
        recommended_certs = course_res.get("recommended_certifications", [])

        num_missing = len(missing_skills)
        missing_set_lower = {s.lower() for s in missing_skills}

        if num_missing == 0:
            # Full match candidate
            coverage_rate = 100.0
            top1_cov = 100.0
            top3_cov = 100.0
            top5_cov = 100.0
            relevance_rate = 100.0
            cert_relevance_rate = 100.0
            covered_gaps_all = set()
        else:
            # 1. Overall Gap Coverage
            covered_gaps_all = set()
            for c in essential_courses:
                for g in c.get("matched_gaps", []):
                    if g.lower() in missing_set_lower:
                        covered_gaps_all.add(g.lower())

            coverage_rate = (len(covered_gaps_all) / num_missing) * 100.0

            # 2. Top-1 Coverage
            top1_covered = set()
            if essential_courses:
                for g in essential_courses[0].get("matched_gaps", []):
                    if g.lower() in missing_set_lower:
                        top1_covered.add(g.lower())
            top1_cov = (len(top1_covered) / num_missing) * 100.0

            # 3. Top-3 Coverage
            top3_covered = set()
            for c in essential_courses[:3]:
                for g in c.get("matched_gaps", []):
                    if g.lower() in missing_set_lower:
                        top3_covered.add(g.lower())
            top3_cov = (len(top3_covered) / num_missing) * 100.0

            # 4. Top-5 Coverage
            top5_covered = set()
            for c in essential_courses[:5]:
                for g in c.get("matched_gaps", []):
                    if g.lower() in missing_set_lower:
                        top5_covered.add(g.lower())
            top5_cov = (len(top5_covered) / num_missing) * 100.0

            # 5. Course Relevance: do recommended courses cover at least one actual missing gap?
            relevant_courses_count = 0
            for c in essential_courses:
                if any(g.lower() in missing_set_lower for g in c.get("matched_gaps", [])):
                    relevant_courses_count += 1
            relevance_rate = (relevant_courses_count / len(essential_courses) * 100.0) if essential_courses else 100.0

            # 6. Certification Relevance
            relevant_certs_count = 0
            for cert in recommended_certs:
                if any(g.lower() in missing_set_lower for g in cert.get("matched_gaps", [])):
                    relevant_certs_count += 1
            cert_relevance_rate = (relevant_certs_count / len(recommended_certs) * 100.0) if recommended_certs else 100.0

            total_missing_skills_count += num_missing
            total_covered_skills_count += len(covered_gaps_all)
            top1_covered_count += len(top1_covered)
            top3_covered_count += len(top3_covered)
            top5_covered_count += len(top5_covered)
            total_courses_recommended += len(essential_courses)
            total_relevant_courses += relevant_courses_count
            total_certs_recommended += len(recommended_certs)
            total_relevant_certs += relevant_certs_count

        eval_records.append({
            "profile_id": profile_id,
            "target_career": target_career_name,
            "missing_skills_count": num_missing,
            "missing_skills": missing_skills,
            "covered_skills_count": len(covered_gaps_all),
            "gap_coverage_rate_percent": round(coverage_rate, 2),
            "top1_coverage_percent": round(top1_cov, 2),
            "top3_coverage_percent": round(top3_cov, 2),
            "top5_coverage_percent": round(top5_cov, 2),
            "courses_recommended_count": len(essential_courses),
            "course_relevance_rate_percent": round(relevance_rate, 2),
            "certs_recommended_count": len(recommended_certs),
            "cert_relevance_rate_percent": round(cert_relevance_rate, 2),
        })

    # Overall Summary Aggregation
    overall_coverage = (
        (total_covered_skills_count / total_missing_skills_count * 100.0)
        if total_missing_skills_count > 0 else 100.0
    )
    overall_top1_coverage = (
        (top1_covered_count / total_missing_skills_count * 100.0)
        if total_missing_skills_count > 0 else 100.0
    )
    overall_top3_coverage = (
        (top3_covered_count / total_missing_skills_count * 100.0)
        if total_missing_skills_count > 0 else 100.0
    )
    overall_top5_coverage = (
        (top5_covered_count / total_missing_skills_count * 100.0)
        if total_missing_skills_count > 0 else 100.0
    )
    overall_course_relevance = (
        (total_relevant_courses / total_courses_recommended * 100.0)
        if total_courses_recommended > 0 else 100.0
    )
    overall_cert_relevance = (
        (total_relevant_certs / total_certs_recommended * 100.0)
        if total_certs_recommended > 0 else 100.0
    )

    macro_gap_coverage = sum(r["gap_coverage_rate_percent"] for r in eval_records) / len(eval_records)
    macro_top1_coverage = sum(r["top1_coverage_percent"] for r in eval_records) / len(eval_records)
    macro_top3_coverage = sum(r["top3_coverage_percent"] for r in eval_records) / len(eval_records)
    macro_top5_coverage = sum(r["top5_coverage_percent"] for r in eval_records) / len(eval_records)

    result_data = {
        "summary": {
            "total_profiles_evaluated": len(eval_records),
            "total_missing_skills": total_missing_skills_count,
            "overall_gap_coverage_percent": round(overall_coverage, 2),
            "macro_gap_coverage_percent": round(macro_gap_coverage, 2),
            "top1_course_coverage_percent": round(overall_top1_coverage, 2),
            "top3_course_coverage_percent": round(overall_top3_coverage, 2),
            "top5_course_coverage_percent": round(overall_top5_coverage, 2),
            "course_relevance_percent": round(overall_course_relevance, 2),
            "certification_relevance_percent": round(overall_cert_relevance, 2),
        },
        "per_profile_results": eval_records,
        "limitations": (
            "Course recommendations depend on the 67 curated courses in courses.csv. "
            "Highly specialized or newly emerging sub-skills may rely on general category courses."
        ),
    }

    # Export JSON
    json_path = os.path.join(RESULTS_DIR, "course_recs_evaluation.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result_data, f, indent=2)

    # Export CSV
    csv_path = os.path.join(RESULTS_DIR, "course_recs_summary.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Profile ID", "Target Career", "Missing Skills Count",
            "Covered Skills Count", "Gap Coverage (%)", "Top-1 Coverage (%)",
            "Top-3 Coverage (%)", "Top-5 Coverage (%)", "Course Relevance (%)", "Cert Relevance (%)"
        ])
        for r in eval_records:
            writer.writerow([
                r["profile_id"], r["target_career"], r["missing_skills_count"],
                r["covered_skills_count"], r["gap_coverage_rate_percent"],
                r["top1_coverage_percent"], r["top3_coverage_percent"],
                r["top5_coverage_percent"], r["course_relevance_rate_percent"],
                r["cert_relevance_rate_percent"]
            ])

    return result_data


if __name__ == "__main__":
    res = evaluate_course_recommendations()
    print("=== COURSE RECOMMENDATIONS EVALUATION ===")
    print(json.dumps(res["summary"], indent=2))
