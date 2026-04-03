from crewai_tools import tool
import chromadb

client = chromadb.Client()
collection = client.get_or_create_collection("notes")

@tool("Search Notes")
def search_notes(query: str) -> str:
    results = collection.query(query_texts=[query], n_results=5)
    return "\n".join(results["documents"][0])