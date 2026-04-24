# KIET CollegeAI Assistant

## 1. Project Overview
KIET CollegeAI Assistant is a hybrid AI-powered chatbot for KIET Group of Institutions, Delhi-NCR, Ghaziabad.
It is designed only for B.Tech CSE/CS students (Even Semester 2025-26, 3rd and 4th semester scope).

Hybrid architecture:
- Layer 1: Structured JSON lookup (fast and accurate answers)
- Layer 2: FAISS + Groq RAG fallback (semantic retrieval for complex queries)

## 2. Tech Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI (Python) |
| Structured Engine | Custom JSON loader/search |
| RAG Framework | LangChain + FAISS |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| LLM | Groq API (llama3-8b-8192) |
| PDF Extraction | pdfplumber + PyMuPDF |
| Frontend | HTML + CSS + Vanilla JavaScript |
| Storage | Local vector store (FAISS index on disk) |

## 3. Prerequisites
- Python 3.9+
- pip
- Git
- Optional but recommended: VS Code

## 4. Run Locally on Your Laptop (Step by Step)

Follow these steps exactly to make Acadify live on localhost.

### Step 1) Open terminal in project folder

If you already downloaded this project, open terminal and go to the folder:

```powershell
Set-Location "C:\path\to\Acadify"
```

If you have not downloaded it yet:

```powershell
git clone <your-repo-url>
Set-Location Acadify
```

### Step 2) Create virtual environment

```powershell
python -m venv .venv
```

### Step 3) Activate virtual environment

PowerShell:

```powershell
(Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned)
& .\.venv\Scripts\Activate.ps1
```

CMD:

```bat
.venv\Scripts\activate.bat
```

### Step 4) Install dependencies

```powershell
pip install -r backend/requirements.txt
```

### Step 5) Add your Groq API key

1. Go to https://console.groq.com
2. Generate API key
3. Create a file named `.env` in project root and add:

```env
GROQ_API_KEY=your_key_here
```

### Step 6) Verify data folders

Make sure these folders contain data:

- `data/structured/` (JSON files)
- `data/pdfs/` (PDF files, optional but recommended for RAG)

### Step 7) Build vector index (one-time or whenever PDFs change)

```powershell
python backend/ingest.py
```

### Step 8) Start backend API server

```powershell
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Keep this terminal running.

### Step 9) Start frontend static server (new terminal)

Open another terminal in same project folder and run:

```powershell
python -m http.server 5500 --directory frontend
```

Keep this terminal running.

### Step 10) Open app in browser

- Frontend UI: http://127.0.0.1:5500/index.html
- Backend health: http://127.0.0.1:8000/health

### Step 11) Confirm everything is live

You are ready if:

- Frontend page opens at port 5500
- `/health` returns status JSON at port 8000
- Chat replies are coming from the backend

### Stop the app

Press `Ctrl + C` in both terminal windows.

## 5. Folder Structure

```text
college-ai-assistant/
├── backend/
│   ├── calculator.py
│   ├── chat_handler.py
│   ├── config.py
│   ├── ingest.py
│   ├── json_loader.py
│   ├── llm_handler.py
│   ├── main.py
│   ├── retriever.py
│   └── requirements.txt
├── data/
│   ├── pdfs/
│   └── structured/
├── frontend/
│   ├── app.js
│   ├── index.html
│   └── style.css
├── vector_store/
├── .env
├── .gitignore
└── README.md
```

## 6. Example Questions
- When is MSE1?
- Show exam schedule for ESE.
- When is Holi holiday?
- Subjects in 4th sem?
- Syllabus of CS401L.
- Marks for IT302L.
- What is attendance policy?
- How many classes do I need to attend for 75%?
- Professional elective options in 4th sem.

## 7. Troubleshooting

### Backend not reachable from frontend
- Ensure FastAPI is running at `http://localhost:8000`
- Check terminal logs for startup errors

### GROQ key errors
- Verify `.env` contains valid `GROQ_API_KEY`
- Restart API server after updating `.env`

### JSON answers not coming
- Confirm files exist in `data/structured/`
- Confirm JSON is valid (no syntax errors)
- Check `/health` to verify `json_files_loaded`

### Vector store not loading
- Run `python backend/ingest.py`
- Ensure `vector_store/faiss_index` exists and contains `index.faiss` and `index.pkl`

### PDF extraction issues
- Prefer selectable-text PDFs over scanned image PDFs
- Re-run ingestion after replacing files

## 8. Branch Note
Designed for KIET CSE/CS branch only.
