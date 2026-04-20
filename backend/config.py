import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
STRUCTURED_DATA_FOLDER = "data/structured"
PDF_FOLDER = "data/pdfs"
VECTOR_STORE_PATH = "vector_store/faiss_index"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
GROQ_MODEL = "llama-3.1-8b-instant"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K_RESULTS = 5
BRANCH = "CSE and CS"
COLLEGE_NAME = "KIET Group of Institutions, Delhi-NCR, Ghaziabad"
