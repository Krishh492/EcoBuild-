"""
ML predictor — loads the saved joblib models once at import time.
Never retrains; only calls .predict() on the frozen artefacts.
"""
import json
from pathlib import Path

import joblib
import numpy as np

_ROOT = Path(__file__).resolve().parent.parent   # EcoBuild root (parent of ml/)
_MODELS_DIR = _ROOT / "models"

# ── Load once ──────────────────────────────────────────────────────────────────
heating_model = joblib.load(_MODELS_DIR / "heating_model.joblib")
cooling_model = joblib.load(_MODELS_DIR / "cooling_model.joblib")

with open(_MODELS_DIR / "feature_metadata.json") as f:
    METADATA = json.load(f)

FEATURE_ORDER = METADATA["feature_order"]
_FEATURE_MAP = {feat["name"]: feat for feat in METADATA["features"]}

# Model version tag derived from metadata (no version field stored — use hash of order)
MODEL_VERSION = "gbr-v1"


# ── Public API ─────────────────────────────────────────────────────────────────

def get_feature_spec(name: str) -> dict:
    """Return the metadata spec dict for one feature."""
    return _FEATURE_MAP[name]


def validate_and_build_input(form_data: dict) -> tuple[np.ndarray, list[str]]:
    """
    Validate a dict of {feature_name: raw_string_value} against metadata.
    Returns (X_row, errors).
    X_row is a (1, 8) ndarray if valid, else None.
    errors is a list of human-readable error strings.
    """
    errors = []
    row = []

    for name in FEATURE_ORDER:
        spec = _FEATURE_MAP[name]
        raw = form_data.get(name, "").strip()

        if raw == "":
            errors.append(f"{name}: value is required.")
            row.append(None)
            continue

        try:
            val = float(raw)
        except ValueError:
            errors.append(f"{name}: must be a number.")
            row.append(None)
            continue

        # Discrete integer check
        if "valid_values" in spec:
            int_val = int(val)
            if int_val not in spec["valid_values"]:
                errors.append(
                    f"{name}: must be one of {spec['valid_values']} (got {int_val})."
                )
                row.append(None)
                continue
            row.append(float(int_val))
        else:
            # Range check with small tolerance for boundary floats
            lo, hi = spec["min"], spec["max"]
            if val < lo - 1e-9 or val > hi + 1e-9:
                errors.append(
                    f"{name}: must be between {lo} and {hi} (got {val})."
                )
                row.append(None)
                continue
            row.append(val)

    if errors:
        return None, errors

    X = np.array(row, dtype=np.float64).reshape(1, -1)
    return X, []


def predict(X: np.ndarray) -> tuple[float, float]:
    """Run both models on a validated (1, 8) array. Returns (heating, cooling)."""
    heating = float(heating_model.predict(X)[0])
    cooling = float(cooling_model.predict(X)[0])
    return round(heating, 4), round(cooling, 4)
