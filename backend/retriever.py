from typing import List, Tuple

from langchain_community.vectorstores import FAISS


def retrieve_context(query: str, vector_store: FAISS, top_k: int = 5) -> Tuple[str, List[str]]:
    docs = vector_store.similarity_search(query, k=top_k)

    if not docs:
        return "", []

    context_blocks: List[str] = []
    sources: List[str] = []

    for doc in docs:
        source = doc.metadata.get("source", "Unknown")
        page = doc.metadata.get("page", "?")
        source_label = f"{source} (Page {page})"
        sources.append(source_label)

        context_blocks.append(
            f"[Source: {source} | Page: {page}]\n{doc.page_content.strip()}\n---"
        )

    unique_sources = sorted(set(sources))
    context = "\n".join(context_blocks)
    return context, unique_sources
