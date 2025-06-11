import os
import uuid
from typing import List, Dict, Any
from datetime import datetime

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.types import Send
from langgraph.graph import StateGraph, START, END
from langgraph.graph import add_messages
from langchain_core.runnables import RunnableConfig

# Import LLM providers
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

# Import our custom modules
from agent.osint_state import (
    OSINTState,
    QueryAnalysisOutput,
    OrchestrationOutput,
    PivotAnalysisOutput,
    SynthesisOutput,
    JudgeOutput,
    OSINTTask,
    DataPoint,
    InvestigationPhase
)
from agent.osint_configuration import OSINTConfiguration
from agent.osint_prompts import (
    get_current_date,
    QUERY_ANALYSIS_PROMPT,
    ORCHESTRATION_PROMPT,
    RETRIEVAL_PROMPT,
    PIVOT_ANALYSIS_PROMPT,
    SYNTHESIS_PROMPT,
    JUDGE_PROMPT
)

load_dotenv()

# Verify required API keys
required_keys = ["GEMINI_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY"]
for key in required_keys:
    if os.getenv(key) is None:
        raise ValueError(f"{key} is not set")


# Node 1: Query Analysis Agent (Claude Sonnet 4)
def analyze_query(state: OSINTState, config: RunnableConfig) -> OSINTState:
    """Analyze the user query and extract entities, scope, and investigation parameters."""
    configurable = OSINTConfiguration.from_runnable_config(config)
    
    # Initialize Claude Sonnet for query analysis
    llm = ChatAnthropic(
        model=configurable.query_analysis_model,
        temperature=0.3,
        max_tokens=4096,
        api_key=os.getenv("ANTHROPIC_API_KEY"),
    )
    
    # Prepare the prompt
    formatted_prompt = QUERY_ANALYSIS_PROMPT.format(
        query=state["query"],
        context=state.get("memory_context", {}),
        current_date=get_current_date()
    )
    
    # Get structured output
    result = llm.invoke(formatted_prompt)
    # For now, we'll parse the JSON from the response
    # In production, use with_structured_output
    
    # Update state with analysis results
    return {
        "investigation_id": str(uuid.uuid4()),
        "investigation_phase": InvestigationPhase.INITIAL,
        "entities": [],  # Would be populated from parsed result
        "investigation_scope": {},  # Would be populated from parsed result
        "messages": [HumanMessage(content=state["query"]), result]
    }


# Node 2: Planning & Orchestration Agent (Claude Sonnet 4)
def plan_investigation(state: OSINTState, config: RunnableConfig) -> OSINTState:
    """Create a strategic investigation plan with prioritized tasks."""
    configurable = OSINTConfiguration.from_runnable_config(config)
    
    # Initialize Claude Sonnet for orchestration
    llm = ChatAnthropic(
        model=configurable.orchestration_model,
        temperature=0.5,
        max_tokens=4096,
        api_key=os.getenv("ANTHROPIC_API_KEY"),
    )
    
    # Prepare the prompt with current state
    formatted_prompt = ORCHESTRATION_PROMPT.format(
        query_analysis=state.get("entities", []),
        completed_tasks=state.get("completed_tasks", []),
        current_date=get_current_date()
    )
    
    # Get investigation plan
    result = llm.invoke(formatted_prompt)
    
    # Create tasks (simplified for now)
    tasks = []
    for i in range(configurable.minimum_retrievals):
        task = OSINTTask(
            task_id=f"task_{uuid.uuid4().hex[:8]}",
            task_type="SEARCH",
            target_entity=state["query"],
            sources=[{"source_type": "web_search"}],
            dependencies=[],
            parallel_group=f"group_{i // configurable.parallel_retrieval_limit}",
            status="PENDING",
            results=None
        )
        tasks.append(task)
    
    return {
        "search_plan": tasks,
        "pending_tasks": tasks,
        "messages": state["messages"] + [result]
    }


# Node 3: Multi-Source Retrieval Agent (Claude Sonnet 4)
def retrieve_data(state: Dict[str, Any], config: RunnableConfig) -> OSINTState:
    """Execute retrieval operations across multiple sources."""
    configurable = OSINTConfiguration.from_runnable_config(config)
    task = state["task"]
    
    # Initialize Claude Sonnet for retrieval
    llm = ChatAnthropic(
        model=configurable.retrieval_model,
        temperature=0.2,
        max_tokens=4096,
        api_key=os.getenv("ANTHROPIC_API_KEY"),
    )
    
    # Execute retrieval
    formatted_prompt = RETRIEVAL_PROMPT.format(
        task_details=task,
        target_entity=task["target_entity"],
        current_date=get_current_date()
    )
    
    result = llm.invoke(formatted_prompt)
    
    # Create data point (simplified)
    data_point = DataPoint(
        source_url="https://example.com",
        source_type="web_search",
        credibility_score=0.8,
        extraction_timestamp=datetime.now(),
        title="Sample Result",
        snippet="Sample snippet",
        full_content=result.content,
        metadata={},
        extracted_entities=[],
        key_facts=[],
        relevance_explanation="Relevant to investigation"
    )
    
    # Mark task as completed
    task["status"] = "COMPLETED"
    task["results"] = {"data_point": data_point}
    
    return {
        "completed_tasks": [task],
        "raw_data": [data_point],
        "retrievals_completed": state.get("retrievals_completed", 0) + 1
    }


