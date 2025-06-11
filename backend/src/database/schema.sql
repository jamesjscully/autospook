-- AutoSpook OSINT Database Schema
-- PostgreSQL schema for persistent memory and investigation tracking

-- Create schema
CREATE SCHEMA IF NOT EXISTS osint;

-- Entity knowledge graph
CREATE TABLE IF NOT EXISTS osint.entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    aliases JSONB DEFAULT '[]'::jsonb,
    attributes JSONB DEFAULT '{}'::jsonb,
    confidence_score FLOAT DEFAULT 0.0,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT entity_type_check CHECK (entity_type IN ('PERSON', 'ORGANIZATION', 'LOCATION', 'EVENT', 'IDENTIFIER'))
);

-- Create indexes for entities
CREATE INDEX idx_entities_name ON osint.entities(name);
CREATE INDEX idx_entities_type ON osint.entities(entity_type);
CREATE INDEX idx_entities_confidence ON osint.entities(confidence_score DESC);

-- Relationships between entities
CREATE TABLE IF NOT EXISTS osint.relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_entity_id UUID REFERENCES osint.entities(id) ON DELETE CASCADE,
    target_entity_id UUID REFERENCES osint.entities(id) ON DELETE CASCADE,
    relationship_type VARCHAR(100) NOT NULL,
    properties JSONB DEFAULT '{}'::jsonb,
    confidence_score FLOAT DEFAULT 0.0,
    evidence_ids JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_relationship UNIQUE(source_entity_id, target_entity_id, relationship_type)
);

-- Create indexes for relationships
CREATE INDEX idx_relationships_source ON osint.relationships(source_entity_id);
CREATE INDEX idx_relationships_target ON osint.relationships(target_entity_id);
CREATE INDEX idx_relationships_type ON osint.relationships(relationship_type);

-- Source credibility tracking
CREATE TABLE IF NOT EXISTS osint.sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_url VARCHAR(500) UNIQUE,
    source_type VARCHAR(100),
    credibility_score FLOAT DEFAULT 0.5,
    domain VARCHAR(255),
    last_accessed TIMESTAMP,
    reliability_history JSONB DEFAULT '[]'::jsonb,
    total_uses INTEGER DEFAULT 0,
    successful_uses INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for sources
CREATE INDEX idx_sources_domain ON osint.sources(domain);
CREATE INDEX idx_sources_credibility ON osint.sources(credibility_score DESC);
CREATE INDEX idx_sources_type ON osint.sources(source_type);

-- Investigation state tracking
CREATE TABLE IF NOT EXISTS osint.investigations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    investigation_id VARCHAR(255) UNIQUE NOT NULL,
    query TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    phase VARCHAR(50) DEFAULT 'INITIAL',
    state JSONB NOT NULL,
    memory_context JSONB DEFAULT '{}'::jsonb,
    confidence_scores JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    total_retrievals INTEGER DEFAULT 0,
    processing_time_seconds FLOAT,
    CONSTRAINT status_check CHECK (status IN ('active', 'completed', 'failed', 'cancelled')),
    CONSTRAINT phase_check CHECK (phase IN ('INITIAL', 'EXPANSION', 'DEEP_DIVE', 'SYNTHESIS'))
);

-- Create indexes for investigations
CREATE INDEX idx_investigations_status ON osint.investigations(status);
CREATE INDEX idx_investigations_created ON osint.investigations(created_at DESC);
CREATE INDEX idx_investigations_query ON osint.investigations USING gin(to_tsvector('english', query));

-- Evidence chain and data points
CREATE TABLE IF NOT EXISTS osint.evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    investigation_id UUID REFERENCES osint.investigations(id) ON DELETE CASCADE,
    source_id UUID REFERENCES osint.sources(id),
    data_point_type VARCHAR(100),
    raw_data JSONB NOT NULL,
    extracted_facts JSONB DEFAULT '[]'::jsonb,
    extracted_entities JSONB DEFAULT '[]'::jsonb,
    cross_references JSONB DEFAULT '[]'::jsonb,
    relevance_score FLOAT DEFAULT 0.0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for evidence
