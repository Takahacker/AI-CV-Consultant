import os
from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import ChatNVIDIA

load_dotenv()

# LLM — NVIDIA NIM
llm = ChatNVIDIA(
    model=os.environ.get("NVIDIA_MODEL", "meta/llama-3.3-70b-instruct"),
    api_key=os.environ["NVIDIA_API_KEY"],
    temperature=0,
)

# Thresholds
SCORE_THRESHOLD = 80
MAX_ITERATIONS = 3
