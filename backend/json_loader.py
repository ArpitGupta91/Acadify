import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from backend.config import BRANCH, STRUCTURED_DATA_FOLDER
except ImportError:
    from config import BRANCH, STRUCTURED_DATA_FOLDER

JSON_FILE_INDEX: Dict[str, str] = {}

# =========================================================
# SUBJECT CODE MAPPING - FOR CONSISTENT LOOKUPS
# =========================================================
SUBJECT_CODE_MAP = {
    "data analytics": "IT202B",
    "it202b": "IT202B",
    "da": "IT202B",
    "ann and machine learning": "CS303B",
    "ann": "CS303B",
    "machine learning": "CS303B",
    "cs303b": "CS303B",
    "web technology": "CS208B",
    "web tech": "CS208B",
    "cs208b": "CS208B",
    "database systems": "IT301L",
    "dbms": "IT301L",
    "it301l": "IT301L",
    "operating system": "CS206L",
    "os": "CS206L",
    "cs206l": "CS206L",
    "java": "CS301L",
    "oop": "CS301L",
    "cs301l": "CS301L",
    "probability": "MA105L",
    "statistics": "MA105L",
    "ma105l": "MA105L",
    "data structure": "CS302B",
    "ads": "CS302B",
    "cs302b": "CS302B",
    "artificial intelligence": "CS205B",
    "ai": "CS205B",
    "cs205b": "CS205B",
    "daa": "CS401L",
    "algorithm": "CS401L",
    "cs401l": "CS401L",
    "computer networks": "IT302L",
    "cn": "IT302L",
    "it302l": "IT302L",
}

# =========================================================
# DATE PARSING & HOLIDAY/EXAM HELPERS
# =========================================================
MONTH_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "may": 5, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    "january": 1, "february": 2, "march": 3,
    "april": 4, "june": 6, "july": 7,
    "august": 8, "september": 9, "october": 10,
    "november": 11, "december": 12
}

# Session context shared with chat_handler
session_context: Dict[str, Dict[str, Any]] = {}


def parse_holiday_date(date_str: str) -> Optional[datetime]:
    """
    Parses date strings like:
    "3rd Jan 2026", "18th Feb 2026", "26th March 2026"
    Returns datetime object or None if parsing fails.
    """
    try:
        # Remove ordinal suffixes: 1st→1, 2nd→2, 3rd→3, 4th→4
        clean = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str.strip())
        # Try multiple formats
        for fmt in ["%d %b %Y", "%d %B %Y", "%d %b", "%d %B"]:
            try:
                parsed = datetime.strptime(clean, fmt)
                # If year missing, assume 2026
                if parsed.year == 1900:
                    parsed = parsed.replace(year=2026)
                return parsed
            except:
                continue
        return None
    except:
        return None


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def find_course_by_code(json_data: Dict[str, Dict[str, Any]], subject_code: str,
                        prefer_theory: bool = True) -> Optional[Dict[str, Any]]:
    """
    Finds course data by code.
    If prefer_theory=True, prefers L (lecture) courses over P (lab).
    CS401L is preferred over CS401P when both could match.
    """
    theory_result = None
    lab_result = None
    
    for filename, data in json_data.items():
        if not isinstance(data, dict):
            continue
        
        # Direct match at top level
        if data.get("course_code") == subject_code:
            if subject_code.endswith("P"):
                lab_result = data
            else:
                theory_result = data
            continue
        
        # Search inside nested "courses" array
        if "courses" in data:
            for course in data["courses"]:
                if isinstance(course, dict):
                    if course.get("course_code") == subject_code:
                        if subject_code.endswith("P"):
                            lab_result = course
                        else:
                            theory_result = course
        
        # Search inside lab_courses array
        if "lab_courses" in data:
            for course in data["lab_courses"]:
                if isinstance(course, dict):
                    if course.get("course_code") == subject_code:
                        lab_result = course
    
    if prefer_theory and theory_result:
        return theory_result
    if not prefer_theory and lab_result:
        return lab_result
    return theory_result or lab_result


