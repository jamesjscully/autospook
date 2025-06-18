"""
AutoSpook OSINT Research API

A clean, simple FastAPI backend for open source intelligence research
using LangChain's built-in search tools.
"""

import logging
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from .agent import research

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AutoSpook OSINT API",
    version="0.2.0",
    description="Open Source Intelligence research tool using LangChain"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#base models --domain logic here for now.
class ResearchRequest(BaseModel):
    """Request model for OSINT research."""
    message: str
    max_steps: Optional[int] = 1


class ResearchResponse(BaseModel):
    """Response model for OSINT research."""
    response: str
    sources: List[str] = []
    notes: List[str] = []
    step_count: int = 0
    search_results: List[dict] = []


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "AutoSpook OSINT Research API",
        "status": "running",
        "version": "0.2.0",
        "description": "Open Source Intelligence research using LangChain tools",
        "endpoints": {
            "research": "/chat or /research - POST (Temporal-orchestrated)",
            "health": "/health - GET",
            "docs": "/docs - Interactive API documentation"
        },
        "temporal": {
            "status": "required",
            "setup": "Run 'make temporal-dev' to start Temporal infrastructure and workers",
            "note": "All research is executed via Temporal workflows for reliability and fault tolerance"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "autospook-api",
        "version": "0.2.0"
    }


@app.post("/chat", response_model=ResearchResponse)
async def chat(request: ResearchRequest):
    """
    Main chat endpoint for OSINT research requests.
    
    Accepts a research query and returns comprehensive analysis
    with sources and metadata.
    """
    try:
        logger.info(f"Received OSINT research request: {request.message}")
        
        # Validate request
        if not request.message.strip():
            raise HTTPException(
                status_code=400,
                detail="Research query cannot be empty"
            )
        
        # Execute research using Temporal workflows
        from .agent import research
        result = await research(
            query=request.message.strip(),
            max_steps=request.max_steps
        )
        
        # Format response from ResearchState
        response = ResearchResponse(
            response=result.context or result.final_report or "No analysis generated",
            sources=result.sources,
            notes=result.notes,
            step_count=result.step,
            search_results=[]  # Simplified for response
        )
        
        logger.info(f"Research completed successfully for: {request.message}")
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except ImportError as e:
        logger.error(f"Temporal not available: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Temporal workflows not available. Ensure Temporal server is running with 'make temporal-dev'"
        )
    except Exception as e:
        error_msg = str(e)
        if "temporal" in error_msg.lower() or "connection" in error_msg.lower():
            logger.error(f"Temporal connection error: {error_msg}")
            raise HTTPException(
                status_code=503,
                detail="Unable to connect to Temporal server. Run 'make temporal-dev' to start the infrastructure."
            )
        else:
            logger.error(f"Error processing research request: {error_msg}")
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error during research: {error_msg}"
            )


@app.post("/research", response_model=ResearchResponse)
async def research_endpoint(request: ResearchRequest):
    """Dedicated research endpoint (alias for /chat)."""
    return await chat(request)




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)