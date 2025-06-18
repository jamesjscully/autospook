"""
OSINT Research Agent for AutoSpook

A simplified, clean implementation using LangChain's built-in search tools
for open source intelligence gathering and analysis.
"""

from __future__ import annotations

import os
import logging
import asyncio
import uuid
from dataclasses import dataclass, field, replace
from datetime import timedelta
from typing import Dict, Any, List, Optional, Union, Literal
from typing_extensions import TypedDict

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from langsmith import traceable, tracing_context
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_community.tools import WikipediaQueryRun
from dotenv import load_dotenv

# Temporal imports
import temporalio.activity as activity
import temporalio.workflow as workflow
from temporalio.client import Client
from temporalio.worker import Worker

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


# Typed classes for search results
class DuckDuckGoResultItem(TypedDict):
    """Individual DuckDuckGo search result item."""
    title: str
    link: str
    snippet: str


class SuccessfulWebSearchResult(TypedDict):
    """Successful web search result."""
    tool: Literal["web_search"]
    query: str
    result: Union[List[DuckDuckGoResultItem], str]  # Can be structured list or raw string
    status: Literal["success"]


class FailedWebSearchResult(TypedDict):
    """Failed web search result."""
    tool: Literal["web_search"]
    query: str
    error: str
    status: Literal["error"]


class SuccessfulWikipediaResult(TypedDict):
    """Successful Wikipedia search result."""
    tool: Literal["wikipedia"]
    query: str
    result: str
    status: Literal["success"]


class FailedWikipediaResult(TypedDict):
    """Failed Wikipedia search result."""
    tool: Literal["wikipedia"]
    query: str
    error: str
    status: Literal["error"]


class GenericErrorResult(TypedDict):
    """Generic error result."""
    tool: str
    error: str
    status: Literal["error"]


# Union type for all possible search results
SearchResult = Union[
    SuccessfulWebSearchResult,
    FailedWebSearchResult,
    SuccessfulWikipediaResult,
    FailedWikipediaResult,
    GenericErrorResult
]


class ResearchQuestion(TypedDict):
    """Individual research question with metadata."""
    question: str
    priority: Literal["high", "medium", "low"]
    status: Literal["pending", "in_progress", "completed", "failed"]
    search_results: List[SearchResult]
    answer: str
    sources: List[str]
    created_step: int


class IncidentalObservation(TypedDict):
    """Unexpected findings discovered during research."""
    observation: str
    source: str
    relevance: str
    discovered_at_step: int


