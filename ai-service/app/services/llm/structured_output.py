"""Structured output helpers."""

import json
import time
from typing import Type, TypeVar

from app.core.logger import get_logger
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)
logger = get_logger(__name__)


class StructuredOutputError(Exception):
    pass


def parse_structured_output(raw_text: str, schema: Type[T]) -> T:
    start = time.perf_counter()
    logger.info(
        "structured_output_parse_started schema=%s raw_text_chars=%s",
        schema.__name__,
        len(raw_text),
    )
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        logger.warning(
            "structured_output_invalid_json schema=%s error=%s",
            schema.__name__,
            exc,
        )
        raise StructuredOutputError(f"Model returned invalid JSON: {exc}") from exc

    try:
        parsed = schema.model_validate(data)
        logger.info(
            "structured_output_parse_completed schema=%s elapsed_ms=%.2f",
            schema.__name__,
            (time.perf_counter() - start) * 1000,
        )
        return parsed
    except ValidationError as exc:
        logger.warning(
            "structured_output_validation_failed schema=%s error=%s",
            schema.__name__,
            exc,
        )
        raise StructuredOutputError(f"Output failed schema validation: {exc}") from exc
