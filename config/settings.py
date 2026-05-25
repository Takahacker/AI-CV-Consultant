import os
import time
from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import ChatNVIDIA

load_dotenv()

# LLM via NVIDIA NIM
llm = ChatNVIDIA(
    model=os.environ.get("NVIDIA_MODEL", "meta/llama-3.3-70b-instruct"),
    api_key=os.environ["NVIDIA_API_KEY"],
    temperature=0,
)

# Thresholds
SCORE_THRESHOLD = 80
MAX_ITERATIONS = 3


def llm_invoke(prompt, max_retries: int = 5, base_delay: float = 3.0):
    """llm.invoke() com backoff exponencial em 429 (rate limit do NVIDIA NIM)."""
    last_exc = None
    for attempt in range(max_retries):
        try:
            return llm.invoke(prompt)
        except Exception as e:
            last_exc = e
            msg = str(e)
            if "429" in msg and attempt < max_retries - 1:
                wait = base_delay * (2 ** attempt)
                time.sleep(wait)
                continue
            raise
    raise last_exc  # pragma: no cover
