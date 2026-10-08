"""
EcoBuild - ML Training Pipeline
Dataset : UCI Energy Efficiency (ENB2012_data.xlsx)
Targets : Heating Load (Y1), Cooling Load (Y2)
Run     : python ml/train_model.py
"""

import json
import os
import sys
import warnings
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")          # headless - no display required
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, cross_val_score, train_test_split

warnings.filterwarnings("ignore")

# -- Paths ----------------------------------------------------------------------
ROOT        = Path(__file__).resolve().parent.parent
DATASET     = ROOT / "dataset" / "ENB2012_data.xlsx"
MODELS_DIR  = ROOT / "models"
PLOTS_DIR   = ROOT / "plots"
MODELS_DIR.mkdir(exist_ok=True)
PLOTS_DIR.mkdir(exist_ok=True)

# -- Column mapping (UCI ENB2012) -----------------------------------------------
RAW_COLS = ["X1", "X2", "X3", "X4", "X5", "X6", "X7", "X8", "Y1", "Y2"]
FEATURE_NAMES = [
    "Relative Compactness",
    "Surface Area",
    "Wall Area",
    "Roof Area",
    "Overall Height",
    "Orientation",
    "Glazing Area",
    "Glazing Area Distribution",
]
TARGET_NAMES = ["Heating Load", "Cooling Load"]

# Discrete features (integer-valued categories in the dataset)
DISCRETE_FEATURES = {"Orientation", "Glazing Area Distribution"}


# ==============================================================================
# 1. LOAD & INSPECT
# ==============================================================================
def load_and_inspect(path: Path) -> pd.DataFrame:
    print("\n" + "=" * 70)
    print("STEP 1 - DATASET INSPECTION")
    print("=" * 70)

    # Read the first sheet (Greek name "Φύλλο1"); header row present
    df_raw = pd.read_excel(path, sheet_name=0, header=0)

    # Drop fully-empty columns (K, L in the original file)
    df_raw = df_raw.dropna(axis=1, how="all")

    # Keep only the 10 meaningful columns
    df_raw = df_raw.iloc[:, :10]
    df_raw.columns = RAW_COLS

    # Rename to human-readable names
    col_map = dict(zip(RAW_COLS, FEATURE_NAMES + TARGET_NAMES))
    df = df_raw.rename(columns=col_map)

    # -- Shape
    print(f"\nShape          : {df.shape[0]} rows × {df.shape[1]} columns")

    # -- Column names
    print(f"\nColumns        :\n  Features : {FEATURE_NAMES}")
    print(f"  Targets  : {TARGET_NAMES}")

    # -- First 5 rows
    print("\nFirst 5 rows:")
    print(df.head().to_string())

    # -- Data types
    print("\nData types:")
    print(df.dtypes.to_string())

    # -- Missing values
    missing = df.isnull().sum()
    print(f"\nMissing values : {missing.sum()} total")
    if missing.sum() > 0:
        print(missing[missing > 0].to_string())

    # -- Duplicate rows
    dupes = df.duplicated().sum()
    print(f"\nDuplicate rows : {dupes}")

    # -- Min / Max
    print("\nMin / Max values:")
    print(df.agg(["min", "max"]).to_string())

    # -- Unique values for discrete features
    print("\nUnique values for discrete features:")
    for feat in DISCRETE_FEATURES:
        vals = sorted(df[feat].dropna().unique().tolist())
        print(f"  {feat}: {vals}")

    return df


# ==============================================================================
# 2. SPLIT
# ==============================================================================
def split_data(df: pd.DataFrame):
    X = df[FEATURE_NAMES].values
    y_heat = df["Heating Load"].values
    y_cool = df["Cooling Load"].values

    X_train, X_test, yh_train, yh_test, yc_train, yc_test = train_test_split(
        X, y_heat, y_cool, test_size=0.20, random_state=42
    )

    print("\n" + "=" * 70)
    print("STEP 2 - TRAIN / TEST SPLIT  (80 / 20, random_state=42)")
    print("=" * 70)
    print(f"  Training samples : {X_train.shape[0]}")
    print(f"  Test samples     : {X_test.shape[0]}")

    return X_train, X_test, yh_train, yh_test, yc_train, yc_test


# ==============================================================================
# 3. CROSS-VALIDATE CANDIDATES
# ==============================================================================
CANDIDATES = {
    "LinearRegression":         LinearRegression(),
    "RandomForestRegressor":    RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1),
    "GradientBoostingRegressor": GradientBoostingRegressor(n_estimators=200, learning_rate=0.1,
                                                            max_depth=4, random_state=42),
}


