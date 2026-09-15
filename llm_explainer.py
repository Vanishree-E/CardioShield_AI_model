"""
llm_explainer.py
-----------------
The "Ask AI to explain" feature: turns a prediction's raw SHAP feature
contributions into a short paragraph an actual patient can read and
understand, in English or Tamil.

Two modes, chosen automatically -- the caller never has to know which one
ran:

1. TEMPLATE MODE (default, zero setup, works fully offline).
   A rule-based natural-language generator: it ranks the SHAP
   contributions by importance, looks up a human phrase + the patient's
   own value for each of the top factors, and assembles a paragraph. This
   is deterministic and needs no internet or API key, so it is what runs
   during a live demo even with bad wifi -- the feature can never go down
   in front of a judge.

2. LLM MODE (optional upgrade). If an ANTHROPIC_API_KEY environment
   variable is set, the same structured data (prediction, probability,
   top SHAP contributors with the patient's real values) is sent to
   Claude as context, and Claude writes a warmer, more natural paragraph.
   If that call fails for any reason -- no key, no network, rate limit,
   timeout -- this silently falls back to template mode. The feature
   never breaks the demo either way.

Either way the response says which mode produced it, so the UI can label
it honestly (nobody should mistake this for something a doctor wrote).
"""

import os
import json
import urllib.request
import urllib.error

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
REQUEST_TIMEOUT_SECONDS = 8

TOP_N_FACTORS = 3


# ---------------------------------------------------------------------------
# Feature -> human-readable, value-aware phrase (English + Tamil)
# ---------------------------------------------------------------------------
def _cp_phrase(v, lang):
    v = int(v)
    labels = {
        0: ("typical angina-type chest pain", "வழக்கமான ஆஞ்சினா வகை மார்பு வலி"),
        1: ("atypical angina-type chest pain", "அசாதாரண ஆஞ்சினா வகை மார்பு வலி"),
        2: ("non-anginal chest pain", "ஆஞ்சினா அல்லாத மார்பு வலி"),
        3: ("no chest pain symptoms", "மார்பு வலி அறிகுறிகள் இல்லாதது"),
    }
    en, ta = labels.get(v, labels[3])
    return en if lang == "en" else ta


def _restecg_phrase(v, lang):
    v = int(v)
    labels = {
        0: ("a normal resting ECG", "ஒரு சாதாரண ஓய்வு ECG"),
        1: ("an ST-T wave abnormality on the resting ECG", "ஓய்வு ECG-யில் ST-T அலை முரண்பாடு"),
        2: ("signs of probable heart enlargement on the resting ECG", "ஓய்வு ECG-யில் இதயம் பெரிதாகும் அறிகுறிகள்"),
    }
    en, ta = labels.get(v, labels[0])
    return en if lang == "en" else ta


def _slope_phrase(v, lang):
    v = int(v)
    labels = {
        0: ("an upsloping exercise ST segment", "மேல்நோக்கிச் செல்லும் உடற்பயிற்சி ST பகுதி"),
        1: ("a flat exercise ST segment", "தட்டையான உடற்பயிற்சி ST பகுதி"),
        2: ("a downsloping exercise ST segment", "கீழ்நோக்கிச் செல்லும் உடற்பயிற்சி ST பகுதி"),
    }
    en, ta = labels.get(v, labels[0])
    return en if lang == "en" else ta


def _thal_phrase(v, lang):
    v = int(v)
    labels = {
        1: ("a normal thalassemia result", "ஒரு சாதாரண தலசீமியா முடிவு"),
        2: ("a fixed thalassemia defect", "ஒரு நிலையான தலசீமியா குறைபாடு"),
        3: ("a reversible thalassemia defect", "ஒரு மீளக்கூடிய தலசீமியா குறைபாடு"),
    }
    en, ta = labels.get(v, labels[1])
    return en if lang == "en" else ta


FEATURE_PHRASE_FUNCS = {
    "age": lambda v, lang: (f"your age ({int(v)} years)" if lang == "en" else f"உங்கள் வயது ({int(v)} ஆண்டுகள்)"),
    "sex": lambda v, lang: (("being male" if int(v) == 1 else "being female") if lang == "en"
                             else ("ஆணாக இருப்பது" if int(v) == 1 else "பெண்ணாக இருப்பது")),
    "cp": _cp_phrase,
    "trestbps": lambda v, lang: (f"your resting blood pressure of {int(v)} mm Hg" if lang == "en"
                                  else f"உங்கள் ஓய்வு இரத்த அழுத்தம் {int(v)} mm Hg"),
    "chol": lambda v, lang: (f"your cholesterol level of {int(v)} mg/dl" if lang == "en"
                              else f"உங்கள் கொலஸ்ட்ரால் அளவு {int(v)} mg/dl"),
    "fbs": lambda v, lang: (("fasting blood sugar above 120 mg/dl" if int(v) == 1 else "normal fasting blood sugar")
                             if lang == "en" else
                             ("120 mg/dl-க்கு மேல் உண்ணாவிரத சர்க்கரை" if int(v) == 1 else "சாதாரண உண்ணாவிரத சர்க்கரை")),
    "restecg": _restecg_phrase,
    "thalach": lambda v, lang: (f"your maximum heart rate of {int(v)} bpm during exercise" if lang == "en"
                                 else f"உடற்பயிற்சியின் போது உங்கள் அதிகபட்ச இதயத் துடிப்பு {int(v)} bpm"),
    "exang": lambda v, lang: (("chest pain that appears during exercise" if int(v) == 1 else "no chest pain during exercise")
                               if lang == "en" else
                               ("உடற்பயிற்சியின் போது ஏற்படும் மார்பு வலி" if int(v) == 1 else "உடற்பயிற்சியின் போது மார்பு வலி இல்லை")),
    "oldpeak": lambda v, lang: (f"an ST depression reading of {v}" if lang == "en"
                                 else f"ST அமுக்க அளவீடு {v}"),
    "slope": _slope_phrase,
    "ca": lambda v, lang: (f"{int(v)} major blood vessel(s) showing narrowing on fluoroscopy" if lang == "en"
                            else f"ஃப்ளூரோஸ்கோபியில் {int(v)} முக்கிய இரத்த நாளங்கள் குறுகியிருப்பது"),
    "thal": _thal_phrase,
}


