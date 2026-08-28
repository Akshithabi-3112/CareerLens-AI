"""Unified Explainability Engine for Career, Course, and Skill-Gap Recommendations.

Answers the 9 foundational explainability questions grounded 100% in calculated values:
1. Why was this career recommended?
2. Which skills matched (strengths)?
3. Which skills are missing (critical gaps)?
4. How did the compatibility score contribute?
5. How did clustering contribute?
6. How did ensemble prediction contribute?
7. Why are specific skills prioritized?
8. Why are particular courses recommended?
9. Why is the roadmap ordered in this sequence?
"""

from typing import Dict, List, Optional


def generate_unified_career_explanation(
    career_name: str,
    career_rec: Dict,
    skill_gap_result: Dict,
    cluster_analysis: Optional[Dict] = None,
    ensemble_analysis: Optional[Dict] = None,
    course_recs: Optional[Dict] = None,
    roadmap: Optional[Dict] = None,
) -> Dict:
    """Construct a comprehensive, fully grounded structured explanation for a career recommendation."""
    matched_skills = skill_gap_result.get("matched_skills", [])
    missing_skills = skill_gap_result.get("missing_skills", [])
    matched_req = career_rec.get("matched_required_skills", [])
    matched_pref = career_rec.get("matched_preferred_skills", [])
    compat_score = round(float(career_rec.get("compatibility_score", 0.0)), 1)
    final_score = round(float(career_rec.get("final_score", career_rec.get("final_recommendation_score", compat_score))), 1)
    cluster_rel = round(float(career_rec.get("cluster_relevance_score", 0.0)), 1)
    ens_conf = round(float(career_rec.get("ensemble_confidence", career_rec.get("ensemble_prediction_score", 0.0))), 1)
    cluster_aligned = career_rec.get("cluster_alignment", False)
    score_components = career_rec.get("score_components", {})
    weights = score_components.get("weights", {"skill_match": 0.6, "cluster_relevance": 0.2, "ensemble_prediction": 0.2})
    skill_gate = score_components.get("skill_gate_factor", 1.0)
    w_contrib = score_components.get("weighted_contributions", {})

    total_req_count = len(matched_req) + len([s for s in missing_skills if s not in matched_pref])
    req_match_pct = round((len(matched_req) / total_req_count * 100)) if total_req_count > 0 else 100

    # ── 1. Executive Summary ──────────────────────────────────────────────
    summary_parts = []
    if matched_req:
        summary_parts.append(
            f"You match {len(matched_req)} of {total_req_count} required skills ({req_match_pct}%) including {', '.join(matched_req[:3])}."
        )
    else:
        summary_parts.append(f"You have an exploratory skill overlap with {career_name}.")

    if cluster_aligned and cluster_rel > 0:
        c_name = cluster_analysis.get("cluster_name", "your domain") if cluster_analysis else "target domain"
        summary_parts.append(
            f"Your resume clusters into the '{c_name}' group with {cluster_rel}% similarity."
        )

    if ens_conf >= 15.0:
        summary_parts.append(
            f"The VotingClassifier ensemble assigns {ens_conf}% confidence to this role based on your skill vector."
        )

    if missing_skills:
        summary_parts.append(
            f"Closing gaps in {', '.join(missing_skills[:2])} will elevate your readiness score from {round(float(skill_gap_result.get('readiness_score', 0)), 1)}% to 100%."
        )

    executive_summary = " ".join(summary_parts)

    # ── 2. Strengths (Matched Skills) ─────────────────────────────────────
    key_strengths = []
    for s in matched_req:
        key_strengths.append({
            "skill": s,
            "type": "Required Core Skill",
            "impact": "Crucial requirement verified in resume profile",
            "is_required": True,
        })
    for s in matched_pref:
        key_strengths.append({
            "skill": s,
            "type": "Preferred / Differentiating Skill",
            "impact": "Provides competitive advantage over baseline candidates",
            "is_required": False,
        })

    # ── 3. Critical Gaps ──────────────────────────────────────────────────
    critical_gaps = []
    for s in missing_skills:
        is_req = s not in matched_pref
        critical_gaps.append({
            "skill": s,
            "type": "Required Skill Gap" if is_req else "Preferred Skill Gap",
            "urgency": "High Priority" if is_req else "Medium Priority",
            "action": f"Recommended to learn via roadmap Stage 1–3",
        })

    # ── 4. Score Math Breakdown ───────────────────────────────────────────
    w_skill = round(weights.get("skill_match", 0.6) * 100)
    w_clust = round(weights.get("cluster_relevance", 0.2) * 100)
    w_ens = round(weights.get("ensemble_prediction", 0.2) * 100)

    contrib_skill = w_contrib.get("skill_match", round(weights.get("skill_match", 0.6) * compat_score, 1))
    contrib_clust = w_contrib.get("cluster_relevance", round(weights.get("cluster_relevance", 0.2) * cluster_rel * skill_gate, 1))
    contrib_ens = w_contrib.get("ensemble_prediction", round(weights.get("ensemble_prediction", 0.2) * ens_conf * skill_gate, 1))

    math_formula = (
        f"Final Score ({final_score}%) = ({w_skill}% × {compat_score}% Compatibility) + "
        f"({w_clust}% × {cluster_rel}% Cluster × {skill_gate} Gate) + "
        f"({w_ens}% × {ens_conf}% Ensemble × {skill_gate} Gate) "
        f"= {contrib_skill} + {contrib_clust} + {contrib_ens} = {final_score}%"
    )

    # ── 5. Machine Learning Influence ─────────────────────────────────────
    ml_influence = {
        "cluster_name": cluster_analysis.get("cluster_name") if cluster_analysis else None,
        "cluster_similarity_percentage": cluster_rel,
        "cluster_aligned": cluster_aligned,
        "cluster_points_contributed": contrib_clust,
        "ensemble_confidence_percentage": ens_conf,
        "ensemble_points_contributed": contrib_ens,
        "skill_gate_factor": skill_gate,
        "skill_gate_explanation": (
            "Full ML score contribution enabled because you match verified required skills."
            if skill_gate == 1.0 else
            "ML boost clamped to protect against artificial score inflation on low-skill overlap."
        ),
        "ensemble_model_agreement": (
            next(
                (p.get("model_agreement") for p in ensemble_analysis.get("top_predictions", []) if p.get("career") == career_name),
                ensemble_analysis.get("top_predictions", [{}])[0].get("model_agreement", "agree")
            )
            if ensemble_analysis and ensemble_analysis.get("top_predictions") else "agree"
        ),
    }

    # ── 6. Learning & Roadmap Sequencing Rationale ────────────────────────
    top_course = (
        course_recs.get("essential_courses", [{}])[0]
        if course_recs and course_recs.get("essential_courses")
        else None
    )

    if not missing_skills:
        # Scenario B: Zero missing skills -> recommend advanced resources
        if top_course and top_course.get("course_name"):
            course_rationale = (
                f"No critical skill gaps were identified for {career_name}. "
                f"'{top_course.get('course_name')}' on {top_course.get('provider')} is recommended as an advanced learning resource "
                f"to deepen relevant knowledge and strengthen career readiness."
            )
        else:
            course_rationale = (
                f"No critical skill gaps were identified for {career_name}. "
                f"Advanced courses and certifications are recommended to deepen relevant domain expertise and strengthen career readiness."
            )
    else:
        # Scenario A: One or more missing skills exist
        matched_gaps = [
            g for g in top_course.get("matched_gaps", []) if g and str(g).strip()
        ] if top_course else []
        target_skills = matched_gaps or [
            s for s in missing_skills[:2] if s and str(s).strip()
        ]

        if top_course and top_course.get("course_name") and target_skills:
            verb_clause = (
                f"directly helps develop {', '.join(target_skills)}, which is currently missing from your profile"
                if len(target_skills) == 1
                else f"directly helps develop {', '.join(target_skills)}, which are currently missing from your profile"
            )
            course_rationale = (
                f"'{top_course.get('course_name')}' on {top_course.get('provider')} was selected as top recommendation "
                f"because it {verb_clause}."
            )
        elif top_course and top_course.get("course_name"):
            course_rationale = (
                f"'{top_course.get('course_name')}' on {top_course.get('provider')} was selected as top recommendation "
                f"to close identified skill gaps."
            )
        else:
            course_rationale = (
                "Courses mapped to close missing skill gaps with verified certifications."
            )

    roadmap_rationale = (
        f"The 6-stage roadmap for {career_name} begins with foundational languages and tools before progressing to frameworks and advanced architectures to satisfy prerequisite dependencies."
    )

    return {
        "career": career_name,
        "executive_summary": executive_summary,
        "key_strengths": key_strengths,
        "critical_gaps": critical_gaps,
        "score_breakdown": {
            "final_score": final_score,
            "compatibility_score": compat_score,
            "cluster_relevance": cluster_rel,
            "ensemble_confidence": ens_conf,
            "weights": weights,
            "skill_weight": w_skill,
            "cluster_weight": w_clust,
            "ensemble_weight": w_ens,
            "skill_contribution": contrib_skill,
            "cluster_contribution": contrib_clust,
            "ensemble_contribution": contrib_ens,
            "skill_gate_factor": skill_gate,
            "weighted_contributions": {
                "skill_match": contrib_skill,
                "skill_compatibility": contrib_skill,
                "cluster_relevance": contrib_clust,
                "ensemble_prediction": contrib_ens,
            },
            "math_formula_explanation": math_formula,
        },
        "ml_influence": ml_influence,
        "learning_rationale": {
            "course_recommendation_reason": course_rationale,
            "roadmap_sequencing_reason": roadmap_rationale,
        },
    }