def cross_validate_candidates(X_train, y_train, target_label: str) -> dict:
    print(f"\n  -- {target_label} --")
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    results = {}

    for name, model in CANDIDATES.items():
        neg_mae  = cross_val_score(model, X_train, y_train, cv=kf,
                                   scoring="neg_mean_absolute_error",   n_jobs=-1)
        neg_rmse = cross_val_score(model, X_train, y_train, cv=kf,
                                   scoring="neg_root_mean_squared_error", n_jobs=-1)
        r2       = cross_val_score(model, X_train, y_train, cv=kf,
                                   scoring="r2",                          n_jobs=-1)

        mae  = -neg_mae.mean()
        rmse = -neg_rmse.mean()
        r2m  = r2.mean()

        results[name] = {"cv_mae": mae, "cv_rmse": rmse, "cv_r2": r2m}
        print(f"    {name:<35}  MAE={mae:.4f}  RMSE={rmse:.4f}  R²={r2m:.4f}")

    # Best by lowest CV RMSE
    best_name = min(results, key=lambda k: results[k]["cv_rmse"])
    print(f"    → Best : {best_name}")
    return best_name, results


# ==============================================================================
# 4. TRAIN BEST MODEL ON FULL TRAINING SET
# ==============================================================================
def train_best(best_name: str, X_train, y_train):
    import copy
    model = copy.deepcopy(CANDIDATES[best_name])
    model.fit(X_train, y_train)
    return model


# ==============================================================================
# 5. EVALUATE ON HELD-OUT TEST SET (ONCE)
# ==============================================================================
def evaluate_on_test(model, X_test, y_test, label: str) -> dict:
    y_pred = model.predict(X_test)
    mae  = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2   = r2_score(y_test, y_pred)
    print(f"\n  {label} - Test Set Evaluation")
    print(f"    MAE  = {mae:.4f}")
    print(f"    RMSE = {rmse:.4f}")
    print(f"    R²   = {r2:.4f}")
    return {"mae": round(mae, 6), "rmse": round(rmse, 6), "r2": round(r2, 6)}


# ==============================================================================
# 6. PLOTS
# ==============================================================================
def plot_actual_vs_predicted(model, X_test, y_test, label: str, filename: str):
    y_pred = model.predict(X_test)

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.scatter(y_test, y_pred, alpha=0.5, s=20, color="#3b82d4", edgecolors="none")
    lims = [min(y_test.min(), y_pred.min()) - 1, max(y_test.max(), y_pred.max()) + 1]
    ax.plot(lims, lims, "r--", linewidth=1, label="Perfect fit")
    ax.set_xlabel("Actual")
    ax.set_ylabel("Predicted")
    ax.set_title(f"{label} - Actual vs Predicted")
    ax.legend(fontsize=8)
    plt.tight_layout()
    out = PLOTS_DIR / filename
    plt.savefig(out, dpi=120)
    plt.close()
    print(f"    Saved plot: {out}")


def plot_feature_importance(model, label: str, filename: str):
    if not hasattr(model, "feature_importances_"):
        print(f"    {label}: feature importances not supported - skipping.")
        return

    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]
    sorted_names = [FEATURE_NAMES[i] for i in indices]
    sorted_vals  = importances[indices]

    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.barh(sorted_names[::-1], sorted_vals[::-1], color="#3b82d4")
    ax.set_xlabel("Importance")
    ax.set_title(f"{label} - Feature Importances")
    plt.tight_layout()
    out = PLOTS_DIR / filename
    plt.savefig(out, dpi=120)
    plt.close()
    print(f"    Saved plot: {out}")


# ==============================================================================
# 7. SAVE METADATA
# ==============================================================================
def build_feature_metadata(df: pd.DataFrame) -> dict:
    features = []
    for feat in FEATURE_NAMES:
        col = df[feat]
        entry = {
            "name":  feat,
            "dtype": "float64" if feat not in DISCRETE_FEATURES else "int64",
            "min":   float(col.min()),
            "max":   float(col.max()),
        }
        if feat in DISCRETE_FEATURES:
            entry["valid_values"] = sorted([int(v) for v in col.dropna().unique()])
        features.append(entry)

    return {
        "feature_order": FEATURE_NAMES,
        "features":      features,
        "targets":       TARGET_NAMES,
    }


