from typing import List

from sentence_transformers import SentenceTransformer

from src.config.settings import settings

# Loaded once at import time, reused across requests for low latency.
_MODEL = SentenceTransformer(settings.embedding_model)


def embed_documents(texts: List[str]) -> List[List[float]]:
    if not texts:
        return []
    vectors = _MODEL.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        batch_size=64,
        show_progress_bar=False,
    )
    return vectors.tolist()


def embed_query(text: str) -> List[float]:
    vector = _MODEL.encode(
        [text],
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )[0]
    return vector.tolist()
