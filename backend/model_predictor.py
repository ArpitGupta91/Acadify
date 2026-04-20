import os
from pathlib import Path

import joblib

# Load models once at module level (happens at server startup)
_intent_model = None
_subject_model = None


def _models_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "models"


def load_models():
    global _intent_model, _subject_model

    models_dir = _models_dir()
    intent_path = models_dir / "intent_classifier.pkl"
    subject_path = models_dir / "subject_classifier.pkl"

    if not intent_path.exists() or not subject_path.exists():
        print("[MODEL] WARNING: .pkl files not found.")
        print("[MODEL] Please run: python backend/train_models.py")
        return False

    _intent_model = joblib.load(intent_path)
    _subject_model = joblib.load(subject_path)
    print("[MODEL] Intent classifier loaded.")
    print("[MODEL] Subject classifier loaded.")
    return True


def predict_intent(query: str) -> tuple:
    """
    Returns (intent_label, confidence_score)
    Example: ("syllabus", 0.94)
    """
    if _intent_model is None:
        return ("unknown", 0.0)

    proba = _intent_model.predict_proba([query])[0]
    classes = _intent_model.classes_
    best_idx = proba.argmax()

    return (classes[best_idx], float(proba[best_idx]))


def predict_subject(query: str) -> tuple:
    """
    Returns (subject_code, confidence_score)
    Example: ("CS401L", 0.91)
    """
    if _subject_model is None:
        return ("unknown", 0.0)

    proba = _subject_model.predict_proba([query])[0]
    classes = _subject_model.classes_
    best_idx = proba.argmax()

    return (classes[best_idx], float(proba[best_idx]))


def predict_both(query: str) -> dict:
    """
    Returns both intent and subject in one call.
    Used by chat_handler.py for every query.
    """
    intent, intent_conf = predict_intent(query)
    subject, subject_conf = predict_subject(query)

    return {
        "intent": intent,
        "intent_confidence": intent_conf,
        "subject_code": subject,
        "subject_confidence": subject_conf,
        # Only trust subject if confidence is high enough
        "subject_reliable": subject_conf >= 0.60,
        # Only trust intent if confidence is high enough
        "intent_reliable": intent_conf >= 0.55,
    }
