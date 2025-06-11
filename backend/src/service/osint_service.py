"""
OSINT LangGraph Service
Exposes the OSINT graph to LangGraph server
"""

from langgraph.graph import StateGraph
from typing import Dict, Any, Optional
import logging

from src.agent.osint_graph_integrated import IntegratedOSINTGraph, create_integrated_osint_graph
from src.agent.osint_state import OSINTState, InvestigationPhase
from src.api.osint_api import app as fastapi_app

logger = logging.getLogger(__name__)

# Create a simple wrapper graph for LangGraph server
def create_osint_service_graph():
    """Create OSINT graph for LangGraph server"""
    
    async def run_osint_investigation(state: Dict[str, Any]) -> Dict[str, Any]:
        """Main node that runs the integrated OSINT investigation"""
        try:
            # Extract parameters from state
            query = state.get("investigation_query", "")
            max_retrievals = state.get("max_retrievals", 12)
            focus_areas = state.get("focus_areas", [])
            
            if not query:
                return {
                    "error": "No investigation query provided",
                    "status": "failed"
                }
            
            # Create and run integrated investigation
            graph = await create_integrated_osint_graph(query)
            result = await graph.run_investigation(
                query,
                {
                    "max_retrievals": max_retrievals,
                    "focus_areas": focus_areas
                }
            )
            
            # Return results
            return {
                "investigation_id": result["investigation_id"],
                "report": result["report"],
                "quality_score": result["quality_score"],
                "entities_found": result["entities_found"],
                "sources_used": result["sources_used"],
                "status": "complete"
            }
            
        except Exception as e:
            logger.error(f"OSINT investigation failed: {e}")
            return {
                "error": str(e),
                "status": "failed"
            }
    
    # Create the graph
    workflow = StateGraph(dict)
    
    # Add the main investigation node
    workflow.add_node("investigate", run_osint_investigation)
    
    # Set entry point
    workflow.set_entry_point("investigate")
    
    # Set finish point
    workflow.set_finish_point("investigate")
    
    # Compile the graph
    return workflow.compile()

# Create the graph instance
osint_graph = create_osint_service_graph()

# Export for LangGraph server
graph = osint_graph

# Also export the FastAPI app for additional endpoints
__all__ = ["graph", "fastapi_app"] 