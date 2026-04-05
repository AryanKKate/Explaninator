from crewai import Agent, Task, Crew, Process, LLM
from src.tools.rag_tool import search_notes
from langchain_google_genai import ChatGoogleGenerativeAI
llm = LLM(
    model="gemini-2.5-flash",
    temperature=0.3
)

retriever = Agent(
    role="Retriever",
    goal="Fetch relevant notes",
    backstory="You are an expert researcher. You can navigate databases to extract exactly the right study notes needed.",
    tools=[search_notes],
    llm=llm
)

teacher = Agent(
    role="Teacher",
    goal="Explain clearly",
    backstory="You are a compassionate, clear, and insightful teacher. You break down complex ideas so that a student easily understands them.",
    llm=llm,
    memory=True
)

verifier = Agent(
    role="Verifier",
    goal="Validate answers",
    backstory="You are a meticulous fact-checker. You rigorously review explanations to ensure they are fully accurate and helpful.",
    llm=llm
)

def run_crew(query):
    retrieve = Task(
        description=f"Find relevant notes for: {query}",
        expected_output="A list of relevant notes or facts extracted from the database.",
        agent=retriever
    )

    teach = Task(
        description=f"Explain: {query}",
        expected_output="A clear, easy-to-understand explanation of the queried topic.",
        agent=teacher
    )

    verify = Task(
        description="Validate answer",
        expected_output="The final, fact-checked answer ready to be shown to the user.",
        agent=verifier
    )

    crew = Crew(
        agents=[retriever, teacher, verifier],
        tasks=[retrieve, teach, verify],
        process=Process.sequential
    )

    return crew.kickoff()