import re
from typing import Dict, List, Tuple

import chromadb
from crewai.tools import tool
from litellm import completion
from src.config.settings import settings
from src.tools.embeddings import embed_query

_client = chromadb.PersistentClient(path=settings.chroma_path)
_collection = _client.get_or_create_collection(name=settings.collection_name)
_MAX_QUERY_VARIANTS = 3


@tool("Search Notes")
def search_notes(query: str) -> str:
    """Search the indexed notes and return the most relevant chunks."""
    payload = retrieve_chunks(query, settings.max_retrieval_chunks)
    if not payload["chunks"]:
        return "NO_CONTEXT_FOUND"
    formatted_chunks = []
    for idx, chunk in enumerate(payload["chunks"], start=1):
        source = payload["sources"][idx - 1] if idx - 1 < len(payload["sources"]) else "unknown"
        formatted_chunks.append(f"[Source: {source}]\n{chunk}")
    return "\n\n---\n\n".join(formatted_chunks)


def _resolve_litellm_model(model_name: str) -> str:
    model_name = model_name.strip()
    if "/" in model_name:
        return model_name
    if model_name.startswith("gemini-"):
        return f"gemini/{model_name}"
    return model_name


def _generate_hypothetical_answer(query: str) -> str:
    model = _resolve_litellm_model(settings.llm_model)
    response = completion(
        model=model,
        temperature=0.1,
        max_tokens=220,
        messages=[
            {
                "role": "system",
                "content": (
                    "Write a concise hypothetical study-note answer that could plausibly answer "
                    "the user's question. Focus on concepts and terminology."
                ),
            },
            {"role": "user", "content": query},
        ],
    )
    message = response.choices[0].message
    content = getattr(message, "content", "") or ""
    return content.strip()


def _parse_query_variants(raw: str) -> List[str]:
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    cleaned: List[str] = []
    for line in lines:
        normalized = re.sub(r"^\d+[\).\-\s]*", "", line).strip(" -•*")
        if normalized:
            cleaned.append(normalized)
    return cleaned[:_MAX_QUERY_VARIANTS]


def _generate_query_variants(query: str) -> List[str]:
    model = _resolve_litellm_model(settings.llm_model)
    response = completion(
        model=model,
        temperature=0.2,
        max_tokens=180,
        messages=[
            {
                "role": "system",
                "content": (
                    "Rewrite the user question into 3 different semantic search queries. "
                    "Use alternate wording and synonyms. Output one query per line only."
                ),
            },
            {"role": "user", "content": query},
        ],
    )
    content = getattr(response.choices[0].message, "content", "") or ""
    return _parse_query_variants(content)


def _collect_ranked_results(
    query_text: str, k: int
) -> Tuple[List[str], List[str], List[float]]:
    query_embedding = embed_query(query_text)
    results = _collection.query(
        query_embeddings=[query_embedding],
        n_results=max(1, k),
        include=["documents", "metadatas", "distances"],
    )
    documents = results.get("documents", [[]])[0] if results.get("documents") else []
    metadatas = results.get("metadatas", [[]])[0] if results.get("metadatas") else []
    distances = results.get("distances", [[]])[0] if results.get("distances") else []
    sources = [m.get("source", "unknown") for m in metadatas] if metadatas else []
    return documents or [], sources, distances or []


def retrieve_chunks(query: str, k: int = 5) -> Dict[str, List[str]]:
    query = query.strip()
    if not query:
        return {"chunks": [], "sources": []}

    expanded_queries = [query]

    try:
        for variant in _generate_query_variants(query):
            if variant and variant not in expanded_queries:
                expanded_queries.append(variant)
    except Exception:
        pass

    try:
        hyde_answer = _generate_hypothetical_answer(query)
        if hyde_answer:
            expanded_queries.append(hyde_answer)
    except Exception:
        pass

    ranked_candidates: List[Tuple[float, str, str]] = []
    for semantic_query in expanded_queries:
        documents, sources, distances = _collect_ranked_results(semantic_query, max(2, k))
        for doc, source, distance in zip(documents, sources, distances):
            ranked_candidates.append((float(distance), doc, source))

    ranked_candidates.sort(key=lambda item: item[0])
    deduped_chunks: List[str] = []
    deduped_sources: List[str] = []
    seen_docs = set()
    for _, chunk, source in ranked_candidates:
        normalized_chunk = " ".join(chunk.split()).lower()
        if normalized_chunk in seen_docs:
            continue
        seen_docs.add(normalized_chunk)
        deduped_chunks.append(chunk)
        deduped_sources.append(source)
        if len(deduped_chunks) >= max(1, k):
            break

    return {"chunks": deduped_chunks, "sources": deduped_sources}
