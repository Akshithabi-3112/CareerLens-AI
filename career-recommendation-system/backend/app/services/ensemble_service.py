"""Ensemble career predictions from synthetic skill profiles.

The careers dataset supplies one curated skill profile per career, not real
resume-to-career outcomes. This module creates reproducible, simulated
variations of each profile and trains a formal VotingClassifier ensemble.

Production ranking keeps the rule-based matcher as its primary signal.
Ensemble predictions contribute as a weighted secondary signal (default 20%).
"""

import csv
import os
from functools import lru_cache

import numpy as np
from sklearn.ensemble import (
    GradientBoostingClassifier,
    RandomForestClassifier,
    VotingClassifier,
)
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.preprocessing import MultiLabelBinarizer

from app.services.skill_normalizer import normalize_skill_name


# ── Configuration ────────────────────────────────────────────────────────
RANDOM_STATE = 42
SYNTHETIC_PROFILES_PER_CAREER = 32
TEST_FRACTION = 0.25
CROSS_VALIDATION_FOLDS = 5
TOP_FEATURES_COUNT = 10
TOP_PREDICTIONS_COUNT = 5

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
CAREERS_FILE = os.path.join(BASE_DIR, "data", "careers.csv")


# ── Data loading ─────────────────────────────────────────────────────────
def _load_career_profiles():
    """Load labelled, curated career profiles from the existing CSV."""
    profiles = []

    with open(CAREERS_FILE, "r", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            required_skills = [
                normalize_skill_name(skill)
                for skill in row["required_skills"].split("|")
                if skill.strip()
            ]
            preferred_skills = [
                normalize_skill_name(skill)
                for skill in row["preferred_skills"].split("|")
                if skill.strip()
            ]
            profiles.append({
                "career": row["career"].strip(),
                "required_skills": required_skills,
                "preferred_skills": preferred_skills,
            })

    return profiles


# ── Synthetic training data ──────────────────────────────────────────────
def generate_synthetic_profiles(
    profiles,
    profiles_per_career=SYNTHETIC_PROFILES_PER_CAREER,
    random_state=RANDOM_STATE,
):
    """Create deterministic, imperfect resume-like profiles for experiments.

    Required skills are retained more frequently than preferred skills, and a
    small amount of unrelated skill noise is added. These samples are not
    real user data and must not be interpreted as production model evidence.
    """
    random_generator = np.random.default_rng(random_state)
    all_skills = sorted({
        skill
        for profile in profiles
        for skill in (
            profile["required_skills"] + profile["preferred_skills"]
        )
    }, key=str.casefold)

    synthetic_profiles = []
    labels = []

    for profile in profiles:
        career_skills = set(
            profile["required_skills"] + profile["preferred_skills"]
        )
        unrelated_skills = [
            skill for skill in all_skills if skill not in career_skills
        ]

        for _ in range(profiles_per_career):
            selected_skills = [
                skill for skill in profile["required_skills"]
                if random_generator.random() < 0.80
            ]
            selected_skills.extend(
                skill for skill in profile["preferred_skills"]
                if random_generator.random() < 0.45
            )

            if not selected_skills and profile["required_skills"]:
                selected_skills.append(profile["required_skills"][0])

            noise_count = int(random_generator.integers(0, 3))
            if noise_count and unrelated_skills:
                selected_skills.extend(
                    random_generator.choice(
                        unrelated_skills,
                        size=min(noise_count, len(unrelated_skills)),
                        replace=False,
                    ).tolist()
                )

            synthetic_profiles.append(
                sorted(set(selected_skills), key=str.casefold)
            )
            labels.append(profile["career"])

    return synthetic_profiles, labels


# ── Model training ───────────────────────────────────────────────────────
@lru_cache(maxsize=4)
def _train_ensemble_model(dataset_modified_time):
    """Train and cache the VotingClassifier ensemble once per dataset version."""
    profiles = _load_career_profiles()
    synthetic_profiles, labels = generate_synthetic_profiles(profiles)
    vectorizer = MultiLabelBinarizer()
    feature_matrix = vectorizer.fit_transform(synthetic_profiles)

    train_features, test_features, train_labels, test_labels = (
        train_test_split(
            feature_matrix,
            labels,
            test_size=TEST_FRACTION,
            random_state=RANDOM_STATE,
            stratify=labels,
        )
    )

    # ── Individual base models ───────────────────────────────────────
    random_forest = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=RANDOM_STATE,
        n_jobs=1,
    )
    gradient_boosting = GradientBoostingClassifier(
        n_estimators=15,
        learning_rate=0.1,
        max_depth=2,
        random_state=RANDOM_STATE,
    )

    # ── Formal sklearn VotingClassifier (soft voting) ────────────────
    voting_ensemble = VotingClassifier(
        estimators=[
            ("random_forest", random_forest),
            ("gradient_boosting", gradient_boosting),
        ],
        voting="soft",
    )
    voting_ensemble.fit(train_features, train_labels)

    fitted_rf = voting_ensemble.named_estimators_["random_forest"]
    fitted_gb = voting_ensemble.named_estimators_["gradient_boosting"]

    classes = voting_ensemble.classes_
    rf_pred_raw = fitted_rf.predict(test_features)
    gb_pred_raw = fitted_gb.predict(test_features)
    rf_predictions = classes[rf_pred_raw] if np.issubdtype(rf_pred_raw.dtype, np.integer) else rf_pred_raw
    gb_predictions = classes[gb_pred_raw] if np.issubdtype(gb_pred_raw.dtype, np.integer) else gb_pred_raw
    ensemble_predictions = voting_ensemble.predict(test_features)

    metrics = {
        "random_forest_accuracy": round(
            accuracy_score(test_labels, rf_predictions), 4
        ),
        "gradient_boosting_accuracy": round(
            accuracy_score(test_labels, gb_predictions), 4
        ),
        "ensemble_accuracy": round(
            accuracy_score(test_labels, ensemble_predictions), 4
        ),
        "random_forest_macro_f1": round(
            f1_score(test_labels, rf_predictions,
                     average="macro", zero_division=0), 4
        ),
        "gradient_boosting_macro_f1": round(
            f1_score(test_labels, gb_predictions,
                     average="macro", zero_division=0), 4
        ),
        "ensemble_macro_f1": round(
            f1_score(test_labels, ensemble_predictions,
                     average="macro", zero_division=0), 4
        ),
        "ensemble_precision_macro": round(
            precision_score(test_labels, ensemble_predictions,
                            average="macro", zero_division=0), 4
        ),
        "ensemble_recall_macro": round(
            recall_score(test_labels, ensemble_predictions,
                         average="macro", zero_division=0), 4
        ),
    }

    # ── Fast Cross-validation on Random Forest (3 folds) ─────────────
    cv_scores = cross_val_score(
        RandomForestClassifier(n_estimators=80, max_depth=10, random_state=RANDOM_STATE, n_jobs=1),
        feature_matrix,
        labels,
        cv=3,
        scoring="accuracy",
        n_jobs=1,
    )
    metrics["cross_validation_mean_accuracy"] = round(float(cv_scores.mean()), 4)
    metrics["cross_validation_std"] = round(float(cv_scores.std()), 4)
    metrics["cross_validation_folds"] = 3

    # ── Feature importance from Random Forest ────────────────────────
    feature_names = vectorizer.classes_.tolist()
    rf_importances = fitted_rf.feature_importances_
    top_indices = np.argsort(rf_importances)[::-1][:TOP_FEATURES_COUNT]
    top_features = [
        {
            "skill": feature_names[i],
            "importance": round(float(rf_importances[i]), 4),
        }
        for i in top_indices
        if rf_importances[i] > 0
    ]

    # ── Per-class classification report (stored as dict) ─────────────
    report = classification_report(
        test_labels,
        ensemble_predictions,
        output_dict=True,
        zero_division=0,
    )
    per_class_metrics = {
        career: {
            "precision": round(data["precision"], 4),
            "recall": round(data["recall"], 4),
            "f1_score": round(data["f1-score"], 4),
            "support": int(data["support"]),
        }
        for career, data in report.items()
        if career not in ("accuracy", "macro avg", "weighted avg")
    }

    return {
        "vectorizer": vectorizer,
        "voting_ensemble": voting_ensemble,
        "random_forest": fitted_rf,
        "gradient_boosting": fitted_gb,
        "metrics": metrics,
        "top_features": top_features,
        "per_class_metrics": per_class_metrics,
        "sample_count": len(synthetic_profiles),
        "career_label_count": len(profiles),
    }


