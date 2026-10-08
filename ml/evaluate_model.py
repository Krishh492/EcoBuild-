"""
EcoBuild – ML Evaluation Module
Usage : python ml/evaluate_model.py [--heating] [--cooling] [--all]

Loads the saved models and feature_metadata.json, then re-evaluates
on any set of samples supplied via stdin as a JSON array, or (default)
runs a quick sanity-check using the saved test metrics.
"""

import argparse
import json
import sys
from pathlib import Path

import joblib
import numpy as np

ROOT       = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT / "models"


def load_artifacts():
    heat_model  = joblib.load(MODELS_DIR / "heating_model.joblib")
    cool_model  = joblib.load(MODELS_DIR / "cooling_model.joblib")
    with open(MODELS_DIR / "feature_metadata.json") as f:
        metadata = json.load(f)
    with open(MODELS_DIR / "model_metrics.json") as f:
        metrics = json.load(f)
    return heat_model, cool_model, metadata, metrics


def validate_input(sample: dict, metadata: dict) -> np.ndarray:
    """Validate a single input dict against feature metadata and return a row vector."""
    row = []
    for feat in metadata["feature_order"]:
        if feat not in sample:
            raise ValueError(f"Missing feature: '{feat}'")
        val = float(sample[feat])
        # find feature spec
        spec = next(s for s in metadata["features"] if s["name"] == feat)
        if val < spec["min"] or val > spec["max"]:
            print(f"  WARNING: '{feat}' value {val} is outside training range "
                  f"[{spec['min']}, {spec['max']}]", file=sys.stderr)
        if "valid_values" in spec and int(val) not in spec["valid_values"]:
            print(f"  WARNING: '{feat}' value {int(val)} not in valid set "
                  f"{spec['valid_values']}", file=sys.stderr)
        row.append(val)
    return np.array(row).reshape(1, -1)


def predict_sample(sample: dict, heat_model, cool_model, metadata: dict) -> dict:
    X = validate_input(sample, metadata)
    return {
        "Heating Load": round(float(heat_model.predict(X)[0]), 4),
        "Cooling Load": round(float(cool_model.predict(X)[0]), 4),
    }


def print_metrics_report(metrics: dict):
    print("\n" + "=" * 60)
    print("SAVED TEST METRICS  (from models/model_metrics.json)")
    print("=" * 60)
    for target in ("heating_load", "cooling_load"):
        m   = metrics[target]
        tm  = m["test_metrics"]
        cvm = m["cross_validation"]
        label = target.replace("_", " ").title()
        print(f"\n  {label}")
        print(f"    Model      : {m['model']}")
        print(f"    CV  MAE    : {cvm['cv_mae']:.4f}")
        print(f"    CV  RMSE   : {cvm['cv_rmse']:.4f}")
        print(f"    CV  R²     : {cvm['cv_r2']:.4f}")
        print(f"    Test MAE   : {tm['mae']:.4f}")
        print(f"    Test RMSE  : {tm['rmse']:.4f}")
        print(f"    Test R²    : {tm['r2']:.4f}")
    print()


def main():
    parser = argparse.ArgumentParser(description="EcoBuild – evaluate saved models")
    parser.add_argument("--predict", metavar="JSON_FILE",
                        help="Path to a JSON file with a list of input samples")
    parser.add_argument("--report", action="store_true", default=True,
                        help="Print saved metrics report (default)")
    args = parser.parse_args()

    heat_model, cool_model, metadata, metrics = load_artifacts()

    if args.predict:
        with open(args.predict) as f:
            samples = json.load(f)
        if isinstance(samples, dict):
            samples = [samples]
        print(f"\nRunning predictions on {len(samples)} sample(s)...")
        for i, sample in enumerate(samples):
            result = predict_sample(sample, heat_model, cool_model, metadata)
            print(f"  Sample {i+1}: {result}")
    else:
        print_metrics_report(metrics)

    print("  Feature order:")
    for i, feat in enumerate(metadata["feature_order"]):
        spec = next(s for s in metadata["features"] if s["name"] == feat)
        line = f"    [{i+1}] {feat:<35} dtype={spec['dtype']}  range=[{spec['min']}, {spec['max']}]"
        if "valid_values" in spec:
            line += f"  valid={spec['valid_values']}"
        print(line)
    print()


if __name__ == "__main__":
    main()
