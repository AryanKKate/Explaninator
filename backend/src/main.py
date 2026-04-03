from fastapi import FastAPI, UploadFile
from crew import run_crew

app = FastAPI()

@app.post("/ask")
async def ask(query: str):
    response = run_crew(query)
    return {"answer": response}