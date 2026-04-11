from pathlib import Path
from typing import Any, Dict, List

import yaml
from crewai import Agent, Crew, Process, Task
from langchain_groq import ChatGroq

from src.config.settings import settings
from src.tools.rag_tool import search_notes
from src.tools.web_tool import web_research

_CONFIG_DIR = Path(__file__).resolve().parent / "config"


def _load_yaml(file_name: str) -> Dict[str, Any]:
    with (_CONFIG_DIR / file_name).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


AGENT_CONFIG = _load_yaml("agents.yaml")
TASK_CONFIG = _load_yaml("task.yaml")

shared_llm = ChatGroq(
    model=settings.groq_model,
    temperature=0.2,
)


def _cfg(section: Dict[str, Any], key: str, field: str, fallback: str) -> str:
    return str(section.get(key, {}).get(field, fallback)).strip()


def run_crew(query: str, conversation_history: List[dict], web_enabled: bool = False):
    history_block = "\n".join(
        [f"{m.get('role', 'user')}: {m.get('content', '')}" for m in conversation_history[-8:]]
    )

    retriever_tools = [search_notes]
    if web_enabled:
        retriever_tools.append(web_research)

    retriever = Agent(
        role=_cfg(AGENT_CONFIG, "retriever", "role", "Retriever"),
        goal=_cfg(AGENT_CONFIG, "retriever", "goal", "Retrieve relevant note chunks."),
        backstory=_cfg(AGENT_CONFIG, "retriever", "backstory", "You are a retrieval expert."),
        llm=shared_llm,
        tools=retriever_tools,
        verbose=False,
    )

    teacher = Agent(
        role=_cfg(AGENT_CONFIG, "teacher", "role", "Teacher"),
        goal=_cfg(AGENT_CONFIG, "teacher", "goal", "Teach clearly from retrieved notes."),
        backstory=_cfg(AGENT_CONFIG, "teacher", "backstory", "You are a patient tutor."),
        llm=shared_llm,
        verbose=False,
    )

    verifier = Agent(
        role=_cfg(AGENT_CONFIG, "verifier", "role", "Verifier"),
        goal=_cfg(AGENT_CONFIG, "verifier", "goal", "Validate grounded answers."),
        backstory=_cfg(
            AGENT_CONFIG,
            "verifier",
            "backstory",
            "You are strict about grounding and hallucination prevention.",
        ),
        llm=shared_llm,
        verbose=False,
    )

    retrieve_task = Task(
        description=_cfg(TASK_CONFIG, "retrieve_task", "description", "Retrieve relevant context.").format(
            query=query,
            history_block=history_block,
        ),
        expected_output=_cfg(
            TASK_CONFIG,
            "retrieve_task",
            "expected_output",
            "Relevant chunks from notes, or NO_CONTEXT_FOUND.",
        ),
        agent=retriever,
    )

    teach_task = Task(
        description=_cfg(TASK_CONFIG, "teach_task", "description", "Teach from retrieval output."),
        expected_output=_cfg(
            TASK_CONFIG,
            "teach_task",
            "expected_output",
            "A clear grounded teaching response.",
        ),
        agent=teacher,
        context=[retrieve_task],
    )

    verify_task = Task(
        description=_cfg(TASK_CONFIG, "verify_task", "description", "Validate final response."),
        expected_output=_cfg(
            TASK_CONFIG,
            "verify_task",
            "expected_output",
            "Final grounded answer suitable for user display.",
        ),
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
