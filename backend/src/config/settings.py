import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

if "GOOGLE_API_KEY" in os.environ and "GEMINI_API_KEY" not in os.environ:
    os.environ["GEMINI_API_KEY"] = os.environ["GOOGLE_API_KEY"]


@dataclass(frozen=True)
class Settings:
    app_name: str = "AI Tutor API"
    upload_dir: str = os.getenv("UPLOAD_DIR", "uploads")
    chroma_path: str = os.getenv("CHROMA_PATH", "./chroma_db")
    collection_name: str = os.getenv("CHROMA_COLLECTION", "notes")
    llm_model: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "800"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "120"))
    max_retrieval_chunks: int = int(os.getenv("MAX_RETRIEVAL_CHUNKS", "5"))


settings = Settings()
os.makedirs(settings.upload_dir, exist_ok=True)