def get_ensemble_model():
    """Return cached models, refreshing when the careers CSV is modified."""
    dataset_modified_time = os.stat(CAREERS_FILE).st_mtime_ns
    return _train_ensemble_model(dataset_modified_time)


# ── Prediction ───────────────────────────────────────────────────────────
def get_ensemble_predictions(extracted_skills):
    """Return explainable career probabilities for one resume profile."""
    try:
        ensemble_model = get_ensemble_model()
        normalized_skills = [
            normalize_skill_name(skill)
            for skill in extracted_skills
            if skill and skill.strip()
        ]
        known_skills = set(ensemble_model["vectorizer"].classes_)
        normalized_skills = [
            skill for skill in normalized_skills if skill in known_skills
        ]
        feature_vector = ensemble_model["vectorizer"].transform(
            [normalized_skills]
        )

        if not feature_vector.any():
            return {
                "career_probabilities": {},
                "ensemble_analysis": _unavailable_analysis(
                    "No extracted skills overlap with the model features."
                ),
            }

        voting = ensemble_model["voting_ensemble"]
        rf = ensemble_model["random_forest"]
        gb = ensemble_model["gradient_boosting"]

        # ── Per-career probabilities ─────────────────────────────────
        ensemble_classes = voting.classes_.tolist()
        rf_prob_map = _map_model_probabilities(rf, feature_vector, ensemble_classes)
        gb_prob_map = _map_model_probabilities(gb, feature_vector, ensemble_classes)
        ens_prob_map = _map_model_probabilities(voting, feature_vector, ensemble_classes)

        career_probabilities = {}
        for career in ensemble_classes:
            rf_p = rf_prob_map.get(career, 0.0)
            gb_p = gb_prob_map.get(career, 0.0)
            ens_p = ens_prob_map.get(career, 0.0)

            career_probabilities[career] = {
                "random_forest_probability": round(rf_p * 100, 2),
                "gradient_boosting_probability": round(gb_p * 100, 2),
                "ensemble_probability": round(ens_p * 100, 2),
            }

        # ── Top-N predicted careers with agreement info ──────────────
        sorted_careers = sorted(
            career_probabilities.items(),
            key=lambda item: item[1]["ensemble_probability"],
            reverse=True,
        )[:TOP_PREDICTIONS_COUNT]

        top_predictions = []
        for career, scores in sorted_careers:
            rf_rank = _rank_of(career, career_probabilities, "random_forest_probability")
            gb_rank = _rank_of(career, career_probabilities, "gradient_boosting_probability")
            agreement = "agree" if abs(rf_rank - gb_rank) <= 2 else "disagree"

            top_predictions.append({
                "career": career,
                "confidence": scores["ensemble_probability"],
                "rf_probability": scores["random_forest_probability"],
                "gb_probability": scores["gradient_boosting_probability"],
                "rf_rank": rf_rank,
                "gb_rank": gb_rank,
                "model_agreement": agreement,
            })

        # ── Top contributing skills for this prediction ──────────────
        feature_names = ensemble_model["vectorizer"].classes_.tolist()
        rf_importances = rf.feature_importances_
        active_features = feature_vector[0] if isinstance(feature_vector, np.ndarray) else feature_vector.toarray()[0]
        contributing_skills = []

        for i, (is_active, importance) in enumerate(
            zip(active_features, rf_importances)
        ):
            if is_active > 0 and importance > 0:
                contributing_skills.append({
                    "skill": feature_names[i],
                    "importance": round(float(importance), 4),
                })

        contributing_skills.sort(key=lambda x: x["importance"], reverse=True)
        contributing_skills = contributing_skills[:8]

        return {
            "career_probabilities": career_probabilities,
            "ensemble_analysis": {
                "status": "experimental",
                "training_data": (
                    "Synthetic profiles generated from the curated careers "
                    "dataset; no real resume outcomes are available."
                ),
                "model_metrics": ensemble_model["metrics"],
                "top_features": ensemble_model["top_features"],
                "per_class_sample": _top_n_per_class(
                    ensemble_model["per_class_metrics"], 5
                ),
                "sample_count": ensemble_model["sample_count"],
                "top_predictions": top_predictions,
                "contributing_skills": contributing_skills,
                "explanation": (
                    "A scikit-learn VotingClassifier (soft voting) combines "
                    "Random Forest and Gradient Boosting classifiers to rank and "
                    "recommend career roles based on multiple ML signals. "
                    "This is used as a secondary signal alongside "
                    "rule-based skill matching and K-Means clustering."
                ),
            },
        }
    except (OSError, ValueError):
        return {
            "career_probabilities": {},
            "ensemble_analysis": _unavailable_analysis(
                "The ensemble model could not be trained."
            ),
        }


