from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware
from langgraph.checkpoint.memory import MemorySaver
from rag.config import LLM
from rag.tools.company_docs_tool import company_knowledge_tool
from rag.tools.employee_tool import employee_knowledge_tool
from rag.tools.action_tool import (
    get_current_date,
    add_employee_tool,
    assign_task_tool,
    create_project_tool,
    assign_employee_to_project_tool,
    add_task_to_project_tool,
)
from rag.prompts.hr_prompt import HR_SYSTEM_PROMPT

hr_tools = [
    company_knowledge_tool,
    employee_knowledge_tool,
    get_current_date,
    add_employee_tool,
    assign_task_tool,
    create_project_tool,
    assign_employee_to_project_tool,
    add_task_to_project_tool,
]

memory = MemorySaver()

hr_agent = create_agent(
    model=LLM,
    tools=hr_tools,
    checkpointer=memory,
    system_prompt=HR_SYSTEM_PROMPT,
    middleware=[SummarizationMiddleware(LLM, trigger=("tokens", 8000))],
)