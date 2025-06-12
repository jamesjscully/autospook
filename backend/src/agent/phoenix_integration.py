"""Arize Phoenix integration utilities."""

from __future__ import annotations

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from phoenix.trace import OpenInferenceTracer
    from phoenix.trace.langchain import LangChainInstrumentor
except Exception:  # pragma: no cover - optional dependency
    OpenInferenceTracer = None  # type: ignore
    LangChainInstrumentor = None

_tracer: Optional[OpenInferenceTracer] = None


def initialize_phoenix() -> Optional[OpenInferenceTracer]:
    """Initialize Arize Phoenix tracing if enabled via environment variable."""
    enable = os.getenv("ENABLE_PHOENIX", "false").lower() in {"1", "true", "yes"}
    if not enable:
        logger.debug("Phoenix tracing not enabled")
        return None

    if OpenInferenceTracer is None or LangChainInstrumentor is None:
        logger.warning("Arize Phoenix is not installed; tracing disabled")
        return None

    global _tracer
    if _tracer is None:
        _tracer = OpenInferenceTracer()
        LangChainInstrumentor().instrument(tracer=_tracer)
        logger.info("Arize Phoenix tracing enabled")
    return _tracer


def get_tracer() -> Optional[OpenInferenceTracer]:
    """Return the global Phoenix tracer if initialized."""
    return _tracer
