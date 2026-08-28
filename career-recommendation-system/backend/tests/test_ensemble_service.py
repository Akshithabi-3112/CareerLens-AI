"""Reproducible checks for the experimental synthetic-profile ensemble.

Run from backend with:
    venv\\Scripts\\python.exe -m tests.test_ensemble_service
"""

from app.services.ensemble_service import (
    generate_synthetic_profiles,
    get_ensemble_model,
    get_ensemble_predictions,
)


model = get_ensemble_model()
predictions = get_ensemble_predictions(
    ["Python", "SQL", "Machine Learning", "Pandas"]
)

assert model["sample_count"] == model["career_label_count"] * 32
expected_keys = {
    "random_forest_accuracy",
    "gradient_boosting_accuracy",
    "ensemble_accuracy",
    "ensemble_macro_f1",
}
assert expected_keys.issubset(set(model["metrics"]))
assert predictions["ensemble_analysis"]["status"] == "experimental"
assert predictions["career_probabilities"]

# ── Regression checks for probability alignment ───────────────────────────
top_preds = predictions["ensemble_analysis"]["top_predictions"]
assert len(top_preds) > 0, "Top predictions should not be empty"

for pred in top_preds:
    career = pred["career"]
    conf = pred["confidence"]
    rf_p = pred["rf_probability"]
    gb_p = pred["gb_probability"]
    
    # Assert RF and GB probabilities are not 0% for high-confidence predictions
    if conf > 5.0:
        assert rf_p > 0.0 or gb_p > 0.0, f"Expected non-zero RF or GB probability for {career} with {conf}% confidence"
    
    # Assert soft voting consistency: ensemble is approximately the mean of RF and GB
    expected_ens = round((rf_p + gb_p) / 2.0, 2)
    assert abs(conf - expected_ens) <= 0.05, (
        f"Ensemble probability {conf}% for {career} does not match average of RF ({rf_p}%) and GB ({gb_p}%)"
    )

print("Synthetic sample count:", model["sample_count"])
print("Synthetic-only metrics:", model["metrics"])
print("Top ensemble careers:", sorted(
    predictions["career_probabilities"].items(),
    key=lambda item: item[1]["ensemble_probability"],
    reverse=True,
)[:5])
print("Ensemble top predictions verified with consistent RF/GB alignment.")