# ==============================================================================
# MAIN
# ==============================================================================
def main():
    print("\n" + "+" + "=" * 68 + "+")
    print("|" + "  EcoBuild ML Training Pipeline".center(68) + "|")
    print("+" + "=" * 68 + "+")

    # 1. Load & inspect
    df = load_and_inspect(DATASET)

    # 2. Split
    X_train, X_test, yh_train, yh_test, yc_train, yc_test = split_data(df)

    # 3. Cross-validate candidates
    print("\n" + "=" * 70)
    print("STEP 3 - 5-FOLD CROSS-VALIDATION ON TRAINING SET")
    print("=" * 70)
    heat_best_name, heat_cv = cross_validate_candidates(X_train, yh_train, "Heating Load")
    cool_best_name, cool_cv = cross_validate_candidates(X_train, yc_train, "Cooling Load")

    # 4. Train best models on full training data
    print("\n" + "=" * 70)
    print("STEP 4 - TRAIN BEST MODELS ON FULL TRAINING SET")
    print("=" * 70)
    print(f"  Heating Load model : {heat_best_name}")
    print(f"  Cooling Load model : {cool_best_name}")

    heat_model = train_best(heat_best_name, X_train, yh_train)
    cool_model = train_best(cool_best_name, X_train, yc_train)

    # 5. Final evaluation on held-out test set (ONCE)
    print("\n" + "=" * 70)
    print("STEP 5 - FINAL TEST SET EVALUATION (held-out, evaluated once)")
    print("=" * 70)
    heat_metrics = evaluate_on_test(heat_model, X_test, yh_test, "Heating Load")
    cool_metrics = evaluate_on_test(cool_model, X_test, yc_test, "Cooling Load")

    # 6. Plots
    print("\n" + "=" * 70)
    print("STEP 6 - PLOTS")
    print("=" * 70)
    plot_actual_vs_predicted(heat_model, X_test, yh_test,
                             "Heating Load", "heating_actual_vs_predicted.png")
    plot_actual_vs_predicted(cool_model, X_test, yc_test,
                             "Cooling Load", "cooling_actual_vs_predicted.png")
    plot_feature_importance(heat_model, "Heating Load", "heating_feature_importance.png")
    plot_feature_importance(cool_model, "Cooling Load", "cooling_feature_importance.png")

    # 7. Save models
    print("\n" + "=" * 70)
    print("STEP 7 - SAVE MODELS & METADATA")
    print("=" * 70)
    joblib.dump(heat_model, MODELS_DIR / "heating_model.joblib")
    joblib.dump(cool_model, MODELS_DIR / "cooling_model.joblib")
    print("  Saved: models/heating_model.joblib")
    print("  Saved: models/cooling_model.joblib")

    # 8. Save metrics JSON
    metrics = {
        "heating_load": {
            "model":          heat_best_name,
            "cross_validation": heat_cv[heat_best_name],
            "test_metrics":   heat_metrics,
        },
        "cooling_load": {
            "model":          cool_best_name,
            "cross_validation": cool_cv[cool_best_name],
            "test_metrics":   cool_metrics,
        },
    }
    with open(MODELS_DIR / "model_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    print("  Saved: models/model_metrics.json")

    # 9. Save feature metadata JSON
    meta = build_feature_metadata(df)
    with open(MODELS_DIR / "feature_metadata.json", "w") as f:
        json.dump(meta, f, indent=2)
    print("  Saved: models/feature_metadata.json")

    # -- Final summary
    print("\n" + "+" + "=" * 68 + "+")
    print("|" + "  TRAINING COMPLETE - SUMMARY".center(68) + "|")
    print("+" + "=" * 68 + "+")
    print(f"\n  Heating Load model : {heat_best_name}")
    print(f"    Test MAE  = {heat_metrics['mae']:.4f}")
    print(f"    Test RMSE = {heat_metrics['rmse']:.4f}")
    print(f"    Test R²   = {heat_metrics['r2']:.4f}")
    print(f"\n  Cooling Load model : {cool_best_name}")
    print(f"    Test MAE  = {cool_metrics['mae']:.4f}")
    print(f"    Test RMSE = {cool_metrics['rmse']:.4f}")
    print(f"    Test R²   = {cool_metrics['r2']:.4f}")

    files_created = [
        "models/heating_model.joblib",
        "models/cooling_model.joblib",
        "models/model_metrics.json",
        "models/feature_metadata.json",
        "plots/heating_actual_vs_predicted.png",
        "plots/cooling_actual_vs_predicted.png",
        "plots/heating_feature_importance.png",
        "plots/cooling_feature_importance.png",
    ]
    print("\n  Files created:")
    for f in files_created:
        print(f"    {f}")
    print()


if __name__ == "__main__":
    main()
