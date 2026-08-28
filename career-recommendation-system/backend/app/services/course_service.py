"""Course and certification recommendation service for closing skill gaps.

Maps identified missing skills to curated courses, professional specializations,
and industry-recognized certifications with priority scoring based on skill criticality.
"""

import csv
import os
from functools import lru_cache
from typing import Dict, List, Optional

from app.services.skill_normalizer import normalize_skill_name


BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)
COURSES_FILE = os.path.join(BASE_DIR, "data", "courses.csv")

SECTION_EXPLANATION = (
    "Based on your current skills and career goals, completing the following courses and "
    "certifications can help you close your skill gaps, improve your job readiness, and "
    "strengthen your chances for relevant job opportunities."
)


def _load_courses_catalog() -> List[Dict]:
    """Load all available courses from the CSV dataset."""
    if not os.path.exists(COURSES_FILE):
        return []

    catalog = []
    with open(COURSES_FILE, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            skills_covered = [
                normalize_skill_name(s.strip())
                for s in row.get("skills_covered", "").split("|")
                if s.strip()
            ]
            primary_skill = normalize_skill_name(row.get("skill", "").strip())
            if primary_skill and primary_skill not in skills_covered:
                skills_covered.insert(0, primary_skill)

            is_cert = row.get("certification_available", "False").strip().lower() in ("true", "1", "yes")
            course_type = row.get("course_type", "Course").strip()
            cert_name = (
                f"{row.get('course_name', '').strip()} ({course_type})"
                if is_cert or "certificate" in course_type.lower() or "certification" in course_type.lower()
                else None
            )

            catalog.append({
                "skill": primary_skill,
                "course_name": row.get("course_name", "").strip(),
                "provider": row.get("provider", "").strip(),
                "difficulty": row.get("difficulty", "Beginner").strip(),
                "duration": row.get("duration", "4 Weeks").strip(),
                "course_type": course_type,
                "certification_available": is_cert,
                "recommended_certification": cert_name,
                "url": row.get("url", "").strip(),
                "skills_covered": skills_covered,
            })
    return catalog


@lru_cache(maxsize=2)
def get_courses_catalog() -> List[Dict]:
    """Cached accessor for course catalog."""
    return _load_courses_catalog()


def _generate_action_reason(
    skill_name: str,
    course_name: str,
    career_name: Optional[str],
    is_required: bool,
    is_certification: bool,
    difficulty: str,
) -> str:
    """Generate a clear, action-oriented explanation for why this course/cert is recommended."""
    career_str = f"{career_name} roles" if career_name else "target career roles"

    if is_certification:
        return (
            f"This certification can strengthen your {skill_name} credentials and "
            f"improve your eligibility and competitive profile for {career_str}."
        )
    if is_required:
        return (
            f"Complete this course to strengthen your {skill_name} skills, which are critical "
            f"requirements for {career_str}."
        )
    if difficulty.lower() == "advanced":
        return (
            f"Take this advanced course in {skill_name} to deepen your domain expertise "
            f"and qualify for high-impact {career_str}."
        )
    return (
        f"Completing this course will develop your {skill_name} capabilities, improving "
        f"your overall job readiness for {career_str}."
    )


def recommend_courses_for_gaps(
    missing_skills: List[str],
    career_name: Optional[str] = None,
    required_missing_skills: Optional[List[str]] = None,
    matched_skills: Optional[List[str]] = None,
    top_n: int = 8,
) -> Dict:
    """Recommend prioritized courses and certifications matching identified skill gaps.

    Prioritizes in strict order:
    1. Critical missing skills required for the target job
    2. Important skills that significantly improve job readiness
    3. Certifications that improve the user's professional profile
    4. Advanced or optional skills / Specializations

    If there are no missing skills, provides advanced specialization courses and
    industry certifications to help the user strengthen their profile and access
    higher-level opportunities.
    """
    catalog = get_courses_catalog()

    # Case: No missing skills -> Recommend Advanced Specializations & Career Certifications
    if not missing_skills:
        career_keywords = set()
        if career_name:
            for word in career_name.lower().replace("-", " ").split():
                if len(word) > 2 and word not in ("developer", "engineer", "specialist", "analyst"):
                    career_keywords.add(word)

        matched_set = {normalize_skill_name(s).lower() for s in (matched_skills or [])}

        advanced_list = []
        for course in catalog:
            course_skills_norm = [s.lower() for s in course["skills_covered"]]
            has_career_match = any(
                kw in course["course_name"].lower() or any(kw in sk for sk in course_skills_norm)
                for kw in career_keywords
            )
            has_matched_skill = any(sk in matched_set for sk in course_skills_norm)

            if has_career_match or has_matched_skill or course["difficulty"].lower() == "advanced":
                score = 70.0
                if course["certification_available"]:
                    score += 15.0
                if course["difficulty"].lower() == "advanced":
                    score += 10.0
                if has_career_match:
                    score += 10.0

                reason = (
                    f"This advanced program in {course['skill']} strengthens your professional portfolio "
                    f"and accelerates your qualification for senior {career_name or 'target'} opportunities."
                )

                item = {
                    "missing_skill": course["skill"],
                    "course_name": course["course_name"],
                    "provider": course["provider"],
                    "difficulty": course["difficulty"],
                    "duration": course["duration"],
                    "course_type": course["course_type"],
                    "certification_available": course["certification_available"],
                    "recommended_certification": course["recommended_certification"] or (
                        f"{course['course_name']} Certificate" if course["certification_available"] else None
                    ),
                    "why_recommended": reason,
                    "skills_gained": course["skills_covered"],
                    "skills_covered": course["skills_covered"],
                    "relevance_score": min(98, int(score)),
                    "priority_tier": "Advanced Specialization",
                    "recommendation_category": "Advanced Learning",
                    "url": course["url"],
                    "is_certification": course["certification_available"],
                }
                advanced_list.append(item)

        advanced_list.sort(key=lambda x: (x["relevance_score"], x["is_certification"]), reverse=True)
        seen = set()
        unique_adv = []
        for item in advanced_list:
            if item["course_name"] not in seen:
                seen.add(item["course_name"])
                unique_adv.append(item)

        certs = [c for c in unique_adv if c["certification_available"]][:4]
        courses = [c for c in unique_adv if not c["certification_available"]][:top_n]
        if not courses and unique_adv:
            courses = unique_adv[:top_n]

        return {
            "has_missing_skills": False,
            "section_explanation": (
                "Your profile satisfies the core skill prerequisites for this role! To further "
                "strengthen your profile, increase your market value, and access senior-level opportunities, "
                "we recommend these advanced specializations and certifications:"
            ),
            "total_courses_recommended": len(courses) + len(certs),
            "essential_courses": courses,
            "recommended_certifications": certs,
            "advanced_resources": [c for c in unique_adv if c["difficulty"].lower() == "advanced"][:4],
            "skill_course_map": {},
            "summary": (
                f"No missing skill gaps found for {career_name or 'this career'}. "
                f"Recommending {len(courses)} advanced courses and {len(certs)} industry certifications to elevate your profile."
            ),
        }

    # Case: Missing skills exist -> Prioritized mapping
    normalized_missing = {
        normalize_skill_name(s).lower(): s
        for s in missing_skills
        if s and s.strip()
    }
    required_set = {
        normalize_skill_name(s).lower()
        for s in (required_missing_skills or missing_skills)
        if s and s.strip()
    }

    scored_courses = []
    skill_course_map: Dict[str, List[Dict]] = {s: [] for s in missing_skills}

    for course in catalog:
        course_skills_normalized = [s.lower() for s in course["skills_covered"]]
        primary_skill_norm = course["skill"].lower()

        # Find matching missing skills covered by this course
        matched_gaps = [
            normalized_missing[sk]
            for sk in course_skills_normalized
            if sk in normalized_missing
        ]

        if not matched_gaps:
            continue

        # Priority scoring calculation (Prioritize 1. Critical -> 2. Important -> 3. Certifications -> 4. Advanced)
        score = 50.0
        is_critically_required = any(g.lower() in required_set for g in matched_gaps)
        is_primary_target = primary_skill_norm in normalized_missing

        if is_primary_target:
            score += 20.0
            if primary_skill_norm in required_set:
                score += 18.0  # Critical required skill highest boost
            else:
                score += 10.0  # Important skill

        # Multi-skill coverage bonus: +8 pts per additional covered missing skill
        score += len(matched_gaps) * 8.0

        # Certification available bonus (+10 pts)
        if course["certification_available"]:
            score += 10.0

        # Difficulty bonus (Beginner/Intermediate progression)
        diff = course["difficulty"].lower()
        if diff == "beginner":
            score += 4.0
        elif diff == "intermediate":
            score += 3.0

        # Determine priority tier
        if is_critically_required:
            priority_tier = "Critical Missing Skill"
        elif course["certification_available"]:
            priority_tier = "Professional Certification"
        elif diff == "advanced":
            priority_tier = "Advanced Specialization"
        else:
            priority_tier = "Important Job Readiness"

        target_missing_skill = matched_gaps[0] if matched_gaps else course["skill"]
        action_reason = _generate_action_reason(
            skill_name=target_missing_skill,
            course_name=course["course_name"],
            career_name=career_name,
            is_required=is_critically_required,
            is_certification=course["certification_available"],
            difficulty=course["difficulty"],
        )

        cert_name = course["recommended_certification"]
        if course["certification_available"] and not cert_name:
            cert_name = f"{course['course_name']} Certificate"

        scored_item = {
            "missing_skill": target_missing_skill,
            "course_name": course["course_name"],
            "provider": course["provider"],
            "difficulty": course["difficulty"],
            "duration": course["duration"],
            "course_type": course["course_type"],
            "certification_available": course["certification_available"],
            "recommended_certification": cert_name,
            "why_recommended": action_reason,
            "skills_gained": course["skills_covered"],
            "skills_covered": course["skills_covered"],
            "relevance_score": min(99, int(score)),
            "priority_tier": priority_tier,
            "recommendation_category": "Skill Gap Learning",
            "matched_gaps": matched_gaps,
            "gap_coverage_count": len(matched_gaps),
            "url": course["url"],
            "is_certification": course["certification_available"],
        }
        scored_courses.append(scored_item)

        # Populate per-skill lookup for Roadmap / Detail Views
        for gap in matched_gaps:
            if len(skill_course_map[gap]) < 3:
                skill_course_map[gap].append({
                    "missing_skill": gap,
                    "course_name": course["course_name"],
                    "provider": course["provider"],
                    "difficulty": course["difficulty"],
                    "duration": course["duration"],
                    "skills_gained": course["skills_covered"],
                    "recommended_certification": cert_name,
                    "why_recommended": action_reason,
                    "relevance_score": min(99, int(score)),
                    "priority_tier": priority_tier,
                    "recommendation_category": "Skill Gap Learning",
                    "url": course["url"],
                    "is_certification": course["certification_available"],
                })

    # Sort scored courses descending by relevance score
    scored_courses.sort(
        key=lambda x: (
            x["priority_tier"] == "Critical Missing Skill",
            x["relevance_score"],
            x["gap_coverage_count"]
        ),
        reverse=True
    )

    # Separate into structured categories
    essential_courses = []
    recommended_certifications = []
    advanced_resources = []
    seen_names = set()

    for item in scored_courses:
        if item["course_name"] in seen_names:
            continue
        seen_names.add(item["course_name"])

        # Categorize into Certifications vs Courses
        if item["certification_available"] or item["course_type"] in ("Certification", "Professional Certificate"):
            if len(recommended_certifications) < 5:
                recommended_certifications.append(item)

        if item["difficulty"].lower() == "advanced" or item["course_type"] == "Specialization":
            if len(advanced_resources) < 4:
                advanced_resources.append(item)

        if len(essential_courses) < top_n:
            essential_courses.append(item)

    covered_gaps = {g for c in scored_courses for g in c.get("matched_gaps", [])}
    summary = (
        f"Identified {len(essential_courses)} prioritized courses and {len(recommended_certifications)} "
        f"certifications covering {len(covered_gaps)} of {len(missing_skills)} missing skills for "
        f"{career_name or 'your target career'}."
    )

    return {
        "has_missing_skills": True,
        "section_explanation": SECTION_EXPLANATION,
        "total_courses_recommended": len(essential_courses) + len(recommended_certifications),
        "essential_courses": essential_courses,
        "recommended_certifications": recommended_certifications,
        "advanced_resources": advanced_resources,
        "skill_course_map": {k: v for k, v in skill_course_map.items() if v},
        "summary": summary,
    }