# Conditional edge to spawn parallel retrievals
def spawn_retrievals(state: OSINTState):
    """Spawn parallel retrieval tasks."""
    sends = []
    for task in state.get("pending_tasks", [])[:5]:  # Limit parallel tasks
        if task["status"] == "PENDING":
            sends.append(Send("retrieve_data", {"task": task, **state}))
    return sends if sends else "pivot_analysis"


# Node 4: Pivot Analysis Agent (GPT-4o)
def analyze_pivot(state: OSINTState, config: RunnableConfig) -> OSINTState:
    """Analyze collected data for patterns and pivot opportunities."""
    configurable = OSINTConfiguration.from_runnable_config(config)
    
    # Initialize GPT-4o for analysis
    llm = ChatOpenAI(
        model=configurable.pivot_analysis_model,
        temperature=0.4,
        max_tokens=4096,
        api_key=os.getenv("OPENAI_API_KEY"),
    )
    
    # Analyze collected data
    formatted_prompt = PIVOT_ANALYSIS_PROMPT.format(
        collected_data=state.get("raw_data", []),
        investigation_objectives=state.get("investigation_scope", {}),
        current_date=get_current_date()
    )
    
    result = llm.invoke(formatted_prompt)
    
    # Determine if more investigation is needed
    continue_investigation = (
        state.get("retrievals_completed", 0) < configurable.minimum_retrievals or
        state.get("research_loop_count", 0) < configurable.max_research_loops
    )
    
    return {
        "analysis_results": {"pivot_analysis": result.content},
        "pivot_suggestions": ["New search angle 1", "New search angle 2"],
        "research_loop_count": state.get("research_loop_count", 0) + 1,
        "messages": state["messages"] + [result]
    }


# Conditional edge for investigation flow
def evaluate_investigation(state: OSINTState, config: RunnableConfig):
    """Determine whether to continue investigation or synthesize report."""
    configurable = OSINTConfiguration.from_runnable_config(config)
    
    if (state.get("retrievals_completed", 0) >= configurable.minimum_retrievals and
        state.get("research_loop_count", 0) >= 2):
        return "synthesize_report"
    else:
        # Create new tasks based on pivot suggestions
        return "plan_investigation"


# Node 5: Synthesis & Reporting Agent (Gemini 1.5 Pro)
def synthesize_report(state: OSINTState, config: RunnableConfig) -> OSINTState:
    """Synthesize all collected data into a comprehensive report."""
    configurable = OSINTConfiguration.from_runnable_config(config)
    
    # Initialize Gemini 1.5 Pro for large context synthesis
    llm = ChatGoogleGenerativeAI(
        model=configurable.synthesis_model,
        temperature=0.3,
        max_retries=2,
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    
    # Prepare comprehensive data for synthesis
    formatted_prompt = SYNTHESIS_PROMPT.format(
        raw_intelligence=state.get("raw_data", []),
        analysis_results=state.get("analysis_results", {}),
        current_date=get_current_date()
    )
    
    result = llm.invoke(formatted_prompt)
    
    return {
        "final_report": result.content,
        "investigation_phase": InvestigationPhase.SYNTHESIS,
        "messages": state["messages"] + [result]
    }


# Node 6: LLM Judge Agent (Claude Opus 4)
def judge_quality(state: OSINTState, config: RunnableConfig) -> OSINTState:
    """Final quality assurance and report validation."""
    configurable = OSINTConfiguration.from_runnable_config(config)
    
    # Initialize Claude Opus for judgment
    llm = ChatAnthropic(
        model=configurable.judge_model,
        temperature=0.2,
        max_tokens=4096,
        api_key=os.getenv("ANTHROPIC_API_KEY"),
    )
    
    # Evaluate the report
    formatted_prompt = JUDGE_PROMPT.format(
        final_report=state.get("final_report", ""),
        investigation_objectives=state.get("investigation_scope", {}),
        current_date=get_current_date()
    )
    
    result = llm.invoke(formatted_prompt)
    
    # Update confidence scores
    return {
        "confidence_scores": {"overall": 0.85, "accuracy": 0.9, "completeness": 0.8},
        "messages": state["messages"] + [result, AIMessage(content=state["final_report"])]
    }


# Build the OSINT Agent Graph
def create_osint_graph():
    """Create the LangGraph workflow for OSINT operations."""
    builder = StateGraph(OSINTState, config_schema=OSINTConfiguration)
    
    # Add all nodes
    builder.add_node("analyze_query", analyze_query)
    builder.add_node("plan_investigation", plan_investigation)
    builder.add_node("retrieve_data", retrieve_data)
    builder.add_node("pivot_analysis", analyze_pivot)
    builder.add_node("synthesize_report", synthesize_report)
    builder.add_node("judge_quality", judge_quality)
    
    # Define the flow
    builder.add_edge(START, "analyze_query")
    builder.add_edge("analyze_query", "plan_investigation")
    
    # Conditional edge for parallel retrievals
    builder.add_conditional_edges(
        "plan_investigation",
        spawn_retrievals,
        ["retrieve_data", "pivot_analysis"]
    )
    
    # Retrieval leads to pivot analysis
    builder.add_edge("retrieve_data", "pivot_analysis")
    
    # Conditional edge for investigation continuation
    builder.add_conditional_edges(
        "pivot_analysis",
        evaluate_investigation,
        ["plan_investigation", "synthesize_report"]
    )
    
    # Final steps
    builder.add_edge("synthesize_report", "judge_quality")
    builder.add_edge("judge_quality", END)
    
    # Compile the graph
    return builder.compile(name="autospook-osint-agent")


# Export the graph
osint_graph = create_osint_graph() 