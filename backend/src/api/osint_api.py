"""
OSINT API Server
Provides REST and WebSocket endpoints for the frontend
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import asyncio
import json
import uuid
from datetime import datetime
import logging

from src.agent.osint_graph_integrated import create_integrated_osint_graph, IntegratedOSINTGraph
from src.database.osint_database import get_database, OSINTDatabase
from src.agent.osint_memory import OSINTMemoryManager

logger = logging.getLogger(__name__)

app = FastAPI(title="AutoSpook OSINT API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class InvestigationRequest(BaseModel):
    query: str
    max_retrievals: Optional[int] = Field(default=12, ge=8, le=20)
    focus_areas: Optional[List[str]] = Field(default_factory=list)
    entity_types: Optional[List[str]] = Field(default_factory=list)

class InvestigationResponse(BaseModel):
    investigation_id: str
    status: str
    message: str

class InvestigationStatus(BaseModel):
    investigation_id: str
    status: str
    progress: float
    entities_count: int
    sources_count: int
    key_findings: List[str]
    current_phase: str

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.redis_client = None
        self.subscriptions = {}
    
    async def initialize(self):
        """Initialize Redis connection for pub/sub"""
        db = await get_database()
        self.redis_client = db.redis_client
    
    async def connect(self, websocket: WebSocket, investigation_id: str):
        """Accept WebSocket connection"""
        await websocket.accept()
        if investigation_id not in self.active_connections:
            self.active_connections[investigation_id] = []
        self.active_connections[investigation_id].append(websocket)
        
        # Subscribe to Redis channel for this investigation
        await self._subscribe_to_investigation(investigation_id)
    
    def disconnect(self, websocket: WebSocket, investigation_id: str):
        """Remove WebSocket connection"""
        if investigation_id in self.active_connections:
            self.active_connections[investigation_id].remove(websocket)
            if not self.active_connections[investigation_id]:
                del self.active_connections[investigation_id]
    
    async def send_to_investigation(self, investigation_id: str, message: dict):
        """Send message to all connections for an investigation"""
        if investigation_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[investigation_id]:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.append(connection)
            
            # Clean up disconnected clients
            for conn in disconnected:
                self.disconnect(conn, investigation_id)
    
    async def _subscribe_to_investigation(self, investigation_id: str):
        """Subscribe to Redis channel for investigation updates"""
        if investigation_id not in self.subscriptions:
            channel = f"investigation:{investigation_id}"
            pubsub = self.redis_client.pubsub()
            await pubsub.subscribe(channel)
            
            # Start listening task
            self.subscriptions[investigation_id] = asyncio.create_task(
                self._listen_to_channel(pubsub, investigation_id)
            )
    
    async def _listen_to_channel(self, pubsub, investigation_id: str):
        """Listen to Redis channel and forward messages"""
        try:
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    data = json.loads(message['data'])
                    await self.send_to_investigation(investigation_id, data)
        except asyncio.CancelledError:
            await pubsub.unsubscribe()
            await pubsub.close()

# Global connection manager
manager = ConnectionManager()

# Dependency to get database
async def get_db() -> OSINTDatabase:
    return await get_database()

# Active investigations cache
active_investigations: Dict[str, IntegratedOSINTGraph] = {}

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    await manager.initialize()
    logger.info("OSINT API server started")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    # Cancel all subscriptions
    for task in manager.subscriptions.values():
        task.cancel()

    # Close database connections if initialized
    try:
        db = await get_database()
        await db.close()
    except Exception as e:
        logger.error(f"Database cleanup failed: {e}")

    # Close active WebSocket connections
    for inv_id, conns in list(manager.active_connections.items()):
        for conn in conns:
            try:
                await conn.close()
            except Exception:
                pass
        manager.active_connections.pop(inv_id, None)

    logger.info("OSINT API server stopped")

# REST Endpoints

@app.post("/api/investigations", response_model=InvestigationResponse)
async def create_investigation(
    request: InvestigationRequest,
    db: OSINTDatabase = Depends(get_db)
) -> InvestigationResponse:
    """Create a new OSINT investigation"""
    try:
        # Create investigation in database
        investigation_id = await db.create_investigation(
            query=request.query,
            user_id="api_user"  # TODO: Get from auth
        )
        
        # Create and start the investigation graph
        graph = IntegratedOSINTGraph(investigation_id)
        active_investigations[investigation_id] = graph
        
        # Start investigation in background
        asyncio.create_task(
            _run_investigation_async(
                graph, 
                request.query, 
                {
                    "max_retrievals": request.max_retrievals,
                    "focus_areas": request.focus_areas,
                    "entity_types": request.entity_types
                }
            )
        )
        
        return InvestigationResponse(
            investigation_id=investigation_id,
            status="started",
            message=f"Investigation started for: {request.query}"
        )
        
    except Exception as e:
        logger.error(f"Failed to create investigation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/investigations/{investigation_id}", response_model=InvestigationStatus)
async def get_investigation_status(
    investigation_id: str,
    db: OSINTDatabase = Depends(get_db)
) -> InvestigationStatus:
    """Get investigation status"""
    try:
        # Get investigation from database
        investigation = await db.get_investigation(investigation_id)
        if not investigation:
            raise HTTPException(status_code=404, detail="Investigation not found")
        
        # Get memory manager for detailed status
        memory = OSINTMemoryManager(investigation_id)
        await memory.initialize(investigation['query'])
        summary = await memory.get_investigation_summary()
        
        # Determine current phase
        status_to_phase = {
            "active": "query_analysis",
            "retrieving": "retrieval",
            "analyzing": "pivot_analysis",
            "reporting": "synthesis",
            "complete": "complete"
        }
        
        return InvestigationStatus(
            investigation_id=investigation_id,
            status=investigation['status'],
            progress=_calculate_progress(investigation['status'], summary),
            entities_count=summary['entity_count'],
            sources_count=summary['source_count'],
            key_findings=summary['key_findings'],
            current_phase=status_to_phase.get(investigation['status'], "unknown")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get investigation status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/investigations/{investigation_id}/report")
async def get_investigation_report(
    investigation_id: str,
    db: OSINTDatabase = Depends(get_db)
):
    """Get investigation report"""
    try:
        investigation = await db.get_investigation(investigation_id)
        if not investigation:
            raise HTTPException(status_code=404, detail="Investigation not found")
        
        if investigation['status'] != 'complete':
            raise HTTPException(status_code=400, detail="Investigation not complete")
        
        return {
            "investigation_id": investigation_id,
            "query": investigation['query'],
            "report": investigation.get('report_data', {}),
            "completed_at": investigation['completed_at'].isoformat() if investigation['completed_at'] else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/investigations/{investigation_id}/entities")
async def get_investigation_entities(
    investigation_id: str,
    db: OSINTDatabase = Depends(get_db)
):
    """Get all entities for an investigation"""
    try:
        entities = await db.get_investigation_entities(investigation_id)
        return {
            "investigation_id": investigation_id,
            "entities": entities,
            "count": len(entities)
        }
        
    except Exception as e:
        logger.error(f"Failed to get entities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/investigations/{investigation_id}/sources")
async def get_investigation_sources(
    investigation_id: str,
    db: OSINTDatabase = Depends(get_db)
):
    """Get all sources for an investigation"""
    try:
        # Get sources from database
        async with db.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM sources 
                WHERE investigation_id = $1 
                ORDER BY collected_at DESC
                """,
                investigation_id
            )
            
        sources = [dict(row) for row in rows]
        return {
            "investigation_id": investigation_id,
            "sources": sources,
            "count": len(sources)
        }
        
    except Exception as e:
        logger.error(f"Failed to get sources: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/entities/{entity_id}/relationships")
