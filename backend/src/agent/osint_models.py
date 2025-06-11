"""
Comprehensive Pydantic Models for OSINT System
Replaces manual parsing with structured, validated data models
"""

from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator, root_validator
from uuid import UUID, uuid4

# Entity-related models
class EntityType(str, Enum):
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    EVENT = "event"
    PRODUCT = "product"
    CONCEPT = "concept"

class OSINTEntity(BaseModel):
    """Structured representation of an entity discovered during investigation"""
    name: str = Field(..., description="Primary name or identifier of the entity")
    entity_type: EntityType = Field(..., description="Type/category of the entity")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence in entity identification")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Additional entity properties")
    aliases: List[str] = Field(default_factory=list, description="Alternative names or identifiers")
    description: Optional[str] = Field(None, description="Brief description of the entity")
    discovered_in_source: Optional[str] = Field(None, description="Source URL where entity was first discovered")

class EntityRelationship(BaseModel):
    """Relationship between two entities"""
    entity1_name: str = Field(..., description="Name of first entity")
    entity2_name: str = Field(..., description="Name of second entity")
    relationship_type: str = Field(..., description="Type of relationship (e.g., 'employed_by', 'located_in')")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence in relationship")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Additional relationship properties")
    evidence_source: Optional[str] = Field(None, description="Source that provided evidence for this relationship")

# Investigation-related models
class InvestigationPhase(str, Enum):
    QUERY_ANALYSIS = "query_analysis"
    PLANNING = "planning" 
    RETRIEVING = "retrieving"
    ANALYZING = "analyzing"
    SYNTHESIZING = "synthesizing"
    JUDGING = "judging"
    COMPLETE = "complete"

class RetrievalTask(BaseModel):
    """A specific task for information retrieval"""
    task_description: str = Field(..., description="Description of what to retrieve")
    priority: int = Field(1, ge=1, le=5, description="Priority level (1=highest, 5=lowest)")
    source_types: List[str] = Field(default_factory=list, description="Preferred source types for this task")
    entities_of_interest: List[str] = Field(default_factory=list, description="Entities this task should focus on")
    search_terms: List[str] = Field(default_factory=list, description="Specific search terms to use")

class PivotStrategy(BaseModel):
    """Strategy for pivoting investigation in new directions"""
    pivot_description: str = Field(..., description="Description of the pivot strategy")
    new_entities: List[str] = Field(default_factory=list, description="New entities to investigate")
    search_angles: List[str] = Field(default_factory=list, description="New search approaches to try")
    priority: int = Field(1, ge=1, le=5, description="Priority of this pivot strategy")
    rationale: str = Field(..., description="Reasoning behind this pivot strategy")

class KeyFinding(BaseModel):
    """A significant finding from the investigation"""
    finding_text: str = Field(..., description="Description of the finding")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence in this finding")
    supporting_sources: List[str] = Field(default_factory=list, description="Sources that support this finding")
    entities_involved: List[str] = Field(default_factory=list, description="Entities related to this finding")
    significance: str = Field(..., description="Why this finding is significant")

# Report-related models
class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RiskAssessment(BaseModel):
    """Risk assessment for entities or situations"""
    overall_risk: RiskLevel = Field(..., description="Overall risk level")
    risk_factors: List[str] = Field(default_factory=list, description="Specific risk factors identified")
    risk_score: float = Field(0.0, ge=0.0, le=1.0, description="Numerical risk score")
    mitigation_suggestions: List[str] = Field(default_factory=list, description="Suggested risk mitigations")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence in risk assessment")

class InvestigationReport(BaseModel):
    """Complete investigation report"""
    executive_summary: str = Field(..., description="High-level summary for executives")
    key_findings: List[KeyFinding] = Field(default_factory=list, description="Primary investigation findings")
    entities_discovered: List[OSINTEntity] = Field(default_factory=list, description="All entities discovered")
    entity_relationships: List[EntityRelationship] = Field(default_factory=list, description="Relationships between entities")
    risk_assessment: RiskAssessment = Field(..., description="Overall risk assessment")
    source_summary: Dict[str, int] = Field(default_factory=dict, description="Summary of sources by type")
    recommendations: List[str] = Field(default_factory=list, description="Actionable recommendations")
    confidence_assessment: str = Field(..., description="Overall confidence in investigation results")
    limitations: List[str] = Field(default_factory=list, description="Known limitations of the investigation")
    next_steps: List[str] = Field(default_factory=list, description="Suggested next investigative steps")

class QualityMetrics(BaseModel):
    """Quality assessment metrics for investigation"""
    overall_score: float = Field(0.0, ge=0.0, le=100.0, description="Overall quality score (0-100)")
    completeness_score: float = Field(0.0, ge=0.0, le=100.0, description="Completeness of investigation")
    accuracy_score: float = Field(0.0, ge=0.0, le=100.0, description="Accuracy of findings")
    relevance_score: float = Field(0.0, ge=0.0, le=100.0, description="Relevance to original query")
    source_diversity_score: float = Field(0.0, ge=0.0, le=100.0, description="Diversity of sources used")
    credibility_score: float = Field(0.0, ge=0.0, le=100.0, description="Average credibility of sources")
    areas_for_improvement: List[str] = Field(default_factory=list, description="Specific areas needing improvement")
    strengths: List[str] = Field(default_factory=list, description="Strengths of the investigation")

