"""
health_content.py
------------------
Rule-based, *educational* content that is layered on top of a model
prediction:

1. determine_stage()   -- buckets the prediction into a plain-language
                           "risk stage" using the probability plus a couple
                           of clinically-meaningful inputs (vessels narrowed,
                           exercise strain, chest pain on exertion).
2. STAGE_PLANS          -- for each stage: alternate options to raise with a
                           doctor, and a heart-healthy diet plan. Every string
                           is written in English and Tamil.
3. QUOTES               -- a rotating list of short, positive, heart-health
                           quotes/affirmations shown to the patient.

None of this is medical advice or a prescription -- it deliberately avoids
naming drugs, dosages, or anything that requires a clinician's judgement.
It's meant to give people a plain-language starting point for a
conversation with their own doctor, plus some everyday encouragement.
"""

import random

STAGES = ["low", "borderline", "elevated", "high"]

STAGE_LABELS = {
    "low": {"en": "Low risk pattern", "ta": "குறைந்த ஆபத்து நிலை"},
    "borderline": {"en": "Borderline risk pattern", "ta": "எல்லைக்கோடு ஆபத்து நிலை"},
    "elevated": {"en": "Elevated risk pattern", "ta": "அதிகரித்த ஆபத்து நிலை"},
    "high": {"en": "High risk pattern", "ta": "அதிக ஆபத்து நிலை"},
}


def determine_stage(probability_disease: float, patient: dict) -> str:
    """
    Map a model probability + a few raw clinical fields to a coarse,
    plain-language "stage". This is intentionally simple (thresholds, not a
    second model) so it stays transparent and easy to explain to a patient --
    the opposite goal of the SHAP/LIME panels, which explain the *model*.
    """
    ca = patient.get("ca", 0) or 0
    oldpeak = patient.get("oldpeak", 0) or 0
    exang = patient.get("exang", 0) or 0

    # Start from the model's probability...
    if probability_disease < 0.25:
        stage = "low"
    elif probability_disease < 0.50:
        stage = "borderline"
    elif probability_disease < 0.75:
        stage = "elevated"
    else:
        stage = "high"

    # ...then nudge up a level if strong physical warning signs are present,
    # even when the model's probability alone looks moderate. Never nudge
    # downward -- we only add caution, never remove it.
    warning_signs = (ca >= 2) + (oldpeak >= 2.0) + (exang == 1)
    if warning_signs >= 2 and stage in ("low", "borderline"):
        idx = STAGES.index(stage)
        stage = STAGES[min(idx + 1, len(STAGES) - 1)]

    return stage


