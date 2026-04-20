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

## 4. Setup Steps

### a) Clone the repository
```bash
git clone <your-repo-url>
cd college-ai-assistant
```

### b) Install dependencies
```bash
pip install -r backend/requirements.txt
```

### c) Get free Groq API key
- Visit https://console.groq.com
- Create/login account
- Generate API key

### d) Configure environment
Create or edit `.env` in project root:
```env
GROQ_API_KEY=your_key_here
```

### e) Place structured files
Copy your JSON files into:
- `data/structured/`

### f) Place PDF files
Copy your PDFs into:
- `data/pdfs/`

### g) Build vector index
```bash
python backend/ingest.py
```

### h) Run API server
```bash
uvicorn backend.main:app --reload
```

### i) Open frontend
Open this file directly in browser:
- `frontend/index.html`

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