@dataclass
class ResearchState:
    """Authoritative, replay-safe workflow state (serializable to JSON)."""
    
    # Core target information
    query: str
    target_query: str = ""
    investigation_context: str = ""
    
    # Research progression
    step: int = 0
    max_steps: int = 10
    
    # Analysis and findings
    context: str = ""
    analysis_context: str = ""
    final_report: str = ""
    
    # Sources and notes
    sources: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    
    # Research questions (simplified for Temporal serialization)
    research_questions: List[Dict[str, Any]] = field(default_factory=list)
    current_question_index: int = 0
    pivot_questions: List[str] = field(default_factory=list)
    
    # Observations and metadata
    incidental_observations: List[Dict[str, Any]] = field(default_factory=list)
    reflection_sufficient: bool = False
    
    # Search results (simplified for serialization)
    search_results: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary for LangGraph compatibility."""
        return {
            "query": self.query,
            "target_query": self.target_query or self.query,
            "investigation_context": self.investigation_context,
            "step": self.step,
            "max_steps": self.max_steps,
            "context": self.context,
            "analysis_context": self.analysis_context,
            "final_report": self.final_report,
            "sources": self.sources.copy(),
            "notes": self.notes.copy(),
            "research_questions": [q.copy() for q in self.research_questions],
            "current_question_index": self.current_question_index,
            "pivot_questions": self.pivot_questions.copy(),
            "incidental_observations": [obs.copy() for obs in self.incidental_observations],
            "reflection_sufficient": self.reflection_sufficient,
            "search_results": [sr.copy() for sr in self.search_results],
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "ResearchState":
        """Create from dictionary."""
        return cls(
            query=d.get("query", ""),
            target_query=d.get("target_query", d.get("query", "")),
            investigation_context=d.get("investigation_context", ""),
            step=d.get("step", 0),
            max_steps=d.get("max_steps", 10),
            context=d.get("context", ""),
            analysis_context=d.get("analysis_context", ""),
            final_report=d.get("final_report", ""),
            sources=d.get("sources", []),
            notes=d.get("notes", []),
            research_questions=d.get("research_questions", []),
            current_question_index=d.get("current_question_index", 0),
            pivot_questions=d.get("pivot_questions", []),
            incidental_observations=d.get("incidental_observations", []),
            reflection_sufficient=d.get("reflection_sufficient", False),
            search_results=d.get("search_results", []),
        )

    def update_from_dict(self, diff: Dict) -> "ResearchState":
        """Update state with dictionary diff."""
        updated_data = self.to_dict()
        updated_data.update(diff)
        return self.from_dict(updated_data)


def create_llm() -> ChatOpenAI:
    """Create OpenAI LLM instance."""
    return ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0.1,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )


# ----------------------------------------------------------------
# Temporal activity: one LangGraph super-step --------------------
# ----------------------------------------------------------------

@activity.defn(
    retry_policy=activity.RetryPolicy(
        initial_interval=timedelta(seconds=1),
        backoff_coefficient=2.0,
        maximum_interval=timedelta(minutes=1),
        maximum_attempts=3,
        non_retryable_error_types=["ValueError", "TypeError"],
    ),
    start_to_close_timeout=timedelta(minutes=10),
    heartbeat_timeout=timedelta(seconds=30),
)
async def run_langgraph(state_dict: Dict) -> Dict:
    """Execute a single LangGraph super-step and return a diff with Temporal reliability."""

    thread_id = uuid.uuid4().hex
    logging.info("[activity] LangGraph thread=%s, step=%s", thread_id, state_dict.get("step", 0))

    try:
        # Send heartbeat to Temporal
        activity.heartbeat(f"Starting LangGraph execution for step {state_dict.get('step', 0)}")

        # Get the research workflow graph
        graph = get_research_workflow()

        # Make a shallow copy to avoid mutating workflow memory directly
        working_state = {
            k: (v.copy() if isinstance(v, list) else v) for k, v in state_dict.items()
        }

        activity.heartbeat("LangGraph state prepared, executing workflow")

        # Tracing context guarantees nesting under this activity
        with tracing_context(name="LangGraph-step", metadata={"thread_id": thread_id}):
            result = graph.invoke(working_state, config={"thread_id": thread_id})

        activity.heartbeat("LangGraph execution completed, calculating diff")

        # Calculate diff - what changed from the original state
        diff = {}
        for k in working_state:
            if k in result and result[k] != state_dict[k]:
                diff[k] = result[k]

        # Ensure step counter is incremented
        diff["step"] = state_dict.get("step", 0) + 1

        logging.info("[activity] Completed step %d, returning diff with keys: %s", diff["step"], list(diff.keys()))
        return diff

    except Exception as e:
        logging.error("[activity] LangGraph execution failed: %s", str(e))
        # Send heartbeat with error info before re-raising
        activity.heartbeat(f"LangGraph execution failed: {str(e)}")
        raise


def extract_sources_from_search_results(search_results: List[SearchResult]) -> List[str]:
    """Extract actual source URLs and titles from search results."""
    sources = []
    
    for result in search_results:
        if result.get("tool") == "web_search" and "result" in result:
            # DuckDuckGo results contain structured data with links
            web_data = result["result"]
            if isinstance(web_data, list):
                for item in web_data:
                    if isinstance(item, dict) and "link" in item:
                        title = item.get("title", "Unknown")
                        link = item.get("link", "")
                        sources.append(f"{title} - {link}")
            elif isinstance(web_data, str) and "http" in web_data:
                # Fallback: extract URLs from text
                import re
                urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', web_data)
                for url in urls[:3]:  # Limit to first 3 URLs
                    sources.append(f"Web Search Result - {url}")
        
        elif result.get("tool") == "wikipedia" and "result" in result:
            wiki_data = result["result"]
            if "Page:" in wiki_data:
                # Extract Wikipedia page titles
                import re
                pages = re.findall(r'Page: ([^\n]+)', wiki_data)
                for page in pages:
                    sources.append(f"Wikipedia: {page}")
    return sources

@traceable
async def initial_stepback_analysis_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Perform initial analysis of the target and establish investigation context."""
    logger.info(f"Starting initial stepback analysis for target: {state['target_query']}")
    
    llm = create_llm()
    
    # Create stepback analysis prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert OSINT analyst performing initial target assessment.