def _map_model_probabilities(model, feature_vector, target_classes):
    """Safely extract class probabilities from a fitted model and map them to target class names (strings)."""
    proba = model.predict_proba(feature_vector)[0]
    model_classes = model.classes_
    prob_map = {}

    for idx, raw_cls in enumerate(model_classes):
        if isinstance(raw_cls, (int, np.integer)):
            cls_idx = int(raw_cls)
            if 0 <= cls_idx < len(target_classes):
                cls_name = target_classes[cls_idx]
                prob_map[cls_name] = float(proba[idx])
        else:
            cls_name = str(raw_cls)
            prob_map[cls_name] = float(proba[idx])

    return prob_map


def _rank_of(career, probabilities, key):
    """Return the 1-indexed rank of a career for a specific model's probability."""
    sorted_careers = sorted(
        probabilities.items(),
        key=lambda item: item[1][key],
        reverse=True,
    )
    for rank, (name, _) in enumerate(sorted_careers, 1):
        if name == career:
            return rank
    return len(probabilities)


def _top_n_per_class(per_class_metrics, n):
    """Return the top-N and bottom-N classes by F1 for a compact summary."""
    sorted_classes = sorted(
        per_class_metrics.items(),
        key=lambda item: item[1]["f1_score"],
        reverse=True,
    )
    if len(sorted_classes) <= n * 2:
        return {k: v for k, v in sorted_classes}

    top = dict(sorted_classes[:n])
    bottom = dict(sorted_classes[-n:])
    top.update(bottom)
    return top


def _unavailable_analysis(reason):
    return {
        "status": "fallback",
        "training_data": "No production supervised training data is available.",
        "model_metrics": {},
        "top_features": [],
        "per_class_sample": {},
        "sample_count": 0,
        "top_predictions": [],
        "contributing_skills": [],
        "explanation": reason,
    }
