"""
Simple FastAPI server for AutoSpook development
Run this to test the frontend without full backend setup
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import uuid
import json
from datetime import datetime
from typing import Optional, List

app = FastAPI(title="AutoSpook OSINT API - Development", version="1.0.0-dev")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class InvestigationRequest(BaseModel):
    query: str
    max_retrievals: Optional[int] = 12
    focus_areas: Optional[List[str]] = []
    entity_types: Optional[List[str]] = []

# Mock data storage
investigations = {}
mock_entities = [
    {"id": "1", "name": "Ali Khaledi Nasab", "type": "person", "confidence": 0.9},
    {"id": "2", "name": "Iran", "type": "location", "confidence": 0.8},
    {"id": "3", "name": "University of Tehran", "type": "organization", "confidence": 0.7}
]

mock_sources = [
    {"id": "1", "url": "https://example.com/profile", "title": "Profile Information", "type": "web", "credibility": 0.8},
    {"id": "2", "url": "https://linkedin.com/example", "title": "Professional Profile", "type": "social", "credibility": 0.9},
    {"id": "3", "url": "https://university.edu/faculty", "title": "Faculty Directory", "type": "academic", "credibility": 0.95}
]

@app.post("/api/investigations")
async def create_investigation(request: InvestigationRequest):
    """Create a new investigation"""
    investigation_id = str(uuid.uuid4())
    investigation = {
        "id": investigation_id,
        "query": request.query,
        "status": "started",
        "created_at": datetime.now().isoformat(),
        "max_retrievals": request.max_retrievals
    }
    investigations[investigation_id] = investigation
    
    print(f"Created investigation: {investigation_id} for query: {request.query}")
    
    return {
        "investigation_id": investigation_id,
        "status": "started",
        "message": f"Investigation started for: {request.query}"
    }

@app.get("/api/investigations/{investigation_id}")
async def get_investigation_status(investigation_id: str):
    """Get investigation status"""
    if investigation_id not in investigations:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    # Simulate progression (use simple hash-based deterministic progress)
    import hashlib
    hash_value = int(hashlib.md5(investigation_id.encode()).hexdigest()[:8], 16)
    progress_factor = (hash_value % 100) / 100.0  # 0.0 to 1.0
    
    # Simple deterministic status based on investigation age
    if progress_factor < 0.3:
        status = "retrieving"
        progress = 30 + (progress_factor * 50)  # 30-80%
    elif progress_factor < 0.7:
        status = "analyzing"
        progress = 80 + (progress_factor * 10)  # 80-90%
    else:
        status = "complete" 
        progress = 100
    
    return {
        "investigation_id": investigation_id,
        "status": status,
        "progress": progress,
        "entities_count": len(mock_entities),
        "sources_count": len(mock_sources),
        "key_findings": ["Individual identified", "Professional background found", "Academic affiliations confirmed"],
        "current_phase": status
    }

@app.get("/api/investigations/{investigation_id}/entities")
async def get_investigation_entities(investigation_id: str):
    """Get entities for investigation"""
    if investigation_id not in investigations:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    return {
        "investigation_id": investigation_id,
        "entities": mock_entities,
        "count": len(mock_entities)
    }

@app.get("/api/investigations/{investigation_id}/sources")
async def get_investigation_sources(investigation_id: str):
    """Get sources for investigation"""
    if investigation_id not in investigations:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    return {
        "investigation_id": investigation_id,
        "sources": mock_sources,
        "count": len(mock_sources)
    }

@app.get("/api/investigations/{investigation_id}/report")
async def get_investigation_report(investigation_id: str):
    """Get investigation report"""
    if investigation_id not in investigations:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    investigation = investigations[investigation_id]
    
    report = {
        "executive_summary": f"Investigation completed for '{investigation['query']}'. Found comprehensive information across multiple sources including professional profiles, academic affiliations, and public records.",
        "key_findings": [
            "Individual successfully identified with high confidence",
            "Professional background in academic/research field",
            "Multiple online presence indicators found",
            "No adverse information discovered in initial search"
        ],
        "entities": mock_entities,
        "sources": mock_sources,
        "risk_assessment": {
            "overall_risk": "Low",
            "confidence": 0.85,
            "factors": ["Verified professional identity", "Academic background", "Public information available"]
        },
        "recommendations": [
            "Consider deeper dive into professional networks",
            "Cross-reference with additional databases",
            "Monitor for new information"
        ]
    }
    
    return {
        "investigation_id": investigation_id,
        "query": investigation["query"],
        "report": report,
        "completed_at": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "mode": "development",
        "message": "AutoSpook OSINT API is running in development mode",
        "timestamp": datetime.now().isoformat(),
        "active_investigations": len(investigations)
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AutoSpook OSINT API - Development Server",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    print("Starting AutoSpook OSINT Development API...")
    print("API will be available at: http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    print("Health Check: http://localhost:8000/health")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000, 
        log_level="info"
    ) 