Your task is to analyze the investigation target and establish proper context.

INSTRUCTIONS:
- Determine what type of entity this is (person, organization, domain, etc.)
- Identify potential identity disambiguation needs
- Establish investigation context and objectives
- Suggest initial research direction

Target: {target_query}
Investigation Context: {investigation_context}

Provide a structured analysis covering:
1. Target Type Assessment
2. Identity Disambiguation Strategy  
3. Investigation Scope and Objectives
4. Initial Research Direction"""),
        ("human", "Perform initial stepback analysis for target: {target_query}")
    ])
    
    try:
        chain = prompt | llm
        response = await asyncio.to_thread(
            chain.invoke,
            {
                "target_query": state["target_query"],
                "investigation_context": state.get("investigation_context", "General OSINT research")
            }
        )
        
        analysis = response.content
        
        updated_state: ResearchState = {
            **state,
            "analysis_context": analysis,
            "step": state.get("step", 0) + 1,
            "notes": state.get("notes", []) + ["Completed initial stepback analysis"],
        }
        return updated_state
        
    except Exception as e:
        logger.error(f"Error in initial stepback analysis: {e}")
        error_state: ResearchState = {
            **state,
            "analysis_context": f"Initial analysis failed: {str(e)}",
            "notes": state.get("notes", []) + [f"Stepback analysis error: {str(e)}"],
        }
        return error_state


@traceable
async def generate_research_questions_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generate initial research questions based on target analysis."""
    logger.info(f"Generating research questions for target: {state['target_query']}")
    
    llm = create_llm()
    
    # Create question generation prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert OSINT analyst generating targeted research questions.

Based on the initial analysis, generate 3-5 high-priority research questions that will guide the investigation.

INSTRUCTIONS:
- Generate specific, actionable research questions
- Prioritize questions (high, medium, low)
- Focus on publicly available information sources
- Consider identity disambiguation needs
- Think about what would be most valuable for OSINT purposes

Target: {target_query}
Investigation Context: {investigation_context}
Analysis Context: {analysis_context}

Generate research questions in this format:
1. [HIGH] Question about identity verification
2. [MEDIUM] Question about background/history
3. [HIGH] Question about current activities
etc.

