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


def _env_bool(name: str, default: bool) -> bool:
	raw = os.getenv(name)
	if raw is None:
		return default
	return str(raw).strip().lower() in {"1", "true", "yes", "on"}


IS_RENDER = bool(os.getenv("RENDER")) or bool(os.getenv("RENDER_SERVICE_ID"))

# Heavy components consume memory on free Render instances.
ENABLE_VECTOR_STORE = _env_bool("ENABLE_VECTOR_STORE", not IS_RENDER)
ENABLE_ML_MODELS = _env_bool("ENABLE_ML_MODELS", not IS_RENDER)
