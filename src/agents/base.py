from groq import Groq
from loguru import logger
from src.core.config import settings

class BaseAgent:
    def __init__(self):
        self.client = Groq(api_key=settings.groq_api_key)
        self.model = settings.llm_model

    def call_llm(self, prompt: str, max_tokens: int = 1000) -> str:
        logger.debug(f"Calling LLM with prompt length: {len(prompt)}")
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.1
            )
            result = response.choices[0].message.content
            logger.debug(f"LLM response length: {len(result)}")
            return result
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise