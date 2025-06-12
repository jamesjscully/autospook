"""Run agent evaluations with Arize Phoenix."""

from __future__ import annotations

import logging
from typing import Iterable, Any, Dict, Callable

logger = logging.getLogger(__name__)

try:
    from phoenix.evals import run_evaluation  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    run_evaluation = None  # type: ignore


def evaluate_dataset(dataset: Iterable[Dict[str, Any]], agent: Callable[[Dict[str, Any]], Dict[str, Any]]) -> Dict[str, Any]:
    """Run an evaluation dataset through the agent using Phoenix.

    Parameters
    ----------
    dataset: Iterable of data rows to evaluate.
    agent: Callable that processes a single data row and returns a result.
    """
    if run_evaluation is None:
        raise RuntimeError(
            "arize-phoenix is not installed. Install it to run evaluations."
        )

    logger.info("Running evaluation with Arize Phoenix on %d items", len(list(dataset)))
    return run_evaluation(dataset=dataset, agent=agent)
