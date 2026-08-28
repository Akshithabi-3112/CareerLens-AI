"""Personalized dynamic learning roadmap generator.

Constructs a multi-stage career roadmap based on:
1. Missing skills and skill priorities (required vs preferred)
2. Skill prerequisite dependency graph
3. Already matched/completed skills
4. Explainable rationale for stage assignments and unlocking progression.
"""

from typing import Dict, List, Optional, Set
from app.services.skill_normalizer import normalize_skill_name


# ── Dependency Graph (Prerequisite -> Enabled Skills) ─────────────────────
# If Skill A is a prerequisite for Skill B, Skill A must be learned before Skill B.
SKILL_DEPENDENCY_GRAPH = {
    # AI / ML
    "Machine Learning": ["Python", "Mathematics", "Statistics", "Linear Algebra"],
    "Deep Learning": ["Machine Learning", "Python", "Mathematics"],
    "Neural Networks": ["Machine Learning", "Python"],
    "TensorFlow": ["Python", "Machine Learning"],
    "PyTorch": ["Python", "Machine Learning"],
    "Natural Language Processing": ["Python", "Machine Learning", "Deep Learning"],
    "Computer Vision": ["Python", "Machine Learning", "OpenCV"],
    "Scikit-learn": ["Python", "NumPy", "Pandas"],
    "Data Analysis": ["Python", "SQL"],
    "Data Science": ["Python", "SQL", "Statistics", "Data Analysis"],
    "Pandas": ["Python"],
    "NumPy": ["Python"],
    "Matplotlib": ["Python"],
    "Seaborn": ["Python", "Pandas"],
    "Tableau": ["Data Analysis", "SQL"],
    "Power BI": ["Data Analysis", "SQL"],

    # Web / Frontend
    "JavaScript": ["HTML", "CSS"],
    "TypeScript": ["JavaScript"],
    "React": ["JavaScript", "HTML", "CSS"],
    "Next.js": ["React", "JavaScript", "TypeScript"],
    "Vue.js": ["JavaScript", "HTML", "CSS"],
    "Angular": ["TypeScript", "JavaScript", "HTML", "CSS"],
    "Tailwind CSS": ["HTML", "CSS"],
    "Redux": ["React", "JavaScript"],
    "Responsive Design": ["HTML", "CSS"],

    # Backend / Systems
    "Node.js": ["JavaScript"],
    "Express": ["Node.js", "JavaScript"],
    "FastAPI": ["Python", "REST APIs"],
    "Django": ["Python", "SQL"],
    "Flask": ["Python"],
    "Spring Boot": ["Java", "Object-Oriented Programming", "REST APIs"],
    "Microservices": ["Docker", "REST APIs", "Backend Development"],
    "GraphQL": ["REST APIs", "JavaScript"],
    "REST APIs": ["HTTP", "Networking Basics"],

    # Database
    "PostgreSQL": ["SQL", "Database Design"],
    "MySQL": ["SQL", "Database Design"],
    "MongoDB": ["JSON", "Database Concepts"],
    "Redis": ["Database Concepts", "Caching"],
    "Database Design": ["SQL"],

    # DevOps / Cloud
    "Kubernetes": ["Docker", "Linux", "Networking"],
    "Docker": ["Linux", "CLI / Terminal"],
    "CI/CD": ["Git", "Docker"],
    "AWS": ["Cloud Fundamentals", "Networking", "Linux"],
    "Microsoft Azure": ["Cloud Fundamentals", "Networking"],
    "Google Cloud Platform": ["Cloud Fundamentals", "Networking"],
    "Terraform": ["Cloud Fundamentals", "DevOps"],

    # Security
    "Cybersecurity": ["Networking", "Linux", "Operating Systems"],
    "Ethical Hacking": ["Networking", "Linux", "Cybersecurity", "Python"],
    "Penetration Testing": ["Networking", "Linux", "Ethical Hacking"],
    "Network Security": ["Networking", "Cybersecurity"],

    # Mobile
    "Flutter": ["Dart", "Object-Oriented Programming"],
    "React Native": ["React", "JavaScript"],
    "Android App Development": ["Java", "Kotlin"],
    "iOS App Development": ["Swift"],

    # Design
    "UI/UX Design": ["Design Fundamentals", "Wireframing"],
    "Figma": ["UI/UX Design", "Wireframing"],
    "Design Systems": ["Figma", "UI/UX Design", "CSS"],
}

# ── Foundational vs Core vs Advanced Skill Classification ─────────────────
FOUNDATIONAL_SKILLS = {
    "python", "html", "css", "git", "github", "linux", "c", "c++", "java",
    "sql", "mathematics", "statistics", "cli / terminal", "design fundamentals",
    "data structures", "algorithms", "problem solving", "dart", "swift",
}

