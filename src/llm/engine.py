"""
Ollama LLM Engine
Wraps the local Ollama model for generation.
"""
import logging
from langchain_ollama import ChatOllama

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config.settings import LLM_MODEL, OLLAMA_BASE_URL

logger = logging.getLogger(__name__)


class LLMEngine:
    """Wrapper around Ollama ChatOllama for the assistant."""

    def __init__(self, model: str = LLM_MODEL, base_url: str = OLLAMA_BASE_URL):
        self.model = model
        self.base_url = base_url
        self._llm = None

    @property
    def llm(self) -> ChatOllama:
        """Lazy-initialize the LLM instance."""
        if self._llm is None:
            self._llm = ChatOllama(
                model=self.model,
                base_url=self.base_url,
                temperature=0.3,
                num_predict=1024,
                top_p=0.9,
            )
            logger.info(f"LLM initialized: {self.model} @ {self.base_url}")
        return self._llm

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate a response given system and user prompts."""
        from langchain_core.messages import HumanMessage, SystemMessage

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        try:
            response = self.llm.invoke(messages)
            answer = response.content

            # qwen3 sometimes wraps answer in <think>...</think> tags, strip them
            if "<think>" in answer:
                import re
                answer = re.sub(r"<think>.*?</think>", "", answer, flags=re.DOTALL).strip()

            return answer
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return f"⚠️ Error generating response: {e}"

    def is_available(self) -> bool:
        """Check if the Ollama server and model are available."""
        try:
            import requests
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if resp.status_code == 200:
                models = [m["name"] for m in resp.json().get("models", [])]
                # Check if our model is available (with or without :latest tag)
                for m in models:
                    if self.model in m:
                        return True
                logger.warning(f"Model {self.model} not found. Available: {models}")
            return False
        except Exception as e:
            logger.error(f"Ollama not reachable: {e}")
            return False


# Module-level singleton
_engine: LLMEngine | None = None


def get_llm_engine() -> LLMEngine:
    """Get or create the singleton LLM engine."""
    global _engine
    if _engine is None:
        _engine = LLMEngine()
    return _engine