def _direction_word(shap_value, lang):
    if shap_value > 0:
        return "pushing your estimated risk up" if lang == "en" else "உங்கள் மதிப்பிடப்பட்ட ஆபத்தை அதிகரிக்கிறது"
    return "working in your favor, lowering the estimated risk" if lang == "en" else "உங்களுக்குச் சாதகமாக, ஆபத்தை குறைக்கிறது"


def _phrase_for(feature, value, lang):
    fn = FEATURE_PHRASE_FUNCS.get(feature)
    if fn is None:
        return feature
    try:
        return fn(value, lang)
    except Exception:
        return feature


# ---------------------------------------------------------------------------
# Mode 1: rule-based template generator (always available, offline-safe)
# ---------------------------------------------------------------------------
def generate_template_explanation(patient, shap_values, prediction, probability, lang="en", top_n=TOP_N_FACTORS):
    ranked = sorted(shap_values, key=lambda d: abs(d["shap_value"]), reverse=True)[:top_n]
    pct = round(probability * 100, 1)

    if lang == "ta":
        opener = (
            f"இந்த மாதிரி உங்கள் இதய நோய் ஆபத்தை சுமார் {pct}% எனக் கணக்கிட்டுள்ளது. "
            "இந்த முடிவை மிகவும் பாதித்த முக்கியக் காரணிகள் இங்கே:"
        )
        sentences = []
        for item in ranked:
            phrase = _phrase_for(item["feature"], item["value"], "ta")
            direction = _direction_word(item["shap_value"], "ta")
            sentences.append(f"{phrase} — இது {direction}.")
        closer = (
            "இது ஒரு புள்ளிவிவர மதிப்பீடு மட்டுமே, மருத்துவ கண்டறிதல் அல்ல. "
            "இந்த முடிவுகளை உங்கள் மருத்துவரிடம் விவாதிக்கவும்."
        )
    else:
        opener = (
            f"The model estimates about a {pct}% chance of heart disease for this input. "
            "Here's what mattered most to that estimate:"
        )
        sentences = []
        for item in ranked:
            phrase = _phrase_for(item["feature"], item["value"], "en")
            direction = _direction_word(item["shap_value"], "en")
            # Capitalize only the first letter -- phrase.capitalize() would
            # lowercase acronyms like "ST" inside the phrase (e.g. "ST
            # depression" -> "St depression"), which reads as a typo.
            sentences.append(f"{phrase[:1].upper()}{phrase[1:]} — this is {direction}.")
        closer = (
            "This is a statistical estimate from a machine-learning model, not a medical diagnosis. "
            "Please discuss these specific numbers with a real doctor."
        )

    return " ".join([opener] + sentences + [closer])


# ---------------------------------------------------------------------------
# Mode 2: optional real-LLM upgrade (Claude), same structured input
# ---------------------------------------------------------------------------
def _call_claude(patient, shap_values, prediction, probability, lang):
    if not ANTHROPIC_API_KEY:
        return None

    ranked = sorted(shap_values, key=lambda d: abs(d["shap_value"]), reverse=True)[:TOP_N_FACTORS]
    context = {
        "predicted_probability_of_disease": round(probability, 3),
        "top_contributing_factors": [
            {
                "feature": item["feature"],
                "patient_value": item["value"],
                "pushes_risk": "up" if item["shap_value"] > 0 else "down",
            }
            for item in ranked
        ],
    }

    lang_instruction = "Write in Tamil." if lang == "ta" else "Write in English."
    prompt = (
        "You are explaining a heart-disease risk-prediction model's output to the patient "
        "who just used it, in plain, warm, non-alarming language. Use the structured data "
        "below. Do not invent numbers not given. Keep it to 3-5 short sentences, "
        "80-120 words. End by reminding them this is a statistical estimate, not a diagnosis, "
        "and to discuss it with a real doctor. " + lang_instruction + "\n\n"
        f"Data: {json.dumps(context)}"
    )

    body = json.dumps({
        "model": ANTHROPIC_MODEL,
        "max_tokens": 400,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")

    req = urllib.request.Request(
        ANTHROPIC_URL,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text_blocks = [b["text"] for b in data.get("content", []) if b.get("type") == "text"]
        text = " ".join(text_blocks).strip()
        return text or None
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, KeyError):
        # No key set, no network, bad response, rate limited, etc. -- fall back
        # to the template generator rather than surfacing an error to the
        # patient. This is a "nice to have" upgrade, never a hard dependency.
        return None


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def generate_explanation(patient, shap_values, prediction, probability, lang="en"):
    """
    Returns {"explanation": str, "mode": "llm" | "template"}.
    Always succeeds -- LLM mode is a best-effort upgrade over template mode,
    never a replacement that can fail the request.
    """
    if ANTHROPIC_API_KEY:
        llm_text = _call_claude(patient, shap_values, prediction, probability, lang)
        if llm_text:
            return {"explanation": llm_text, "mode": "llm"}

    template_text = generate_template_explanation(patient, shap_values, prediction, probability, lang)
    return {"explanation": template_text, "mode": "template"}