STAGE_PLANS = {
    "low": {
        "alternatives": {
            "en": [
                "Keep up an annual check-up with routine blood pressure and cholesterol screening.",
                "Ask your doctor whether a baseline ECG is worth having on file, even with no symptoms.",
                "If you have a family history of heart disease, mention it at your next visit — screening schedules sometimes change because of it.",
            ],
            "ta": [
                "வருடாந்திர பரிசோதனையையும், வழக்கமான இரத்த அழுத்தம் மற்றும் கொழுப்பு பரிசோதனையையும் தொடரவும்.",
                "அறிகுறிகள் இல்லாவிட்டாலும், ஒரு அடிப்படை ECG பதிவு செய்து வைக்க வேண்டுமா என்று உங்கள் மருத்துவரிடம் கேளுங்கள்.",
                "குடும்பத்தில் இதய நோய் வரலாறு இருந்தால், அடுத்த வருகையில் அதை குறிப்பிடவும் — பரிசோதனை அட்டவணை மாறக்கூடும்.",
            ],
        },
        "diet": {
            "en": [
                "Base most meals on vegetables, whole grains (brown rice, whole wheat, millets/ragi), and legumes (dal, chickpeas, sprouts).",
                "Use minimal added oil/ghee for daily cooking; prefer steaming, boiling, or light sautéing over deep frying.",
                "Include a handful of nuts or seeds a few times a week (unsalted almonds, walnuts, flaxseed).",
                "Limit added sugar and sweetened drinks/tea to occasional treats rather than daily habit.",
                "Keep table salt and pickles/papad modest — most days, aim for gently seasoned rather than heavily salted food.",
            ],
            "ta": [
                "பெரும்பாலான உணவுகளில் காய்கறிகள், முழு தானியங்கள் (சிவப்பு அரிசி, கோதுமை, சிறுதானியங்கள்/கேழ்வரகு), பருப்பு வகைகள் (பருப்பு, கொண்டைக்கடலை, முளைகட்டிய தானியங்கள்) இருக்கட்டும்.",
                "தினசரி சமையலில் எண்ணெய்/நெய் அளவைக் குறைக்கவும்; வறுப்பதைக் காட்டிலும் வேகவைத்தல் அல்லது இலேசாக வதக்குதலை தேர்வு செய்யவும்.",
                "வாரத்தில் சில முறை ஒரு கைப்பிடி அளவு பருப்பு/விதைகள் (உப்பு சேர்க்காத பாதாம், வால்நட், ஆளி விதை) சேர்க்கவும்.",
                "சேர்க்கப்பட்ட சர்க்கரை மற்றும் இனிப்பு பானங்கள்/தேநீரை தினசரி பழக்கமாக இல்லாமல் எப்போதாவது மட்டும் எடுக்கவும்.",
                "உப்பு மற்றும் ஊறுகாய்/பாப்பட் அளவை மிதமாக வைக்கவும் — பெரும்பாலான நாட்களில் லேசான சுவை போதும்.",
            ],
        },
    },
    "borderline": {
        "alternatives": {
            "en": [
                "Discuss a repeat blood pressure and lipid (cholesterol) panel in the next few months to confirm this isn't a one-off reading.",
                "Ask about a supervised exercise stress test if you haven't had one, especially if exercise brings on any chest discomfort.",
                "Bring up your fasting blood sugar result with your doctor — borderline heart risk and blood sugar often need to be managed together.",
                "Consider a structured walking or cardio routine (e.g. 30 minutes most days) after your doctor confirms it's safe for you.",
            ],
            "ta": [
                "இது ஒரு தற்காலிக அளவீடு அல்ல என்பதை உறுதி செய்ய, அடுத்த சில மாதங்களில் இரத்த அழுத்தம் மற்றும் கொழுப்பு பரிசோதனையை மீண்டும் செய்ய விவாதிக்கவும்.",
                "உடற்பயிற்சியின்போது மார்பு அசெளகரியம் இருந்தால், மேற்பார்வையிடப்பட்ட உடற்பயிற்சி மன அழுத்த பரிசோதனை (stress test) பற்றி கேளுங்கள்.",
                "உண்ணாவிரத இரத்த சர்க்கரை முடிவை உங்கள் மருத்துவரிடம் விவாதிக்கவும் — எல்லைக்கோடு இதய ஆபத்தும் இரத்த சர்க்கரையும் பெரும்பாலும் ஒன்றாக நிர்வகிக்கப்பட வேண்டும்.",
                "பாதுகாப்பானது என உங்கள் மருத்துவர் உறுதி செய்த பிறகு, ஒரு கட்டமைக்கப்பட்ட நடைப்பயிற்சி அல்லது கார்டியோ வழக்கத்தை (பெரும்பாலான நாட்களில் 30 நிமிடங்கள்) பரிசீலிக்கவும்.",
            ],
        },
        "diet": {
            "en": [
                "Move toward a Mediterranean/DASH-style pattern: more vegetables, fruit, whole grains, and fish or legumes instead of red meat.",
                "Swap deep-fried snacks (bajji, vada, chips) for roasted or steamed alternatives (roasted chana, idli, steamed dhokla) most days.",
                "Reduce visible salt: taste before adding salt, cut back on papad/pickle/processed sauces.",
                "Choose low-fat dairy (curd, milk) over full-cream versions where practical.",
                "Keep a consistent eating schedule and modest portion sizes rather than large, infrequent meals.",
            ],
            "ta": [
                "மத்திய தரைக்கடல்/DASH பாணி உணவுமுறையை நோக்கி நகரவும்: அதிக காய்கறிகள், பழங்கள், முழு தானியங்கள், சிவப்பு இறைச்சிக்கு பதிலாக மீன் அல்லது பருப்பு வகைகள்.",
                "வறுத்த சிற்றுண்டிகளுக்கு (பஜ்ஜி, வடை, சிப்ஸ்) பதிலாக பொரித்த அல்லது வேகவைத்த மாற்றுகளை (வறுத்த கடலை, இட்லி, தோக்லா) தேர்வு செய்யவும்.",
                "காணக்கூடிய உப்பைக் குறைக்கவும்: உப்பு சேர்க்கும் முன் சுவைத்துப் பாருங்கள், பாப்பட்/ஊறுகாய்/பதப்படுத்தப்பட்ட சாஸ்களைக் குறைக்கவும்.",
                "முடிந்தவரை முழு கிரீம் பால் பொருட்களுக்கு பதிலாக குறைந்த கொழுப்புள்ள தயிர்/பால் தேர்வு செய்யவும்.",
                "பெரிய, அரிதான உணவுகளுக்கு பதிலாக, சீரான உண்ணும் நேரம் மற்றும் மிதமான அளவு உணவை பின்பற்றவும்.",
            ],
        },
    },
    "elevated": {
        "alternatives": {
            "en": [
                "Ask your doctor about a cardiology referral to review these numbers together, rather than managing them alone.",
                "Bring up cardiac rehabilitation or a medically supervised exercise program as a structured, safer alternative to starting exercise on your own.",
                "If chest pain occurs with exertion, ask specifically about further tests (e.g. stress echocardiogram, angiogram) rather than waiting it out.",
                "Ask whether home blood pressure monitoring between visits would help track things more closely.",
            ],
            "ta": [
                "இந்த எண்களை தனியாக நிர்வகிப்பதற்கு பதிலாக, ஒரு இதயநோய் நிபுணரிடம் ஆலோசனை பெற உங்கள் மருத்துவரிடம் கேளுங்கள்.",
                "தானாகவே உடற்பயிற்சியைத் தொடங்குவதற்குப் பதிலாக, கட்டமைக்கப்பட்ட, பாதுகாப்பான மாற்றாக இதய மறுவாழ்வு (cardiac rehab) அல்லது மருத்துவ மேற்பார்வையிலான உடற்பயிற்சி திட்டத்தைப் பற்றி கேளுங்கள்.",
                "உடற்பயிற்சியின்போது மார்பு வலி ஏற்பட்டால், காத்திருப்பதற்கு பதிலாக மேலதிக பரிசோதனைகள் (stress echo, angiogram) பற்றி குறிப்பாக கேளுங்கள்.",
                "வருகைகளுக்கு இடையே வீட்டில் இரத்த அழுத்தத்தை கண்காணிப்பது உதவுமா என்று கேளுங்கள்.",
            ],
        },
        "diet": {
            "en": [
                "Work toward a strict low-sodium pattern: avoid packaged/processed foods, restaurant curries, and salted snacks as a daily habit.",
                "Prioritise fibre-rich foods (oats, whole millets, vegetables, fruit with skin where safe) to help manage cholesterol.",
                "Limit fried food and full-fat dairy/ghee to rare occasions rather than daily use.",
                "Keep alcohol and sugary drinks to a minimum, or avoid them, and discuss this specifically with your doctor.",
                "Ask your doctor or a dietitian for a personalised plan — at this stage, general guidance works best alongside professional review.",
            ],
            "ta": [
                "கடுமையான குறைந்த உப்பு உணவுமுறையை நோக்கி பணியாற்றவும்: பொதி/பதப்படுத்தப்பட்ட உணவுகள், உணவகக் குழம்புகள், உப்பிட்ட சிற்றுண்டிகளை தினசரி பழக்கமாக தவிர்க்கவும்.",
                "கொழுப்பை நிர்வகிக்க உதவும் நார்ச்சத்து நிறைந்த உணவுகளுக்கு (ஓட்ஸ், சிறுதானியங்கள், காய்கறிகள், தோலுடன் கூடிய பழங்கள்) முன்னுரிமை கொடுங்கள்.",
                "வறுத்த உணவு மற்றும் முழு கொழுப்பு பால் பொருட்கள்/நெய்யை தினசரி பயன்பாட்டிற்கு பதிலாக அரிதாக மட்டும் எடுக்கவும்.",
                "மது மற்றும் இனிப்பு பானங்களை குறைந்தபட்சமாக வைக்கவும் அல்லது தவிர்க்கவும், இதை உங்கள் மருத்துவரிடம் குறிப்பாக விவாதிக்கவும்.",
                "இந்த நிலையில், பொது வழிகாட்டுதலுடன் மருத்துவ ஆலோசனையும் தேவை — உங்கள் மருத்துவர் அல்லது உணவியல் நிபுணரிடம் தனிப்பயன் திட்டம் கேளுங்கள்.",
            ],
        },
    },
    "high": {
        "alternatives": {
            "en": [
                "Please treat this as a prompt to see a doctor or cardiologist soon rather than a wait-and-watch situation — this tool cannot diagnose you, but the pattern here is worth acting on.",
                "If you currently have chest pain, breathlessness, or pain spreading to your arm/jaw, treat that as an emergency and seek immediate medical care.",
                "Ask specifically about further diagnostic tests (angiogram, echocardiogram) so treatment decisions are based on direct evidence, not just this estimate.",
                "Ask about a formal cardiac rehabilitation program rather than changing your exercise or medication routine on your own.",
            ],
            "ta": [
                "இதை காத்திருந்து பார்க்கும் நிலையாக அல்ல, விரைவில் ஒரு மருத்துவரை அல்லது இதயநோய் நிபுணரை பார்க்க வேண்டிய அறிகுறியாக கருதவும் — இந்த கருவி நோயறிதல் செய்யாது, ஆனால் இந்த மாதிரி நடவடிக்கை எடுக்கத் தகுந்தது.",
                "தற்போது மார்பு வலி, மூச்சுத் திணறல், அல்லது கை/தாடைக்கு பரவும் வலி இருந்தால், அதை அவசரநிலையாக கருதி உடனடியாக மருத்துவ உதவி பெறவும்.",
                "இந்த மதிப்பீட்டை மட்டும் நம்பாமல், நேரடி ஆதாரங்களின் அடிப்படையில் சிகிச்சை முடிவெடுக்க, மேலதிக பரிசோதனைகள் (angiogram, echocardiogram) பற்றி குறிப்பாக கேளுங்கள்.",
                "உங்கள் சொந்த முடிவில் உடற்பயிற்சி அல்லது மருந்து வழக்கத்தை மாற்றுவதற்கு பதிலாக, முறையான இதய மறுவாழ்வு திட்டத்தைப் பற்றி கேளுங்கள்.",
            ],
        },
        "diet": {
            "en": [
                "Follow any diet plan your cardiologist or dietitian gives you first — this general list is a supplement to that, not a replacement.",
                "As a general pattern: very limited salt/sodium, minimal fried and processed food, and an emphasis on vegetables, whole grains, and lean protein.",
                "Avoid trans fats and excessive ghee/oil (deep-fried snacks, bakery items) as a daily habit.",
                "Keep portions modest and eating times regular; avoid skipping meals and then overeating later.",
                "Track how you feel after meals (breathlessness, discomfort) and mention any pattern you notice to your doctor.",
            ],
            "ta": [
                "முதலில் உங்கள் இதயநோய் நிபுணர் அல்லது உணவியல் நிபுணர் தரும் உணவுத் திட்டத்தைப் பின்பற்றவும் — இந்த பொதுவான பட்டியல் அதற்கு துணையாக மட்டுமே, மாற்றாக அல்ல.",
                "பொது வழிகாட்டுதலாக: மிகக் குறைந்த உப்பு, குறைந்தபட்ச வறுத்த/பதப்படுத்தப்பட்ட உணவு, மற்றும் காய்கறிகள், முழு தானியங்கள், மெலிந்த புரதத்திற்கு முக்கியத்துவம்.",
                "டிரான்ஸ் கொழுப்புகள் மற்றும் அதிகப்படியான நெய்/எண்ணெயை (வறுத்த சிற்றுண்டிகள், பேக்கரி பொருட்கள்) தினசரி பழக்கமாக தவிர்க்கவும்.",
                "மிதமான அளவு உணவு மற்றும் சீரான உணவு நேரங்களை பராமரிக்கவும்; உணவைத் தவிர்த்து பின்னர் அதிகமாக சாப்பிடுவதைத் தவிர்க்கவும்.",
                "உணவுக்குப் பிறகு நீங்கள் எப்படி உணர்கிறீர்கள் என்பதை (மூச்சுத் திணறல், அசெளகரியம்) கவனித்து, கவனிக்கும் எந்த மாதிரியையும் உங்கள் மருத்துவரிடம் கூறவும்.",
            ],
        },
    },
}


