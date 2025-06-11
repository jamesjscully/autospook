"""
OSINT Memory Manager
Provides persistent memory capabilities for the multi-agent OSINT system
"""

import json
import asyncio
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from collections import defaultdict
import logging

from src.database.osint_database import OSINTDatabase, get_database
from langchain.schema import BaseMemory
from langchain.memory import ConversationSummaryBufferMemory
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class EntityMemory(BaseModel):
    """Memory structure for entities"""
    entity_id: str
    entity_type: str
    name: str
    attributes: Dict[str, Any] = Field(default_factory=dict)
    relationships: List[Dict[str, Any]] = Field(default_factory=list)
    mentions: List[Dict[str, Any]] = Field(default_factory=list)
    confidence_score: float = 0.5
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class InvestigationMemory(BaseModel):
    """Memory structure for investigations"""
    investigation_id: str
    query: str
    entities: Dict[str, EntityMemory] = Field(default_factory=dict)
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    key_findings: List[str] = Field(default_factory=list)
    timeline_events: List[Dict[str, Any]] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)


class OSINTMemoryManager:
    """
    Manages memory for OSINT agents with persistent storage
    """
    
    def __init__(self, investigation_id: str):
        self.investigation_id = investigation_id
        self.db: Optional[OSINTDatabase] = None
        self.memory: InvestigationMemory = InvestigationMemory(
            investigation_id=investigation_id,
            query=""
        )
        self._entity_cache: Dict[str, EntityMemory] = {}
        self._relationship_cache: Set[tuple] = set()
        
    async def initialize(self, query: str):
        """Initialize memory manager with database connection"""
        self.db = await get_database()
        self.memory.query = query
        
        # Load existing investigation data if available
        investigation = await self.db.get_investigation(self.investigation_id)
        if investigation:
            await self._load_investigation_memory(investigation)
        
        logger.info(f"Memory manager initialized for investigation {self.investigation_id}")
    
    async def _load_investigation_memory(self, investigation: Dict):
        """Load existing investigation data into memory"""
        # Load entities
        entities = await self.db.get_investigation_entities(self.investigation_id)
        for entity in entities:
            entity_memory = EntityMemory(
                entity_id=entity['id'],
                entity_type=entity['entity_type'],
                name=entity['name'],
                attributes=entity.get('attributes', {}),
                confidence_score=entity.get('confidence_score', 0.5),
                last_updated=entity.get('last_updated', datetime.utcnow())
            )
            
            # Load relationships for this entity
            relationships = await self.db.get_entity_relationships(entity['id'])
            entity_memory.relationships = relationships
            
            self._entity_cache[entity['id']] = entity_memory
            self.memory.entities[entity['name'].lower()] = entity_memory
    
    async def remember_entity(
        self,
        entity_type: str,
        name: str,
        attributes: Dict[str, Any],
        confidence: float = 0.5,
        source_id: Optional[str] = None
    ) -> str:
        """Remember an entity and store it persistently"""
        # Check if entity already exists in memory
        entity_key = name.lower()
        if entity_key in self.memory.entities:
            # Update existing entity
            existing = self.memory.entities[entity_key]
            existing.attributes.update(attributes)
            existing.confidence_score = max(existing.confidence_score, confidence)
            existing.last_updated = datetime.utcnow()
            
            if source_id:
                existing.mentions.append({
                    "source_id": source_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            # Update in database
            await self.db.create_entity(
                self.investigation_id,
                entity_type,
                name,
                attributes,
                confidence
            )
            
            return existing.entity_id
        
        # Create new entity
        entity_id = await self.db.create_entity(
            self.investigation_id,
            entity_type,
            name,
            attributes,
            confidence
        )
        
        entity_memory = EntityMemory(
            entity_id=entity_id,
            entity_type=entity_type,
            name=name,
            attributes=attributes,
            confidence_score=confidence,
            mentions=[{"source_id": source_id, "timestamp": datetime.utcnow().isoformat()}] if source_id else []
        )
        
        self._entity_cache[entity_id] = entity_memory
        self.memory.entities[entity_key] = entity_memory
        
        # Publish event for real-time updates
        await self.db.publish_event(
            f"investigation:{self.investigation_id}:entities",
            {
                "type": "entity_created",
                "entity_id": entity_id,
                "entity_type": entity_type,
                "name": name,
                "confidence": confidence
            }
        )
        
        return entity_id
    
    async def remember_relationship(
        self,
        entity1_name: str,
        entity2_name: str,
        relationship_type: str,
        attributes: Optional[Dict] = None,
        confidence: float = 0.5
    ):
        """Remember a relationship between entities"""
        # Get entity IDs
        entity1 = self.memory.entities.get(entity1_name.lower())
        entity2 = self.memory.entities.get(entity2_name.lower())
        
        if not entity1 or not entity2:
            logger.warning(f"Cannot create relationship: entities not found")
            return
        
        # Check if relationship already exists
        rel_key = (entity1.entity_id, entity2.entity_id, relationship_type)
        if rel_key in self._relationship_cache:
            return
        
        # Create relationship in database
        await self.db.create_relationship(
            entity1.entity_id,
            entity2.entity_id,
            relationship_type,
            attributes,
            confidence
        )
        
        # Update memory
        relationship = {
            "entity1_id": entity1.entity_id,
            "entity2_id": entity2.entity_id,
            "entity2_name": entity2.name,
            "relationship_type": relationship_type,
            "attributes": attributes or {},
            "confidence": confidence
        }
        
        entity1.relationships.append(relationship)
        self._relationship_cache.add(rel_key)
        
        # Publish event
        await self.db.publish_event(
            f"investigation:{self.investigation_id}:relationships",
            {
                "type": "relationship_created",
                "entity1": entity1.name,
                "entity2": entity2.name,
                "relationship_type": relationship_type
            }
        )
    
    async def remember_source(
        self,
        url: str,
        source_type: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        metadata: Optional[Dict] = None,
        credibility: float = 0.5
    ) -> str:
        """Remember a source and store it persistently"""
        source_id = await self.db.create_source(
            self.investigation_id,
            url,
            source_type,
            title,
            content,
            metadata,
            credibility
        )
        
        source_record = {
            "id": source_id,
            "url": url,
            "type": source_type,
            "title": title,
            "credibility": credibility,
            "collected_at": datetime.utcnow().isoformat()
        }
        
        self.memory.sources.append(source_record)
        
        # Cache for quick access
        await self.db.cache_set(
            f"source:{source_id}",
            source_record,
            expire=7200  # 2 hours
        )
        
        return source_id
    
    async def remember_finding(self, finding: str, confidence: float = 0.5):
        """Remember a key finding"""
        self.memory.key_findings.append(finding)
        
        # Store in context for report generation
        if "findings" not in self.memory.context:
            self.memory.context["findings"] = []
        
        self.memory.context["findings"].append({
            "text": finding,
            "confidence": confidence,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def remember_timeline_event(
        self,
        event_date: datetime,
        event_type: str,
        description: str,
        entities: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ):
        """Remember a timeline event"""
        event_id = await self.db.create_timeline_event(
            self.investigation_id,
            event_date,
            event_type,
            description,
            entities,
            metadata
        )
        
        self.memory.timeline_events.append({
            "id": event_id,
            "date": event_date.isoformat(),
            "type": event_type,
            "description": description,
            "entities": entities or []
        })
    
    async def get_entity_context(self, entity_name: str) -> Optional[Dict]:
        """Get full context for an entity"""
        entity = self.memory.entities.get(entity_name.lower())
        if not entity:
            # Try searching in database
            results = await self.db.search_entities(entity_name, limit=1)
            if results:
                return results[0]
            return None
        
        return {
            "id": entity.entity_id,
            "type": entity.entity_type,
            "name": entity.name,
            "attributes": entity.attributes,
            "relationships": entity.relationships,
            "mentions": entity.mentions,
            "confidence": entity.confidence_score
        }
    
    async def get_investigation_summary(self) -> Dict:
        """Get a summary of the investigation"""
        stats = await self.db.get_investigation_stats(self.investigation_id)
        
        return {
            "investigation_id": self.investigation_id,
            "query": self.memory.query,
            "entity_count": len(self.memory.entities),
            "source_count": len(self.memory.sources),
            "key_findings": self.memory.key_findings,
            "timeline_events": len(self.memory.timeline_events),
            "stats": stats,
            "top_entities": sorted(
                [
                    {
                        "name": e.name,
                        "type": e.entity_type,
                        "confidence": e.confidence_score,
                        "relationships": len(e.relationships)
                    }
                    for e in self.memory.entities.values()
                ],
                key=lambda x: x["confidence"],
                reverse=True
            )[:10]
        }
    
    async def search_memory(self, query: str) -> List[Dict]:
        """Search through investigation memory"""
        results = []
        
        # Search entities
        for entity in self.memory.entities.values():
            if query.lower() in entity.name.lower() or \
               any(query.lower() in str(v).lower() for v in entity.attributes.values()):
                results.append({
                    "type": "entity",
                    "data": await self.get_entity_context(entity.name)
                })
        
        # Search sources
        for source in self.memory.sources:
            if query.lower() in (source.get("title", "") + source.get("url", "")).lower():
                results.append({
                    "type": "source",
                    "data": source
                })
        
        # Search findings
        for finding in self.memory.key_findings:
            if query.lower() in finding.lower():
                results.append({
                    "type": "finding",
                    "data": finding
                })
        
        return results
    
    def get_memory_state(self) -> Dict:
        """Get the current memory state for serialization"""
        return {
            "investigation_id": self.investigation_id,
            "query": self.memory.query,
            "entities": {
                name: {
                    "id": entity.entity_id,
                    "type": entity.entity_type,
                    "name": entity.name,
                    "attributes": entity.attributes,
                    "confidence": entity.confidence_score,
                    "relationships": len(entity.relationships)
                }
                for name, entity in self.memory.entities.items()
            },
            "sources": len(self.memory.sources),
            "findings": self.memory.key_findings,
            "timeline_events": len(self.memory.timeline_events)
        }
    
    async def checkpoint(self):
        """Save current memory state to cache"""
        state = self.get_memory_state()
        await self.db.cache_set(
            f"investigation:{self.investigation_id}:memory",
            state,
            expire=86400  # 24 hours
        )
    
    async def restore_from_checkpoint(self):
        """Restore memory from cached checkpoint"""
        cached_state = await self.db.cache_get(
            f"investigation:{self.investigation_id}:memory"
        )
        
        if cached_state:
            # Restore basic state
            self.memory.query = cached_state.get("query", "")
            self.memory.key_findings = cached_state.get("findings", [])
            
            # Full restore would reload from database
            await self._load_investigation_memory(
                {"id": self.investigation_id}
            )


class OSINTConversationMemory(ConversationSummaryBufferMemory):
    """
    Extended conversation memory for OSINT agents with persistent storage
    """
    
    def __init__(self, investigation_id: str, **kwargs):
        super().__init__(**kwargs)
        self.investigation_id = investigation_id
        self.osint_memory = OSINTMemoryManager(investigation_id)
        
    async def initialize(self, query: str):
        """Initialize with database connection"""
        await self.osint_memory.initialize(query)
    
    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, Any]) -> None:
        """Save context with OSINT-specific handling"""
        super().save_context(inputs, outputs)
        
        # Extract and store entities, sources, etc. from the conversation
        # This would be called by agents to persist their findings
        asyncio.create_task(self._async_save_osint_context(inputs, outputs))
    
    async def _async_save_osint_context(self, inputs: Dict[str, Any], outputs: Dict[str, Any]):
        """Async handler for saving OSINT-specific context"""
        # This would parse agent outputs and store relevant data
        # For example, if an agent found entities, sources, etc.
        pass 