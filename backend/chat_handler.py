import random
import re
from datetime import date, datetime
from typing import Any, Dict

try:
    from .calculator import AttendanceCalculator
    from .json_loader import (
        SUBJECT_CODE_MAP,
        get_next_holiday,
        is_professional_elective_query,
        load_all_json_data,
        parse_holiday_date,
        search_json,
        session_context,
    )
    from .llm_handler import get_llm_response
    from .model_predictor import load_models, predict_both
    from .retriever import retrieve_context
except ImportError:
    from calculator import AttendanceCalculator
    from json_loader import (
        SUBJECT_CODE_MAP,
        get_next_holiday,
        is_professional_elective_query,
        load_all_json_data,
        parse_holiday_date,
        search_json,
        session_context,
    )
    from llm_handler import get_llm_response
    from model_predictor import load_models, predict_both
    from retriever import retrieve_context


JSON_DATA = load_all_json_data()

# Load ML models on startup
load_models()

# Confidence thresholds
INTENT_THRESHOLD = 0.55
SUBJECT_THRESHOLD = 0.60


GREETING_PATTERNS = [
    r"\b(hi|hello|hey|hii|helo|heyy|howdy|greetings|good morning|good afternoon|good evening|good night|sup|what's up|whats up|namaste)\b"
]

GREETING_RESPONSES = [
    "Hello! Welcome to KIET Academic Assistant. How can I help you today?",
    "Hi there! I am your KIET Academic Assistant. What would you like to know?",
    "Hey! Great to see you! Ask me anything about your syllabus, exams, attendance, or holidays.",
    "Hello! I am here to help with your academic queries at KIET. What is on your mind?",
]


def is_greeting(query: str) -> bool:
    query_lower = query.lower().strip()
    for pattern in GREETING_PATTERNS:
        if re.search(pattern, query_lower):
            return True
    words = query_lower.split()
    if len(words) <= 2 and any(w in ["hi", "hello", "hey", "hii", "helo"] for w in words):
        return True
    return False


OUT_OF_SCOPE_PATTERNS = [
    r"\b(cricket|ipl|football|movie|song|music|recipe|cook|weather|news|politics|stock|share market|game|meme|joke|girlfriend|boyfriend|love|dating|instagram|youtube|tiktok|netflix)\b"
]

OUT_OF_SCOPE_RESPONSES = [
    "Sorry, I can only help with academic queries related to KIET such as syllabus, exam dates, attendance, holidays, and CGPA.",
    "That is outside my area! I am trained only for KIET academic topics like courses, exams, and schedules. Try asking me about your subjects!",
    "I am not able to help with that. But I can answer questions about your syllabus, MSE/ESE dates, attendance, or CGPA!",
]


def is_out_of_scope(query: str) -> bool:
    query_lower = query.lower()
    for pattern in OUT_OF_SCOPE_PATTERNS:
        if re.search(pattern, query_lower):
            return True
    return False


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


def format_single_subject_response(subject: Dict[str, Any]) -> str:
    course_name = subject.get("course_name", subject.get("subject_name", "Unknown Subject"))
    course_code = subject.get("course_code", "")
    credits = subject.get("credits", "")
    total_hours = subject.get("total_hours", subject.get("total_lecture_hours", ""))

    lines = [f"**{course_name} ({course_code})**"]
    if credits != "":
        lines.append(f"Credits: {credits}")
    if total_hours != "":
        lines.append(f"Total Hours: {total_hours}")

    units = subject.get("units", [])
    if isinstance(units, list) and units:
        lines.append("\n**Units:**")
        for unit in units:
            if not isinstance(unit, dict):
                continue
            unit_no = unit.get("unit_no", "?")
            title = unit.get("title", "")
            lines.append(f"Unit {unit_no}: {title}")
            for topic in unit.get("topics", []) or []:
                lines.append(f"- {topic}")

    return "\n".join(lines)


