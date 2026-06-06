from langchain_core.tools import tool
from rag.vectorstores.employee_store import get_employee_store


@tool
def employee_knowledge_tool(query: str) -> str:
    """Search the NovaTech employee database. Use this tool to find information
    about specific employees including their full name, role, department, email,
    hire date, and assigned tasks with statuses (todo, in_progress, completed)."""
    docs = get_employee_store().similarity_search(query, k=4)

    if not docs:
        return "No relevant employee documents found."

    results = []
    for doc in docs:
        source = doc.metadata.get("source", "Unknown")
        employee_id = doc.metadata.get("employee_id", "Unknown")
        content = doc.page_content.strip()

        results.append(f"Source: {source}\nEmployee ID: {employee_id}\nContent: {content}\n")

    return "\n".join(results)
