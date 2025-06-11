from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

from langgraph.graph import add_messages
from typing_extensions import Annotated
import operator


class EntityType(str, Enum):
    PERSON = "PERSON"
    ORGANIZATION = "ORGANIZATION"
    LOCATION = "LOCATION"
    EVENT = "EVENT"
    IDENTIFIER = "IDENTIFIER"


class InvestigationPhase(str, Enum):
    INITIAL = "INITIAL"
    EXPANSION = "EXPANSION"
    DEEP_DIVE = "DEEP_DIVE"
    SYNTHESIS = "SYNTHESIS"


class SourceReliabilityTier(int, Enum):
    TIER_1 = 1  # Highest: Government databases, official records
    TIER_2 = 2  # High: Academic publications, business registries
    TIER_3 = 3  # Medium: Social media profiles, forums
    TIER_4 = 4  # Low: Unverified sources


class OSINTEntity(TypedDict):
    name: str
    type: EntityType
    aliases: List[str]
    context: str
    confidence: float
    attributes: Dict[str, Any]


class InvestigationScope(TypedDict):
    primary_objective: str
    secondary_objectives: List[str]
    temporal_range: Dict[str, datetime]
    geographic_scope: List[str]
    depth_level: str  # SURFACE|STANDARD|DEEP|EXHAUSTIVE


class OSINTTask(TypedDict):
    task_id: str
    task_type: str  # SEARCH|VERIFY|CORRELATE|ANALYZE
    target_entity: str
    sources: List[Dict[str, Any]]
    dependencies: List[str]
    parallel_group: str
    status: str  # PENDING|RUNNING|COMPLETED|FAILED
    results: Optional[Dict[str, Any]]


class DataPoint(TypedDict):
    source_url: str
    source_type: str
    credibility_score: float
    extraction_timestamp: datetime
    title: str
    snippet: str
    full_content: str
    metadata: Dict[str, Any]
    extracted_entities: List[OSINTEntity]
    key_facts: List[str]
    relevance_explanation: str


class OSINTState(TypedDict):
    # Core investigation data
    messages: Annotated[list, add_messages]
    query: str
    investigation_id: str
    investigation_phase: InvestigationPhase
    
    # Entity and scope management
    entities: List[OSINTEntity]
    investigation_scope: InvestigationScope
    
    # Task and retrieval management
    search_plan: List[OSINTTask]
    completed_tasks: Annotated[List[OSINTTask], operator.add]
    pending_tasks: List[OSINTTask]
    raw_data: Annotated[List[DataPoint], operator.add]
    
    # Analysis results
    analysis_results: Dict[str, Any]
    pivot_suggestions: Annotated[List[str], operator.add]
    relationship_graph: Dict[str, Any]
    timeline_events: List[Dict[str, Any]]
    
    # Memory and context
    memory_context: Dict[str, Any]
    source_credibility_map: Dict[str, float]
    
    # Reporting
    final_report: str
    confidence_scores: Dict[str, float]
    risk_assessment: Dict[str, Any]
    
    # Control flow
    research_loop_count: int
    max_research_loops: int
    minimum_retrievals: int
    retrievals_completed: int


class QueryAnalysisOutput(TypedDict):
    entities: List[OSINTEntity]
    investigation_scope: InvestigationScope
    refined_query: Dict[str, Any]
    risk_indicators: Dict[str, Any]
    recommended_sources: List[str]
    estimated_complexity: str


class OrchestrationOutput(TypedDict):
    investigation_plan: Dict[str, Any]
    resource_allocation: Dict[str, Any]
    success_criteria: Dict[str, Any]


class PivotAnalysisOutput(TypedDict):
    pattern_analysis: Dict[str, Any]
    relationship_insights: Dict[str, Any]
    intelligence_gaps: List[Dict[str, Any]]
    pivot_recommendations: List[Dict[str, Any]]
    contradiction_analysis: List[Dict[str, Any]]
    investigation_assessment: Dict[str, Any]


class SynthesisOutput(TypedDict):
    intelligence_report: Dict[str, Any]
    report_metadata: Dict[str, Any]


class JudgeOutput(TypedDict):
    quality_assessment: Dict[str, Any]
    detailed_evaluation: Dict[str, Any]
    critical_issues: List[Dict[str, Any]]
    improvement_recommendations: List[Dict[str, Any]]
    certification_decision: Dict[str, Any]


@dataclass(kw_only=True)
class OSINTReportOutput:
    investigation_id: str
    final_report: str = field(default="")
    executive_summary: str = field(default="")
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    total_sources: int = field(default=0)
    investigation_duration: float = field(default=0.0) 