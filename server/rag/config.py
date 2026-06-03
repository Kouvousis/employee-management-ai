import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

load_dotenv()

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY")

if not OPENAI_KEY:
    raise ValueError("OPENAI_API_KEY is required for embeddings — set it in .env")

EMBEDDINGS = OpenAIEmbeddings(model="text-embedding-3-small")

if OPENAI_KEY:
    from langchain_openai import ChatOpenAI

    LLM = ChatOpenAI(model="gpt-4o-mini", temperature=0, max_retries=3, timeout=30)
elif ANTHROPIC_KEY:
    from langchain_anthropic import ChatAnthropic

    LLM = ChatAnthropic(model_name="claude-haiku-4-5-20251001", temperature=0, timeout=30, max_retries=3)
else:
    raise ValueError("No LLM API key found — set OPENAI_API_KEY or ANTHROPIC_API_KEY in .env")