Provide 3-5 research questions with clear priorities."""),
        ("human", "Generate research questions for investigation target: {target_query}")
    ])
    
    try:
        chain = prompt | llm
        response = await asyncio.to_thread(
            chain.invoke,
            {
                "target_query": state["target_query"],
                "investigation_context": state.get("investigation_context", ""),
                "analysis_context": state.get("analysis_context", "")
            }
        )
        
        questions_text = response.content
        
        # Parse questions (simple implementation - could be more sophisticated)
        questions = []
        for i, line in enumerate(questions_text.split('\n')):
            if line.strip() and any(priority in line.upper() for priority in ['[HIGH]', '[MEDIUM]', '[LOW]']):
                priority = "high" if "[HIGH]" in line.upper() else "medium" if "[MEDIUM]" in line.upper() else "low"
                question_text = line.split(']', 1)[-1].strip()
                
                question: ResearchQuestion = {
                    "question": question_text,
                    "priority": priority,
                    "status": "pending",
                    "search_results": [],
                    "answer": "",
                    "sources": [],
                    "created_step": state.get("step", 0) + 1
                }
                questions.append(question)
        
        updated_state: ResearchState = {
            **state,
            "research_questions": questions,
            "current_question_index": 0,
            "step": state.get("step", 0) + 1,
            "notes": state.get("notes", []) + [f"Generated {len(questions)} research questions"],
        }
        return updated_state
        
    except Exception as e:
        logger.error(f"Error generating research questions: {e}")
        error_state: ResearchState = {
            **state,
            "research_questions": [],
            "notes": state.get("notes", []) + [f"Question generation error: {str(e)}"],
        }
        return error_state


@traceable
async def answer_research_question_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Answer the current research question through search and analysis."""
    current_index = state.get("current_question_index", 0)
    questions = state.get("research_questions", [])
    
    if current_index >= len(questions):
        logger.warning("No more questions to process")
        return state
        
    current_question = questions[current_index]
    logger.info(f"Answering question {current_index + 1}/{len(questions)}: {current_question['question']}")
    
    # Mark question as in progress
    questions[current_index] = {**current_question, "status": "in_progress"}
    
    # Perform search for this specific question
    search_results = await perform_question_search(current_question["question"])
    
    # Analyze search results to answer the question
    llm = create_llm()
    
    # Format search results for analysis
    search_context = ""
    if search_results:
        search_context = "\n\nSearch Results:\n"
        for i, result in enumerate(search_results, 1):
            if result.get("status") == "success":
                tool_name = result.get("tool", "Unknown")
                content = result.get("result", "")
                search_context += f"{i}. {tool_name.upper()} RESULTS:\n{content}\n\n"
            else:
                tool_name = result.get("tool", "Unknown")
                error = result.get("error", "Unknown error")
                search_context += f"{i}. {tool_name.upper()}: Error - {error}\n\n"
    
    # Create question-answering prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert OSINT analyst answering a specific research question.

INSTRUCTIONS:
- Answer the specific research question based on the search results
- Provide factual, objective analysis
- Cite specific sources when making claims
- Identify any incidental observations that might be relevant to the investigation
- If insufficient information is available, state this clearly

Research Question: {question}
Target: {target_query}
{search_context}"""),
        ("human", "Answer this research question: {question}")
    ])
    
    try:
        chain = prompt | llm
        response = await asyncio.to_thread(
            chain.invoke,
            {
                "question": current_question["question"],
                "target_query": state["target_query"],
                "search_context": search_context
            }
        )
        
        answer = response.content
        sources = extract_sources_from_search_results(search_results)
        
        # Update the question with results
        questions[current_index] = {
            **current_question,
            "status": "completed",
            "search_results": search_results,
            "answer": answer,
            "sources": sources
        }
        
        # Move to next question
        next_index = current_index + 1
        
        updated_state: ResearchState = {
            **state,
            "research_questions": questions,
            "current_question_index": next_index,
            "step": state.get("step", 0) + 1,
            "notes": state.get("notes", []) + [f"Completed question {current_index + 1}: {current_question['question'][:50]}..."],
            "sources": state.get("sources", []) + sources,
        }
        return updated_state
        
    except Exception as e:
        logger.error(f"Error answering research question: {e}")
        # Mark question as failed
        questions[current_index] = {**current_question, "status": "failed"}
        
        error_state: ResearchState = {
            **state,
            "research_questions": questions,
            "current_question_index": current_index + 1,
            "notes": state.get("notes", []) + [f"Failed to answer question {current_index + 1}: {str(e)}"],
        }
        return error_state


async def perform_question_search(question: str) -> List[SearchResult]:
    """Perform search operations for a specific research question."""
    search_results = []
    
    try:
        # Initialize search tools
        web_search = DuckDuckGoSearchResults(num_results=5)
        wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
        
        # Perform web search
        try:
            logger.info(f"Performing web search for question: {question[:50]}...")
            web_result = await asyncio.to_thread(web_search.run, question)
            successful_result: SuccessfulWebSearchResult = {
                "tool": "web_search",
                "query": question,
                "result": web_result,
                "status": "success"
            }
            search_results.append(successful_result)
        except Exception as e:
            logger.warning(f"Web search failed: {e}")
            failed_result: FailedWebSearchResult = {
                "tool": "web_search",
                "query": question,
                "error": str(e),
                "status": "error"
            }
            search_results.append(failed_result)
        
        # Perform Wikipedia search for additional context
        try:
            logger.info(f"Performing Wikipedia search for question: {question[:50]}...")
            wiki_result = await asyncio.to_thread(wikipedia.run, question)
            successful_wiki_result: SuccessfulWikipediaResult = {
                "tool": "wikipedia",
                "query": question,
                "result": wiki_result,
                "status": "success"
            }
            search_results.append(successful_wiki_result)
        except Exception as e:
            logger.warning(f"Wikipedia search failed: {e}")
            failed_wiki_result: FailedWikipediaResult = {
                "tool": "wikipedia",
                "query": question,
                "error": str(e),
                "status": "error"
            }
            search_results.append(failed_wiki_result)
            
    except Exception as e:
        logger.error(f"Critical error in question search: {e}")
        error_result: GenericErrorResult = {
            "tool": "error",
            "error": str(e),
            "status": "error"
        }
        search_results.append(error_result)
    
    return search_results


@traceable
async def reflection_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Reflect on research progress and determine if sufficient information has been gathered."""
    logger.info("Performing reflection on research progress")
    
    llm = create_llm()
    
    # Compile current research findings
    completed_questions = [q for q in state.get("research_questions", []) if q["status"] == "completed"]
    all_answers = "\n\n".join([f"Q: {q['question']}\nA: {q['answer']}" for q in completed_questions])
    
    # Create reflection prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert OSINT analyst performing reflection on research progress.

