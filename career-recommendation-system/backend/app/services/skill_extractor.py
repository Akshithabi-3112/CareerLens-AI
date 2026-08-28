import os
import re
import csv
from collections import defaultdict


BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)

SKILLS_FILE = os.path.join(
    BASE_DIR,
    "data",
    "skills.csv"
)


def load_skills():
    skills_data = []

    if not os.path.exists(SKILLS_FILE):
        raise FileNotFoundError(
            f"Skills dataset not found: {SKILLS_FILE}"
        )

    with open(
        SKILLS_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:
            aliases = []

            if row.get("aliases"):
                aliases = row["aliases"].split("|")

            skills_data.append({
                "skill": row["skill"].strip(),
                "category": row["category"].strip(),
                "aliases": [
                    alias.strip().lower()
                    for alias in aliases
                    if alias.strip()
                ]
            })

    return skills_data


def find_skill_matches(resume_text, skills_data):
    resume_text_lower = resume_text.lower()

    extracted_skills = []
    skill_categories = defaultdict(list)
    evidence = {}

    for skill_info in skills_data:

        skill = skill_info["skill"]
        category = skill_info["category"]

        search_terms = [
            skill.lower()
        ] + skill_info["aliases"]

        for term in search_terms:

            if not term:
                continue

            pattern = (
                r"(?<!\w)"
                + re.escape(term)
                + r"(?!\w)"
            )

            match = re.search(
                pattern,
                resume_text_lower
            )

            if match:

                if skill not in extracted_skills:

                    extracted_skills.append(skill)

                    skill_categories[
                        category
                    ].append(skill)

                    start = max(
                        0,
                        match.start() - 50
                    )

                    end = min(
                        len(resume_text),
                        match.end() + 50
                    )

                    evidence[skill] = (
                        resume_text[start:end]
                        .strip()
                    )

                break

    return (
        extracted_skills,
        dict(skill_categories),
        evidence
    )


def calculate_confidence(
    extracted_skills,
    evidence
):

    if not extracted_skills:
        return 0.0

    evidence_score = min(
        len(evidence)
        / len(extracted_skills),
        1.0
    )

    confidence = (
        0.70
        + (0.30 * evidence_score)
    )

    return round(confidence, 2)


def extract_skills(resume_text):

    if (
        not resume_text
        or not resume_text.strip()
    ):
        return {
            "extracted_skills": [],
            "skill_categories": {},
            "evidence": {},
            "extraction_confidence": 0.0
        }

    skills_data = load_skills()

    (
        extracted_skills,
        skill_categories,
        evidence
    ) = find_skill_matches(
        resume_text,
        skills_data
    )

    confidence = calculate_confidence(
        extracted_skills,
        evidence
    )

    return {
        "extracted_skills": extracted_skills,
        "skill_categories": skill_categories,
        "evidence": evidence,
        "extraction_confidence": confidence
    }