CREATE INDEX idx_evidence_investigation ON osint.evidence(investigation_id);
CREATE INDEX idx_evidence_source ON osint.evidence(source_id);
CREATE INDEX idx_evidence_timestamp ON osint.evidence(timestamp DESC);
CREATE INDEX idx_evidence_relevance ON osint.evidence(relevance_score DESC);

-- Timeline events
CREATE TABLE IF NOT EXISTS osint.timeline_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    investigation_id UUID REFERENCES osint.investigations(id) ON DELETE CASCADE,
    entity_id UUID REFERENCES osint.entities(id),
    event_date TIMESTAMP NOT NULL,
    event_type VARCHAR(100),
    description TEXT,
    evidence_ids JSONB DEFAULT '[]'::jsonb,
    confidence_score FLOAT DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for timeline
CREATE INDEX idx_timeline_investigation ON osint.timeline_events(investigation_id);
CREATE INDEX idx_timeline_entity ON osint.timeline_events(entity_id);
CREATE INDEX idx_timeline_date ON osint.timeline_events(event_date);

-- Reports and outputs
CREATE TABLE IF NOT EXISTS osint.reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    investigation_id UUID REFERENCES osint.investigations(id) ON DELETE CASCADE,
    report_type VARCHAR(50) DEFAULT 'final',
    content TEXT NOT NULL,
    executive_summary TEXT,
    risk_assessment JSONB DEFAULT '{}'::jsonb,
    confidence_scores JSONB DEFAULT '{}'::jsonb,
    quality_scores JSONB DEFAULT '{}'::jsonb,
    approved BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP,
    approved_by VARCHAR(255)
);

-- Create indexes for reports
CREATE INDEX idx_reports_investigation ON osint.reports(investigation_id);
CREATE INDEX idx_reports_created ON osint.reports(created_at DESC);
CREATE INDEX idx_reports_approved ON osint.reports(approved);

-- Create update trigger for last_updated timestamps
CREATE OR REPLACE FUNCTION osint.update_last_updated()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_updated = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_entities_last_updated
    BEFORE UPDATE ON osint.entities
    FOR EACH ROW
    EXECUTE FUNCTION osint.update_last_updated();

-- Create function to update source credibility
CREATE OR REPLACE FUNCTION osint.update_source_credibility(
    p_source_id UUID,
    p_success BOOLEAN
)
RETURNS VOID AS $$
BEGIN
    UPDATE osint.sources
    SET 
        total_uses = total_uses + 1,
        successful_uses = CASE WHEN p_success THEN successful_uses + 1 ELSE successful_uses END,
        credibility_score = CASE 
            WHEN total_uses > 0 THEN (successful_uses::FLOAT + CASE WHEN p_success THEN 1 ELSE 0 END) / (total_uses + 1)
            ELSE 0.5 
        END,
        last_accessed = CURRENT_TIMESTAMP
    WHERE id = p_source_id;
END;
$$ LANGUAGE plpgsql;

-- Create view for active investigations summary
CREATE OR REPLACE VIEW osint.active_investigations_summary AS
SELECT 
    i.id,
    i.investigation_id,
    i.query,
    i.status,
    i.phase,
    i.created_at,
    i.total_retrievals,
    COUNT(DISTINCT e.id) as evidence_count,
    COUNT(DISTINCT ent.id) as entity_count,
    AVG(e.relevance_score) as avg_relevance,
    (i.confidence_scores->>'overall')::FLOAT as overall_confidence
FROM osint.investigations i
LEFT JOIN osint.evidence e ON e.investigation_id = i.id
LEFT JOIN osint.entities ent ON ent.id IN (
    SELECT DISTINCT (jsonb_array_elements(e.extracted_entities)->>'entity_id')::UUID
    FROM osint.evidence e
    WHERE e.investigation_id = i.id
)
WHERE i.status = 'active'
GROUP BY i.id; 