import os
import uuid
from pathlib import Path
from typing import List

import chromadb
import fitz
import pytesseract
from PIL import Image
from src.config.settings import settings
from src.tools.embeddings import embed_documents

_client = chromadb.PersistentClient(path=settings.chroma_path)
_collection = _client.get_or_create_collection(name=settings.collection_name)


def _extract_pdf_text(file_path: str) -> str:
    text: List[str] = []
    with fitz.open(file_path) as doc:
        for page in doc:
            text.append(page.get_text("text"))
    return "\n".join(text).strip()


def _extract_image_text(file_path: str) -> str:
    with Image.open(file_path) as img:
        return pytesseract.image_to_string(img).strip()


def extract_text(file_path: str) -> str:
    suffix = Path(file_path).suffix.lower()
    if suffix == ".pdf":
        return _extract_pdf_text(file_path)
    if suffix in {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"}:
        return _extract_image_text(file_path)
    raise ValueError(f"Unsupported file type: {suffix}")


def chunk_text(text: str) -> List[str]:
    cleaned = " ".join(text.split())
    if not cleaned:
        return []

    chunks: List[str] = []
    step = max(1, settings.chunk_size - settings.chunk_overlap)
    for start in range(0, len(cleaned), step):
        chunk = cleaned[start : start + settings.chunk_size]
        if len(chunk.strip()) >= 30:
            chunks.append(chunk)
    return chunks


def store_chunks(chunks: List[str], source_file: str) -> int:
    if not chunks:
        return 0

    embeddings = embed_documents(chunks)
    ids = [str(uuid.uuid4()) for _ in chunks]
    metadatas = [{"source": source_file} for _ in chunks]

    _collection.add(ids=ids, documents=chunks, embeddings=embeddings, metadatas=metadatas)
    return len(chunks)


def ingest_file(file_path: str, original_filename: str) -> int:
    text = extract_text(file_path)
    if not text:
        raise ValueError("No text could be extracted from the uploaded file.")

    chunks = chunk_text(text)
    if not chunks:
        raise ValueError("Extracted text is too short or empty after preprocessing.")

    return store_chunks(chunks, original_filename)
