"""
OSINT Research Agent for AutoSpook

A simplified, clean implementation using LangChain's built-in search tools
for open source intelligence gathering and analysis.
"""

import os
import logging
import asyncio
from typing import Dict, Any, List, Optional
from typing_extensions import TypedDict

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from langsmith import traceable
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_community.tools import WikipediaQueryRun
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class ResearchState(TypedDict):
    """State for the OSINT research workflow."""
    query: str
    context: str
    sources: List[str]
    notes: List[str]
    search_results: List[Dict[str, Any]]


def create_llm() -> ChatOpenAI:
    """Create OpenAI LLM instance."""
    return ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0.1,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )


def extract_sources_from_search_results(search_results: List[Dict[str, Any]]) -> List[str]:
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
async def search_node(state: ResearchState) -> Dict[str, Any]:
    """Perform comprehensive search using multiple sources."""
    logger.info(f"Starting search for query: {state['query']}")
    
    search_results = []
    
    try:
        # Initialize search tools
        web_search = DuckDuckGoSearchResults(num_results=5)
        wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
        
        # Perform web search
        try:
            logger.info("Performing web search...")
            web_result = await asyncio.to_thread(web_search.run, state["query"])
            search_results.append({
                "tool": "web_search",
                "query": state["query"],
                "result": web_result,
                "status": "success"
            })
            logger.info("Web search completed successfully")
        except Exception as e:
            logger.warning(f"Web search failed: {e}")
            search_results.append({
                "tool": "web_search",
                "query": state["query"],
                "error": str(e),
                "status": "error"
            })
        
        # Perform Wikipedia search for additional context
        try:
            logger.info("Performing Wikipedia search...")
            wiki_result = await asyncio.to_thread(wikipedia.run, state["query"])
            search_results.append({
                "tool": "wikipedia",
                "query": state["query"],
                "result": wiki_result,
                "status": "success"
            })
            logger.info("Wikipedia search completed successfully")
        except Exception as e:
            logger.warning(f"Wikipedia search failed: {e}")
            search_results.append({
                "tool": "wikipedia",
                "query": state["query"],
                "error": str(e),
                "status": "error"
            })
        
        return {
            **state,
            "search_results": search_results,
        }
        
    except Exception as e:
        logger.error(f"Critical error in search node: {e}")
        return {
            **state,
            "search_results": [{"tool": "error", "error": str(e), "status": "error"}],
        }


@traceable
async def analysis_node(state: ResearchState) -> Dict[str, Any]:
    """Analyze search results and generate intelligence report."""
    logger.info(f"Starting analysis for query: {state['query']}")
    
    llm = create_llm()
    search_results = state.get("search_results", [])
    
    # Format search results for the LLM
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
    
    # Create analysis prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert OSINT analyst for AutoSpook. Your role is to analyze publicly available information and generate comprehensive intelligence reports.

INSTRUCTIONS:
- Provide factual, objective analysis based only on the search results provided
- Structure your response with clear sections: Overview, Key Findings, Background, and Assessment
- Cite specific sources when making claims
- Focus on publicly available information only
- Be professional and analytical in tone
- If information is limited, acknowledge this

Query: {query}
{search_context}"""),
        ("human", "Please provide a comprehensive OSINT analysis for: {query}")
    ])
    
    try:
        # Generate analysis
        chain = prompt | llm
        response = await asyncio.to_thread(
            chain.invoke,
            {
                "query": state["query"],
                "search_context": search_context
            }
        )
        
        analysis = response.content
        
        # Extract sources from search results
        sources = extract_sources_from_search_results(search_results)
        all_sources = state.get("sources", []) + sources
        
        # Generate notes
        notes = state.get("notes", [])
        successful_searches = len([r for r in search_results if r.get("status") == "success"])
        notes.append(f"Executed {len(search_results)} searches ({successful_searches} successful)")
        notes.append(f"Generated analysis with {len(sources)} sources")
        
        return {
            "query": state["query"],
            "context": analysis,
            "sources": all_sources,
            "notes": notes,
            "search_results": search_results,
        }
        
    except Exception as e:
        logger.error(f"Error in analysis node: {e}")
        return {
            **state,
            "context": f"Analysis failed: {str(e)}",
            "notes": state.get("notes", []) + [f"Analysis error: {str(e)}"],
        }


def should_continue(state: ResearchState) -> str:
    """Determine if the workflow should continue."""
    # For now, always end after one iteration
    return END


def create_research_workflow() -> StateGraph:
    """Create the OSINT research workflow."""
    workflow = StateGraph(ResearchState)
    
    # Add nodes
    workflow.add_node("search", search_node)
    workflow.add_node("analysis", analysis_node)
    
    # Set entry point
    workflow.set_entry_point("search")
    
    # Add edges
    workflow.add_edge("search", "analysis")
    workflow.add_conditional_edges("analysis", should_continue)
    
    return workflow.compile()


# Global workflow instance
_workflow = None


def get_research_workflow():
    """Get the compiled research workflow."""
    global _workflow
    if _workflow is None:
        _workflow = create_research_workflow()
    return _workflow


async def research(query: str, max_steps: int = 1) -> Dict[str, Any]:
    """
    Execute OSINT research for a given query.
    
    Args:
        query: The research query
        max_steps: Maximum number of research steps (currently unused)
        
    Returns:
        Dictionary containing research results
    """
    logger.info(f"Starting OSINT research for: {query}")
    
    # Initialize state
    initial_state = {
        "query": query,
        "context": "",
        "sources": [],
        "notes": [],
        "search_results": [],
    }
    
    # Execute workflow
    workflow = get_research_workflow()
    result = await workflow.ainvoke(initial_state)
    
    logger.info(f"OSINT research completed for: {query}")
    return result