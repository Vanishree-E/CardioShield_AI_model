"""
train_models.py
----------------
Trains and compares 4 models for heart disease prediction:
Logistic Regression, Random Forest, XGBoost, Neural Network (MLP).

IMPORTANT: XGBoost is saved in its native .json format (not pickled) because
pickled XGBoost models can become unreadable across different xgboost
versions/machines. This script is called automatically by app.py the first
time it runs, so models are always trained fresh with whatever library
versions are installed locally -- no cross-machine compatibility issues.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
)
from xgboost import XGBClassifier

RANDOM_STATE = 42
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
DATA_PATH = os.path.join(BASE_DIR, "data", "heart.csv")

FEATURE_NAMES = [
    "age", "sex", "cp", "trestbps", "chol", "fbs", "restecg",
    "thalach", "exang", "oldpeak", "slope", "ca", "thal"
]

# ---------------------------------------------------------------------------
# Training-data augmentation
# ---------------------------------------------------------------------------
# The UCI Cleveland dataset has ~300 real patient records. That's a fixed,
# well-known public dataset -- this project has no network access and no
# license to pull in additional real patient data from elsewhere, so we
# can't add genuine new records. What we CAN honestly do is give the models
# more *examples to learn from* by bootstrap-resampling the real records and
# adding small, clinically-plausible noise to the continuous fields. This is
# a standard data-augmentation technique (similar in spirit to SMOTE), not a
# source of new information -- it does not manufacture new medical facts, it
# just varies existing patients' numbers slightly so the models don't
# overfit to the exact 240-ish training rows. This is applied to the
# training split ONLY; the held-out test split always stays 100% real,
# un-augmented rows, so reported accuracy/F1/ROC-AUC are still honest.
AUGMENT_TRAINING_DATA = True
AUGMENT_MULTIPLIER = 4          # training rows become roughly this many times larger
NOISE_FRACTION = 0.03           # jitter = 3% of each continuous feature's std
CONTINUOUS_FEATURES = ["age", "trestbps", "chol", "thalach", "oldpeak"]
FEATURE_BOUNDS = {              # keep jittered values within realistic ranges
    "age": (18, 95),
    "trestbps": (70, 220),
    "chol": (100, 650),
    "thalach": (50, 230),
    "oldpeak": (0.0, 7.0),
}


def augment_training_data(X_train: pd.DataFrame, y_train: pd.Series, multiplier: int = AUGMENT_MULTIPLIER):
    """Bootstrap-resample the real training rows and add small Gaussian
    jitter to continuous features, to give the models a larger effective
    training set without inventing new categorical medical facts."""
    if multiplier <= 1:
        return X_train, y_train

    rng = np.random.RandomState(RANDOM_STATE)
    stds = X_train[CONTINUOUS_FEATURES].std()

    extra_needed = len(X_train) * (multiplier - 1)
    sampled_idx = rng.choice(X_train.index, size=extra_needed, replace=True)
    synthetic = X_train.loc[sampled_idx].reset_index(drop=True).copy()

    for col in CONTINUOUS_FEATURES:
        jitter = rng.normal(loc=0.0, scale=stds[col] * NOISE_FRACTION, size=len(synthetic))
        synthetic[col] = synthetic[col] + jitter
        lo, hi = FEATURE_BOUNDS[col]
        synthetic[col] = synthetic[col].clip(lo, hi)
        if col != "oldpeak":
            synthetic[col] = synthetic[col].round().astype(int)
        else:
            synthetic[col] = synthetic[col].round(1)

    synthetic_y = y_train.loc[sampled_idx].reset_index(drop=True)

    X_augmented = pd.concat([X_train.reset_index(drop=True), synthetic], ignore_index=True)
    y_augmented = pd.concat([y_train.reset_index(drop=True), synthetic_y], ignore_index=True)
    return X_augmented, y_augmented


FEATURE_DESCRIPTIONS = {
    "age": "Age in years",
    "sex": "Sex (1 = male, 0 = female)",
    "cp": "Chest pain type (0-3)",
    "trestbps": "Resting blood pressure (mm Hg)",
    "chol": "Serum cholesterol (mg/dl)",
    "fbs": "Fasting blood sugar > 120 mg/dl (1 = true, 0 = false)",
    "restecg": "Resting ECG results (0-2)",
    "thalach": "Maximum heart rate achieved",
    "exang": "Exercise induced angina (1 = yes, 0 = no)",
    "oldpeak": "ST depression induced by exercise",
    "slope": "Slope of peak exercise ST segment (0-2)",
    "ca": "Number of major vessels colored by fluoroscopy (0-4)",
    "thal": "Thalassemia (1 = normal, 2 = fixed defect, 3 = reversible defect)",
}


def train_and_save():
    os.makedirs(MODELS_DIR, exist_ok=True)
    df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")
    X = df[FEATURE_NAMES]
    y = df["target"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )

    original_train_rows = len(X_train)
    if AUGMENT_TRAINING_DATA:
        X_train, y_train = augment_training_data(X_train, y_train)
    augmented_train_rows = len(X_train)
    print(f"Training rows: {original_train_rows} real -> {augmented_train_rows} after augmentation "
          f"(test set of {len(X_test)} rows stays 100% real, untouched)")

    scaler = StandardScaler()
    X_train_scaled = pd.DataFrame(scaler.fit_transform(X_train), columns=FEATURE_NAMES, index=X_train.index)
    X_test_scaled = pd.DataFrame(scaler.transform(X_test), columns=FEATURE_NAMES, index=X_test.index)

    models = {
        "Logistic Regression": LogisticRegression(max_iter=1000, random_state=RANDOM_STATE),
        "Random Forest": RandomForestClassifier(n_estimators=300, max_depth=6, random_state=RANDOM_STATE),
        "XGBoost": XGBClassifier(
            n_estimators=200, max_depth=4, learning_rate=0.05,
            eval_metric="logloss", random_state=RANDOM_STATE
        ),
        "Neural Network (MLP)": MLPClassifier(
            hidden_layer_sizes=(32, 16), max_iter=2000,
            random_state=RANDOM_STATE, early_stopping=True
        ),
    }
    uses_scaled = {"Logistic Regression", "Neural Network (MLP)"}

    results = {}
    sklearn_models = {}

    for name, model in models.items():
        if name in uses_scaled:
            model.fit(X_train_scaled, y_train)
            preds = model.predict(X_test_scaled)
            probs = model.predict_proba(X_test_scaled)[:, 1]
        else:
            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            probs = model.predict_proba(X_test)[:, 1]

        results[name] = {
            "accuracy": round(accuracy_score(y_test, preds), 4),
            "precision": round(precision_score(y_test, preds), 4),
            "recall": round(recall_score(y_test, preds), 4),
            "f1": round(f1_score(y_test, preds), 4),
            "roc_auc": round(roc_auc_score(y_test, probs), 4),
        }
        print(f"{name:22s} | Acc: {results[name]['accuracy']:.3f} | "
              f"F1: {results[name]['f1']:.3f} | ROC-AUC: {results[name]['roc_auc']:.3f}")

        if name == "XGBoost":
            # Portable, version-safe format
            model.save_model(os.path.join(MODELS_DIR, "xgboost_model.json"))
        else:
            sklearn_models[name] = model

    best_model_name = max(results, key=lambda k: results[k]["roc_auc"])
    print(f"\nBest model by ROC-AUC: {best_model_name}")

    joblib.dump(sklearn_models, os.path.join(MODELS_DIR, "sklearn_models.pkl"))
    joblib.dump(scaler, os.path.join(MODELS_DIR, "scaler.pkl"))
    X_train.to_csv(os.path.join(MODELS_DIR, "X_train_raw.csv"), index=False)
    X_train_scaled.to_csv(os.path.join(MODELS_DIR, "X_train_scaled.csv"), index=False)

    with open(os.path.join(MODELS_DIR, "results.json"), "w") as f:
        json.dump({
            "results": results,
            "best_model": best_model_name,
            "feature_names": FEATURE_NAMES,
            "feature_descriptions": FEATURE_DESCRIPTIONS,
            "uses_scaled": list(uses_scaled),
            "dataset_info": {
                "original_training_rows": original_train_rows,
                "training_rows_after_augmentation": augmented_train_rows,
                "test_rows": len(X_test),
                "augmentation_used": AUGMENT_TRAINING_DATA,
                "note": (
                    "Training rows were expanded via bootstrap resampling + small "
                    "Gaussian jitter on continuous features, since no additional real "
                    "patient records were available in this environment. The test set "
                    "is always 100% real, un-augmented data."
                ),
            },
        }, f, indent=2)

    print("Saved all models and metadata to /models")


if __name__ == "__main__":
    train_and_save()