def format_professional_elective_response(pe_data: Any, query: str) -> str:
    query_lower = query.lower()

    subjects = []
    if isinstance(pe_data, list):
        subjects = [s for s in pe_data if isinstance(s, dict)]
    elif isinstance(pe_data, dict):
        if isinstance(pe_data.get("subjects"), list):
            subjects = [s for s in pe_data.get("subjects", []) if isinstance(s, dict)]
        elif isinstance(pe_data.get("electives"), list):
            subjects = [s for s in pe_data.get("electives", []) if isinstance(s, dict)]
        else:
            pe1 = pe_data.get("professional_elective_1", {})
            if isinstance(pe1, dict):
                subjects = [s for s in pe1.get("electives", []) if isinstance(s, dict)]

    alias_map = {
        "cs318e": ["frontend engineering", "react", "next", "nextjs", "full stack", "full stack development"],
        "cs307e": ["intelligent systems", "text and vision", "vision api", "text & vision", "text vision"],
        "cs304e": ["devops", "version control", "git workflows"],
        "cs335e": ["aws foundations", "data engineering", "aws"],
        "cs321e": ["ios", "apple", "swift", "xcode"],
        "it306e": ["azure fundamentals", "azure", "az-900"],
    }

    matched_subject: Dict[str, Any] = {}
    best_score = 0

    for subject in subjects:
        name = str(subject.get("course_name", subject.get("subject_name", ""))).lower()
        code = str(subject.get("course_code", "")).lower()

        subject_aliases = list(alias_map.get(code, []))
        subject_aliases.extend([name, code])

        score = 0
        for alias in subject_aliases:
            alias = alias.strip().lower()
            if alias and alias in query_lower:
                # Phrase-level matches should dominate token-level noise.
                score += max(2, len(alias.split()))

        if score > best_score:
            best_score = score
            matched_subject = subject

    unit_match = re.search(r"unit\s*(\d+)", query_lower)
    if unit_match:
        unit_num = int(unit_match.group(1))
        target = matched_subject if matched_subject else None
        if not target and subjects:
            target = subjects[0]

        if target:
            for unit in target.get("units", []) or []:
                if not isinstance(unit, dict):
                    continue
                if int(unit.get("unit_no", -1)) == unit_num:
                    topics = unit.get("topics", []) or []
                    return (
                        f"{target.get('course_name', 'Professional Elective')} - Unit {unit_num}: {unit.get('title', '')}\n"
                        + "\n".join([f"- {topic}" for topic in topics])
                    )

    if matched_subject and best_score > 0:
        return format_single_subject_response(matched_subject)

    result = "4th Semester Professional Electives (Choose 1):\n\n"
    for i, subject in enumerate(subjects):
        name = subject.get("course_name", subject.get("subject_name", "Unknown"))
        code = subject.get("course_code", "")
        credits = subject.get("credits", "")
        result += f"{i + 1}. {name} ({code})"
        if credits != "":
            result += f" | {credits} Credits"
        result += "\n"

    result += "\nAsk me about any specific elective for full syllabus details!"
    return result


def handle_chat(query: str, vector_store=None, session_id: str = "default") -> Dict[str, Any]:
    """
    ML-powered hybrid routing:
    1. ML model detects intent + subject (handles spelling mistakes)
    2. Session memory fills in subject for follow-up queries
    3. JSON lookup for instant structured answers
    4. Calculator for math queries
    5. RAG + LLM for complex/unstructured queries
    """

    # GREETING CHECK — must be FIRST
    if is_greeting(query):
        return {
            "answer": random.choice(GREETING_RESPONSES),
            "type": "greeting",
            "sources": [],
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "branch_note": "CSE/CS branch only",
        }

    # OUT OF SCOPE CHECK — must be SECOND
    if is_out_of_scope(query):
        return {
            "answer": random.choice(OUT_OF_SCOPE_RESPONSES),
            "type": "out_of_scope",
            "sources": [],
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "branch_note": "CSE/CS branch only",
        }

    # Professional elective routing must happen before general subject detection.
    if is_professional_elective_query(query):
        pe_data = (
            JSON_DATA.get("professional_electives")
            or JSON_DATA.get("4th_sem_professional_elective")
            or JSON_DATA.get("4thsem_professional_electives")
        )
        if pe_data:
            response_text = format_professional_elective_response(pe_data, query)
            return {
                "answer": response_text,
                "type": "json_lookup",
                "sources": ["JSON - 4th_sem_professional_elective.json"],
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "branch_note": "CSE/CS branch only",
            }

    next_holiday_keywords = [
        "next holiday", "upcoming holiday", "nearest holiday",
        "when is next holiday", "which holiday is next",
        "next off day", "next leave", "coming holiday",
    ]
    query_lower = query.lower().strip()
    if any(kw in query_lower for kw in next_holiday_keywords):
        holiday_list = []
        for key, value in JSON_DATA.items():
            if "academic_calendar" in key and isinstance(value, dict):
                holiday_list = value.get("all_holidays_consolidated", [])
                break

        today = date.today()
        next_hol = get_next_holiday(today, holiday_list)

        # Calculate days away
        next_hol_date = parse_holiday_date(next_hol["date"])
        if next_hol_date:
            days_away = (next_hol_date.date() - today).days
            days_text = str(days_away) + " day(s) from today"
        else:
            days_text = "coming soon"

        response = (
            "Next Holiday: " + next_hol["name"] + "\n"
            "Date: " + next_hol["date"] + " (" + next_hol["day"] + ")\n"
            "That is " + days_text + "!"
        )

        return {
            "answer": response,
            "type": "json_lookup",
            "sources": ["JSON - academic_calendar"],
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "branch_note": "CSE/CS branch only",
        }

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
                    "sources": ["Calculator"],
                    "type": "calculator_error",
                    "branch_note": "CSE/CS branch only",
                }
            result = AttendanceCalculator().calculate(total, attended)
            return {
                "answer": format_attendance_result(result),
                "sources": ["Calculator"],
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
            "sources": ["Calculator"],
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
            "sources": ["Calculator"],
            "type": "calculator_redirect",
            "branch_note": "CSE/CS branch only",
        }

    # -- STEP 5: JSON Lookup --
    json_result = search_json(enriched_query, JSON_DATA, session_id)
    if json_result and json_result.get("found"):
        source_value = json_result.get("source") or "JSON - structured_data"
        return {
            "answer": json_result["formatted_answer"],
            "sources": [source_value],
            "type": "json_lookup",
            "branch_note": "CSE/CS branch only",
        }

    # Also try with original query if enriched failed
    if enriched_query != query:
        json_result2 = search_json(query, JSON_DATA, session_id)
        if json_result2 and json_result2.get("found"):
            source_value = json_result2.get("source") or "JSON - structured_data"
            return {
                "answer": json_result2["formatted_answer"],
                "sources": [source_value],
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