def find_course_in_nested(json_data: Dict[str, Dict[str, Any]], subject_code: str) -> Optional[Dict[str, Any]]:
    """
    Searches for a course inside files that have
    a nested "courses" array (like file 11).
    Returns the course dict if found, else None.
    """
    normalized_code = str(subject_code).upper()
    for _, data in json_data.items():
        # Check if this file has a "courses" array
        if isinstance(data, dict) and "courses" in data:
            for course in data["courses"]:
                if isinstance(course, dict):
                    code = str(course.get("course_code", "")).upper()
                    name = str(course.get("course_name", "")).lower()
                    if code == normalized_code or normalized_code.lower() in name:
                        return course
        # Also check top-level course_code
        if isinstance(data, dict):
            if str(data.get("course_code", "")).upper() == normalized_code:
                return data
    return None


def _resolve_subject_code_from_query(query_lower: str, session_id: str) -> Optional[str]:
    # Longest keywords first to avoid partial collisions like "da" matching "daa".
    sorted_keywords = sorted(SUBJECT_CODE_MAP.keys(), key=len, reverse=True)
    for code_keyword in sorted_keywords:
        pattern = rf"\b{re.escape(code_keyword)}\b"
        if re.search(pattern, query_lower):
            return SUBJECT_CODE_MAP[code_keyword]

    if session_id in session_context:
        remembered = session_context[session_id].get("last_subject_code")
        if remembered:
            return str(remembered).upper()

    return None


def get_specific_unit(json_data: Dict[str, Dict[str, Any]], subject_code: str, 
                      unit_number: int) -> Optional[Dict[str, Any]]:
    """
    Returns only the specific unit asked for.
    """
    course = find_course_by_code(json_data, subject_code)
    if not course:
        return None
    
    units = course.get("units", [])
    for unit in units:
        if unit.get("unit_no") == unit_number:
            return {
                "course_name": course.get("course_name"),
                "course_code": subject_code,
                "unit": unit
            }
    return None


