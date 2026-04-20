import re
from typing import Any, Dict

try:
    from backend.calculator import AttendanceCalculator
    from backend.json_loader import SUBJECT_CODE_MAP, load_all_json_data, search_json, session_context
    from backend.llm_handler import get_llm_response
    from backend.model_predictor import load_models, predict_both
    from backend.retriever import retrieve_context
except ImportError:
    from calculator import AttendanceCalculator
    from json_loader import SUBJECT_CODE_MAP, load_all_json_data, search_json, session_context
    from llm_handler import get_llm_response
    from model_predictor import load_models, predict_both
    from retriever import retrieve_context


JSON_DATA = load_all_json_data()

# Load ML models on startup
load_models()

# Confidence thresholds
INTENT_THRESHOLD = 0.55
SUBJECT_THRESHOLD = 0.60


def get_theory_code(code: str) -> str:
    """
    Always returns theory course code.
    Converts lab code to theory code if needed.
    CS401P → CS401L
    IT301P → IT301L
    CS206P → CS206L
    CS301P → CS301L
    IT302P → IT302L
    """
    LAB_TO_THEORY = {
        "CS401P": "CS401L",
        "IT301P": "IT301L",
        "CS206P": "CS206L",
        "CS301P": "CS301L",
        "IT302P": "IT302L",
    }
    return LAB_TO_THEORY.get(code, code)


def _resolve_subject_from_query(query: str) -> str:
    query_lower = query.lower()
    sorted_keywords = sorted(SUBJECT_CODE_MAP.keys(), key=len, reverse=True)
    for keyword in sorted_keywords:
        if re.search(rf"\b{re.escape(keyword)}\b", query_lower):
            return SUBJECT_CODE_MAP[keyword]
    return ""


def format_attendance_result(result: Dict[str, Any]) -> str:
    status = "Detained" if result.get("is_detained") else "Safe"
    return (
        f"Current Attendance: {result.get('current_percentage', 0)}%\n"
        f"Status: {status}\n"
        f"Classes needed to reach 75%: {result.get('classes_needed_to_reach_75', 0)}\n"
        f"Classes you can still skip: {result.get('classes_can_skip', 0)}\n"
        f"Message: {result.get('status_message', '')}"
    )


def handle_chat(query: str, vector_store=None, session_id: str = "default") -> Dict[str, Any]:
    """
    ML-powered hybrid routing:
    1. ML model detects intent + subject (handles spelling mistakes)
    2. Session memory fills in subject for follow-up queries
    3. JSON lookup for instant structured answers
    4. Calculator for math queries
    5. RAG + LLM for complex/unstructured queries
    """

    # -- STEP 1: ML Prediction --
    prediction = predict_both(query)

    intent = prediction["intent"]
    intent_conf = prediction["intent_confidence"]
    subject_code = prediction["subject_code"]
    subject_conf = prediction["subject_confidence"]

    print(f"[ML] Query: '{query}'")
    print(f"[ML] Intent: {intent} ({intent_conf:.2f})")
    print(f"[ML] Subject: {subject_code} ({subject_conf:.2f})")

    # -- STEP 2: Subject Context Memory --
    subject_reliable = subject_conf >= SUBJECT_THRESHOLD
    intent_reliable = intent_conf >= INTENT_THRESHOLD

    explicit_subject = _resolve_subject_from_query(query)

    if subject_reliable:
        # Update session with newly detected subject
        # Always store theory code, not lab code
        session_context[session_id] = {
            "last_subject_code": get_theory_code(subject_code),
            "last_subject_confidence": subject_conf,
        }
    elif explicit_subject:
        subject_code = explicit_subject
        session_context[session_id] = {
            "last_subject_code": get_theory_code(subject_code),
            "last_subject_confidence": subject_conf,
        }
    else:
        # Subject not confident in this query -> use last known
        if session_id in session_context:
            subject_code = session_context[session_id]["last_subject_code"]
            print(f"[CONTEXT] Using remembered subject: {subject_code}")
        else:
            subject_code = None

    # -- STEP 3: Build enriched query for JSON lookup --
    enriched_query = query
    if subject_code and intent_reliable:
        enriched_query = f"{subject_code} {intent} {query}"
        print(f"[ENRICHED] {enriched_query}")

    # -- STEP 4: Route by intent --

    # Calculator intents - no JSON needed
    if intent == "attendance" and intent_conf >= 0.65:
        numbers = re.findall(r"\d+", query)
        if len(numbers) >= 2:
            total = int(numbers[0])
            attended = int(numbers[1])
            if attended > total:
                return {
                    "answer": "⚠️ Attended classes cannot exceed total classes. Please recheck.",
                    "sources": [],
                    "type": "calculator_error",
                    "branch_note": "CSE/CS branch only",
                }
            result = AttendanceCalculator().calculate(total, attended)
            return {
                "answer": format_attendance_result(result),
                "sources": ["Attendance Calculator"],
                "type": "calculator",
                "branch_note": "CSE/CS branch only",
            }
        return {
            "answer": (
                "Please provide both numbers!\n\n"
                "Examples:\n"
                "• 'I attended 35 out of 50 classes'\n"
                "• 'Total 60 classes, present in 40'\n"
                "• '30 attended 45 total'"
            ),
            "sources": [],
            "type": "calculator_input_needed",
            "branch_note": "CSE/CS branch only",
        }

    if intent == "cgpa" and intent_conf >= 0.65:
        return {
            "answer": (
                "Please use the **🎯 CGPA Calculator** tab in the sidebar.\n\n"
                "It has your actual subject list pre-filled with credits. "
                "Just select your grade for each subject!"
            ),
            "sources": [],
            "type": "calculator_redirect",
            "branch_note": "CSE/CS branch only",
        }

    # -- STEP 5: JSON Lookup --
    json_result = search_json(enriched_query, JSON_DATA, session_id)
    if json_result and json_result.get("found"):
        return {
            "answer": json_result["formatted_answer"],
            "sources": [json_result["source"]],
            "type": "json_lookup",
            "branch_note": "CSE/CS branch only",
        }

    # Also try with original query if enriched failed
    if enriched_query != query:
        json_result2 = search_json(query, JSON_DATA, session_id)
        if json_result2 and json_result2.get("found"):
            return {
                "answer": json_result2["formatted_answer"],
                "sources": [json_result2["source"]],
                "type": "json_lookup",
                "branch_note": "CSE/CS branch only",
            }

    # -- STEP 6: RAG Fallback --
    if vector_store:
        try:
            retrieved = retrieve_context(query, vector_store)
            context = retrieved[0] if isinstance(retrieved, tuple) else retrieved
            answer = get_llm_response(query, context)
            return {
                "answer": answer,
                "sources": ["PDF Documents"],
                "type": "rag",
                "branch_note": "CSE/CS branch only",
            }
        except Exception as error:
            print(f"[RAG ERROR] {error}")

    return {
        "answer": (
            "I couldn't find information about this. "
            "Could you rephrase or be more specific?\n\n"
            "Try asking like:\n"
            "• 'Syllabus of DAA'\n"
            "• 'Marks of Computer Networks'\n"
            "• 'When is MSE1?'"
        ),
        "sources": [],
        "type": "not_found",
        "branch_note": "CSE/CS branch only",
    }