# Agent response models for structured outputs
class QueryAnalysisResponse(BaseModel):
    """Structured response from Query Analysis Agent"""
    entities_identified: List[OSINTEntity] = Field(default_factory=list, description="Entities extracted from query")
    investigation_scope: str = Field(..., description="Scope and focus of investigation")
    primary_objectives: List[str] = Field(default_factory=list, description="Primary investigation objectives")
    entity_priorities: Dict[str, int] = Field(default_factory=dict, description="Priority ranking of entities")
    investigation_type: str = Field(..., description="Type of investigation (person, org, event, etc.)")

class PlanningResponse(BaseModel):
    """Structured response from Planning Agent"""
    retrieval_tasks: List[RetrievalTask] = Field(default_factory=list, description="Specific retrieval tasks to execute")
    search_strategy: str = Field(..., description="Overall search strategy description")
    source_priorities: List[str] = Field(default_factory=list, description="Prioritized list of source types")
    estimated_effort: int = Field(1, ge=1, le=5, description="Estimated effort level (1-5)")
    success_criteria: List[str] = Field(default_factory=list, description="Criteria for successful investigation")

class PivotAnalysisResponse(BaseModel):
    """Structured response from Pivot Analysis Agent"""
    pivot_strategies: List[PivotStrategy] = Field(default_factory=list, description="New investigation directions")
    relationships_discovered: List[EntityRelationship] = Field(default_factory=list, description="New entity relationships")
    key_findings: List[KeyFinding] = Field(default_factory=list, description="Significant findings from analysis")
    information_gaps: List[str] = Field(default_factory=list, description="Identified information gaps")
    recommended_next_actions: List[str] = Field(default_factory=list, description="Recommended next steps")

class SynthesisResponse(BaseModel):
    """Structured response from Synthesis Agent"""
    investigation_report: InvestigationReport = Field(..., description="Complete investigation report")
    source_analysis: str = Field(..., description="Analysis of sources used")
    confidence_factors: List[str] = Field(default_factory=list, description="Factors affecting confidence")
    validation_notes: List[str] = Field(default_factory=list, description="Cross-validation notes")

class JudgeResponse(BaseModel):
    """Structured response from Judge Agent"""
    quality_metrics: QualityMetrics = Field(..., description="Comprehensive quality assessment")
    approval_status: str = Field(..., description="Whether report meets quality standards")
    required_improvements: List[str] = Field(default_factory=list, description="Required improvements before approval")
    validation_results: Dict[str, bool] = Field(default_factory=dict, description="Validation check results")
    final_recommendations: List[str] = Field(default_factory=list, description="Final recommendations for report")

# Source credibility and metadata models
class SourceCredibilityFactors(BaseModel):
    """Factors contributing to source credibility assessment"""
    domain_authority: float = Field(0.0, ge=0.0, le=1.0, description="Authority of the domain")
    content_quality: float = Field(0.0, ge=0.0, le=1.0, description="Quality of content")
    publication_date: Optional[datetime] = Field(None, description="When content was published")
    author_credibility: float = Field(0.0, ge=0.0, le=1.0, description="Credibility of author if known")
    peer_validation: float = Field(0.0, ge=0.0, le=1.0, description="Level of peer validation")
    bias_indicators: List[str] = Field(default_factory=list, description="Potential bias indicators")

# Validation models for API endpoints
class InvestigationStartRequest(BaseModel):
    """Request to start a new investigation"""
    query: str = Field(..., min_length=3, description="Investigation query")
    max_retrievals: int = Field(12, ge=8, le=20, description="Maximum number of sources to retrieve")
    priority: str = Field("normal", description="Investigation priority level")
    constraints: List[str] = Field(default_factory=list, description="Investigation constraints")

class EntitySearchRequest(BaseModel):
    """Request to search for entities"""
    entity_name: str = Field(..., min_length=2, description="Name of entity to search for")
    entity_type: Optional[EntityType] = Field(None, description="Type of entity if known")
    search_depth: int = Field(2, ge=1, le=5, description="Depth of search (1-5)")

# Note: Pydantic v2 uses field validators instead of @validator decorator
# Confidence and priority validation is handled by Field constraints (ge, le)

# Export all models for easy importing
__all__ = [
    'EntityType', 'OSINTEntity', 'EntityRelationship',
    'InvestigationPhase', 'RetrievalTask', 'PivotStrategy', 'KeyFinding',
    'RiskLevel', 'RiskAssessment', 'InvestigationReport', 'QualityMetrics',
    'QueryAnalysisResponse', 'PlanningResponse', 'PivotAnalysisResponse', 
    'SynthesisResponse', 'JudgeResponse',
    'SourceCredibilityFactors', 'InvestigationStartRequest', 'EntitySearchRequest'
] 