QUOTES = [
    {"en": "A healthy heart today is a gift to the person you'll be in twenty years.",
     "ta": "இன்று ஆரோக்கியமான இதயம் என்பது இருபது ஆண்டுகள் கழித்து நீங்கள் இருக்கப்போகும் நபருக்கான பரிசு."},
    {"en": "Small, steady changes — a short walk, one less fried snack — add up more than one big effort ever will.",
     "ta": "சிறிய, நிலையான மாற்றங்கள் — ஒரு குறுகிய நடைப்பயிற்சி, ஒரு குறைவான வறுத்த சிற்றுண்டி — ஒரு பெரிய முயற்சியை விட அதிகமாக சேரும்."},
    {"en": "Every meal is a new chance to be kind to your heart.",
     "ta": "ஒவ்வொரு உணவும் உங்கள் இதயத்திற்கு அன்பு காட்ட ஒரு புதிய வாய்ப்பு."},
    {"en": "You don't need to be perfect — you need to be consistent.",
     "ta": "நீங்கள் முழுமையாக இருக்க வேண்டியதில்லை — தொடர்ச்சியாக இருக்க வேண்டும்."},
    {"en": "Taking this test is already a sign you care about your health — that matters.",
     "ta": "இந்த பரிசோதனையை எடுத்திருப்பது நீங்கள் உங்கள் ஆரோக்கியத்தை பற்றி கவலைப்படுகிறீர்கள் என்பதற்கான அடையாளம் — அது முக்கியம்."},
    {"en": "Walking is medicine you can take for free, any time of day.",
     "ta": "நடைபயிற்சி என்பது நாள் முழுவதும் இலவசமாக எடுக்கக்கூடிய மருந்து."},
    {"en": "Your heart has been with you every single day of your life — a little care goes a long way back.",
     "ta": "உங்கள் வாழ்க்கையின் ஒவ்வொரு நாளும் உங்கள் இதயம் உங்களுடன் இருந்திருக்கிறது — கொஞ்சம் கவனிப்பு நீண்ட தூரம் செல்லும்."},
    {"en": "Progress, not perfection, is what protects your heart over the years.",
     "ta": "ஆண்டுகளாக உங்கள் இதயத்தைப் பாதுகாப்பது முழுமையல்ல, முன்னேற்றம்தான்."},
    {"en": "A calm mind and a good night's sleep are heart medicine too.",
     "ta": "அமைதியான மனமும் நல்ல தூக்கமும் இதயத்திற்கான மருந்துகள்தான்."},
    {"en": "You are not just a number on a screen — you're someone worth taking care of.",
     "ta": "நீங்கள் திரையில் ஒரு எண் மட்டுமல்ல — நீங்கள் கவனிக்கப்பட வேண்டிய ஒருவர்."},
    {"en": "Laughter, connection with loved ones, and light movement are all part of a healthy heart.",
     "ta": "சிரிப்பு, அன்புக்குரியவர்களுடன் தொடர்பு, இலகுவான உடல் அசைவு ஆகியவை ஆரோக்கியமான இதயத்தின் ஒரு பகுதி."},
    {"en": "One good habit at a time is still real progress.",
     "ta": "ஒரு நேரத்தில் ஒரு நல்ல பழக்கம் கூட உண்மையான முன்னேற்றம்தான்."},
]


def get_stage_label(stage: str, lang: str) -> str:
    entry = STAGE_LABELS.get(stage, STAGE_LABELS["borderline"])
    return entry.get(lang) or entry["en"]


def get_stage_plan(stage: str, lang: str) -> dict:
    plan = STAGE_PLANS.get(stage, STAGE_PLANS["borderline"])
    return {
        "stage": stage,
        "stage_label": get_stage_label(stage, lang),
        "alternatives": plan["alternatives"].get(lang) or plan["alternatives"]["en"],
        "diet": plan["diet"].get(lang) or plan["diet"]["en"],
    }


def get_random_quote(lang: str) -> str:
    q = random.choice(QUOTES)
    return q.get(lang) or q["en"]
