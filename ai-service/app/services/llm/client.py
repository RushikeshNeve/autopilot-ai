"""LLM client wrapper."""

import time
from typing import Optional

from openai import OpenAI

from app.core.config import get_settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class LLMClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.model = settings.openai_model
        self.client: Optional[OpenAI] = None
        if settings.openai_api_key:
            self.client = OpenAI(
                api_key=settings.openai_api_key,
                timeout=settings.openai_timeout,
                max_retries=settings.openai_max_retries,
            )
            logger.info(
                "llm_client_initialized model=%s timeout=%s max_retries=%s",
                self.model,
                settings.openai_timeout,
                settings.openai_max_retries,
            )
        else:
            logger.warning(
                "llm_client_not_initialized_missing_api_key model=%s",
                self.model,
            )

    def generate_text(self, prompt: str) -> str:
        if self.client is None:
            raise ValueError("OPENAI_API_KEY is not configured")

        start = time.perf_counter()
        logger.info(
            "llm_request_started model=%s prompt_chars=%s timeout=%s max_retries=%s",
            self.model,
            len(prompt),
            get_settings().openai_timeout,
            get_settings().openai_max_retries,
        )
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )
        content = response.choices[0].message.content or ""
        logger.info(
            "llm_request_completed model=%s response_chars=%s elapsed_ms=%.2f",
            self.model,
            len(content),
            (time.perf_counter() - start) * 1000,
        )
        return content