ADVANCED_SKILLS = {
    "deep learning", "kubernetes", "microservices", "natural language processing",
    "computer vision", "penetration testing", "ethical hacking", "distributed systems",
    "system design", "cloud architecture", "cloud security", "terraform",
}


def _get_skill_prerequisites(skill_name: str) -> List[str]:
    """Return explicit prerequisites for a skill."""
    for key, prereqs in SKILL_DEPENDENCY_GRAPH.items():
        if key.lower() == skill_name.lower():
            return prereqs
    return []


def _calculate_prerequisite_depth(
    skill: str,
    known_skills_set: Set[str],
    visited: Optional[Set[str]] = None,
) -> int:
    """Calculate depth of unmet prerequisites for topological-like stage ordering."""
    if visited is None:
        visited = set()

    skill_lower = skill.lower()
    if skill_lower in known_skills_set or skill_lower in visited:
        return 0

    visited.add(skill_lower)
    prereqs = _get_skill_prerequisites(skill)
    unmet_prereqs = [p for p in prereqs if p.lower() not in known_skills_set]

    if not unmet_prereqs:
        return 1 if skill_lower in FOUNDATIONAL_SKILLS else 2

    max_sub = max(
        (_calculate_prerequisite_depth(p, known_skills_set, visited.copy()) for p in unmet_prereqs),
        default=0,
    )
    return max_sub + 1


