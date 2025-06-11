"""
OSINT Database Module
Handles all database operations for the AutoSpook OSINT system
"""

import os
import asyncio
import asyncpg
import redis.asyncio as redis
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class OSINTEntity:
    """Entity data model"""
    entity_type: str
    name: str
    attributes: Dict[str, Any]
    confidence_score: float
    first_seen: datetime
    last_updated: datetime
    investigation_id: Optional[str] = None
    id: Optional[str] = None


@dataclass
class InvestigationRecord:
    """Investigation data model"""
    query: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    entities_count: int = 0
    sources_count: int = 0
    report_data: Optional[Dict] = None
    id: Optional[str] = None


class OSINTDatabase:
    """Main database handler for OSINT operations"""
    
    def __init__(self, database_url: str = None, redis_url: str = None):
        self.database_url = database_url or os.getenv(
            "DATABASE_URL", 
            "postgresql://osint_user:osint_secure_pass_2024@localhost:5432/osint_db"
        )
        self.redis_url = redis_url or os.getenv(
            "REDIS_URL",
            "redis://localhost:6379"
        )
        self.pool: Optional[asyncpg.Pool] = None
        self.redis_client: Optional[redis.Redis] = None
        
    async def initialize(self):
        """Initialize database connections"""
        try:
            # Create PostgreSQL connection pool
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            
            # Create Redis connection
            self.redis_client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            
            logger.info("Database connections initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database connections: {e}")
            raise
    
    async def close(self):
        """Close database connections"""
        if self.pool:
            await self.pool.close()
        if self.redis_client:
            await self.redis_client.close()
    
    @asynccontextmanager
    async def acquire(self):
        """Acquire a database connection from the pool"""
        async with self.pool.acquire() as connection:
            yield connection
    
    # Investigation Operations
    async def create_investigation(self, query: str, user_id: str = "system") -> str:
        """Create a new investigation"""
        async with self.acquire() as conn:
            investigation_id = await conn.fetchval(
                """
                INSERT INTO investigations (query, status, user_id, started_at)
                VALUES ($1, 'active', $2, $3)
                RETURNING id
                """,
                query, user_id, datetime.utcnow()
            )
            
            # Cache in Redis
            await self.redis_client.hset(
                f"investigation:{investigation_id}",
                mapping={
                    "query": query,
                    "status": "active",
                    "started_at": datetime.utcnow().isoformat()
                }
            )
            
            return investigation_id
    
    async def update_investigation_status(
        self, 
        investigation_id: str, 
        status: str,
        report_data: Optional[Dict] = None
    ):
        """Update investigation status"""
        async with self.acquire() as conn:
            if status == "complete" and report_data:
                await conn.execute(
                    """
                    UPDATE investigations 
                    SET status = $2, 
                        completed_at = $3,
                        report_data = $4::jsonb
                    WHERE id = $1
                    """,
                    investigation_id, status, datetime.utcnow(), json.dumps(report_data)
                )
            else:
                await conn.execute(
                    """
                    UPDATE investigations 
                    SET status = $2 
                    WHERE id = $1
                    """,
                    investigation_id, status
                )
            
            # Update Redis cache
            await self.redis_client.hset(
                f"investigation:{investigation_id}",
                "status", status
            )
    
    # Entity Operations
    async def create_entity(
        self,
        investigation_id: str,
        entity_type: str,
        name: str,
        attributes: Dict[str, Any],
        confidence_score: float = 0.5
    ) -> str:
        """Create or update an entity"""
        async with self.acquire() as conn:
            # Check if entity exists
            existing_id = await conn.fetchval(
                """
                SELECT id FROM entities 
                WHERE LOWER(name) = LOWER($1) AND entity_type = $2
                """,
                name, entity_type
            )
            
            if existing_id:
                # Update existing entity
                await conn.execute(
                    """
                    UPDATE entities 
                    SET attributes = attributes || $3::jsonb,
                        confidence_score = GREATEST(confidence_score, $4),
                        last_updated = $5
                    WHERE id = $1
                    """,
                    existing_id, entity_type, json.dumps(attributes), 
                    confidence_score, datetime.utcnow()
                )
                entity_id = existing_id
            else:
                # Create new entity
                entity_id = await conn.fetchval(
                    """
                    INSERT INTO entities 
                    (entity_type, name, attributes, confidence_score, first_seen, last_updated)
                    VALUES ($1, $2, $3::jsonb, $4, $5, $5)
                    RETURNING id
                    """,
                    entity_type, name, json.dumps(attributes), 
                    confidence_score, datetime.utcnow()
                )
            
            # Link to investigation
            await conn.execute(
                """
                INSERT INTO entity_mentions (entity_id, investigation_id, mention_date)
                VALUES ($1, $2, $3)
                ON CONFLICT (entity_id, investigation_id) DO NOTHING
                """,
                entity_id, investigation_id, datetime.utcnow()
            )
            
            # Cache in Redis for quick access
            await self.redis_client.hset(
                f"entity:{entity_id}",
                mapping={
                    "type": entity_type,
                    "name": name,
                    "confidence": str(confidence_score)
                }
            )
            
            return entity_id
    
    async def create_relationship(
        self,
        entity1_id: str,
        entity2_id: str,
        relationship_type: str,
        attributes: Optional[Dict] = None,
        confidence_score: float = 0.5
    ):
        """Create a relationship between entities"""
        async with self.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO entity_relationships 
                (entity1_id, entity2_id, relationship_type, attributes, confidence_score)
                VALUES ($1, $2, $3, $4::jsonb, $5)
                ON CONFLICT (entity1_id, entity2_id, relationship_type) 
                DO UPDATE SET 
                    confidence_score = GREATEST(entity_relationships.confidence_score, $5),
                    attributes = entity_relationships.attributes || $4::jsonb
                """,
                entity1_id, entity2_id, relationship_type, 
                json.dumps(attributes or {}), confidence_score
            )
    
    # Source Operations
    async def create_source(
        self,
        investigation_id: str,
        url: str,
        source_type: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        metadata: Optional[Dict] = None,
        credibility_score: float = 0.5
    ) -> str:
        """Create a source record"""
        async with self.acquire() as conn:
            source_id = await conn.fetchval(
                """
                INSERT INTO sources 
                (investigation_id, source_type, url, title, content, 
                 metadata, credibility_score, collected_at)
                VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7, $8)
                RETURNING id
                """,
                investigation_id, source_type, url, title, content,
                json.dumps(metadata or {}), credibility_score, datetime.utcnow()
            )
            
            # Update investigation source count
            await conn.execute(
                """
                UPDATE investigations 
                SET sources_count = sources_count + 1 
                WHERE id = $1
                """,
                investigation_id
            )
            
            return source_id
    
    # Evidence Operations
    async def create_evidence(
        self,
        entity_id: str,
        source_id: str,
        evidence_type: str,
        content: str,
        confidence_score: float = 0.5
    ):
        """Link evidence from a source to an entity"""
        async with self.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO evidence 
                (entity_id, source_id, evidence_type, content, confidence_score)
                VALUES ($1, $2, $3, $4, $5)
                """,
                entity_id, source_id, evidence_type, content, confidence_score
            )
    
    # Timeline Operations
    async def create_timeline_event(
        self,
        investigation_id: str,
        event_date: datetime,
        event_type: str,
        description: str,
        entities: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ):
        """Create a timeline event"""
        async with self.acquire() as conn:
            event_id = await conn.fetchval(
                """
                INSERT INTO timeline_events 
                (investigation_id, event_date, event_type, description, 
                 entities, metadata)
                VALUES ($1, $2, $3, $4, $5::text[], $6::jsonb)
                RETURNING id
                """,
                investigation_id, event_date, event_type, description,
                entities or [], json.dumps(metadata or {})
            )
            
            return event_id
    
    # Query Operations
    async def get_investigation(self, investigation_id: str) -> Optional[Dict]:
        """Get investigation details"""
        async with self.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM investigations WHERE id = $1
                """,
                investigation_id
            )
            
            if row:
                return dict(row)
            return None
    
    async def get_investigation_entities(self, investigation_id: str) -> List[Dict]:
        """Get all entities for an investigation"""
        async with self.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT e.* 
                FROM entities e
                JOIN entity_mentions em ON e.id = em.entity_id
                WHERE em.investigation_id = $1
                ORDER BY e.confidence_score DESC
                """,
                investigation_id
            )
            
            return [dict(row) for row in rows]
    
    async def get_entity_relationships(self, entity_id: str) -> List[Dict]:
        """Get all relationships for an entity"""
        async with self.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    er.*,
                    e1.name as entity1_name,
                    e1.entity_type as entity1_type,
                    e2.name as entity2_name,
                    e2.entity_type as entity2_type
                FROM entity_relationships er
                JOIN entities e1 ON er.entity1_id = e1.id
                JOIN entities e2 ON er.entity2_id = e2.id
                WHERE er.entity1_id = $1 OR er.entity2_id = $1
                ORDER BY er.confidence_score DESC
                """,
                entity_id
            )
            
            return [dict(row) for row in rows]
    
    async def search_entities(
        self, 
        query: str, 
        entity_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """Search entities by name or attributes"""
        async with self.acquire() as conn:
            if entity_type:
                rows = await conn.fetch(
                    """
                    SELECT * FROM entities 
                    WHERE (LOWER(name) LIKE LOWER($1) OR 
                           attributes::text LIKE $1)
                    AND entity_type = $2
                    ORDER BY confidence_score DESC
                    LIMIT $3
                    """,
                    f"%{query}%", entity_type, limit
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT * FROM entities 
                    WHERE LOWER(name) LIKE LOWER($1) OR 
                          attributes::text LIKE $1
                    ORDER BY confidence_score DESC
                    LIMIT $2
                    """,
                    f"%{query}%", limit
                )
            
            return [dict(row) for row in rows]
    
    # Cache Operations
    async def cache_set(self, key: str, value: Any, expire: int = 3600):
        """Set a value in Redis cache"""
        await self.redis_client.setex(
            key, expire, json.dumps(value)
        )
    
    async def cache_get(self, key: str) -> Optional[Any]:
        """Get a value from Redis cache"""
        value = await self.redis_client.get(key)
        if value:
            return json.loads(value)
        return None
    
    async def publish_event(self, channel: str, event: Dict):
        """Publish an event to Redis pub/sub"""
        await self.redis_client.publish(
            channel, json.dumps(event)
        )
    
    # Analytics Operations
    async def get_investigation_stats(self, investigation_id: str) -> Dict:
        """Get statistics for an investigation"""
        async with self.acquire() as conn:
            stats = await conn.fetchrow(
                """
                SELECT 
                    COUNT(DISTINCT em.entity_id) as entity_count,
                    COUNT(DISTINCT s.id) as source_count,
                    COUNT(DISTINCT er.id) as relationship_count,
                    COUNT(DISTINCT te.id) as timeline_event_count
                FROM investigations i
                LEFT JOIN entity_mentions em ON i.id = em.investigation_id
                LEFT JOIN sources s ON i.id = s.investigation_id
                LEFT JOIN entity_relationships er ON (
                    er.entity1_id IN (
                        SELECT entity_id FROM entity_mentions WHERE investigation_id = i.id
                    ) OR er.entity2_id IN (
                        SELECT entity_id FROM entity_mentions WHERE investigation_id = i.id
                    )
                )
                LEFT JOIN timeline_events te ON i.id = te.investigation_id
                WHERE i.id = $1
                GROUP BY i.id
                """,
                investigation_id
            )
            
            return dict(stats) if stats else {}


# Singleton instance
_db_instance: Optional[OSINTDatabase] = None


async def get_database() -> OSINTDatabase:
    """Get or create database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = OSINTDatabase()
        await _db_instance.initialize()
    return _db_instance 