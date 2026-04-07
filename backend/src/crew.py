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
        backstory="You are a disciplined retrieval specialist. You must call Search Notes first.",
        llm=shared_llm,
        tools=retriever_tools,
        verbose=False,
    )

    teacher = Agent(
        role="Teacher",
        goal="Explain concepts clearly like a patient tutor using only retrieved context.",
        backstory="You teach beginners with structured and simple explanations.",
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
            "If no notes are found, return exactly: NO_CONTEXT_FOUND. "
            "If web is enabled, optionally call Web Research after Search Notes for enrichment."
        ),
        expected_output="Relevant chunks from notes, or NO_CONTEXT_FOUND.",
        agent=retriever,
    )

    teach_task = Task(
        description=(
            "Based on the retriever output, explain the answer in a beginner-friendly structure:"
            " 1) direct answer, 2) short explanation, 3) key points. "
            "If retriever returned NO_CONTEXT_FOUND, explain that no answer can be grounded in notes."
        ),
        expected_output="A clear teaching response grounded in retrieved content.",
        agent=teacher,
        context=[retrieve_task],
    )

    verify_task = Task(
        description=(
            "Review the teacher response and ensure it is grounded in retrieved notes. "
            "Remove unsupported claims and return the final safe answer."
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
