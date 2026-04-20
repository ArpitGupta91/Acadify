import os
import json
from pathlib import Path
from typing import List

import fitz
import pdfplumber
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.docstore.document import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

try:
    from backend.config import (
        CHUNK_OVERLAP,
        CHUNK_SIZE,
        EMBEDDING_MODEL,
        PDF_FOLDER,
        STRUCTURED_DATA_FOLDER,
        VECTOR_STORE_PATH,
    )
except ImportError:
    from config import (
        CHUNK_OVERLAP,
        CHUNK_SIZE,
        EMBEDDING_MODEL,
        PDF_FOLDER,
        STRUCTURED_DATA_FOLDER,
        VECTOR_STORE_PATH,
    )


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    return _project_root() / path


def _is_text_usable(text: str) -> bool:
    if not text:
        return False
    stripped = text.strip()
    if len(stripped) < 30:
        return False

    printable_count = sum(ch.isprintable() for ch in stripped)
    ratio = printable_count / max(1, len(stripped))
    return ratio > 0.85


def load_pdfs(pdf_folder: str) -> List[Document]:
    pdf_root = _resolve_path(pdf_folder)
    if not pdf_root.exists():
        raise FileNotFoundError(
            f"PDF folder not found at '{pdf_root}'. Create it and add PDF files first."
        )

    documents: List[Document] = []
    pdf_files = sorted(pdf_root.rglob("*.pdf"))

    if not pdf_files:
        raise FileNotFoundError(
            f"No PDF files found in '{pdf_root}'. Add PDFs and run ingestion again."
        )

    for pdf_path in pdf_files:
        source_name = pdf_path.name

        try:
            with pdfplumber.open(str(pdf_path)) as plumber_pdf:
                for page_index, page in enumerate(plumber_pdf.pages, start=1):
                    text = page.extract_text() or ""

                    if not _is_text_usable(text):
                        try:
                            with fitz.open(str(pdf_path)) as fitz_pdf:
                                fitz_page = fitz_pdf[page_index - 1]
                                text = fitz_page.get_text("text") or ""
                        except Exception as fitz_error:
                            print(
                                f"[WARN] PyMuPDF fallback failed for {source_name} page {page_index}: {fitz_error}"
                            )

                    if _is_text_usable(text):
                        documents.append(
                            Document(
                                page_content=text.strip(),
                                metadata={"source": source_name, "page": page_index},
                            )
                        )
        except Exception as plumber_error:
            print(f"[WARN] pdfplumber failed for {source_name}: {plumber_error}")
            try:
                with fitz.open(str(pdf_path)) as fitz_pdf:
                    for page_index in range(len(fitz_pdf)):
                        page = fitz_pdf[page_index]
                        text = page.get_text("text") or ""
                        if _is_text_usable(text):
                            documents.append(
                                Document(
                                    page_content=text.strip(),
                                    metadata={
                                        "source": source_name,
                                        "page": page_index + 1,
                                    },
                                )
                            )
            except Exception as fitz_error:
                print(f"[ERROR] Failed to extract {source_name} with both engines: {fitz_error}")

    if not documents:
        raise ValueError(
            "No readable text was extracted from PDFs. Ensure PDFs contain selectable text."
        )

    return documents


def chunk_documents(documents: List[Document]) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = splitter.split_documents(documents)

    if not chunks:
        raise ValueError("Chunking produced 0 chunks. Check the extracted document content.")

    return chunks


def json_to_readable_text(data: dict, prefix: str = "") -> str:
    lines: List[str] = []

    if isinstance(data, dict):
        for key, value in data.items():
            key_path = f"{prefix}_{key}" if prefix else str(key)
            lines.append(json_to_readable_text(value, key_path))
    elif isinstance(data, list):
        for index, value in enumerate(data, start=1):
            list_prefix = f"{prefix}_{index}" if prefix else f"item_{index}"
            lines.append(json_to_readable_text(value, list_prefix))
    else:
        lines.append(f"{prefix}: {data}")

    return "\n".join(line for line in lines if line)


def ingest_json_as_documents(structured_folder: str) -> List[Document]:
    structured_root = _resolve_path(structured_folder)
    if not structured_root.exists():
        print(f"[WARN] Structured JSON folder not found at '{structured_root}'. Skipping JSON ingestion.")
        return []

    documents: List[Document] = []
    for json_file in sorted(structured_root.rglob("*.json")):
        try:
            with json_file.open("r", encoding="utf-8") as file:
                data = json.load(file)
            text = json_to_readable_text(data)
            if text.strip():
                documents.append(
                    Document(
                        page_content=text,
                        metadata={"source": json_file.name, "type": "structured_json"},
                    )
                )
        except Exception as error:
            print(f"[WARN] Could not ingest JSON file '{json_file.name}': {error}")

    return documents


def build_vector_store(chunks: List[Document]) -> FAISS:
    store_path = _resolve_path(VECTOR_STORE_PATH)
    store_path.parent.mkdir(parents=True, exist_ok=True)

    json_documents = ingest_json_as_documents(STRUCTURED_DATA_FOLDER)
    combined_documents = list(chunks) + json_documents

    if not combined_documents:
        raise ValueError("No documents available to embed. Add PDFs/JSON files and retry ingestion.")

    try:
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        vector_store = FAISS.from_documents(combined_documents, embeddings)
        vector_store.save_local(str(store_path))
    except Exception as error:
        raise RuntimeError(f"Failed to build and save FAISS index: {error}") from error

    print(
        f"Embedded and saved {len(combined_documents)} documents "
        f"({len(chunks)} PDF chunks + {len(json_documents)} JSON docs) to '{store_path}'."
    )
    return vector_store


def load_vector_store() -> FAISS:
    store_path = _resolve_path(VECTOR_STORE_PATH)
    index_file = store_path / "index.faiss"
    pkl_file = store_path / "index.pkl"

    if not index_file.exists() or not pkl_file.exists():
        raise FileNotFoundError(
            f"FAISS index not found at '{store_path}'. Run 'python backend/ingest.py' first."
        )

    try:
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        return FAISS.load_local(
            str(store_path),
            embeddings,
            allow_dangerous_deserialization=True,
        )
    except Exception as error:
        raise RuntimeError(f"Failed to load FAISS index from '{store_path}': {error}") from error


if __name__ == "__main__":
    loaded_docs = load_pdfs(PDF_FOLDER)
    chunked_docs = chunk_documents(loaded_docs)
    json_docs = ingest_json_as_documents(STRUCTURED_DATA_FOLDER)
    build_vector_store(chunked_docs)
    print(
        "Ingestion complete. "
        f"{len(loaded_docs)} PDF documents, {len(chunked_docs)} PDF chunks, {len(json_docs)} JSON documents indexed."
    )