async def get_entity_relationships(
    entity_id: str,
    db: OSINTDatabase = Depends(get_db)
):
    """Get relationships for an entity"""
    try:
        relationships = await db.get_entity_relationships(entity_id)
        return {
            "entity_id": entity_id,
            "relationships": relationships,
            "count": len(relationships)
        }
        
    except Exception as e:
        logger.error(f"Failed to get relationships: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint
@app.websocket("/ws/{investigation_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    investigation_id: str
):
    """WebSocket for real-time investigation updates"""
    await manager.connect(websocket, investigation_id)
    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connection",
            "message": f"Connected to investigation {investigation_id}",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Keep connection alive
        while True:
            # Wait for any message from client (ping/pong)
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, investigation_id)

# Helper functions

async def _run_investigation_async(
    graph: IntegratedOSINTGraph, 
    query: str, 
    config: Dict
):
    """Run investigation asynchronously"""
    try:
        await graph.initialize(query)
        result = await graph.run_investigation(query, config)
        logger.info(f"Investigation {graph.investigation_id} completed: {result}")
    except Exception as e:
        logger.error(f"Investigation {graph.investigation_id} failed: {e}")
        db = await get_database()
        await db.update_investigation_status(graph.investigation_id, "failed")
    finally:
        # Clean up
        if graph.investigation_id in active_investigations:
            del active_investigations[graph.investigation_id]

def _calculate_progress(status: str, summary: Dict) -> float:
    """Calculate investigation progress"""
    progress_map = {
        "active": 10,
        "retrieving": 40,
        "analyzing": 70,
        "reporting": 90,
        "complete": 100,
        "failed": 0
    }
    
    base_progress = progress_map.get(status, 0)
    
    # Adjust based on actual work done
    if status == "retrieving" and summary['source_count'] > 0:
        # Progress based on sources gathered
        source_progress = min(summary['source_count'] / 12 * 30, 30)
        base_progress = 40 + source_progress
    
    return base_progress

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        db = await get_database()
        # Test database connection
        async with db.acquire() as conn:
            await conn.fetchval("SELECT 1")
        
        # Test Redis connection
        pong = await db.redis_client.ping()
        
        return {
            "status": "healthy",
            "database": "connected",
            "redis": "connected" if pong else "disconnected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        } 