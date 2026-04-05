import os
from dotenv import load_dotenv
load_dotenv()
if "GOOGLE_API_KEY" in os.environ and "GEMINI_API_KEY" not in os.environ:
    os.environ["GEMINI_API_KEY"] = os.environ["GOOGLE_API_KEY"]

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.crew import run_crew
from src.tools.rag_tool import insert_note
import fitz  # PyMuPDF
import chromadb
from sentence_transformers import SentenceTransformer
print("API KEY LOADED:", bool(os.getenv("GOOGLE_API_KEY")))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AskRequest(BaseModel):
    query: str

@app.post("/ask")
async def ask(req: AskRequest):
    response = run_crew(req.query)
    # CrewAI tasks might return a string or object. Convert appropriately.
    ans = response.raw if hasattr(response, "raw") else str(response)
    return {"answer": ans}

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

client = chromadb.Client()
collection = client.get_or_create_collection("notes")

embedder = SentenceTransformer("all-MiniLM-L6-v2")

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_path = f"uploads/{file.filename}"

    with open(file_path, "wb") as f:
        f.write(await file.read())

    # ✅ Extract text from PDF
    text = ""
    doc = fitz.open(file_path)
    for page in doc:
        text += page.get_text()

    # ✅ Chunk text
    chunks = [text[i:i+500] for i in range(0, len(text), 500)]

    # ✅ Embed + store
    embeddings = embedder.encode(chunks).tolist()

    collection.add(
        documents=chunks,
        embeddings=embeddings,
        ids=[f"{file.filename}_{i}" for i in range(len(chunks))]
    )

    return {"message": "File processed and stored ✅"}