def generate_career_roadmap(
    career_name: str,
    missing_skills: List[str],
    matched_skills: Optional[List[str]] = None,
    completed_skills: Optional[List[str]] = None,
    required_skills: Optional[List[str]] = None,
) -> Dict:
    """Generate a dynamic 6-stage personalized learning roadmap.

    Stage 1: Foundation (Languages & Base Tooling)
    Stage 2: Core Skills (Frameworks, Databases & Core Concepts)
    Stage 3: Intermediate Skills (APIs, Tooling & Workflow)
    Stage 4: Projects and Practice (Full-stack / Pipeline Implementation)
    Stage 5: Advanced Skills & Specializations
    Stage 6: Job Readiness & Professional Portfolio
    """
    matched_set = {s.lower() for s in (matched_skills or [])}
    completed_set = {s.lower() for s in (completed_skills or [])}
    known_set = matched_set | completed_set

    req_set = {s.lower() for s in (required_skills or [])}
    normalized_missing = [normalize_skill_name(s) for s in missing_skills if s and s.strip()]

    # Deduplicate while preserving order
    seen = set()
    clean_missing = []
    for s in normalized_missing:
        if s.lower() not in seen and s.lower() not in completed_set:
            seen.add(s.lower())
            clean_missing.append(s)

    # Score and classify each missing skill into a target stage (1..5)
    skill_plan = []
    for skill in clean_missing:
        skill_lower = skill.lower()
        prereqs = _get_skill_prerequisites(skill)
        unmet_prereqs = [p for p in prereqs if p.lower() not in known_set]
        is_required = skill_lower in req_set or not req_set
        depth = _calculate_prerequisite_depth(skill, known_set)

        # Stage determination logic
        if skill_lower in FOUNDATIONAL_SKILLS and not unmet_prereqs:
            stage_num = 1
            stage_name = "Foundation"
        elif depth <= 1 and (is_required or skill_lower in FOUNDATIONAL_SKILLS):
            stage_num = 1 if not unmet_prereqs else 2
            stage_name = "Foundation" if stage_num == 1 else "Core Skills"
        elif depth == 2 or (is_required and not unmet_prereqs):
            stage_num = 2
            stage_name = "Core Skills"
        elif depth == 3 or not is_required:
            stage_num = 3
            stage_name = "Intermediate Skills"
        elif skill_lower in ADVANCED_SKILLS or depth >= 4:
            stage_num = 5
            stage_name = "Advanced Skills"
        else:
            stage_num = 3
            stage_name = "Intermediate Skills"

        # Explainability metadata
        why_prioritized = (
            f"High-priority required skill for {career_name}"
            if is_required
            else f"Recommended preferred skill for {career_name}"
        )
        if unmet_prereqs:
            why_prioritized += f" (Recommended after learning {', '.join(unmet_prereqs[:2])})"

        enables = [
            k for k, deps in SKILL_DEPENDENCY_GRAPH.items()
            if any(d.lower() == skill_lower for d in deps)
        ]
        enables_text = f"Unlocks: {', '.join(enables[:3])}" if enables else "Core role competency"

        skill_plan.append({
            "skill": skill,
            "target_stage": stage_num,
            "stage_name": stage_name,
            "is_required": is_required,
            "unmet_prerequisites": unmet_prereqs,
            "why_prioritized": why_prioritized,
            "enables_next": enables_text,
            "is_completed": skill_lower in completed_set,
        })

    # Sort skills by stage, then required first, then fewer unmet prereqs
    skill_plan.sort(key=lambda x: (x["target_stage"], not x["is_required"], len(x["unmet_prerequisites"])))

    # Assemble 6 Standard Roadmap Stages
    stages = [
        {
            "stage_number": 1,
            "title": "Stage 1 — Foundation",
            "theme": "Core Languages, Tools & Prerequisites",
            "description": f"Master foundational syntax, terminal tools, and fundamental principles required for {career_name}.",
            "skills": [s for s in skill_plan if s["target_stage"] == 1],
            "action_items": [
                "Set up local development environment and version control.",
                "Complete syntax basics, data structures, and core programming paradigms.",
            ],
            "estimated_duration": "2–4 Weeks",
            "status": "in-progress" if any(s["target_stage"] == 1 for s in skill_plan) else "completed",
        },
        {
            "stage_number": 2,
            "title": "Stage 2 — Core Skills",
            "theme": "Essential Role Competencies",
            "description": f"Build fluency in the primary libraries, databases, and frameworks essential for daily {career_name} responsibilities.",
            "skills": [s for s in skill_plan if s["target_stage"] == 2],
            "action_items": [
                "Implement algorithmic problem solving and database design patterns.",
                "Build functional modules demonstrating idiomatic code structure.",
            ],
            "estimated_duration": "3–5 Weeks",
            "status": "pending" if any(s["target_stage"] <= 1 and not s["is_completed"] for s in skill_plan) else "unlocked",
        },
        {
            "stage_number": 3,
            "title": "Stage 3 — Intermediate Skills",
            "theme": "Frameworks, APIs & Ecosystem Tooling",
            "description": f"Integrate backend APIs, modern state/data workflows, and industry-standard architecture for {career_name}.",
            "skills": [s for s in skill_plan if s["target_stage"] == 3],
            "action_items": [
                "Connect frontend/client interfaces with robust backend APIs.",
                "Implement automated testing, logging, and error handling.",
            ],
            "estimated_duration": "3–4 Weeks",
            "status": "pending",
        },
        {
            "stage_number": 4,
            "title": "Stage 4 — Projects and Practice",
            "theme": "End-to-End Real-World Application",
            "description": f"Combine your newly acquired skills to engineer complete, deployment-ready projects tailored to {career_name}.",
            "skills": [s for s in skill_plan if s["target_stage"] == 4],
            "action_items": [
                f"Design and ship a portfolio-grade project solving a real problem in {career_name}.",
                "Write clear documentation, README, and unit tests with CI workflow.",
            ],
            "estimated_duration": "4 Weeks",
            "status": "pending",
        },
        {
            "stage_number": 5,
            "title": "Stage 5 — Advanced Skills",
            "theme": "Production Specialization & Scalability",
            "description": f"Deepen expertise with high-performance architectures, optimization, security, and cloud deployment for {career_name}.",
            "skills": [s for s in skill_plan if s["target_stage"] == 5],
            "action_items": [
                "Optimize performance, scalability, and security configurations.",
                "Explore distributed architectures or advanced domain paradigms.",
            ],
            "estimated_duration": "3–4 Weeks",
            "status": "pending",
        },
        {
            "stage_number": 6,
            "title": "Stage 6 — Job Readiness",
            "theme": "Certifications & Industry Interview Prep",
            "description": f"Prepare for technical interviews, finalize your GitHub portfolio, and achieve recognized industry certifications for {career_name}.",
            "skills": [],
            "action_items": [
                "Refine technical resume and publish live demo links on GitHub.",
                f"Practice mock interview technical screenings for {career_name} roles.",
                "Earn relevant industry certifications to validate your skill gaps closure.",
            ],
            "estimated_duration": "2 Weeks",
            "status": "pending",
        },
    ]

    total_missing = len(clean_missing)
    completed_count = len([s for s in clean_missing if s.lower() in completed_set])
    progress_pct = round((completed_count / total_missing * 100), 1) if total_missing > 0 else 100.0

    return {
        "career": career_name,
        "total_missing_skills": total_missing,
        "completed_skills_count": completed_count,
        "roadmap_progress_percentage": progress_pct,
        "stages": stages,
        "skill_plan": skill_plan,
        "summary": (
            f"Personalized 6-stage roadmap for {career_name} organizing {total_missing} missing skills "
            f"by prerequisite dependencies and priority."
        ),
    }
