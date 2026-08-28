"""Canonicalize extracted skill names without changing extraction behavior.

The extractor remains responsible for finding skills in resume text.  This
module is intentionally a post-extraction layer: it consolidates equivalent
names before the results are scored or returned by the API.
"""

from collections import defaultdict


# Keep aliases that are common resume spellings but are not guaranteed to be
# represented identically by every extractor or future data source. Add new
# variants here, pointing them to an existing canonical dataset skill.
SKILL_ALIASES = {
    "react": "React",
    "react.js": "React",
    "reactjs": "React",
    "react js": "React",
    "node": "Node.js",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "node js": "Node.js",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "python": "Python",
    "py": "Python",
    "power bi": "Power BI",
    "powerbi": "Power BI",
}


def _alias_key(skill_name):
    """Return a case-insensitive, whitespace-stable alias lookup key."""
    return " ".join(skill_name.strip().casefold().split())


def normalize_skill_name(skill_name):
    """Return the canonical name for a skill, preserving unknown skills."""
    if not isinstance(skill_name, str):
        return skill_name

    cleaned_name = skill_name.strip()

    if not cleaned_name:
        return cleaned_name

    return SKILL_ALIASES.get(
        _alias_key(cleaned_name),
        cleaned_name
    )


def normalize_skills_result(skills_result):
    """Normalize an extractor result while preserving its public schema.

    Duplicate variants are collapsed in first-seen order. Evidence is kept
    under the canonical key, retaining the first non-empty source snippet for
    that skill. Categories are rebuilt from the normalized skills so they do
    not contain duplicate aliases.
    """
    if not skills_result:
        return skills_result

    extracted_skills = skills_result.get("extracted_skills", [])
    skill_categories = skills_result.get("skill_categories", {})
    evidence = skills_result.get("evidence", {})

    normalized_skills = []
    seen_skills = set()
    original_to_canonical = {}

    for skill in extracted_skills:
        canonical_skill = normalize_skill_name(skill)

        if not canonical_skill:
            continue

        original_to_canonical[skill] = canonical_skill
        canonical_key = _alias_key(canonical_skill)

        if canonical_key not in seen_skills:
            normalized_skills.append(canonical_skill)
            seen_skills.add(canonical_key)

    normalized_categories = defaultdict(list)

    for category, category_skills in skill_categories.items():
        category_seen = set()

        for skill in category_skills:
            canonical_skill = original_to_canonical.get(
                skill,
                normalize_skill_name(skill)
            )
            canonical_key = _alias_key(canonical_skill)

            if canonical_skill and canonical_key not in category_seen:
                normalized_categories[category].append(canonical_skill)
                category_seen.add(canonical_key)

    normalized_evidence = {}

    for original_skill, snippet in evidence.items():
        canonical_skill = original_to_canonical.get(
            original_skill,
            normalize_skill_name(original_skill)
        )

        if canonical_skill and canonical_skill not in normalized_evidence:
            normalized_evidence[canonical_skill] = snippet

    normalized_result = dict(skills_result)
    normalized_result.update({
        "extracted_skills": normalized_skills,
        "skill_categories": dict(normalized_categories),
        "evidence": normalized_evidence,
    })

    return normalized_result
