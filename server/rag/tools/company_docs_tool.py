from langchain_core.tools import tool
from rag.vectorstores.company_store import get_company_store


@tool
def company_knowledge_tool(query: str) -> str:
    """Search NovaTech's internal company documents. Use this tool to answer questions
    about company history, mission and values, leadership team, office locations,
    org chart, PTO policy, remote work policy, health benefits, 401k plan,
    parental leave, code of conduct, onboarding process, performance reviews,
    and promotion criteria."""
    docs = get_company_store().similarity_search(query, k=4)

    if not docs:
        return "No relevant company documents found."

    results = []
    for doc in docs:
        source = doc.metadata.get("source", "Unknown")
        topic = doc.metadata.get("topic", "Unknown")
        content = doc.page_content.strip()

        results.append(f"Source: {source}\nTopic: {topic}\nContent: {content}\n")

    return "\n".join(results)
