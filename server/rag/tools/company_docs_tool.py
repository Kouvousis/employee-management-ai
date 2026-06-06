from langchain_core.tools import tool
from rag.vectorstores.company_store import get_company_store


@tool
def company_knowledge_tool(query) -> str:
    """Search NovaTechs internal company knowledge documents, policies,
    benefits, and any other information contained in the company_docs/ txt files."""
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
