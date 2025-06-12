"""
Integrated OSINT Graph with Data Layer
This module integrates the multi-agent OSINT system with persistent storage
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, TypedDict, Annotated
from datetime import datetime
import uuid
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint import MemorySaver
from langgraph.prebuilt import ToolNode
import logging

from src.agent.osint_state import (
    OSINTState, 
    EntityType, 
    InvestigationPhase,
    OSINTEntity,
    SourceInfo,
    PivotStrategy
)
from src.agent.osint_configuration import get_model_config, create_agent
from src.agent.osint_prompts import AGENT_PROMPTS
from src.database.osint_database import get_database, OSINTDatabase
from src.agent.osint_memory import OSINTMemoryManager, OSINTConversationMemory
from src.agent.osint_tools import osint_retrieval_manager, OSINTSource, SourceType
from src.agent.phoenix_integration import initialize_phoenix
from src.agent.osint_agents_structured import (
    structured_agents, query_analysis_structured, planning_structured,
    pivot_analysis_structured, synthesis_structured, judge_structured
)
from src.agent.osint_models import (
    OSINTEntity, EntityType, QueryAnalysisResponse, PlanningResponse,
    PivotAnalysisResponse, SynthesisResponse, JudgeResponse
)

logger = logging.getLogger(__name__)


class IntegratedOSINTGraph:
    """OSINT Graph with integrated data layer"""
    
    def __init__(self, investigation_id: Optional[str] = None):
        self.investigation_id = investigation_id or str(uuid.uuid4())
        self.db: Optional[OSINTDatabase] = None
        self.memory: Optional[OSINTMemoryManager] = None
        self.graph = None
        self.is_initialized = False
        
    async def initialize(self, query: str, user_id: str = "system"):
        """Initialize the graph with database connections"""
        # Enable Phoenix tracing if configured
        initialize_phoenix()
        # Get database instance
        self.db = await get_database()
        
        # Create or get investigation
        if not await self.db.get_investigation(self.investigation_id):
            self.investigation_id = await self.db.create_investigation(query, user_id)
        
        # Initialize memory manager
        self.memory = OSINTMemoryManager(self.investigation_id)
        await self.memory.initialize(query)
        
        # Build the graph
        self._build_graph()
        
        self.is_initialized = True
        logger.info(f"Initialized OSINT graph for investigation {self.investigation_id}")
    
    def _build_graph(self):
        """Build the integrated LangGraph workflow"""
        workflow = StateGraph(OSINTState)
        
        # Add nodes with data layer integration
        workflow.add_node("query_analysis", self._query_analysis_with_memory)
        workflow.add_node("planning", self._planning_with_memory)
        workflow.add_node("retrieval", self._retrieval_with_memory)
        workflow.add_node("pivot_analysis", self._pivot_analysis_with_memory)
        workflow.add_node("synthesis", self._synthesis_with_memory)
        workflow.add_node("judge", self._judge_with_memory)
        
        # Add edges
        workflow.set_entry_point("query_analysis")
        workflow.add_edge("query_analysis", "planning")
        workflow.add_edge("planning", "retrieval")
        workflow.add_edge("retrieval", "pivot_analysis")
        
        # Conditional edges
        workflow.add_conditional_edges(
            "pivot_analysis",
            self._should_continue_investigation,
            {
                "continue": "planning",
                "synthesize": "synthesis"
            }
        )
        
        workflow.add_edge("synthesis", "judge")
        workflow.add_edge("judge", END)
        
        # Compile with checkpointer
        checkpointer = MemorySaver()
        self.graph = workflow.compile(checkpointer=checkpointer)
    
    async def _query_analysis_with_memory(self, state: OSINTState) -> OSINTState:
        """Query analysis with entity persistence using structured output"""
        logger.info("Starting structured query analysis")
        
        # Get structured response from query analysis agent
        analysis_response: QueryAnalysisResponse = await query_analysis_structured(
            query=state["investigation_query"],
            agents=structured_agents
        )
        
        # Store entities in database
        stored_entities = []
        for entity in analysis_response.entities_identified:
            try:
                entity_id = await self.memory.remember_entity(
                    entity_type=entity.entity_type.value,
                    name=entity.name,
                    attributes=entity.attributes,
                    confidence=entity.confidence
                )
                # Create entity dict for state (maintaining compatibility)
                entity_dict = {
                    "id": entity_id,
                    "name": entity.name,
                    "type": entity.entity_type.value,
                    "confidence": entity.confidence,
                    "attributes": entity.attributes,
                    "description": entity.description
                }
                stored_entities.append(entity_dict)
                logger.info(f"Stored entity: {entity.name} ({entity.entity_type})")
            except Exception as e:
                logger.warning(f"Failed to store entity {entity.name}: {e}")
        
        # Update state
        state["entities"] = stored_entities
        state["phase"] = InvestigationPhase.PLANNING
        state["investigation_scope"] = analysis_response.investigation_scope
        state["primary_objectives"] = analysis_response.primary_objectives
        
        # Create a mock message for compatibility
        from langchain_core.messages import HumanMessage
        mock_message = HumanMessage(content=f"Analysis complete: {analysis_response.investigation_scope}")
        state["messages"].append(mock_message)
        
        # Publish structured event for real-time updates
        await self.db.publish_event(
            f"investigation:{self.investigation_id}",
            {
                "type": "query_analysis_structured",
                "entities": [e for e in stored_entities],
                "investigation_scope": analysis_response.investigation_scope,
                "primary_objectives": analysis_response.primary_objectives,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        logger.info(f"Query analysis complete: identified {len(stored_entities)} entities")
        return state
    
    async def _planning_with_memory(self, state: OSINTState) -> OSINTState:
        """Planning with task persistence using structured output"""
        logger.info("Starting structured planning")
        
        # Convert entities to OSINTEntity objects for structured planning
        osint_entities = []
        for entity_dict in state["entities"]:
            try:
                entity = OSINTEntity(
                    name=entity_dict["name"],
                    entity_type=EntityType(entity_dict["type"]),
                    confidence=entity_dict.get("confidence", 0.7),
                    attributes=entity_dict.get("attributes", {}),
                    description=entity_dict.get("description")
                )
                osint_entities.append(entity)
            except Exception as e:
                logger.warning(f"Failed to convert entity {entity_dict.get('name')}: {e}")
        
        # Get structured response from planning agent
        planning_response: PlanningResponse = await planning_structured(
            query=state["investigation_query"],
            entities=osint_entities,
            agents=structured_agents
        )
        
        # Convert structured tasks to state format
        task_strings = []
        for task in planning_response.retrieval_tasks:
            task_string = f"{task.task_description} (Priority: {task.priority})"
            task_strings.append(task_string)
        
        # Update state
        state["retrieval_tasks"].extend(task_strings)
        state["search_strategy"] = planning_response.search_strategy
        state["source_priorities"] = planning_response.source_priorities
        state["success_criteria"] = planning_response.success_criteria
        state["estimated_effort"] = planning_response.estimated_effort
        
        # Create compatibility message
        from langchain_core.messages import HumanMessage
        mock_message = HumanMessage(content=f"Planning complete: {planning_response.search_strategy}")
        state["messages"].append(mock_message)
        
        # Update investigation status
        await self.db.update_investigation_status(self.investigation_id, "retrieving")
        
        # Publish structured planning event
        await self.db.publish_event(
            f"investigation:{self.investigation_id}",
            {
                "type": "planning_structured",
                "retrieval_tasks": len(planning_response.retrieval_tasks),
                "search_strategy": planning_response.search_strategy,
                "estimated_effort": planning_response.estimated_effort,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        logger.info(f"Planning complete: {len(planning_response.retrieval_tasks)} tasks created")
        return state
    
    async def _retrieval_with_memory(self, state: OSINTState) -> OSINTState:
        """Multi-source OSINT retrieval with source persistence"""
        logger.info(f"Starting OSINT retrieval for {len(state['retrieval_tasks'])} tasks")
        
        # Get primary entity for focused retrieval
        primary_entity = state["entities"][0].name if state["entities"] else state["investigation_query"]
        
        # Execute real OSINT retrieval across multiple sources
        try:
            osint_sources = await osint_retrieval_manager.retrieve_from_multiple_sources(
                query=state["investigation_query"],
                entity_name=primary_entity,
                max_sources=state["max_retrievals"]
            )
            
            logger.info(f"Retrieved {len(osint_sources)} sources from OSINT tools")
            
            # Convert OSINTSource objects to state format and store in database
            sources_processed = []
            for osint_source in osint_sources:
                try:
                    source_data = {
                        "url": osint_source.url,
                        "type": osint_source.source_type.value,
                        "title": osint_source.title,
                        "content": osint_source.content,
                        "credibility": osint_source.credibility_score,
                        "metadata": osint_source.metadata,
                        "retrieved_at": osint_source.retrieved_at.isoformat(),
                        "entities_mentioned": osint_source.entities_mentioned or []
                    }
                    
                    # Store source in memory/database
                    source_id = await self.memory.remember_source(
                        url=osint_source.url,
                        source_type=osint_source.source_type.value,
                        title=osint_source.title,
                        content=osint_source.content,
                        metadata=osint_source.metadata,
                        credibility=osint_source.credibility_score
                    )
                    
                    source_data["id"] = source_id
                    sources_processed.append(source_data)
                    
                    # Extract and store entities from source content
                    await self._extract_entities_from_source(source_data, source_id)
                    
                except Exception as e:
                    logger.error(f"Error processing source {osint_source.url}: {e}")
                    continue
            
            # Update state
            state["sources"].extend(sources_processed)
            state["phase"] = InvestigationPhase.ANALYZING
            state["retrieval_count"] = len(sources_processed)
            
            # Publish progress event with source breakdown
            source_types = {}
            for source in sources_processed:
                source_type = source["type"]
                source_types[source_type] = source_types.get(source_type, 0) + 1
            
            await self.db.publish_event(
                f"investigation:{self.investigation_id}",
                {
                    "type": "retrieval_complete",
                    "sources_found": len(sources_processed),
                    "source_breakdown": source_types,
                    "avg_credibility": sum(s["credibility"] for s in sources_processed) / len(sources_processed) if sources_processed else 0,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Stored {len(sources_processed)} sources in investigation memory")
            
        except Exception as e:
            logger.error(f"OSINT retrieval failed: {e}")
            # Fallback to minimal mock data if retrieval completely fails
            mock_source = {
                "url": "https://example.com/mock",
                "type": "web",
                "title": f"Mock source for {primary_entity}",
                "content": f"Investigation information for {primary_entity} from mock source.",
                "credibility": 0.3,
                "metadata": {"source": "fallback_mock"},
                "id": "mock_001"
            }
            state["sources"].append(mock_source)
            state["retrieval_count"] = 1
        
        return state
    

    
    async def _extract_entities_from_source(self, source: Dict, source_id: str):
        """Extract and store entities found in a source"""
        content = source.get("content", "")
        title = source.get("title", "")
        
        if not content:
            return
        
        # Look for known entities in content
        entities_found = []
        
        # Check for entities already known to the investigation
        all_entities = await self.memory.get_all_entities()
        for entity in all_entities:
            entity_name = entity.get("name", "").lower()
            if entity_name and (entity_name in content.lower() or entity_name in title.lower()):
                entities_found.append(entity)
                
                # Create evidence link
                try:
                    await self.db.create_evidence(
                        entity_id=entity.get("entity_id"),
                        source_id=source_id,
                        evidence_type="mention",
                        content=f"Entity '{entity['name']}' mentioned in source",
                        confidence_score=0.8
                    )
                except Exception as e:
                    logger.warning(f"Could not create evidence link: {e}")
        
        # Extract new potential entities using simple pattern matching
        import re
        
        # Person names (simple pattern - capitalized words)
        person_pattern = r'\b[A-Z][a-z]+ [A-Z][a-z]+(?:\s[A-Z][a-z]+)?\b'
        potential_persons = re.findall(person_pattern, content)
        
        # Organizations (look for Corp, Inc, LLC, University, etc.)
        org_pattern = r'\b[A-Z][a-zA-Z\s]+(Corp|Inc|LLC|Ltd|University|Institute|Company|Organization|Agency)\b'
        potential_orgs = re.findall(org_pattern, content)
        
        # Locations (look for common location indicators)
        location_pattern = r'\b[A-Z][a-zA-Z\s]+(City|County|State|Country|Province|Region)\b'
        potential_locations = re.findall(location_pattern, content)
        
        # Store newly discovered entities
        for person_match in potential_persons[:3]:  # Limit to avoid noise
            if len(person_match.strip()) > 3:  # Avoid short matches
                try:
                    await self.memory.remember_entity(
                        entity_type="person",
                        name=person_match.strip(),
                        attributes={"discovered_in": source["url"]},
                        confidence=0.6
                    )
                except Exception as e:
                    logger.debug(f"Could not store potential person entity {person_match}: {e}")
        
        for org_match in potential_orgs[:2]:  # Limit organizations
            if len(org_match[0].strip()) > 5:
                try:
                    await self.memory.remember_entity(
                        entity_type="organization",
                        name=org_match[0].strip(),
                        attributes={"discovered_in": source["url"]},
                        confidence=0.6
                    )
                except Exception as e:
                    logger.debug(f"Could not store potential org entity {org_match}: {e}")
        
        logger.debug(f"Extracted {len(entities_found)} known entities and discovered {len(potential_persons + potential_orgs)} new entities from source")
    
    async def _pivot_analysis_with_memory(self, state: OSINTState) -> OSINTState:
        """Pivot analysis with relationship discovery using structured output"""
        logger.info("Starting structured pivot analysis")
        
        # Get investigation summary and prepare findings
        summary = await self.memory.get_investigation_summary()
        current_findings = [
            f"Entities found: {summary.get('entity_count', 0)}",
            f"Sources gathered: {summary.get('source_count', 0)}",
            f"Average credibility: {summary.get('avg_credibility', 0):.2f}"
        ]
        
        # Add key findings from summary
        if summary.get('key_findings'):
            current_findings.extend(summary['key_findings'][:3])  # Limit to top 3
        
        # Get structured response from pivot analysis agent
        pivot_response: PivotAnalysisResponse = await pivot_analysis_structured(
            query=state["investigation_query"],
            sources=state["sources"],
            findings=current_findings,
            agents=structured_agents
        )
        
        # Store relationships discovered
        for relationship in pivot_response.relationships_discovered:
            try:
                await self.memory.remember_relationship(
                    entity1_name=relationship.entity1_name,
                    entity2_name=relationship.entity2_name,
                    relationship_type=relationship.relationship_type,
                    attributes=relationship.attributes,
                    confidence=relationship.confidence
                )
                logger.info(f"Stored relationship: {relationship.entity1_name} -> {relationship.entity2_name}")
            except Exception as e:
                logger.warning(f"Failed to store relationship: {e}")
        
        # Store key findings
        for finding in pivot_response.key_findings:
            try:
                await self.memory.remember_finding(finding.finding_text, finding.confidence)
                logger.info(f"Stored finding: {finding.finding_text[:50]}...")
            except Exception as e:
                logger.warning(f"Failed to store finding: {e}")
        
        # Convert pivot strategies to state format
        pivot_strings = []
        for strategy in pivot_response.pivot_strategies:
            pivot_string = f"{strategy.pivot_description} (Priority: {strategy.priority})"
            pivot_strings.append(pivot_string)
        
        # Update state
        state["pivot_strategies"].extend(pivot_strings)
        state["information_gaps"] = pivot_response.information_gaps
        state["recommended_actions"] = pivot_response.recommended_next_actions
        state["investigation_depth"] += 1
        
        # Create compatibility message
        from langchain_core.messages import HumanMessage
        mock_message = HumanMessage(content=f"Pivot analysis complete: {len(pivot_response.pivot_strategies)} new strategies")
        state["messages"].append(mock_message)
        
        # Publish structured pivot event
        await self.db.publish_event(
            f"investigation:{self.investigation_id}",
            {
                "type": "pivot_analysis_structured",
                "pivot_strategies": len(pivot_response.pivot_strategies),
                "relationships_found": len(pivot_response.relationships_discovered),
                "key_findings": len(pivot_response.key_findings),
                "information_gaps": len(pivot_response.information_gaps),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        logger.info(f"Pivot analysis complete: {len(pivot_response.pivot_strategies)} strategies, {len(pivot_response.relationships_discovered)} relationships")
        return state
    
    def _should_continue_investigation(self, state: OSINTState) -> str:
        """Decide whether to continue investigation"""
        # Check termination conditions
        if state["investigation_depth"] >= 3:
            return "synthesize"
        
        if state["retrieval_count"] >= state["max_retrievals"]:
            return "synthesize"
        
        if len(state["pivot_strategies"]) == 0:
            return "synthesize"
        
        # Check if we have enough information
        if len(state["sources"]) >= state["max_retrievals"] * 0.8:
            return "synthesize"
        
        return "continue"
    
    async def _synthesis_with_memory(self, state: OSINTState) -> OSINTState:
        """Synthesis with report generation using structured output"""
        logger.info("Starting structured synthesis")
        
        # Get full investigation context
        summary = await self.memory.get_investigation_summary()
        
        # Convert state entities to OSINTEntity objects
        osint_entities = []
        for entity_dict in state["entities"]:
            try:
                entity = OSINTEntity(
                    name=entity_dict["name"],
                    entity_type=EntityType(entity_dict["type"]),
                    confidence=entity_dict.get("confidence", 0.7),
                    attributes=entity_dict.get("attributes", {}),
                    description=entity_dict.get("description")
                )
                osint_entities.append(entity)
            except Exception as e:
                logger.warning(f"Failed to convert entity for synthesis: {e}")
        
        # Prepare findings for synthesis
        all_findings = []
        if summary.get('key_findings'):
            for finding_text in summary['key_findings']:
                all_findings.append({
                    "text": finding_text,
                    "confidence": 0.7,
                    "source": "investigation_memory"
                })
        
        # Get structured response from synthesis agent
        synthesis_response: SynthesisResponse = await synthesis_structured(
            query=state["investigation_query"],
            all_findings=all_findings,
            entities=osint_entities,
            sources=state["sources"],
            agents=structured_agents
        )
        
        # Convert structured report to state format
        report_dict = {
            "executive_summary": synthesis_response.investigation_report.executive_summary,
            "key_findings": [finding.dict() for finding in synthesis_response.investigation_report.key_findings],
            "entities": [entity.dict() for entity in synthesis_response.investigation_report.entities_discovered],
            "entity_relationships": [rel.dict() for rel in synthesis_response.investigation_report.entity_relationships],
            "risk_assessment": synthesis_response.investigation_report.risk_assessment.dict(),
            "source_summary": synthesis_response.investigation_report.source_summary,
            "recommendations": synthesis_response.investigation_report.recommendations,
            "confidence_assessment": synthesis_response.investigation_report.confidence_assessment,
            "limitations": synthesis_response.investigation_report.limitations,
            "next_steps": synthesis_response.investigation_report.next_steps
        }
        
        # Update state
        state["report"] = report_dict
        state["source_analysis"] = synthesis_response.source_analysis
        state["confidence_factors"] = synthesis_response.confidence_factors
        
        # Create compatibility message
        from langchain_core.messages import HumanMessage
        mock_message = HumanMessage(content=f"Synthesis complete: {synthesis_response.investigation_report.executive_summary[:100]}...")
        state["messages"].append(mock_message)
        
        # Store report in database
        await self.db.update_investigation_status(
            self.investigation_id, 
            "complete",
            report_data=report_dict
        )
        
        # Publish structured report event
        await self.db.publish_event(
            f"investigation:{self.investigation_id}",
            {
                "type": "report_generation_structured",
                "report_summary": {
                    "key_findings_count": len(synthesis_response.investigation_report.key_findings),
                    "entities_count": len(synthesis_response.investigation_report.entities_discovered),
                    "risk_level": synthesis_response.investigation_report.risk_assessment.overall_risk,
                    "recommendations_count": len(synthesis_response.investigation_report.recommendations)
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        logger.info(f"Synthesis complete: {len(synthesis_response.investigation_report.key_findings)} findings, risk level: {synthesis_response.investigation_report.risk_assessment.overall_risk}")
        return state
    
    async def _judge_with_memory(self, state: OSINTState) -> OSINTState:
        """Judge with quality assessment using structured output"""
        logger.info("Starting structured quality assessment")
        
        # Convert report dict to InvestigationReport object for structured assessment
        try:
            from src.agent.osint_models import InvestigationReport, RiskAssessment, RiskLevel, KeyFinding
            
            # Convert key findings
            key_findings = []
            for finding_dict in state["report"].get("key_findings", []):
                if isinstance(finding_dict, dict):
                    key_finding = KeyFinding(**finding_dict)
                    key_findings.append(key_finding)
            
            # Convert risk assessment
            risk_dict = state["report"].get("risk_assessment", {})
            if isinstance(risk_dict, dict):
                risk_assessment = RiskAssessment(**risk_dict)
            else:
                risk_assessment = RiskAssessment(
                    overall_risk=RiskLevel.LOW,
                    risk_factors=[],
                    risk_score=0.1,
                    mitigation_suggestions=[],
                    confidence=0.7
                )
            
            # Create investigation report object
            investigation_report = InvestigationReport(
                executive_summary=state["report"].get("executive_summary", ""),
                key_findings=key_findings,
                entities_discovered=[],  # Simplified for assessment
                entity_relationships=[],
                risk_assessment=risk_assessment,
                source_summary=state["report"].get("source_summary", {}),
                recommendations=state["report"].get("recommendations", []),
                confidence_assessment=state["report"].get("confidence_assessment", ""),
                limitations=state["report"].get("limitations", []),
                next_steps=state["report"].get("next_steps", [])
            )
            
        except Exception as e:
            logger.warning(f"Failed to convert report for assessment: {e}")
            # Create minimal report for assessment
            from src.agent.osint_models import InvestigationReport, RiskAssessment, RiskLevel
            investigation_report = InvestigationReport(
                executive_summary=state["report"].get("executive_summary", "Investigation completed"),
                key_findings=[],
                entities_discovered=[],
                entity_relationships=[],
                risk_assessment=RiskAssessment(
                    overall_risk=RiskLevel.LOW,
                    risk_factors=[],
                    risk_score=0.1,
                    mitigation_suggestions=[],
                    confidence=0.7
                ),
                source_summary=state["report"].get("source_summary", {}),
                recommendations=state["report"].get("recommendations", []),
                confidence_assessment="Assessment completed",
                limitations=[],
                next_steps=[]
            )
        
        # Prepare investigation summary for judge
        investigation_summary = {
            "sources_retrieved": len(state["sources"]),
            "investigation_depth": state["investigation_depth"],
            "entities_found": len(state["entities"]),
            "avg_credibility": sum(s.get("credibility", 0) for s in state["sources"]) / len(state["sources"]) if state["sources"] else 0
        }
        
        # Get structured response from judge agent
        judge_response: JudgeResponse = await judge_structured(
            report=investigation_report,
            investigation_summary=investigation_summary,
            agents=structured_agents
        )
        
        # Convert structured quality metrics to state format
        quality_dict = {
            "overall_score": judge_response.quality_metrics.overall_score,
            "completeness_score": judge_response.quality_metrics.completeness_score,
            "accuracy_score": judge_response.quality_metrics.accuracy_score,
            "relevance_score": judge_response.quality_metrics.relevance_score,
            "source_diversity_score": judge_response.quality_metrics.source_diversity_score,
            "credibility_score": judge_response.quality_metrics.credibility_score,
            "areas_for_improvement": judge_response.quality_metrics.areas_for_improvement,
            "strengths": judge_response.quality_metrics.strengths
        }
        
        # Update state
        state["quality_score"] = quality_dict
        state["approval_status"] = judge_response.approval_status
        state["required_improvements"] = judge_response.required_improvements
        state["final_recommendations"] = judge_response.final_recommendations
        
        # Create compatibility message
        from langchain_core.messages import HumanMessage
        mock_message = HumanMessage(content=f"Quality assessment complete: {judge_response.approval_status} (Score: {judge_response.quality_metrics.overall_score:.1f})")
        state["messages"].append(mock_message)
        
        # Final checkpoint
        await self.memory.checkpoint()
        
        # Publish structured completion event
        await self.db.publish_event(
            f"investigation:{self.investigation_id}",
            {
                "type": "quality_assessment_structured",
                "approval_status": judge_response.approval_status,
                "overall_score": judge_response.quality_metrics.overall_score,
                "quality_breakdown": {
                    "completeness": judge_response.quality_metrics.completeness_score,
                    "accuracy": judge_response.quality_metrics.accuracy_score,
                    "relevance": judge_response.quality_metrics.relevance_score,
                    "source_diversity": judge_response.quality_metrics.source_diversity_score,
                    "credibility": judge_response.quality_metrics.credibility_score
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        logger.info(f"Quality assessment complete: {judge_response.approval_status}, Overall Score: {judge_response.quality_metrics.overall_score:.1f}")
        return state
    
    # Note: Manual parsing methods removed - now using structured outputs with instructor/pydantic
    
    async def run_investigation(self, query: str, config: Optional[Dict] = None) -> Dict:
        """Run a complete investigation"""
        if not self.is_initialized:
            await self.initialize(query)
        
        # Initial state
        initial_state = OSINTState(
            investigation_query=query,
            messages=[],
            entities=[],
            sources=[],
            retrieval_tasks=[],
            search_queries=[],
            pivot_strategies=[],
            phase=InvestigationPhase.QUERY_ANALYSIS,
            investigation_depth=0,
            retrieval_count=0,
            max_retrievals=config.get("max_retrievals", 12) if config else 12,
            confidence_threshold=0.7,
            report={},
            quality_score={}
        )
        
        # Run the graph
        final_state = await self.graph.ainvoke(
            initial_state,
            config={"configurable": {"thread_id": self.investigation_id}}
        )
        
        return {
            "investigation_id": self.investigation_id,
            "report": final_state["report"],
            "quality_score": final_state["quality_score"],
            "entities_found": len(final_state["entities"]),
            "sources_used": len(final_state["sources"])
        }


# Factory function
async def create_integrated_osint_graph(
    query: str, 
    investigation_id: Optional[str] = None,
    user_id: str = "system"
) -> IntegratedOSINTGraph:
    """Create and initialize an integrated OSINT graph"""
    graph = IntegratedOSINTGraph(investigation_id)
    await graph.initialize(query, user_id)
    return graph 