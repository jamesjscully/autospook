from __future__ import annotations

# Standard library imports
import asyncio
import logging
import os
import uuid
from dataclasses import dataclass, field, replace
from datetime import timedelta
from typing import Dict, List

# Third-party imports
from langsmith import traceable, tracing_context

# Temporal imports
import temporalio.activity as activity
import temporalio.workflow as workflow
from temporalio.client import Client
from temporalio.worker import Worker

# Local imports
from .agent import cached_compiled_graph

"""AutoSpook deep-research agent that combines **Temporal** for orchestration, **LangGraph** for
reasoning, **LangSmith** for tracing.

Key design points
-----------------
* **Single source of truth** – `ResearchState` lives only in the Temporal workflow.
* **Activity boundary** – LangGraph executes inside a Temporal *activity* so it can
  perform arbitrary I/O. Each invocation constitutes one *super-step*.
* **Tracing** – All LangGraph runs (and their nested functions) are captured by
  LangSmith when `LANGSMITH_TRACING=true`.
"""

# ----------------------------------------------------------------
# Domain model
# ----------------------------------------------------------------


@dataclass
class ResearchState:
    """Authoritative, replay-safe workflow state (serializable to JSON)."""

    query: str
    context: str = ""
    sources: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    step: int = 0
    max_steps: int = 3  # termination criterion for OSINT research

    def to_dict(self) -> Dict:
        return {
            "query": self.query,
            "context": self.context,
            "sources": self.sources,
            "notes": self.notes,
            "step": self.step,
            "max_steps": self.max_steps,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "ResearchState":
        return cls(**d)


# ----------------------------------------------------------------
# OSINT Research helpers ------------------------------------------
# ----------------------------------------------------------------


@traceable(run_type="tool", name="OSINT Search")
def osint_search(query: str) -> List[str]:
    """Simulate OSINT data source search (stub implementation)."""
    logging.info("[osint_search] researching: %s", query)
    # In real implementation, this would search:
    # - Social media APIs
    # - Public records databases
    # - News sources
    # - Domain/IP information
    return [
        f"social_media_profile_{uuid.uuid4().hex[:8]}",
        f"public_record_{uuid.uuid4().hex[:8]}",
        f"news_article_{uuid.uuid4().hex[:8]}",
    ]


@traceable(run_type="tool", name="Analyze Sources")
def analyze_sources(sources: List[str], context: str) -> str:
    """Analyze and synthesize OSINT sources (stub implementation)."""
    logging.info("[analyze_sources] analyzing %d sources", len(sources))
    # In real implementation, this would:
    # - Extract relevant information
    # - Cross-reference data points
    # - Generate intelligence report
    return f"Analysis of {len(sources)} OSINT sources. Previous context: {context[:100]}..."


# ----------------------------------------------------------------
# Temporal activity: one LangGraph super-step --------------------
# ----------------------------------------------------------------


@activity.defn
async def run_langgraph(state_dict: Dict) -> Dict:
    """Execute a single LangGraph super-step and return a diff."""

    thread_id = uuid.uuid4().hex
    logging.info("[activity] LangGraph thread=%s", thread_id)

    # Get the cached graph from agent.py
    graph = cached_compiled_graph()

    # Make a shallow copy to avoid mutating workflow memory directly
    working_state = {
        k: (v.copy() if isinstance(v, list) else v) for k, v in state_dict.items()
    }

    # Tracing context guarantees nesting under this activity
    with tracing_context(name="LangGraph-step", metadata={"thread_id": thread_id}):
        result = graph.invoke(working_state, config={"thread_id": thread_id})

    # Calculate diff - what changed from the original state
    diff = {}
    for k in working_state:
        if k in result and result[k] != state_dict[k]:
            diff[k] = result[k]

    # Ensure step counter is incremented
    diff["step"] = state_dict.get("step", 0) + 1

    return diff


# ----------------------------------------------------------------
# Temporal workflow ----------------------------------------------
# ----------------------------------------------------------------


@workflow.defn
class DeepResearchWorkflow:
    """Temporal coordinator – **owns** the authoritative state."""

    state: ResearchState

    @workflow.run
    async def run(self, initial_query: str, max_steps: int = 3) -> ResearchState:
        self.state = ResearchState(query=initial_query, max_steps=max_steps)

        workflow.logger.info("[workflow] Starting research for: %s", initial_query)

        while self.state.step < self.state.max_steps:
            try:
                diff: Dict = await workflow.execute_activity(
                    run_langgraph,
                    self.state.to_dict(),
                    start_to_close_timeout=timedelta(minutes=5),
                )

                self.state = replace(self.state, **diff)
                workflow.logger.info(
                    "[workflow] step %d completed, diff=%s",
                    self.state.step,
                    diff.keys(),
                )

            except Exception as e:
                workflow.logger.error(
                    "[workflow] step %d failed: %s", self.state.step, str(e)
                )
                # Continue with next step or break based on error severity
                self.state = replace(self.state, step=self.state.step + 1)

        workflow.logger.info(
            "[workflow] Research completed after %d steps", self.state.step
        )
        return self.state


# ----------------------------------------------------------------
# Worker bootstrap -----------------------------------------------
# ----------------------------------------------------------------


async def start_worker():
    """Start the Temporal worker for AutoSpook research workflows."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )

    # Enable tracing programmatically if env vars absent
    if os.getenv("LANGSMITH_TRACING", "false").lower() != "true":
        os.environ["LANGSMITH_TRACING"] = "true"

    client = await Client.connect("localhost:7233")

    worker = Worker(
        client,
        task_queue="autospook-research-q",
        workflows=[DeepResearchWorkflow],
        activities=[run_langgraph],
    )

    logging.info("[worker] Starting AutoSpook research worker...")
    async with worker:
        # Keep worker running
        await asyncio.Event().wait()


async def run_demo():
    """Run a demo research workflow."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )

    client = await Client.connect("localhost:7233")

    try:
        result: ResearchState = await client.execute_workflow(
            DeepResearchWorkflow.run,
            "Research public information about John Doe",
            max_steps=2,
            id="demo-research-" + uuid.uuid4().hex[:8],
            task_queue="autospook-research-q",
            execution_timeout=timedelta(minutes=10),
        )
        logging.info("Demo workflow completed: %s", result)
        return result
    except Exception as e:
        logging.error("Demo workflow failed: %s", str(e))
        raise


if __name__ == "__main__":
    # Choose demo or worker mode
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "worker":
        asyncio.run(start_worker())
    else:
        asyncio.run(run_demo())
