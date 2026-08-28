"""Explainable, cached K-Means clustering for career skill profiles."""

import csv
import os
from functools import lru_cache

from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import MultiLabelBinarizer

from app.services.skill_normalizer import normalize_skill_name


RANDOM_STATE = 42
MIN_CLUSTERS = 2
MAX_CLUSTERS = 8
SIMILAR_CAREER_LIMIT = 6

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
CAREERS_FILE = os.path.join(BASE_DIR, "data", "careers.csv")


def _load_career_profiles():
    """Load only the career fields needed to build skill vectors."""
    profiles = []

    with open(CAREERS_FILE, "r", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            skills = [
                normalize_skill_name(skill)
                for field in ("required_skills", "preferred_skills")
                for skill in row.get(field, "").split("|")
                if skill.strip()
            ]

            profiles.append({
                "career": row["career"].strip(),
                "skills": sorted(set(skills), key=str.casefold),
            })

    return profiles


def _select_cluster_count(skill_matrix):
    """Choose K with the strongest cosine silhouette score on sparse skills."""
    profile_count = skill_matrix.shape[0]
    candidate_max = min(MAX_CLUSTERS, profile_count - 1)
    scores = {}

    for cluster_count in range(MIN_CLUSTERS, candidate_max + 1):
        labels = KMeans(
            n_clusters=cluster_count,
            random_state=RANDOM_STATE,
            n_init=20,
        ).fit_predict(skill_matrix)

        scores[cluster_count] = silhouette_score(
            skill_matrix,
            labels,
            metric="cosine",
        )

    selected_count = max(scores, key=scores.get)
    return selected_count, scores


@lru_cache(maxsize=4)
def _train_cluster_model(dataset_modified_time):
    """Train once per dataset version and cache the model for API requests."""
    profiles = _load_career_profiles()
    vectorizer = MultiLabelBinarizer(sparse_output=True)
    skill_matrix = vectorizer.fit_transform(
        [profile["skills"] for profile in profiles]
    )

    cluster_count, silhouette_scores = _select_cluster_count(skill_matrix)
    model = KMeans(
        n_clusters=cluster_count,
        random_state=RANDOM_STATE,
        n_init=20,
    ).fit(skill_matrix)

    labels = model.labels_.tolist()
    skill_frequency = skill_matrix.mean(axis=0).A1

    return {
        "profiles": profiles,
        "vectorizer": vectorizer,
        "model": model,
        "labels": labels,
        "cluster_count": cluster_count,
        "silhouette_scores": silhouette_scores,
        "skill_frequency": skill_frequency,
    }


def get_cluster_model():
    """Return the cached model, retraining automatically after data changes."""
    dataset_modified_time = os.stat(CAREERS_FILE).st_mtime_ns
    return _train_cluster_model(dataset_modified_time)


def _cluster_name(cluster_model, cluster_id):
    """Name a cluster from skills that distinguish it from the full dataset."""
    cluster_center = cluster_model["model"].cluster_centers_[cluster_id]
    skill_lift = cluster_center - cluster_model["skill_frequency"]
    ranked_indices = sorted(
        range(len(skill_lift)),
        key=lambda index: skill_lift[index],
        reverse=True,
    )

    distinguishing_skills = [
        cluster_model["vectorizer"].classes_[index]
        for index in ranked_indices
        if cluster_center[index] > 0
    ][:3]

    if not distinguishing_skills:
        return "Related career group"

    return f"{' / '.join(distinguishing_skills)} careers"


def _cluster_dominant_skills(cluster_model, cluster_id, top_n=5):
    """Return the skills with the highest centroid weight in a cluster."""
    center = cluster_model["model"].cluster_centers_[cluster_id]
    classes = cluster_model["vectorizer"].classes_
    ranked_indices = sorted(
        range(len(center)),
        key=lambda i: center[i],
        reverse=True,
    )
    return [
        classes[i] for i in ranked_indices
        if center[i] > 0
    ][:top_n]


def _career_groups(cluster_model, cluster_id):
    return [
        profile["career"]
        for profile, label in zip(
            cluster_model["profiles"],
            cluster_model["labels"],
        )
        if label == cluster_id
    ]


def analyze_profile_cluster(extracted_skills):
    """Assign a resume skill profile to its nearest career group.

    Cluster identifiers stay internal. The API returns a descriptive name,
    representative careers, and a similarity score instead of a raw label.
    """
    cluster_model = get_cluster_model()
    normalized_skills = [
        normalize_skill_name(skill)
        for skill in extracted_skills
        if skill and skill.strip()
    ]
    profile_vector = cluster_model["vectorizer"].transform(
        [normalized_skills]
    )

    if profile_vector.nnz == 0:
        return {
            "cluster_id": None,
            "cluster_analysis": {
                "cluster_name": "No career group identified",
                "similar_career_group": [],
                "profile_cluster_similarity": 0.0,
                "dominant_skills": [],
                "matched_cluster_skills": [],
                "cluster_count": cluster_model["cluster_count"],
                "explanation": (
                    "None of the extracted skills overlap with the current "
                    "career-skill dataset."
                ),
            },
        }

    cluster_id = int(cluster_model["model"].predict(profile_vector)[0])
    center = cluster_model["model"].cluster_centers_[cluster_id]
    similarity = (
        profile_vector.multiply(center).sum()
        / ((profile_vector.multiply(profile_vector).sum() ** 0.5)
           * ((center * center).sum() ** 0.5))
    )
    similar_careers = _career_groups(cluster_model, cluster_id)
    dominant = _cluster_dominant_skills(cluster_model, cluster_id, top_n=8)
    normalized_set = set(normalized_skills)
    matched_cluster_skills = [s for s in dominant if s in normalized_set]

    cluster_name = _cluster_name(cluster_model, cluster_id)
    if matched_cluster_skills:
        skill_list = ", ".join(matched_cluster_skills[:4])
        explanation = (
            f"Your profile is most similar to the {cluster_name} cluster "
            f"because your resume contains skills such as {skill_list}."
        )
    else:
        explanation = (
            f"Your profile is most similar to the {cluster_name} cluster "
            f"based on overall skill-vector proximity."
        )

    return {
        "cluster_id": cluster_id,
        "cluster_analysis": {
            "cluster_name": cluster_name,
            "similar_career_group": similar_careers[
                :SIMILAR_CAREER_LIMIT
            ],
            "profile_cluster_similarity": round(float(similarity) * 100, 2),
            "dominant_skills": dominant,
            "matched_cluster_skills": matched_cluster_skills,
            "cluster_count": cluster_model["cluster_count"],
            "explanation": explanation,
        },
    }


def get_career_cluster_ids():
    """Return internal career-to-cluster mappings for ranking only."""
    cluster_model = get_cluster_model()
    return {
        profile["career"]: label
        for profile, label in zip(
            cluster_model["profiles"],
            cluster_model["labels"],
        )
    }


def get_all_clusters_overview():
    """Return a human-readable summary of every cluster for explainability."""
    cluster_model = get_cluster_model()
    cluster_count = cluster_model["cluster_count"]
    overview = []

    for cluster_id in range(cluster_count):
        careers = _career_groups(cluster_model, cluster_id)
        overview.append({
            "cluster_id": cluster_id,
            "cluster_name": _cluster_name(cluster_model, cluster_id),
            "dominant_skills": _cluster_dominant_skills(
                cluster_model, cluster_id, top_n=6
            ),
            "careers": careers,
            "career_count": len(careers),
        })

    return {
        "cluster_count": cluster_count,
        "silhouette_scores": cluster_model["silhouette_scores"],
        "best_silhouette_score": round(
            cluster_model["silhouette_scores"].get(cluster_count, 0.0), 4
        ),
        "clusters": overview,
    }
