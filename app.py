"""
app.py
------
Flask backend for Heart Disease Prediction with Explainable AI.

Run with:
    python app.py
Then open http://localhost:5000 in your browser.
"""

import os
import json
import uuid
import functools
import joblib
import numpy as np
import pandas as pd
import shap
from lime.lime_tabular import LimeTabularExplainer
from xgboost import XGBClassifier
from flask import (
    Flask, render_template, request, jsonify, session, redirect, url_for,
    flash, g, send_from_directory, abort
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

import database
import train_models
import health_content
import llm_explainer
from i18n import t, SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")

# Uploaded reports are stored OUTSIDE static/ on purpose: Flask's static route
# serves files to anyone with the URL, with no login check. Reports are
# personal medical files, so they're served through the /uploads/<id> route
# below, which checks the requester actually owns the report first.
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
ALLOWED_REPORT_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "pdf"}
MAX_REPORT_SIZE_MB = 10

app = Flask(__name__)
# NOTE: for real deployment, set this from an environment variable instead
# (e.g. app.secret_key = os.environ["SECRET_KEY"]) so it isn't in source control.
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-this-in-production")
app.config["MAX_CONTENT_LENGTH"] = MAX_REPORT_SIZE_MB * 1024 * 1024
os.makedirs(UPLOADS_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Authentication helpers
# ---------------------------------------------------------------------------
@app.before_request
def load_logged_in_user():
    user_id = session.get("user_id")
    g.user = database.get_user_by_id(user_id) if user_id else None

    # Language preference: logged-in user's saved preference takes priority,
    # then whatever is already in the session (e.g. picked before logging
    # in), then the default.
    if g.user:
        g.lang = g.user.get("preferred_language") or session.get("lang", DEFAULT_LANGUAGE)
    else:
        g.lang = session.get("lang", DEFAULT_LANGUAGE)


def login_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            flash("Please log in to continue." if g.lang == "en" else "தொடர உள்நுழையவும்.")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


@app.context_processor
def inject_globals():
    # Makes `current_user`, `t()`, and `current_lang` available in every
    # Jinja template automatically.
    return {
        "current_user": g.get("user"),
        "current_lang": g.get("lang", DEFAULT_LANGUAGE),
        "t": lambda key: t(key, g.get("lang", DEFAULT_LANGUAGE)),
    }


@app.route("/set-language/<lang>")
def set_language(lang):
    if lang not in SUPPORTED_LANGUAGES:
        abort(404)
    session["lang"] = lang
    if g.user:
        database.set_user_language(g.user["id"], lang)
    next_url = request.args.get("next") or request.referrer or url_for("index")
    return redirect(next_url)

# ---------------------------------------------------------------------------
# Ensure models exist -- train automatically on first run so there is never
# a "model file from a different machine/version" problem.
# ---------------------------------------------------------------------------
def ensure_models_trained():
    required = [
        os.path.join(MODELS_DIR, "sklearn_models.pkl"),
        os.path.join(MODELS_DIR, "xgboost_model.json"),
        os.path.join(MODELS_DIR, "scaler.pkl"),
        os.path.join(MODELS_DIR, "results.json"),
    ]
    if not all(os.path.exists(p) for p in required):
        print("Models not found -- training now (first run only, ~1-2 min)...")
        train_models.train_and_save()
    else:
        print("Found existing trained models, skipping training.")


ensure_models_trained()
database.init_db()

# ---------------------------------------------------------------------------
# Load everything into memory once at startup
# ---------------------------------------------------------------------------
sklearn_models = joblib.load(os.path.join(MODELS_DIR, "sklearn_models.pkl"))
scaler = joblib.load(os.path.join(MODELS_DIR, "scaler.pkl"))

xgb_model = XGBClassifier()
xgb_model.load_model(os.path.join(MODELS_DIR, "xgboost_model.json"))

MODELS = dict(sklearn_models)
MODELS["XGBoost"] = xgb_model

with open(os.path.join(MODELS_DIR, "results.json")) as f:
    META = json.load(f)

FEATURE_NAMES = META["feature_names"]
FEATURE_DESCRIPTIONS = META["feature_descriptions"]
USES_SCALED = set(META["uses_scaled"])
BEST_MODEL = META["best_model"]
RESULTS = META["results"]

X_train = pd.read_csv(os.path.join(MODELS_DIR, "X_train_raw.csv"))
X_train_scaled = pd.read_csv(os.path.join(MODELS_DIR, "X_train_scaled.csv"))

# Pre-build a SHAP TreeExplainer for tree models (fast) -- KernelExplainer for
# LR/MLP is built lazily since it's slower.
TREE_EXPLAINERS = {
    "Random Forest": shap.TreeExplainer(MODELS["Random Forest"]),
    "XGBoost": shap.TreeExplainer(MODELS["XGBoost"]),
}


def get_patient_df(payload: dict) -> pd.DataFrame:
    row = {k: payload[k] for k in FEATURE_NAMES}
    return pd.DataFrame([row])[FEATURE_NAMES]


def compute_shap(model_name: str, patient_df: pd.DataFrame):
    model = MODELS[model_name]
    is_scaled = model_name in USES_SCALED
    X_input = pd.DataFrame(
        scaler.transform(patient_df) if is_scaled else patient_df.values,
        columns=FEATURE_NAMES
    )

    if model_name in TREE_EXPLAINERS:
        explainer = TREE_EXPLAINERS[model_name]
        sv = explainer.shap_values(X_input)
        if isinstance(sv, list):
            sv1 = np.array(sv[1][0])
            base = explainer.expected_value[1]
        elif np.ndim(sv) == 3:
            sv1 = sv[0, :, 1]
            base = explainer.expected_value[1] if hasattr(explainer.expected_value, "__len__") else explainer.expected_value
        else:
            sv1 = sv[0]
            base = explainer.expected_value
    else:
        background = (X_train_scaled if is_scaled else X_train).sample(
            min(50, len(X_train)), random_state=42
        )
        explainer = shap.KernelExplainer(model.predict_proba, background)
        sv = explainer.shap_values(X_input, nsamples=100)
        if isinstance(sv, list):
            sv1 = np.array(sv[1][0])
            base = explainer.expected_value[1]
        else:
            sv1 = sv[0, :, 1]
            base = explainer.expected_value[1]

    return [
        {"feature": f, "value": float(patient_df.iloc[0][f]), "shap_value": float(v)}
        for f, v in zip(FEATURE_NAMES, sv1)
    ], float(base)


def compute_lime(model_name: str, patient_df: pd.DataFrame):
    model = MODELS[model_name]
    is_scaled = model_name in USES_SCALED
    X_input = scaler.transform(patient_df) if is_scaled else patient_df.values
    bg = (X_train_scaled if is_scaled else X_train).values

    explainer = LimeTabularExplainer(
        bg, feature_names=FEATURE_NAMES,
        class_names=["No Disease", "Disease"], mode="classification"
    )
    exp = explainer.explain_instance(X_input[0], model.predict_proba, num_features=len(FEATURE_NAMES))
    return [{"condition": cond, "contribution": float(val)} for cond, val in exp.as_list()]


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if g.user:
        return redirect(url_for("index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        error = None
        if not name:
            error = "Please enter your name."
        elif not email or "@" not in email:
            error = "Please enter a valid email address."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."
        elif password != confirm:
            error = "Passwords do not match."
        elif database.get_user_by_email(email):
            error = "An account with that email already exists."

        if error:
            flash(error)
            return render_template("register.html", active="register", name=name, email=email)

        user_id = database.create_user(name, email, generate_password_hash(password))
        session.clear()
        session["user_id"] = user_id
        flash("Account created — welcome!")
        return redirect(url_for("index"))

    return render_template("register.html", active="register")


@app.route("/login", methods=["GET", "POST"])
def login():
    if g.user:
        return redirect(url_for("index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        user = database.get_user_by_email(email)

        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Incorrect email or password.")
            return render_template("login.html", active="login", email=email)

        session.clear()
        session["user_id"] = user["id"]
        flash(f"Welcome back, {user['name']}!")
        next_url = request.args.get("next") or url_for("index")
        return redirect(next_url)

    return render_template("login.html", active="login")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Page routes
# ---------------------------------------------------------------------------
@app.route("/")
@login_required
def index():
    return render_template(
        "index.html",
        feature_descriptions=FEATURE_DESCRIPTIONS,
        model_names=list(MODELS.keys()),
        best_model=BEST_MODEL,
        active="predict",
    )


@app.route("/symptoms")
@login_required
def symptoms_page():
    return render_template("symptoms.html", active="symptoms")


@app.route("/history")
@login_required
def history_page():
    return render_template("history.html", active="history")


@app.route("/compare")
@login_required
def compare_page():
    return render_template("compare.html", active="compare")


def _allowed_report_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_REPORT_EXTENSIONS


@app.route("/reports", methods=["GET", "POST"])
@login_required
def reports_page():
    if request.method == "POST":
        file = request.files.get("report_file")
        note = request.form.get("note", "").strip()

        if file is None or file.filename == "":
            flash("Please choose a file to upload." if g.lang == "en" else "பதிவேற்ற ஒரு கோப்பைத் தேர்ந்தெடுக்கவும்.")
            return redirect(url_for("reports_page"))

        if not _allowed_report_file(file.filename):
            flash("That file type isn't supported. Please upload an image or a PDF."
                  if g.lang == "en" else "இந்த கோப்பு வகை ஆதரிக்கப்படவில்லை. ஒரு படம் அல்லது PDF பதிவேற்றவும்.")
            return redirect(url_for("reports_page"))

        # Store under a per-user folder using a random name -- never trust the
        # original filename for the on-disk path, and never let one user's
        # files land in a path guessable from another user's id.
        ext = file.filename.rsplit(".", 1)[1].lower()
        stored_name = f"{uuid.uuid4().hex}.{ext}"
        user_dir = os.path.join(UPLOADS_DIR, str(g.user["id"]))
        os.makedirs(user_dir, exist_ok=True)
        file.save(os.path.join(user_dir, stored_name))

        database.insert_report(
            g.user["id"], stored_name, secure_filename(file.filename), note
        )
        flash("Report uploaded." if g.lang == "en" else "அறிக்கை பதிவேற்றப்பட்டது.")
        return redirect(url_for("reports_page"))

    reports = database.get_reports_for_user(g.user["id"])
    return render_template("reports.html", active="reports", reports=reports)


@app.route("/uploads/<int:report_id>")
@login_required
def serve_report(report_id):
    report = database.get_report_by_id(report_id)
    # Ownership check -- this is what keeps one user's scan/report private
    # from every other user, even if they guess another report's id.
    if report is None or report["user_id"] != g.user["id"]:
        abort(404)
    user_dir = os.path.join(UPLOADS_DIR, str(report["user_id"]))
    return send_from_directory(user_dir, report["filename"])


@app.route("/reports/<int:report_id>/delete", methods=["POST"])
@login_required
def delete_report(report_id):
    report = database.get_report_by_id(report_id)
    if report and report["user_id"] == g.user["id"]:
        deleted = database.delete_report(report_id, g.user["id"])
        if deleted:
            try:
                os.remove(os.path.join(UPLOADS_DIR, str(g.user["id"]), report["filename"]))
            except OSError:
                pass
    return redirect(url_for("reports_page"))


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------
@app.route("/predict", methods=["POST"])
@login_required
def predict():
    payload = request.get_json()
    model_name = payload.get("model_name", BEST_MODEL)
    if model_name not in MODELS:
        return jsonify({"error": f"Unknown model '{model_name}'"}), 400

    try:
        patient_df = get_patient_df(payload)
    except KeyError as e:
        return jsonify({"error": f"Missing field: {e}"}), 400

    model = MODELS[model_name]
    is_scaled = model_name in USES_SCALED
    X_input = scaler.transform(patient_df) if is_scaled else patient_df.values

    proba = model.predict_proba(X_input)[0]
    prediction = int(np.argmax(proba))

    shap_values, base_value = compute_shap(model_name, patient_df)
    lime_values = compute_lime(model_name, patient_df)

    row_id = database.insert_prediction(
        g.user["id"], payload, model_name, prediction, float(proba[1])
    )

    stage = health_content.determine_stage(float(proba[1]), payload)
    plan = health_content.get_stage_plan(stage, g.lang)
    quote = health_content.get_random_quote(g.lang)

    return jsonify({
        "id": row_id,
        "prediction": prediction,
        "probability_disease": float(proba[1]),
        "probability_no_disease": float(proba[0]),
        "model_used": model_name,
        "shap_values": shap_values,
        "shap_base_value": base_value,
        "lime_values": lime_values,
        "plan": plan,
        "quote": quote,
    })


@app.route("/explain", methods=["POST"])
@login_required
def explain():
    """
    "Ask AI to explain" -- takes the SHAP contributions from a prediction
    the user just ran (sent back by the frontend, not recomputed) and turns
    them into a plain-language paragraph. Uses a real LLM call if
    ANTHROPIC_API_KEY is configured, otherwise a deterministic rule-based
    generator -- see llm_explainer.py. Never fails the request just because
    the LLM upgrade is unavailable.
    """
    data = request.get_json() or {}
    try:
        result = llm_explainer.generate_explanation(
            patient=data["payload"],
            shap_values=data["shap_values"],
            prediction=int(data["prediction"]),
            probability=float(data["probability_disease"]),
            lang=g.lang,
        )
    except (KeyError, TypeError, ValueError) as e:
        return jsonify({"error": f"Missing or invalid field: {e}"}), 400
    return jsonify(result)


@app.route("/api/history", methods=["GET"])
@login_required
def api_history():
    return jsonify(database.get_predictions_for_user(g.user["id"]))


@app.route("/api/history/clear", methods=["POST"])
@login_required
def api_history_clear():
    database.clear_predictions_for_user(g.user["id"])
    return jsonify({"status": "cleared"})


@app.route("/api/compare", methods=["GET"])
@login_required
def api_compare():
    return jsonify({"results": RESULTS, "best_model": BEST_MODEL})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
