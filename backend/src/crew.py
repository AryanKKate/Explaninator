from typing import List

from crewai import Agent, Crew, Process, Task
from langchain_google_genai import ChatGoogleGenerativeAI

from src.config.settings import settings
from src.tools.rag_tool import search_notes
from src.tools.web_tool import web_research

shared_llm = ChatGoogleGenerativeAI(
    model=settings.llm_model,
    temperature=0.2,
    google_api_key=None,
)


def run_crew(query: str, conversation_history: List[dict], web_enabled: bool = False):
    history_block = "\n".join(
        [f"{m.get('role', 'user')}: {m.get('content', '')}" for m in conversation_history[-8:]]
    )

    retriever_tools = [search_notes]
    if web_enabled:
        retriever_tools.append(web_research)

    retriever = Agent(
        role="Retriever",
        goal="Fetch only relevant note chunks that directly answer the student question.",
        backstory=(
            "You are a disciplined retrieval specialist. You must call Search Notes first and "
            "run multiple semantic searches, not just one literal keyword search. For each "
            "question, break it into concepts and issue at least 3 distinct query phrasings "
            "that use synonyms, alternate wording, and domain-specific variants."
        ),
        llm=shared_llm,
        tools=retriever_tools,
        verbose=False,
    )

    teacher = Agent(
        role="Teacher",
        goal=(
            "Teach the answer with clear reasoning, practical intuition, and beginner-friendly "
            "structure using only retrieved context."
        ),
        backstory=(
            "You are a patient expert tutor. You do not dump raw retrieved text. Instead, you "
            "synthesize it into a guided explanation with steps, intuition, and a short example."
        ),
        llm=shared_llm,
        verbose=False,
    )

    verifier = Agent(
        role="Verifier",
        goal="Ensure every claim is grounded in retrieved notes and flag missing evidence.",
        backstory="You are strict about hallucination prevention and source grounding.",
        llm=shared_llm,
        verbose=False,
    )

    retrieve_task = Task(
        description=(
            "Use Search Notes to retrieve note chunks for this question: "
            f"'{query}'.\nConversation history:\n{history_block}\n"
            "You must do agentic multi-query retrieval:\n"
            "1) Identify the underlying concepts in the user question.\n"
            "2) Generate at least 3 materially different semantic search queries.\n"
            "3) Call Search Notes multiple times (once per query variant).\n"
            "4) Merge and deduplicate the best relevant chunks before returning.\n"
            "Do not rely on a single exact-phrase query.\n"
            "If no notes are found, return exactly: NO_CONTEXT_FOUND. "
            "If web is enabled, optionally call Web Research after Search Notes for enrichment."
        ),
        expected_output="Relevant chunks from notes, or NO_CONTEXT_FOUND.",
        agent=retriever,
    )

    teach_task = Task(
        description=(
            "Based on the retriever output, teach the concept like a real tutor.\n"
            "Required structure:\n"
            "1) Direct answer in 1-2 sentences.\n"
            "2) Why this is the answer (reasoning grounded in retrieved notes).\n"
            "3) Step-by-step breakdown.\n"
            "4) Mini example or analogy.\n"
            "5) Key takeaways and common mistake to avoid.\n"
            "Do not copy raw chunks verbatim; synthesize and explain."
            "If retriever returned NO_CONTEXT_FOUND, explain that no answer can be grounded in notes."
        ),
        expected_output="A clear teaching response grounded in retrieved content.",
        agent=teacher,
        context=[retrieve_task],
    )

    verify_task = Task(
        description=(
            "Review the teacher response and ensure it is grounded in retrieved notes. "
            "Remove unsupported claims and preserve a clear teaching structure with reasoning."
        ),
        expected_output="Final grounded answer suitable for user display.",
        agent=verifier,
        context=[retrieve_task, teach_task],
    )

    crew = Crew(
        agents=[retriever, teacher, verifier],
        tasks=[retrieve_task, teach_task, verify_task],
        process=Process.sequential,
        verbose=False,
        memory=True,
    )

    return crew.kickoff()
