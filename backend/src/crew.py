from crewai import Agent, Task, Crew, Process
from langchain_google_genai import ChatGoogleGenerativeAI
from tools.rag_tool import search_notes

llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")

retriever = Agent(
    role="Retriever",
    goal="Fetch relevant notes",
    tools=[search_notes],
    llm=llm
)

teacher = Agent(
    role="Teacher",
    goal="Explain clearly",
    llm=llm,
    memory=True
)

verifier = Agent(
    role="Verifier",
    goal="Validate answers",
    llm=llm
)

def run_crew(query):
    retrieve = Task(
        description=f"Find relevant notes for: {query}",
        agent=retriever
    )

    teach = Task(
        description=f"Explain: {query}",
        agent=teacher
    )

    verify = Task(
        description="Validate answer",
        agent=verifier
    )

    crew = Crew(
        agents=[retriever, teacher, verifier],
        tasks=[retrieve, teach, verify],
        process=Process.sequential
    )

    return crew.kickoff()