def get_next_holiday(json_data: Dict[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Returns the single next upcoming holiday from today.
    """
    today = datetime.now()
    _, calendar = _get_item_by_key_fragment(json_data, "academic_calendar")
    if not calendar:
        return None
    holidays = calendar.get("all_holidays_consolidated", [])
    
    upcoming = []
    for h in holidays:
        date_str = h.get("date", "")
        parsed = parse_holiday_date(date_str)
        if parsed and parsed.date() >= today.date():
            upcoming.append({
                "date": date_str,
                "day": h.get("day", ""),
                "reason": h.get("reason", ""),
                "parsed_date": parsed
            })
    
    if not upcoming:
        return None
    
    # Sort by date and return the nearest one
    upcoming.sort(key=lambda x: x["parsed_date"])
    next_h = upcoming[0]
    
    # Also get next 3 for context
    next_few = upcoming[:4]
    
    return {
        "next": next_h,
        "upcoming_few": next_few
    }


def get_next_exam(json_data: Dict[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Returns the next UPCOMING exam from today's date.
    Skips exams that have already passed.
    """
    today = datetime.now()
    _, calendar = _get_item_by_key_fragment(json_data, "academic_calendar")
    if not calendar:
        return None
    exam_schedule = calendar.get("exam_schedule", {})
    
    EXAM_DATES = {
        "MSE1": {
            "name": "Mid Semester Exam 1 (MSE1)",
            "start": "9th March 2026",
            "end": "14th March 2026",
            "details": exam_schedule.get("MSE1", {})
        },
        "MSE2": {
            "name": "Mid Semester Exam 2 (MSE2)",
            "start": "20th April 2026",
            "end": "25th April 2026",
            "details": exam_schedule.get("MSE2", {})
        },
        "ESE": {
            "name": "End Semester Examination (ESE)",
            "start": "15th May 2026",
            "end": "30th May 2026",
            "details": exam_schedule.get("ESE", {})
        },
        "PRACTICAL": {
            "name": "End Semester Practical Exam",
            "start": "1st June 2026",
            "end": "5th June 2026",
            "details": {}
        }
    }
    
    upcoming_exams = []
    for key, exam in EXAM_DATES.items():
        start_date = parse_holiday_date(exam["start"])
        end_date = parse_holiday_date(exam["end"])
        
        if start_date and end_date:
            # Exam is upcoming if end date is in future
            if end_date.date() >= today.date():
                exam["key"] = key
                exam["start_parsed"] = start_date
                upcoming_exams.append(exam)
    
    if not upcoming_exams:
        return None
    
    # Sort and return nearest
    upcoming_exams.sort(key=lambda x: x["start_parsed"])
    return upcoming_exams[0]


def _resolve_data_path(folder: str) -> Path:
    raw = Path(folder)
    return raw if raw.is_absolute() else _project_root() / raw


def _normalize_key(stem: str) -> str:
    key = re.sub(r"^\d+_", "", stem)
    key = re.sub(r"[^a-zA-Z0-9]+", "_", key).strip("_").lower()
    return key


def _flatten_tokens(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _match_any(query: str, keywords: List[str]) -> bool:
    return any(word in query for word in keywords)


def _get_item_by_key_fragment(json_data: Dict[str, Dict[str, Any]], fragment: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    for key, value in json_data.items():
        if fragment in key:
            return key, value
    return None, None


def _collect_subject_records(json_data: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    subjects: List[Dict[str, Any]] = []

    for source_key, payload in json_data.items():
        if not isinstance(payload, dict):
            continue

        if "course_code" in payload and "course_name" in payload:
            subjects.append(
                {
                    "source_key": source_key,
                    "course_code": str(payload.get("course_code", "")).upper(),
                    "course_name": str(payload.get("course_name", "")),
                    "units": payload.get("units", []),
                    "marks": payload.get("marks", {}),
                    "credits": payload.get("credits", ""),
                    "total_hours": payload.get("total_lecture_hours", payload.get("total_hours", "")),
                    "raw": payload,
                }
            )

        for course in payload.get("courses", []):
            if not isinstance(course, dict):
                continue
            if "course_code" in course and "course_name" in course:
                subjects.append(
                    {
                        "source_key": source_key,
                        "course_code": str(course.get("course_code", "")).upper(),
                        "course_name": str(course.get("course_name", "")),
                        "units": course.get("units", []),
                        "marks": course.get("marks", {}),
                        "credits": course.get("credits", ""),
                        "total_hours": course.get("total_lecture_hours", course.get("total_hours", "")),
                        "raw": course,
                    }
                )

    return subjects


def _detect_subject(query: str, subjects: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    alias_map = {
        "it301l": ["database", "dbms", "sql", "it301l"],
        "cs206l": ["operating system", "os", "cs206l"],
        "cs301l": ["java", "oop", "object oriented", "cs301l"],
        "ma105l": ["probability", "statistics", "ma105l"],
        "cs302b": ["data structure", "advance data structure", "ads", "cs302b"],
        "cs205b": ["artificial intelligence", "ai", "cs205b"],
        "cs401l": ["algorithm", "daa", "design and analysis", "cs401l"],
        "it302l": ["computer networks", "cn", "it302l"],
        "it202b": ["da", "data analytics", "it202b"],
        "cs303b": ["machine learning", "ann", "cs303b"],
        "cs208b": ["web technology", "web tech", "cs208b"],
        "cs318e": ["elective", "react", "nextjs", "cs318e"],
        "cs307e": ["elective", "intelligent systems", "text", "vision", "cs307e"],
        "cs304e": ["elective", "devops", "cs304e"],
        "cs335e": ["elective", "aws", "cs335e"],
        "cs321e": ["elective", "ios", "apple", "cs321e"],
        "it306e": ["elective", "azure", "it306e"],
    }

    query_lower = query.lower()

    for subject in subjects:
        code = subject.get("course_code", "").lower()
        name = subject.get("course_name", "").lower()

        if code and code in query_lower:
            return subject
        if name and name in query_lower:
            return subject

    for code, aliases in alias_map.items():
        if any(alias in query_lower for alias in aliases):
            for subject in subjects:
                if subject.get("course_code", "").lower() == code:
                    return subject

    return None


def load_all_json_data() -> Dict[str, Dict[str, Any]]:
    global JSON_FILE_INDEX

    structured_dir = _resolve_data_path(STRUCTURED_DATA_FOLDER)
    if not structured_dir.exists():
        raise FileNotFoundError(
            f"Structured data folder not found: '{structured_dir}'. Ensure JSON files are present."
        )

    json_data: Dict[str, Dict[str, Any]] = {}
    JSON_FILE_INDEX = {}

    for json_file in sorted(structured_dir.rglob("*.json")):
        try:
            with json_file.open("r", encoding="utf-8") as file:
                payload = json.load(file)
            key = _normalize_key(json_file.stem)
            json_data[key] = payload
            JSON_FILE_INDEX[key] = json_file.name
        except Exception as error:
            print(f"[WARN] Failed to load JSON file '{json_file.name}': {error}")

    print(f"Loaded {len(json_data)} JSON files from '{structured_dir}'.")
    return json_data


def format_json_answer(category: str, data: Dict[str, Any]) -> str:
    if category == "exam_schedule":
        exam_name = data.get("exam_name", "Examination")
        details = data.get("details", {})
        lines = [f"📅 {exam_name}:"]
        for key, value in details.items():
            label = key.replace("_", " ").strip().title()
            lines.append(f"• {label}: {value}")
        return "\n".join(lines)

    if category == "syllabus":
        units = data.get("units", [])
        lines = [f"📚 {data.get('course_name', 'Subject')} ({data.get('course_code', '')})"]
        for unit in units:
            unit_no = unit.get("unit_no", "?")
            title = unit.get("title", "")
            topics = unit.get("topics", [])
            summary = ", ".join(topics[:4]) if isinstance(topics, list) else str(topics)
            if isinstance(topics, list) and len(topics) > 4:
                summary += ", ..."
            lines.append(f"Unit {unit_no}: {title} - {summary}")
        lines.append(f"Total Hours: {data.get('total_hours', 'NA')} | Credits: {data.get('credits', 'NA')}")
        return "\n".join(lines)

    if category == "marks":
        marks = data.get("marks", {})
        mse1 = marks.get("MSE1", "NA")
        mse2 = marks.get("MSE2", "NA")
        mse_total = marks.get("MSE", "NA")
        if mse_total == "NA" and isinstance(mse1, (int, float)) and isinstance(mse2, (int, float)):
            mse_total = mse1 + mse2
        return (
            f"📊 Marks Breakdown for {data.get('course_name', 'Subject')}:\n"
            f"MSE: {mse_total} | "
            f"MSE1: {mse1} | "
            f"MSE2: {mse2} | "
            f"CA: {marks.get('total_CA', marks.get('CA', 'NA'))} | "
            f"ESE: {marks.get('ESE', 'NA')} | "
            f"Total: {marks.get('total', 'NA')}"
        )

    if category == "holidays":
        lines = ["🏖️ Holiday List:"]
        for holiday in data.get("holidays", []):
            lines.append(
                f"• {holiday.get('date', 'NA')} ({holiday.get('day', 'NA')}): {holiday.get('reason', 'Holiday')}"
            )
        return "\n".join(lines)

    if category == "semester_subjects":
        lines = [f"📘 {data.get('semester', 'Semester')} Subjects:"]
        for index, course in enumerate(data.get("courses", []), start=1):
            lines.append(
                f"{index}. {course.get('code', 'NA')} - {course.get('name', 'NA')} "
                f"(Credits: {course.get('credits', 'NA')})"
            )
        return "\n".join(lines)

    if category == "attendance":
        policy = data.get("policy", {})
        calendar_attendance = data.get("calendar", {})
        lines = [
            "📌 Attendance Policy:",
            f"• Minimum Required: {policy.get('minimum_required_percentage', calendar_attendance.get('minimum_percentage', 'NA'))}%",
            f"• Rule: {policy.get('consequence_below_75', calendar_attendance.get('detention_rule', 'NA'))}",
            f"• CA Attendance Marks: {policy.get('CA3_attendance_marks', 'As per subject scheme')}",
        ]

        display_schedule = calendar_attendance.get("display_schedule", [])
        if display_schedule:
            lines.append("• Attendance Display Schedule:")
            for item in display_schedule:
                lines.append(f"  - {item.get('event', 'Event')}: {item.get('date', 'NA')}")

        return "\n".join(lines)

    if category == "important_dates":
        lines = ["⏳ Important Dates:"]
        for item in data.get("dates", []):
            lines.append(f"• {item.get('label', 'Event')}: {item.get('date', 'NA')}")
        return "\n".join(lines)

    if category == "faq":
        return f"❓ {data.get('question', '')}\n✅ {data.get('answer', '')}"

    if category == "professional_electives":
        lines = ["🎯 Professional Elective-1 Options (Choose ONE):"]
        for index, option in enumerate(data.get("options", []), start=1):
            lines.append(
                f"{index}. {option.get('course_code', 'NA')} - {option.get('course_name', 'NA')} "
                f"({option.get('elective_name', option.get('elective_track', ''))})"
            )
        return "\n".join(lines)

    return str(data)


def search_json(query: str, json_data: Dict[str, Dict[str, Any]], 
                session_id: str = "default") -> Optional[Dict[str, Any]]:
    query_lower = query.lower().strip()
    query_tokens = set(_flatten_tokens(query_lower))
    subjects = _collect_subject_records(json_data)
    matched_subject = _detect_subject(query_lower, subjects)
    resolved_subject_code = _resolve_subject_code_from_query(query_lower, session_id)

    calendar_key, calendar = _get_item_by_key_fragment(json_data, "academic_calendar")
    metadata_key, metadata = _get_item_by_key_fragment(json_data, "college_metadata")
    faq_key, faq = _get_item_by_key_fragment(json_data, "quick_reference_faq")
    third_sem_key, third_sem = _get_item_by_key_fragment(json_data, "3rd_sem_overview")
    fourth_sem_key, fourth_sem = _get_item_by_key_fragment(json_data, "4th_sem_overview")

    # ========== SPECIAL: Next Holiday ==========
    next_holiday_keywords = [
        "next holiday", "upcoming holiday", "nearest holiday",
        "when is next holiday", "which holiday is next",
        "next off day", "next leave", "coming holiday"
    ]
    if any(kw in query_lower for kw in next_holiday_keywords):
        result = get_next_holiday(json_data)
        if result:
            next_h = result["next"]
            upcoming = result["upcoming_few"]
            
            answer = f"🗓️ **Next Holiday:**\n"
            answer += f"📅 {next_h['date']} ({next_h['day']})\n"
            answer += f"🎉 {next_h['reason']}\n\n"
            
            if len(upcoming) > 1:
                answer += "**Upcoming holidays after that:**\n"
                for h in upcoming[1:]:
                    answer += f"• {h['date']} ({h['day']}) - {h['reason']}\n"
            
            answer += "\n📌 For CSE/CS branch, Even Sem 2025-26"
            
            return {
                "found": True,
                "source": f"JSON - {JSON_FILE_INDEX.get(calendar_key or '', 'academic_calendar.json')}",
                "formatted_answer": answer
            }

    # ========== SPECIAL: Next Exam ==========
    next_exam_keywords = [
        "next exam", "upcoming exam", "nearest exam",
        "which exam is next", "when is next exam",
        "coming exam", "next mse", "next test"
    ]
    if any(kw in query_lower for kw in next_exam_keywords):
        result = get_next_exam(json_data)
        if result:
            answer = f"📝 **Next Upcoming Exam:**\n\n"
            answer += f"🎯 **{result['name']}**\n"
            answer += f"📅 {result['start']} to {result['end']}\n"
            
            details = result.get("details", {})
            if details:
                if details.get("detention_list_by_COE"):
                    answer += f"📋 Detention List: {details['detention_list_by_COE']}\n"
                if details.get("grievance_redressal_deadline"):
                    answer += f"🔔 Grievance Deadline: {details['grievance_redressal_deadline']}\n"
            
            answer += "\n📌 For CSE/CS branch, Even Sem 2025-26"
            
            return {
                "found": True,
                "source": f"JSON - {JSON_FILE_INDEX.get(calendar_key or '', 'academic_calendar.json')}",
                "formatted_answer": answer
            }
        else:
            return {
                "found": True,
                "source": f"JSON - {JSON_FILE_INDEX.get(calendar_key or '', 'academic_calendar.json')}",
                "formatted_answer": (
                    "✅ All major exams (MSE1, MSE2, ESE) for "
                    "Even Semester 2025-26 have been completed.\n"
                    "📌 For CSE/CS branch, Even Sem 2025-26"
                )
            }

    # ========== SPECIAL: Specific Unit Query ==========
    unit_match = re.search(r'unit\s*(\d+)', query_lower)
    
    if unit_match:
        unit_number = int(unit_match.group(1))
        subject_code = _resolve_subject_code_from_query(query_lower, session_id)
        
        if subject_code:
            result = get_specific_unit(json_data, subject_code, unit_number)
            if result:
                unit = result["unit"]
                topics = unit.get("topics", [])
                
                answer = (
                    f"📚 **{result['course_name']} ({result['course_code']})**\n"
                    f"**Unit {unit_number}: {unit.get('title', '')}**\n"
                    f"⏱️ Hours: {unit.get('hours', 'N/A')}\n\n"
                    f"**Topics covered:**\n"
                )
                
                if isinstance(topics, list):
                    for i, topic in enumerate(topics, 1):
                        answer += f"  {i}. {topic}\n"
                else:
                    answer += str(topics)
                
                # Add problem solving if present
                problems = unit.get("problem_solving", [])
                if problems:
                    answer += f"\n**Problem Solving ({len(problems)} problems)**\n"
                    for p in problems[:3]:  # Show first 3 only
                        answer += f"  • {p}\n"
                    if len(problems) > 3:
                        answer += f"  ... and {len(problems)-3} more\n"
                
                answer += "\n📌 For CSE/CS branch, Even Sem 2025-26"
                
                return {
                    "found": True,
                    "source": f"JSON - {result['course_code']}",
                    "formatted_answer": answer
                }

    # Now continue with existing categories below...
    matched_subject = _detect_subject(query_lower, subjects)

    # CATEGORY 1: EXAM SCHEDULE
    exam_keywords = [
        "mse1",
        "mse2",
        "ese",
        "end sem",
        "mid sem",
        "exam date",
        "exam schedule",
        "when is mse",
        "exam timetable",
    ]
    if calendar and _match_any(query_lower, exam_keywords):
        exam_schedule = calendar.get("exam_schedule", {})
        exam_code = "MSE1"
        if "mse2" in query_lower:
            exam_code = "MSE2"
        elif "ese" in query_lower or "end sem" in query_lower or "end semester" in query_lower:
            exam_code = "ESE"
        elif "ca1" in query_lower or "ca2" in query_lower:
            exam_code = "continuous_assessment"

        selected = exam_schedule.get(exam_code, exam_schedule)
        exam_name = selected.get("full_name", exam_code if exam_code != "continuous_assessment" else "Continuous Assessment") if isinstance(selected, dict) else "Examination Schedule"

        answer = format_json_answer(
            "exam_schedule",
            {"exam_name": exam_name, "details": selected if isinstance(selected, dict) else exam_schedule},
        )
        return {
            "found": True,
            "source": f"JSON - {JSON_FILE_INDEX.get(calendar_key or '', 'academic_calendar.json')}",
            "data": selected,
            "formatted_answer": f"{answer}\n\nNote: This information is for CSE/CS branch only.",
            "branch_note": "This information is for CSE/CS branch only.",
        }

    # CATEGORY 2: HOLIDAYS
    holiday_keywords = [
        "holiday",
        "off",
        "leave",
        "holi",
        "eid",
        "republic day",
        "shivratri",
        "ram navami",
        "ambedkar",
        "bakrid",
        "saturday",
        "sunday",
    ]
    if calendar and _match_any(query_lower, holiday_keywords):
        holidays = calendar.get("all_holidays_consolidated", [])
        filtered = [
            item
            for item in holidays
            if any(token in str(item.get("reason", "")).lower() or token in str(item.get("date", "")).lower() for token in query_tokens)
        ]
        holiday_data = filtered if filtered else holidays

        answer = format_json_answer("holidays", {"holidays": holiday_data})
        return {
            "found": True,
            "source": f"JSON - {JSON_FILE_INDEX.get(calendar_key or '', 'academic_calendar.json')}",
            "data": holiday_data,
            "formatted_answer": f"{answer}\n\nNote: This information is for CSE/CS branch only.",
            "branch_note": "This information is for CSE/CS branch only.",
        }

    # CATEGORY 3: SUBJECT SYLLABUS
    syllabus_keywords = ["syllabus", "topics", "units", "what is taught", "course content"]
    if _match_any(query_lower, syllabus_keywords) or (
        matched_subject and any(token in query_lower for token in ["unit", "topic", "syllabus", "course content"])
    ):
        if matched_subject and matched_subject.get("units"):
            answer = format_json_answer("syllabus", matched_subject)
            return {
                "found": True,
                "source": f"JSON - {JSON_FILE_INDEX.get(matched_subject.get('source_key', ''), matched_subject.get('source_key', 'subject.json'))}",
                "data": matched_subject,
                "formatted_answer": f"{answer}\n\nNote: This information is for CSE/CS branch only.",
                "branch_note": "This information is for CSE/CS branch only.",
            }

    # CATEGORY 4: MARKS/CREDITS
    marks_keywords = [
        "marks",
        "credits",
        "credit",
        "marking scheme",
        "mse marks",
        "ese marks",
        "ca marks",
        "total marks",
        "how many marks",
    ]
    if _match_any(query_lower, marks_keywords):
        if matched_subject and matched_subject.get("marks"):
            answer = format_json_answer("marks", matched_subject)
            return {
                "found": True,
                "source": f"JSON - {JSON_FILE_INDEX.get(matched_subject.get('source_key', ''), matched_subject.get('source_key', 'subject.json'))}",
                "data": matched_subject.get("marks", {}),
                "formatted_answer": f"{answer}\n\nNote: This information is for CSE/CS branch only.",
                "branch_note": "This information is for CSE/CS branch only.",
            }
        # Try finding course by resolved code (handles nested arrays + theory priority)
        course_code = None
        if matched_subject and matched_subject.get("course_code"):
            course_code = str(matched_subject.get("course_code")).upper()
        elif resolved_subject_code:
            course_code = resolved_subject_code

        if course_code:
            course_data = find_course_by_code(json_data, course_code, prefer_theory=True)
            if not course_data:
                course_data = find_course_in_nested(json_data, course_code)

            if course_data and (course_data.get("marks") or course_data.get("credits") is not None):
                marks = course_data.get("marks", {})
                if marks:
                    answer = format_json_answer("marks", {
                        "course_name": course_data.get("course_name"),
                        "course_code": course_code,
                        "marks": marks,
                    })
                else:
                    answer = (
                        f"📊 Credit Details for {course_data.get('course_name', 'Subject')} ({course_code}):\n"
                        f"Credits: {course_data.get('credits', 'NA')}"
                    )

                return {
                    "found": True,
                    "source": f"JSON - {course_code}",
                    "data": course_data,
                    "formatted_answer": f"{answer}\n\nNote: This information is for CSE/CS branch only.",
                    "branch_note": "This information is for CSE/CS branch only.",
                }

    # CATEGORY 5: SEMESTER OVERVIEW
    sem_keywords = [
        "subjects in 3rd sem",
        "4th sem subjects",
        "course list",
        "all subjects",
        "semester subjects",
        "what subjects",
    ]
    semester_pattern = (
        ("subject" in query_lower or "course" in query_lower)
        and any(token in query_lower for token in ["3rd", "4th", "third", "fourth", "semester", "sem"])
    )

    if _match_any(query_lower, sem_keywords) or semester_pattern:
        selected_key = fourth_sem_key if "4" in query_lower or "fourth" in query_lower else third_sem_key
        selected = fourth_sem if selected_key == fourth_sem_key else third_sem

        if selected and selected.get("course_summary"):
            answer = format_json_answer(
                "semester_subjects",
                {
                    "semester": selected.get("semester", "Semester"),
                    "courses": selected.get("course_summary", []),
                },
            )
            return {
                "found": True,
                "source": f"JSON - {JSON_FILE_INDEX.get(selected_key or '', 'semester_overview.json')}",
                "data": selected.get("course_summary", []),
                "formatted_answer": f"{answer}\n\nNote: This information is for CSE/CS branch only.",
                "branch_note": "This information is for CSE/CS branch only.",
            }

    # CATEGORY 6: ATTENDANCE
    attendance_keywords = [
        "attendance",
        "75%",
        "detained",
        "bunk",
        "absent",
        "present",
        "classes",
        "how many classes",
    ]
    if _match_any(query_lower, attendance_keywords):
        policy = metadata.get("attendance_policy", {}) if metadata else {}
        calendar_attendance = calendar.get("attendance", {}) if calendar else {}
        merged = {"policy": policy, "calendar": calendar_attendance}
        answer = format_json_answer("attendance", merged)
        return {
            "found": True,
            "source": f"JSON - {JSON_FILE_INDEX.get(metadata_key or '', 'college_metadata.json')} + {JSON_FILE_INDEX.get(calendar_key or '', 'academic_calendar.json')}",
            "data": merged,
            "formatted_answer": f"{answer}\n\nNote: This information is for CSE/CS branch only.",
            "branch_note": "This information is for CSE/CS branch only.",
        }

    # CATEGORY 7: IMPORTANT DATES
    date_keywords = [
        "last date",
        "deadline",
        "ca1",
        "ca2",
        "upload",
        "erp",
        "grievance",
        "result",
        "when is result",
        "last instructional day",
        "semester start",
        "when does class start",
    ]
    if calendar and _match_any(query_lower, date_keywords):
        key_dates = calendar.get("semester_key_dates", {})
        exam_schedule = calendar.get("exam_schedule", {})

        all_dates: List[Dict[str, Any]] = [
            {"label": label.replace("_", " ").title(), "date": value}
            for label, value in key_dates.items()
        ]

        for exam_name, details in exam_schedule.items():
            if isinstance(details, dict):
                for key, value in details.items():
                    all_dates.append(
                        {
                            "label": f"{exam_name} - {key.replace('_', ' ').title()}",
                            "date": value,
                        }
                    )

        filtered_dates = [
            item
            for item in all_dates
            if any(token in item["label"].lower() or token in str(item["date"]).lower() for token in query_tokens)
        ]
        result_dates = filtered_dates if filtered_dates else all_dates[:12]

        answer = format_json_answer("important_dates", {"dates": result_dates})
        return {
            "found": True,
            "source": f"JSON - {JSON_FILE_INDEX.get(calendar_key or '', 'academic_calendar.json')}",
            "data": result_dates,
            "formatted_answer": f"{answer}\n\nNote: This information is for CSE/CS branch only.",
            "branch_note": "This information is for CSE/CS branch only.",
        }

    # CATEGORY 8: FAQ QUICK ANSWERS
    faq_keywords = [
        "cgpa",
        "how to calculate",
        "grading",
        "grade points",
        "constitution of india",
        "aptitude",
        "soft skills",
        "nc subject",
    ]
    if faq and _match_any(query_lower, faq_keywords):
        faq_items = faq.get("frequently_asked_questions", [])

        best_item = None
        best_score = 0
        for item in faq_items:
            q_tokens = set(_flatten_tokens(item.get("q", "")))
            overlap = len(query_tokens.intersection(q_tokens))
            if overlap > best_score:
                best_score = overlap
                best_item = item

        if best_item and best_score > 0:
            answer = format_json_answer("faq", {"question": best_item.get("q", ""), "answer": best_item.get("a", "")})
            return {
                "found": True,
                "source": f"JSON - {JSON_FILE_INDEX.get(faq_key or '', 'quick_reference_faq.json')}",
                "data": best_item,
                "formatted_answer": f"{answer}\n\nNote: This information is for CSE/CS branch only.",
                "branch_note": "This information is for CSE/CS branch only.",
            }

    # CATEGORY 9: PROFESSIONAL ELECTIVE
    pe_keywords = [
        "professional elective",
        "pe1",
        "elective options",
        "which elective",
        "react",
        "nextjs",
        "devops",
        "aws",
        "ios",
        "azure",
        "intelligent systems",
    ]
    if _match_any(query_lower, pe_keywords):
        options = []
        source_key = None

        if fourth_sem and fourth_sem.get("professional_elective_options", {}).get("options"):
            options = fourth_sem["professional_elective_options"]["options"]
            source_key = fourth_sem_key

        if not options:
            pe_key, pe_data = _get_item_by_key_fragment(json_data, "professional_electives")
            if pe_data:
                options = pe_data.get("professional_elective_1", {}).get("electives", [])
                source_key = pe_key

        if options:
            answer = format_json_answer("professional_electives", {"options": options})
            return {
                "found": True,
                "source": f"JSON - {JSON_FILE_INDEX.get(source_key or '', 'professional_electives.json')}",
                "data": options,
                "formatted_answer": f"{answer}\n\nNote: This information is for CSE/CS branch only.",
                "branch_note": "This information is for CSE/CS branch only.",
            }

    return None