Evaluate the current research findings and determine:
1. Is sufficient information available to generate a comprehensive report?
2. Are there significant gaps that require additional investigation?
3. Should the investigation continue with pivot questions?

Target: {target_query}
Investigation Context: {investigation_context}

Current Findings:
{all_answers}

Respond with:
- SUFFICIENT: If enough information is available for a comprehensive report
- INSUFFICIENT: If significant gaps remain and more research is needed

Provide reasoning for your decision."""),
        ("human", "Evaluate research completeness for target: {target_query}")
    ])
    
    try:
        chain = prompt | llm
        response = await asyncio.to_thread(
            chain.invoke,
            {
                "target_query": state["target_query"],
                "investigation_context": state.get("investigation_context", ""),
                "all_answers": all_answers
            }
        )
        
        reflection_content = response.content
        is_sufficient = "SUFFICIENT" in reflection_content.upper()
        
        updated_state: ResearchState = {
            **state,
            "reflection_sufficient": is_sufficient,
            "step": state.get("step", 0) + 1,
            "notes": state.get("notes", []) + [f"Reflection complete: {'Sufficient' if is_sufficient else 'Insufficient'} information"],
            "analysis_context": state.get("analysis_context", "") + f"\n\nReflection:\n{reflection_content}"
        }
        return updated_state
        
    except Exception as e:
        logger.error(f"Error in reflection: {e}")
        error_state: ResearchState = {
            **state,
            "reflection_sufficient": True,  # Default to sufficient on error
            "notes": state.get("notes", []) + [f"Reflection error: {str(e)}"],
        }
        return error_state


@traceable
async def generate_final_report_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generate comprehensive final intelligence report."""
    logger.info("Generating final intelligence report")
    
    llm = create_llm()
    
    # Compile all research findings
    completed_questions = [q for q in state.get("research_questions", []) if q["status"] == "completed"]
    all_findings = "\n\n".join([f"Research Question: {q['question']}\nFindings: {q['answer']}\nSources: {', '.join(q['sources'])}" for q in completed_questions])
    
    # Create final report prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert OSINT analyst generating a comprehensive intelligence report.

Synthesize all research findings into a professional intelligence report.

REPORT STRUCTURE:
1. Executive Summary
2. Target Assessment
3. Key Findings
4. Detailed Analysis
5. Sources and Citations
6. Recommendations for Further Investigation (if applicable)

Target: {target_query}
Investigation Context: {investigation_context}
Initial Analysis: {analysis_context}

Research Findings:
{all_findings}

