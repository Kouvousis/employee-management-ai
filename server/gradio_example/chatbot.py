import gradio as gr
from rag.agent import hr_agent
from uuid import uuid4

USERS = {
    "HR User 1": "hr-user-1",
    "HR User 2": "hr-user-2",
}


from uuid import uuid4


def make_chat_fn(thread_id: str | None = None):
    current_thread_id = thread_id or str(uuid4())

    def chat(message: str, history: list) -> str:
        nonlocal current_thread_id

        config = {"configurable": {"thread_id": current_thread_id}}

        try:
            result = hr_agent.invoke(
                {"messages": [{"role": "user", "content": message}]},
                config=config,
            )
        except ValueError as error:
            error_message = str(error)

            if "Found AIMessages with tool_calls that do not have a corresponding ToolMessage" not in error_message:
                raise

            current_thread_id = str(uuid4())
            config = {"configurable": {"thread_id": current_thread_id}}

            result = hr_agent.invoke(
                {"messages": [{"role": "user", "content": message}]},
                config=config,
            )

        return result["messages"][-1].content

    return chat


with gr.Blocks(title="NovaTech Nova — HR Chatbot Test") as demo:
    gr.Markdown("## Nova — NovaTech HR Assistant\nEach tab is an independent user with its own conversation memory.")

    with gr.Tabs():
        for username, thread_id in USERS.items():
            with gr.Tab(username):
                gr.ChatInterface(fn=make_chat_fn(thread_id))

demo.launch()