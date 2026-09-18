"""
i18n.py
-------
Very small hand-rolled translation layer (English <-> Tamil).

We don't pull in a heavy i18n framework -- there are only two languages and a
bounded set of UI strings, so a flat dict keyed by a short string id is
simpler to read, edit, and extend than .po files / Flask-Babel for a project
this size.

Usage in Python:
    from i18n import t
    t("nav_predict", lang)                # -> "Check my risk" / "எனது ஆபத்தை பரிசோதி"

Usage in Jinja (registered as a global in app.py):
    {{ t('nav_predict') }}
"""

SUPPORTED_LANGUAGES = ["en", "ta"]
DEFAULT_LANGUAGE = "en"

STRINGS = {
    # ---- brand / nav / sidebar --------------------------------------------
    "brand_tagline": {"en": "Explainable Risk Model", "ta": "விளக்கமளிக்கும் ஆபத்து மாதிரி"},
    "nav_predict": {"en": "Check my risk", "ta": "எனது ஆபத்தைச் சரிபார்"},
    "nav_symptoms": {"en": "Symptoms guide", "ta": "அறிகுறிகள் வழிகாட்டி"},
    "nav_history": {"en": "History", "ta": "வரலாறு"},
    "nav_compare": {"en": "Model Comparison", "ta": "மாதிரி ஒப்பீடு"},
    "nav_reports": {"en": "My Reports", "ta": "எனது அறிக்கைகள்"},
    "nav_login": {"en": "Log in", "ta": "உள்நுழை"},
    "nav_register": {"en": "Register", "ta": "பதிவு செய்"},
    "signed_in_as": {"en": "Signed in as", "ta": "இவராக உள்நுழைந்துள்ளீர்கள்"},
    "log_out": {"en": "Log out", "ta": "வெளியேறு"},
    "footer_text": {
        "en": "Built on the UCI Cleveland Heart Disease dataset, using SHAP + LIME to explain results.<br>This is an educational tool, not a medical device — always check with a real doctor.",
        "ta": "UCI Cleveland இதய நோய் தரவுத்தொகுப்பின் அடிப்படையில், SHAP + LIME மூலம் முடிவுகளை விளக்குகிறோம்.<br>இது ஒரு கல்வி கருவி மட்டுமே, மருத்துவ கருவி அல்ல — எப்போதும் ஒரு மருத்துவரிடம் ஆலோசனை பெறவும்.",
    },

    # ---- login / register --------------------------------------------------
    "login_title": {"en": "Log in", "ta": "உள்நுழைவு"},
    "login_subtitle": {
        "en": "Log in to see your own predictions, history, and health reports — private to your account only.",
        "ta": "உங்கள் சொந்த முடிவுகள், வரலாறு மற்றும் சுகாதார அறிக்கைகளைப் பார்க்க உள்நுழையவும் — இது உங்கள் கணக்கிற்கு மட்டுமே தனிப்பட்டது.",
    },
    "register_title": {"en": "Create your account", "ta": "உங்கள் கணக்கை உருவாக்கவும்"},
    "register_subtitle": {
        "en": "Your results are private — only you can see your own predictions, uploaded reports, and history.",
        "ta": "உங்கள் முடிவுகள் தனிப்பட்டவை — உங்கள் சொந்த முடிவுகள், பதிவேற்றிய அறிக்கைகள் மற்றும் வரலாற்றை நீங்கள் மட்டுமே பார்க்க முடியும்.",
    },
    "label_name": {"en": "Full name", "ta": "முழு பெயர்"},
    "label_email": {"en": "Email", "ta": "மின்னஞ்சல்"},
    "label_password": {"en": "Password", "ta": "கடவுச்சொல்"},
    "label_confirm_password": {"en": "Confirm password", "ta": "கடவுச்சொல்லை உறுதிப்படுத்து"},
    "hint_password_length": {"en": "At least 6 characters.", "ta": "குறைந்தது 6 எழுத்துகள்."},
    "btn_login": {"en": "Log in", "ta": "உள்நுழை"},
    "btn_create_account": {"en": "Create account", "ta": "கணக்கை உருவாக்கு"},
    "no_account": {"en": "Don't have an account?", "ta": "கணக்கு இல்லையா?"},
    "register_here": {"en": "Register here", "ta": "இங்கே பதிவு செய்யவும்"},
    "have_account": {"en": "Already have an account?", "ta": "ஏற்கனவே கணக்கு உள்ளதா?"},
    "login_here": {"en": "Log in here", "ta": "இங்கே உள்நுழையவும்"},

    # ---- predict page -------------------------------------------------------
    "index_title": {"en": "Heart disease risk checker", "ta": "இதய நோய் ஆபத்து பரிசோதனை"},
    "index_subtitle": {
        "en": "Answer the questions below in plain language — no medical background needed. We'll show you a risk estimate and explain, in simple terms, exactly which answers pushed that number up or down.",
        "ta": "கீழே உள்ள கேள்விகளுக்கு எளிய மொழியில் பதிலளிக்கவும் — மருத்துவ அறிவு தேவையில்லை. ஒரு ஆபத்து மதிப்பீட்டைக் காட்டி, எந்த பதில்கள் அந்த எண்ணை அதிகரித்தன அல்லது குறைத்தன என்பதை எளிய முறையில் விளக்குவோம்.",
    },
    "disclaimer_text": {
        "en": "This tool is for learning and general awareness only. It does not diagnose anything and can't replace a doctor. If you're worried about your heart right now, or you have chest pain, please contact a medical professional or emergency services.",
        "ta": "இந்த கருவி கற்றல் மற்றும் பொது விழிப்புணர்வுக்காக மட்டுமே. இது எதையும் கண்டறியாது, மருத்துவரை மாற்ற முடியாது. உங்கள் இதயம் குறித்து இப்போது கவலைப்பட்டால், அல்லது மார்பு வலி இருந்தால், உடனே ஒரு மருத்துவரை அல்லது அவசர சேவையை தொடர்பு கொள்ளவும்.",
    },
    "panel_your_info": {"en": "Your information", "ta": "உங்கள் தகவல்"},
    "panel_your_result": {"en": "Your result", "ta": "உங்கள் முடிவு"},
    "result_fill_hint": {
        "en": 'Fill in the form and click "Check my risk" to see a result here.',
        "ta": 'படிவத்தை நிரப்பி "எனது ஆபத்தைச் சரிபார்" என்பதைக் கிளிக் செய்யவும்.',
    },
    "panel_shap_title": {"en": "Why? Reason #1 (SHAP)", "ta": "ஏன்? காரணம் #1 (SHAP)"},
    "panel_shap_sub": {
        "en": "Shows how much each answer pushed your result up (more risk) or down (less risk).",
        "ta": "ஒவ்வொரு பதிலும் உங்கள் முடிவை எவ்வளவு அதிகரித்தது (அதிக ஆபத்து) அல்லது குறைத்தது (குறைந்த ஆபத்து) என்பதைக் காட்டுகிறது.",
    },
    "panel_lime_title": {"en": "Why? Reason #2 (LIME)", "ta": "ஏன்? காரணம் #2 (LIME)"},
    "panel_lime_sub": {
        "en": "A second, independent way of estimating which answers mattered most, so you can compare the two.",
        "ta": "எந்த பதில்கள் மிக முக்கியமானவை என்பதை மதிப்பிடும் இரண்டாவது, சுயாதீன வழிமுறை.",
    },
    "run_check_hint": {"en": "Run a check to see this breakdown.", "ta": "இந்த விவரத்தைப் பார்க்க ஒரு பரிசோதனையை இயக்கவும்."},

    # ---- AI plain-language explainer ---------------------------------------
    "panel_explain_title": {"en": "Ask AI to explain this in plain language", "ta": "இதை எளிய மொழியில் விளக்க AI-யிடம் கேளுங்கள்"},
    "panel_explain_sub": {
        "en": "Turns the SHAP numbers above into a short paragraph you can actually read.",
        "ta": "மேலே உள்ள SHAP எண்களை நீங்கள் படிக்கக்கூடிய ஒரு சிறு பத்தியாக மாற்றுகிறது.",
    },
    "btn_explain": {"en": "✨ Explain my result", "ta": "✨ எனது முடிவை விளக்கு"},
    "btn_explain_loading": {"en": "Thinking...", "ta": "யோசிக்கிறது..."},
    "explain_source_llm": {"en": "AI-generated (Claude)", "ta": "AI-உருவாக்கியது (Claude)"},
    "explain_source_template": {"en": "Rule-based (offline)", "ta": "விதி-அடிப்படையிலான (ஆஃப்லைன்)"},
    "explain_error": {
        "en": "Couldn't generate an explanation right now. Please try again.",
        "ta": "இப்போது ஒரு விளக்கத்தை உருவாக்க முடியவில்லை. மீண்டும் முயற்சிக்கவும்.",
    },
    "btn_check_risk": {"en": "Check my risk", "ta": "எனது ஆபத்தைச் சரிபார்"},
    "label_model": {"en": "Model to use", "ta": "பயன்படுத்த வேண்டிய மாதிரி"},
    "hint_model": {
        "en": "Different math approaches to the same prediction. If you're not sure, leave this on the recommended one.",
        "ta": "ஒரே கணிப்புக்கான வெவ்வேறு கணித அணுகுமுறைகள். உறுதியில்லை என்றால், பரிந்துரைக்கப்பட்டதை அப்படியே விடவும்.",
    },
    "label_age": {"en": "Age", "ta": "வயது"},
    "label_sex": {"en": "Sex assigned at birth", "ta": "பிறப்பின்போது பாலினம்"},
    "option_male": {"en": "Male", "ta": "ஆண்"},
    "option_female": {"en": "Female", "ta": "பெண்"},
    "label_cp": {"en": "Chest pain — what does it feel like?", "ta": "மார்பு வலி — அது எப்படி உணரப்படுகிறது?"},
    "label_trestbps": {"en": "Resting blood pressure", "ta": "ஓய்வு நேர இரத்த அழுத்தம்"},
    "label_chol": {"en": "Cholesterol", "ta": "கொழுப்பு அளவு (கொலஸ்ட்ரால்)"},
    "label_fbs": {"en": "Is your fasting blood sugar over 120 mg/dl?", "ta": "உண்ணாவிரத இரத்த சர்க்கரை 120 mg/dl -க்கு மேலா?"},
    "option_yes": {"en": "Yes", "ta": "ஆம்"},
    "option_no": {"en": "No", "ta": "இல்லை"},
    "label_restecg": {"en": "Resting ECG (heart electrical test) result", "ta": "ஓய்வு நேர ECG (இதய மின் பரிசோதனை) முடிவு"},
    "label_thalach": {"en": "Highest heart rate reached during exercise", "ta": "உடற்பயிற்சியின் போது எட்டிய அதிகபட்ச இதயத் துடிப்பு"},
    "label_exang": {"en": "Does exercise bring on chest pain?", "ta": "உடற்பயிற்சி மார்பு வலியை ஏற்படுத்துகிறதா?"},
    "label_oldpeak": {"en": "Heart-strain score from an exercise test (ST depression)", "ta": "உடற்பயிற்சி பரிசோதனையின் இதய அழுத்த மதிப்பெண் (ST depression)"},
    "label_slope": {"en": "Shape of the ECG signal during peak exercise", "ta": "உச்ச உடற்பயிற்சியின்போது ECG சமிக்ஞையின் வடிவம்"},
    "label_ca": {"en": "Number of major blood vessels showing narrowing on a scan (0-4)", "ta": "ஸ்கேனில் குறுகலைக் காட்டும் முக்கிய இரத்த நாளங்களின் எண்ணிக்கை (0-4)"},
    "label_thal": {"en": "Thalassemia blood test results", "ta": "தலசீமியா இரத்த பரிசோதனை முடிவு"},

    # ---- personalized plan (shown after a prediction) -----------------------
    "plan_heading": {"en": "Your personalized plan", "ta": "உங்களுக்கான தனிப்பயன் திட்டம்"},
    "plan_stage_label": {"en": "Current risk stage", "ta": "தற்போதைய ஆபத்து நிலை"},
    "plan_alt_heading": {"en": "Alternate options to discuss with your doctor", "ta": "உங்கள் மருத்துவரிடம் விவாதிக்க வேண்டிய மாற்று வழிகள்"},
    "plan_diet_heading": {"en": "Heart-healthy diet plan", "ta": "இதயத்திற்கு ஆரோக்கியமான உணவு திட்டம்"},
    "plan_quote_heading": {"en": "Today's motivation", "ta": "இன்றைய ஊக்கமூட்டல்"},
    "plan_disclaimer": {
        "en": "These are general educational suggestions, not a prescription. Please review any changes with your doctor before starting them, especially any change to medication.",
        "ta": "இவை பொதுவான கல்வி பரிந்துரைகள் மட்டுமே, மருந்து பரிந்துரை அல்ல. எந்த மாற்றத்தையும் தொடங்கும் முன், குறிப்பாக மருந்து மாற்றங்களை, உங்கள் மருத்துவரிடம் சரிபார்க்கவும்.",
    },

    # ---- reports / uploads ---------------------------------------------------
    "reports_title": {"en": "My scan & test reports", "ta": "எனது ஸ்கேன் & பரிசோதனை அறிக்கைகள்"},
    "reports_subtitle": {
        "en": "Upload photos or PDFs of your ECG, angiogram, blood test, or other heart-related reports. Only you can see your own uploads — they are never shown to other users.",
        "ta": "உங்கள் ECG, ஆஞ்சியோகிராம், இரத்த பரிசோதனை அல்லது பிற இதய அறிக்கைகளின் புகைப்படங்கள் அல்லது PDF-களை பதிவேற்றவும். உங்கள் பதிவேற்றங்களை நீங்கள் மட்டுமே பார்க்க முடியும் — வேறு எந்த பயனருக்கும் காட்டப்படாது.",
    },
    "label_report_file": {"en": "Choose a file (image or PDF, max 10 MB)", "ta": "ஒரு கோப்பைத் தேர்ந்தெடுக்கவும் (படம் அல்லது PDF, அதிகபட்சம் 10 MB)"},
    "label_report_note": {"en": "Note (optional) — e.g. \"ECG, 12 July\"", "ta": "குறிப்பு (விருப்பம்) — எ.கா. \"ECG, ஜூலை 12\""},
    "btn_upload": {"en": "Upload report", "ta": "அறிக்கையை பதிவேற்று"},
    "reports_gallery_heading": {"en": "Your uploaded reports", "ta": "நீங்கள் பதிவேற்றிய அறிக்கைகள்"},
    "reports_empty": {"en": "No reports uploaded yet.", "ta": "இன்னும் எந்த அறிக்கையும் பதிவேற்றப்படவில்லை."},
    "btn_delete": {"en": "Delete", "ta": "நீக்கு"},
    "uploaded_on": {"en": "Uploaded", "ta": "பதிவேற்றப்பட்டது"},
}


def t(key: str, lang: str = DEFAULT_LANGUAGE) -> str:
    """Look up a UI string by key for the given language, falling back to
    English (and finally the raw key) if something is missing."""
    entry = STRINGS.get(key)
    if entry is None:
        return key
    return entry.get(lang) or entry.get(DEFAULT_LANGUAGE) or key
