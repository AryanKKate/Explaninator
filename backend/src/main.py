import os
from pathlib import Path
from typing import Dict, List, Literal

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.config.settings import settings
from src.crew import run_crew
from src.tools.ingestion import ingest_file

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_session_memory: Dict[str, List[dict]] = {}
SUPPORTED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"}


class AskRequest(BaseModel):
    query: str = Field(..., min_length=2)
    session_id: str = Field(default="default")
    web_enabled: bool = Field(default=False)


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str


@app.get("/health")
def health_check():
    return {"status": "ok", "model": settings.llm_model}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename in upload.")

    ext = Path(file.filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Supported: {sorted(SUPPORTED_EXTENSIONS)}",
        )

    save_path = os.path.join(settings.upload_dir, file.filename)

    try:
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        with open(save_path, "wb") as f:
            f.write(contents)

        chunk_count = ingest_file(save_path, file.filename)
        return {
            "message": "File processed and indexed successfully.",
            "file": file.filename,
            "chunks_indexed": chunk_count,
        }
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to process upload: {exc}") from exc


@app.post("/ask")
def ask_question(request: AskRequest):
    history = _session_memory.get(request.session_id, [])
    history.append({"role": "user", "content": request.query})

    try:
        response = run_crew(
            query=request.query,
            conversation_history=history,
            web_enabled=request.web_enabled,
        )
        answer = response.raw if hasattr(response, "raw") else str(response)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to generate answer: {exc}") from exc

    history.append({"role": "assistant", "content": answer})
    _session_memory[request.session_id] = history[-20:]

    return {
        "answer": answer,
        "session_id": request.session_id,
        "history": [Message(**m).model_dump() for m in _session_memory[request.session_id]],
    }
