from crewai.tools import tool
import chromadb

import uuid

client = chromadb.Client()
collection = client.get_or_create_collection("notes")

def insert_note(text: str):
    collection.add(documents=[text], ids=[str(uuid.uuid4())])

@tool("Search Notes")
def search_notes(query: str) -> str:
    """Useful to search through the user's stored study notes to find relevant information."""
    results = collection.query(query_texts=[query], n_results=5)
    return "\n".join(results["documents"][0])