Generate a comprehensive, professional OSINT intelligence report."""),
        ("human", "Generate final intelligence report for: {target_query}")
    ])
    
    try:
        chain = prompt | llm
        response = await asyncio.to_thread(
            chain.invoke,
            {
                "target_query": state["target_query"],
                "investigation_context": state.get("investigation_context", ""),
                "analysis_context": state.get("analysis_context", ""),
                "all_findings": all_findings
            }
        )
        
        final_report = response.content
        
        # Collect all sources
        all_sources = []
        for question in completed_questions:
            all_sources.extend(question.get("sources", []))
        
        updated_state: ResearchState = {
            **state,
            "final_report": final_report,
            "context": final_report,  # For compatibility
            "step": state.get("step", 0) + 1,
            "sources": list(set(all_sources)),  # Remove duplicates
            "notes": state.get("notes", []) + ["Generated final intelligence report"],
        }
        return updated_state
        
    except Exception as e:
        logger.error(f"Error generating final report: {e}")
        error_state: ResearchState = {
            **state,
            "final_report": f"Report generation failed: {str(e)}",
            "context": f"Report generation failed: {str(e)}",
            "notes": state.get("notes", []) + [f"Final report error: {str(e)}"],
        }
        return error_state


def should_continue_questions(state: Dict[str, Any]) -> str:
    """Determine if there are more questions to answer."""
    current_index = state.get("current_question_index", 0)
    questions = state.get("research_questions", [])
    
    if current_index < len(questions):
        return "answer_question"
    else:
        return "reflection"


def should_continue_research(state: Dict[str, Any]) -> str:
    """Determine if research should continue or generate final report."""
    is_sufficient = state.get("reflection_sufficient", True)
    current_step = state.get("step", 0)
    max_steps = state.get("max_steps", 10)
    
    if is_sufficient or current_step >= max_steps:
        return "final_report"
    else:
        # Could add pivot question generation here
        return "final_report"  # For now, go to final report


def route_after_final_report(state: Dict[str, Any]) -> str:
    """Route after final report generation."""
    return END


# ----------------------------------------------------------------
# Temporal workflow ----------------------------------------------
# ----------------------------------------------------------------

@workflow.defn
class DeepResearchWorkflow:
    """Temporal coordinator – **owns** the authoritative state."""

    state: ResearchState

    @workflow.run
    async def run(self, initial_query: str, max_steps: int = 3) -> ResearchState:
        self.state = ResearchState(query=initial_query, target_query=initial_query, max_steps=max_steps)

        workflow.logger.info("[workflow] Starting OSINT research for: %s", initial_query)

        while self.state.step < self.state.max_steps:
            try:
                workflow.logger.info(
                    "[workflow] Executing step %d/%d for query: %s",
                    self.state.step + 1,
                    self.state.max_steps,
                    self.state.query[:50] + "..." if len(self.state.query) > 50 else self.state.query
                )

                diff: Dict = await workflow.execute_activity(
                    run_langgraph,
                    self.state.to_dict(),
                    start_to_close_timeout=timedelta(minutes=10),
                    retry_policy=workflow.RetryPolicy(
                        initial_interval=timedelta(seconds=2),
                        backoff_coefficient=2.0,
                        maximum_interval=timedelta(minutes=2),
                        maximum_attempts=5,
                        non_retryable_error_types=["ValueError", "TypeError"],
                    ),
                )

                self.state = self.state.update_from_dict(diff)
                workflow.logger.info(
                    "[workflow] Step %d completed successfully. Updated fields: %s",
                    self.state.step,
                    list(diff.keys()),
                )

                # Check if final report is generated (workflow complete)
                if self.state.final_report:
                    workflow.logger.info("[workflow] Final report generated, ending workflow successfully")
                    break

                # Check if we've completed all research questions and reflection
                questions = self.state.research_questions or []
                completed_questions = [q for q in questions if q.get("status") == "completed"]
                
                if (len(questions) > 0 and 
                    len(completed_questions) == len(questions) and 
                    self.state.reflection_sufficient):
                    workflow.logger.info("[workflow] All research questions completed and reflection sufficient, ending workflow")
                    break

            except Exception as e:
                workflow.logger.error(
                    "[workflow] Step %d failed with error: %s", self.state.step, str(e)
                )
                
                # Add error to notes for debugging
                error_note = f"Step {self.state.step} failed: {str(e)}"
                updated_notes = self.state.notes + [error_note]
                self.state = replace(self.state, notes=updated_notes)
                
                # For critical errors, break the loop
                if "non_retryable" in str(e).lower() or self.state.step >= self.state.max_steps - 1:
                    workflow.logger.error("[workflow] Critical error or max steps reached, ending workflow")
                    break
                
                # Otherwise increment step and continue
                self.state = replace(self.state, step=self.state.step + 1)

        workflow.logger.info(
            "[workflow] OSINT research completed after %d steps", self.state.step
        )
        return self.state


def create_research_workflow() -> StateGraph:
    """Create the sophisticated OSINT research workflow."""
    from typing_extensions import TypedDict
    
    class WorkflowState(TypedDict):
        """State for LangGraph workflow (dictionary-based)."""
        query: str
        target_query: str
        investigation_context: str
        step: int
        max_steps: int
        context: str
        analysis_context: str
        final_report: str
        sources: List[str]
        notes: List[str]
        research_questions: List[Dict[str, Any]]
        current_question_index: int
        pivot_questions: List[str]
        incidental_observations: List[Dict[str, Any]]
        reflection_sufficient: bool
        search_results: List[Dict[str, Any]]
    
    workflow = StateGraph(WorkflowState)
    
    # Add workflow nodes
    workflow.add_node("initial_analysis", initial_stepback_analysis_node)
    workflow.add_node("generate_questions", generate_research_questions_node)
    workflow.add_node("answer_question", answer_research_question_node)
    workflow.add_node("reflection", reflection_node)
    workflow.add_node("final_report", generate_final_report_node)
    
    # Set entry point
    workflow.set_entry_point("initial_analysis")
    
    # Add workflow edges
    workflow.add_edge("initial_analysis", "generate_questions")
    workflow.add_edge("generate_questions", "answer_question")
    
    # Conditional edges for question answering loop
    workflow.add_conditional_edges(
        "answer_question",
        should_continue_questions,
        {
            "answer_question": "answer_question",  # Loop back for next question
            "reflection": "reflection"  # All questions answered, move to reflection
        }
    )
    
    # Conditional edges for research continuation
    workflow.add_conditional_edges(
        "reflection",
        should_continue_research,
        {
            "final_report": "final_report"  # Generate final report
            # Could add "generate_pivot_questions": "generate_pivot_questions" for future
        }
    )
    
    # Final edge to END
    workflow.add_conditional_edges("final_report", route_after_final_report)
    
    return workflow.compile()


def get_research_workflow():
    """Get the compiled research workflow (created fresh each time for Temporal activities)."""
    return create_research_workflow()


async def research(query: str, max_steps: int = 3) -> ResearchState:
    """
    Execute OSINT research using Temporal workflows.
    
    This is now a wrapper around run_temporal_research for backwards compatibility.
    All research execution goes through Temporal for reliability and fault tolerance.
    
    Args:
        query: The research query
        max_steps: Maximum number of research steps
        
    Returns:
        ResearchState containing research results
    """
    logger.info(f"Starting Temporal OSINT research for: {query}")
    return await run_temporal_research(query, max_steps)


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


async def run_temporal_research(query: str, max_steps: int = 3) -> ResearchState:
    """
    Execute OSINT research using Temporal workflows.
    
    Args:
        query: The research query
        max_steps: Maximum number of research steps
        
    Returns:
        ResearchState containing research results
    """
    logging.info(f"Starting Temporal OSINT research for: {query}")
    
    client = await Client.connect("localhost:7233")
    
    try:
        result: ResearchState = await client.execute_workflow(
            DeepResearchWorkflow.run,
            query,
            max_steps,
            id="research-" + uuid.uuid4().hex[:8],
            task_queue="autospook-research-q",
            execution_timeout=timedelta(minutes=30),
        )
        logging.info(f"Temporal OSINT research completed for: {query}")
        return result
    except Exception as e:
        logging.error(f"Temporal research failed: {str(e)}")
        raise


if __name__ == "__main__":
    # Choose demo or worker mode
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "worker":
        asyncio.run(start_worker())
    elif len(sys.argv) > 1 and sys.argv[1] == "demo":
        asyncio.run(run_demo())
    else:
        print("Usage: python agent.py [worker|demo]")
        print("  worker: Start Temporal worker")
        print("  demo: Run demo research workflow")