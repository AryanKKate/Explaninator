from crewai.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun

_search = DuckDuckGoSearchRun()


@tool("Web Research")
def web_research(query: str) -> str:
    """Perform a lightweight web search for supplemental context."""
    return _search.run(query)
