from datetime import datetime
from pathlib import Path
import threading
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.calculator import AttendanceCalculator, CGPACalculator
from backend.chat_handler import handle_chat
from backend.config import BRANCH, PDF_FOLDER
from backend.ingest import build_vector_store, chunk_documents, load_pdfs, load_vector_store
from backend.json_loader import load_all_json_data

app = FastAPI(title="CollegeAI Assistant", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

VECTOR_STORE = None
VECTOR_STORE_STATUS = "not_loaded"
try:
    JSON_DATA: Dict[str, Dict[str, Any]] = load_all_json_data()
except Exception:
    JSON_DATA = {}
LAST_INGEST_CHUNKS = 0
INGESTION_STATUS = "idle"


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _pdf_folder_path() -> Path:
    pdf_path = Path(PDF_FOLDER)
    if pdf_path.is_absolute():
        return pdf_path
    return _project_root() / pdf_path


def _find_json_payload(key_fragment: str) -> Optional[Dict[str, Any]]:
    global JSON_DATA
    if not JSON_DATA:
        try:
            JSON_DATA = load_all_json_data()
        except Exception:
            return None

    for key, value in JSON_DATA.items():
        if key_fragment in key:
            return value
    return None


def _month_from_date(date_text: str) -> str:
    normalized = date_text.lower()
    month_alias = {
        "jan": "january",
        "feb": "february",
        "mar": "march",
        "apr": "april",
        "may": "may",
        "jun": "june",
        "jul": "july",
        "aug": "august",
        "sep": "september",
        "oct": "october",
        "nov": "november",
        "dec": "december",
    }
    for short, month in month_alias.items():
        if short in normalized:
            return month
    return "unknown"


def _sort_holidays(holidays: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    month_order = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
    }

    def sort_key(item: Dict[str, Any]) -> tuple:
        date_text = str(item.get("date", ""))
        month = _month_from_date(date_text)
        day_num = 99
        tokens = date_text.split()
        if tokens:
            digits = "".join(ch for ch in tokens[0] if ch.isdigit())
            if digits:
                day_num = int(digits)
        return month_order.get(month, 99), day_num, date_text

    return sorted(holidays, key=sort_key)


def _normalize_chat_type(raw_type: str) -> str:
    allowed = {"json_lookup", "calculator", "rag", "not_found"}
    if raw_type in allowed:
        return raw_type
    if "rag" in raw_type:
        return "rag"
    return "not_found"


class ChatRequest(BaseModel):
    query: str
    session_id: str = "default"


class AttendanceRequest(BaseModel):
    total_classes: int = Field(..., gt=0)
    attended_classes: int = Field(..., ge=0)


class SubjectInput(BaseModel):
    name: str
    grade_points: float = Field(..., ge=0, le=10)
    credits: float = Field(..., gt=0)


class CGPARequest(BaseModel):
    subjects: List[SubjectInput]


def _run_ingestion_job() -> int:
    global VECTOR_STORE
    global LAST_INGEST_CHUNKS
    global INGESTION_STATUS

    INGESTION_STATUS = "running"

    pdf_docs = []
    try:
        pdf_docs = load_pdfs(PDF_FOLDER)
    except Exception as error:
        print(f"[WARN] PDF ingestion skipped/failed: {error}")

    chunks = chunk_documents(pdf_docs) if pdf_docs else []
    VECTOR_STORE = build_vector_store(chunks)
    LAST_INGEST_CHUNKS = len(chunks)
    INGESTION_STATUS = "completed"
    return len(chunks)


def _load_vector_store_background() -> None:
    global VECTOR_STORE
    global VECTOR_STORE_STATUS

    VECTOR_STORE_STATUS = "loading"
    try:
        VECTOR_STORE = load_vector_store()
        VECTOR_STORE_STATUS = "loaded"
        print("Vector store loaded successfully.")
    except FileNotFoundError:
        VECTOR_STORE = None
        VECTOR_STORE_STATUS = "missing"
        print("Run python backend/ingest.py first!")
    except Exception as error:
        VECTOR_STORE = None
        VECTOR_STORE_STATUS = "failed"
        print(f"Failed to load vector store at startup: {error}")


@app.on_event("startup")
def on_startup() -> None:
    global JSON_DATA

    try:
        JSON_DATA = load_all_json_data()
    except Exception as error:
        JSON_DATA = {}
        print(f"Failed to load structured JSON data: {error}")

    threading.Thread(target=_load_vector_store_background, daemon=True).start()


@app.post("/chat")
def chat_endpoint(request: ChatRequest) -> Dict[str, Any]:
    try:
        result = handle_chat(
            query=request.query,
            vector_store=VECTOR_STORE,
            session_id=request.session_id
        )
        return {
            "answer": result.get("answer", ""),
            "sources": result.get("sources", []),
            "type": _normalize_chat_type(result.get("type", "not_found")),
            "branch_note": result.get("branch_note", "CSE/CS branch only"),
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {error}") from error


@app.post("/ingest")
def ingest_endpoint(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    def ingestion_task() -> None:
        global INGESTION_STATUS
        try:
            indexed = _run_ingestion_job()
            print(f"Re-ingestion finished. Chunks indexed: {indexed}")
        except Exception as error:
            INGESTION_STATUS = "failed"
            print(f"Re-ingestion failed: {error}")

    background_tasks.add_task(ingestion_task)
    return {
        "status": "success",
        "chunks_indexed": LAST_INGEST_CHUNKS,
        "message": "Ingestion started in background.",
        "ingestion_state": INGESTION_STATUS,
    }


@app.get("/subjects/{semester}")
def get_subjects(semester: str) -> Dict[str, Any]:
    sem = semester.strip()
    if sem not in {"3", "4"}:
        raise HTTPException(status_code=400, detail="Semester must be '3' or '4'.")

    target_key = "3rd_sem_overview" if sem == "3" else "4th_sem_overview"
    payload = _find_json_payload(target_key)
    if not payload:
        raise HTTPException(status_code=404, detail=f"Semester {sem} structured overview not found.")

    course_summary = payload.get("course_summary", [])
    subjects = [
        {
            "code": item.get("code"),
            "name": item.get("name"),
            "credits": item.get("credits"),
            "total_marks": item.get("total_marks"),
            "type": item.get("type"),
            "category": item.get("category"),
        }
        for item in course_summary
    ]

    return {
        "semester": int(sem),
        "subjects": subjects,
        "total_credits": payload.get("total_credits", 0),
    }


@app.get("/syllabus/{course_code}")
def get_syllabus(course_code: str) -> Dict[str, Any]:
    target = course_code.strip().upper()

    for _, payload in JSON_DATA.items():
        if not isinstance(payload, dict):
            continue

        if str(payload.get("course_code", "")).upper() == target:
            return {
                "course_code": payload.get("course_code"),
                "course_name": payload.get("course_name"),
                "units": payload.get("units", []),
                "marks": payload.get("marks", {}),
                "credits": payload.get("credits"),
                "total_lecture_hours": payload.get("total_lecture_hours", payload.get("total_hours")),
                "textbooks": payload.get("textbooks", []),
                "reference_books": payload.get("reference_books", []),
            }

        for course in payload.get("courses", []):
            if str(course.get("course_code", "")).upper() == target:
                return {
                    "course_code": course.get("course_code"),
                    "course_name": course.get("course_name"),
                    "units": course.get("units", []),
                    "marks": course.get("marks", {}),
                    "credits": course.get("credits"),
                    "total_lecture_hours": course.get("total_lecture_hours", course.get("total_hours")),
                    "textbooks": course.get("textbooks", []),
                    "reference_books": course.get("reference_books", []),
                }

    raise HTTPException(
        status_code=404,
        detail=f"Syllabus for course code '{target}' not found in CSE/CS structured data.",
    )


@app.get("/calendar/exam-schedule")
def get_exam_schedule() -> Dict[str, Any]:
    calendar = _find_json_payload("academic_calendar")
    if not calendar:
        raise HTTPException(status_code=404, detail="Academic calendar JSON not found.")

    exam_schedule = calendar.get("exam_schedule", {})
    return {
        "MSE1": exam_schedule.get("MSE1", {}),
        "MSE2": exam_schedule.get("MSE2", {}),
        "ESE": exam_schedule.get("ESE", {}),
    }


@app.get("/calendar/holidays")
def get_holidays(month: Optional[str] = Query(default=None)) -> Dict[str, Any]:
    calendar = _find_json_payload("academic_calendar")
    if not calendar:
        raise HTTPException(status_code=404, detail="Academic calendar JSON not found.")

    holidays = calendar.get("all_holidays_consolidated", [])
    sorted_holidays = _sort_holidays(holidays)

    filtered = sorted_holidays
    if month:
        target_month = month.lower().strip()
        filtered = [
            h
            for h in sorted_holidays
            if target_month in _month_from_date(str(h.get("date", "")))
            or target_month in str(h.get("date", "")).lower()
        ]

    return {
        "count": len(filtered),
        "holidays": filtered,
    }


@app.get("/calendar/important-dates")
def get_important_dates() -> List[Dict[str, str]]:
    calendar = _find_json_payload("academic_calendar")
    if not calendar:
        raise HTTPException(status_code=404, detail="Academic calendar JSON not found.")

    important_dates: List[Dict[str, str]] = []

    for label, date in calendar.get("semester_key_dates", {}).items():
        important_dates.append({"event": label.replace("_", " ").title(), "date": str(date)})

    for exam_name, details in calendar.get("exam_schedule", {}).items():
        if isinstance(details, dict):
            for label, date in details.items():
                important_dates.append(
                    {
                        "event": f"{exam_name} - {label.replace('_', ' ').title()}",
                        "date": str(date),
                    }
                )

    return important_dates


@app.get("/health")
def health_endpoint() -> Dict[str, Any]:
    pdf_dir = _pdf_folder_path()
    pdf_count = len(list(pdf_dir.rglob("*.pdf"))) if pdf_dir.exists() else 0

    return {
        "status": "ok",
        "vector_store_loaded": VECTOR_STORE is not None,
        "vector_store_status": VECTOR_STORE_STATUS,
        "json_files_loaded": len(JSON_DATA),
        "pdf_count": pdf_count,
        "branch": "CSE/CS",
        "semester": "Even 2025-26",
    }


@app.post("/calculate/attendance")
def attendance_endpoint(request: AttendanceRequest) -> Dict[str, Any]:
    try:
        return AttendanceCalculator.calculate(request.total_classes, request.attended_classes)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Attendance calculation failed: {error}") from error


@app.post("/calculate/cgpa")
def cgpa_endpoint(request: CGPARequest) -> Dict[str, Any]:
    try:
        subject_payload = [s.model_dump() for s in request.subjects]
        return CGPACalculator.calculate(subject_payload)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"CGPA calculation failed: {error}") from error
