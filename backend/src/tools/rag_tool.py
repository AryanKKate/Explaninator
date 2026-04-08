from typing import Dict, List

import chromadb
from crewai.tools import tool
from src.config.settings import settings
from src.tools.embeddings import embed_query

_client = chromadb.PersistentClient(path=settings.chroma_path)
_collection = _client.get_or_create_collection(name=settings.collection_name)


@tool("Search Notes")
def search_notes(query: str) -> str:
    """Search the indexed notes and return the most relevant chunks."""
    payload = retrieve_chunks(query, settings.max_retrieval_chunks)
    if not payload["chunks"]:
        return "NO_CONTEXT_FOUND"
    return "\n\n".join(payload["chunks"])


def retrieve_chunks(query: str, k: int = 5) -> Dict[str, List[str]]:
    query = query.strip()
    if not query:
        return {"chunks": [], "sources": []}

    query_embedding = embed_query(query)
    results = _collection.query(
        query_embeddings=[query_embedding],
        n_results=max(1, k),
        include=["documents", "metadatas", "distances"],
    )

    documents = results.get("documents", [[]])[0] if results.get("documents") else []
    metadatas = results.get("metadatas", [[]])[0] if results.get("metadatas") else []

    sources = [m.get("source", "unknown") for m in metadatas] if metadatas else []

    return {"chunks": documents or [], "sources": sources}
