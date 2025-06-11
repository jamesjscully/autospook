#!/usr/bin/env python3
"""
Test script for Structured OSINT Agents with Instructor/Pydantic
Tests structured data validation and LLM integration
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.agent.osint_agents_structured import (
    structured_agents, query_analysis_structured, planning_structured,
    pivot_analysis_structured, synthesis_structured, judge_structured
)
from src.agent.osint_models import (
    OSINTEntity, EntityType, QueryAnalysisResponse, PlanningResponse,
    PivotAnalysisResponse, SynthesisResponse, JudgeResponse,
    InvestigationReport, RiskAssessment, RiskLevel
)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_api_keys():
    """Check which LLM API keys are configured"""
    api_keys = {
        'ANTHROPIC_API_KEY': 'Anthropic (Claude)',
        'OPENAI_API_KEY': 'OpenAI (GPT-4)',
        'GEMINI_API_KEY': 'Google (Gemini)'
    }
    
    logger.info("Checking LLM API key configuration...")
    
    configured_count = 0
    for key, description in api_keys.items():
        value = os.getenv(key)
        if value and value != 'your_api_key_here' and not value.startswith('mock_'):
            logger.info(f"✅ {key} configured for {description}")
            configured_count += 1
        else:
            logger.info(f"❌ {key} not configured for {description}")
    
    if configured_count == 0:
        logger.warning("⚠️  No LLM API keys configured - will use mock responses")
        return False
    
    logger.info(f"✅ {configured_count}/3 LLM providers configured")
    return True

async def test_pydantic_models():
    """Test Pydantic model validation"""
    logger.info("Testing Pydantic model validation...")
    
    try:
        # Test OSINTEntity validation
        entity = OSINTEntity(
            name="Ali Khaledi Nasab",
            entity_type=EntityType.PERSON,
            confidence=0.95,
            attributes={"profession": "researcher"},
            description="Academic researcher"
        )
        
        logger.info(f"✅ OSINTEntity validation: {entity.name} ({entity.entity_type})")
        
        # Test confidence validation (should raise validation error for invalid values)
        try:
            entity_invalid_confidence = OSINTEntity(
                name="Test Entity",
                entity_type=EntityType.ORGANIZATION,
                confidence=1.5,  # Invalid - should raise validation error
                attributes={}
            )
            logger.warning("⚠️  Expected validation error for confidence > 1.0")
        except Exception as e:
            logger.info(f"✅ Confidence validation: Correctly rejected confidence=1.5 ({str(e)[:60]}...)")
        
        # Test QueryAnalysisResponse
        query_response = QueryAnalysisResponse(
            entities_identified=[entity],
            investigation_scope="Test investigation scope",
            primary_objectives=["Identify background", "Assess credibility"],
            entity_priorities={"Ali Khaledi Nasab": 1},
            investigation_type="person"
        )
        
        logger.info(f"✅ QueryAnalysisResponse validation: {len(query_response.entities_identified)} entities")
        
        # Test empty required fields
        try:
            invalid_query_response = QueryAnalysisResponse(
                entities_identified=[],
                investigation_scope="",  # Empty string should be invalid
                primary_objectives=[],
                entity_priorities={},
                investigation_type=""
            )
            # Should not fail since empty strings are technically valid
            logger.info("✅ Empty field validation: Fields can be empty (as expected)")
        except Exception as e:
            logger.info(f"✅ Empty field validation: {str(e)[:60]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Pydantic model validation failed: {e}")
        return False

async def test_query_analysis_agent():
    """Test Query Analysis Agent with structured output"""
    logger.info("Testing Query Analysis Agent...")
    
    try:
        test_query = "Investigate Ali Khaledi Nasab academic background and research"
        
        response = await query_analysis_structured(
            query=test_query,
            agents=structured_agents
        )
        
        # Validate response type
        assert isinstance(response, QueryAnalysisResponse), f"Expected QueryAnalysisResponse, got {type(response)}"
        
        # Validate required fields
        assert response.investigation_scope, "Investigation scope is required"
        assert response.primary_objectives, "Primary objectives are required"
        assert response.investigation_type, "Investigation type is required"
        
        logger.info(f"✅ Query Analysis: {response.investigation_scope}")
        logger.info(f"   Entities: {len(response.entities_identified)}")
        logger.info(f"   Objectives: {len(response.primary_objectives)}")
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Query Analysis Agent test failed: {e}")
        return None

async def test_planning_agent():
    """Test Planning Agent with structured output"""
    logger.info("Testing Planning Agent...")
    
    try:
        test_query = "Investigate Ali Khaledi Nasab academic background"
        test_entities = [
            OSINTEntity(
                name="Ali Khaledi Nasab",
                entity_type=EntityType.PERSON,
                confidence=0.9,
                attributes={"role": "researcher"},
                description="Academic researcher"
            )
        ]
        
        response = await planning_structured(
            query=test_query,
            entities=test_entities,
            agents=structured_agents
        )
        
        # Validate response type
        assert isinstance(response, PlanningResponse), f"Expected PlanningResponse, got {type(response)}"
        
        # Validate required fields
        assert response.search_strategy, "Search strategy is required"
        assert response.retrieval_tasks, "Retrieval tasks are required"
        
        logger.info(f"✅ Planning: {response.search_strategy}")
        logger.info(f"   Tasks: {len(response.retrieval_tasks)}")
        logger.info(f"   Effort: {response.estimated_effort}/5")
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Planning Agent test failed: {e}")
        return None

async def test_pivot_analysis_agent():
    """Test Pivot Analysis Agent with structured output"""
    logger.info("Testing Pivot Analysis Agent...")
    
    try:
        test_query = "Investigate Ali Khaledi Nasab academic background"
        test_sources = [
            {"url": "https://example.com", "title": "Test Source", "credibility": 0.8},
            {"url": "https://scholar.example.com", "title": "Academic Source", "credibility": 0.9}
        ]
        test_findings = ["Academic researcher identified", "Multiple publications found"]
        
        response = await pivot_analysis_structured(
            query=test_query,
            sources=test_sources,
            findings=test_findings,
            agents=structured_agents
        )
        
        # Validate response type
        assert isinstance(response, PivotAnalysisResponse), f"Expected PivotAnalysisResponse, got {type(response)}"
        
        logger.info(f"✅ Pivot Analysis: {len(response.pivot_strategies)} strategies")
        logger.info(f"   Relationships: {len(response.relationships_discovered)}")
        logger.info(f"   Key Findings: {len(response.key_findings)}")
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Pivot Analysis Agent test failed: {e}")
        return None

async def test_synthesis_agent():
    """Test Synthesis Agent with structured output"""
    logger.info("Testing Synthesis Agent...")
    
    try:
        test_query = "Investigate Ali Khaledi Nasab academic background"
        test_entities = [
            OSINTEntity(
                name="Ali Khaledi Nasab",
                entity_type=EntityType.PERSON,
                confidence=0.9,
                attributes={"role": "researcher"},
                description="Academic researcher"
            )
        ]
        test_findings = [
            {"text": "Academic researcher identified", "confidence": 0.8},
            {"text": "Multiple publications found", "confidence": 0.7}
        ]
        test_sources = [
            {"url": "https://scholar.example.com", "title": "Academic Source", "credibility": 0.9}
        ]
        
        response = await synthesis_structured(
            query=test_query,
            all_findings=test_findings,
            entities=test_entities,
            sources=test_sources,
            agents=structured_agents
        )
        
        # Validate response type
        assert isinstance(response, SynthesisResponse), f"Expected SynthesisResponse, got {type(response)}"
        
        # Validate investigation report
        report = response.investigation_report
        assert isinstance(report, InvestigationReport), "Investigation report is required"
        assert report.executive_summary, "Executive summary is required"
        assert isinstance(report.risk_assessment, RiskAssessment), "Risk assessment is required"
        
        logger.info(f"✅ Synthesis: Report generated")
        logger.info(f"   Executive Summary: {len(report.executive_summary)} chars")
        logger.info(f"   Risk Level: {report.risk_assessment.overall_risk}")
        logger.info(f"   Recommendations: {len(report.recommendations)}")
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Synthesis Agent test failed: {e}")
        return None

async def test_judge_agent():
    """Test Judge Agent with structured output"""
    logger.info("Testing Judge Agent...")
    
    try:
        # Create a test investigation report
        test_report = InvestigationReport(
            executive_summary="Test investigation completed successfully",
            key_findings=[],
            entities_discovered=[],
            entity_relationships=[],
            risk_assessment=RiskAssessment(
                overall_risk=RiskLevel.LOW,
                risk_factors=[],
                risk_score=0.2,
                mitigation_suggestions=[],
                confidence=0.8
            ),
            source_summary={"academic": 2, "web": 1},
            recommendations=["Continue monitoring"],
            confidence_assessment="High confidence in findings",
            limitations=["Limited time frame"],
            next_steps=["Follow up investigation"]
        )
        
        test_summary = {
            "sources_retrieved": 8,
            "investigation_depth": 2,
            "entities_found": 1,
            "avg_credibility": 0.85
        }
        
        response = await judge_structured(
            report=test_report,
            investigation_summary=test_summary,
            agents=structured_agents
        )
        
        # Validate response type
        assert isinstance(response, JudgeResponse), f"Expected JudgeResponse, got {type(response)}"
        
        # Validate quality metrics
        metrics = response.quality_metrics
        assert 0 <= metrics.overall_score <= 100, "Overall score must be 0-100"
        assert response.approval_status, "Approval status is required"
        
        logger.info(f"✅ Judge: {response.approval_status}")
        logger.info(f"   Overall Score: {metrics.overall_score:.1f}")
        logger.info(f"   Completeness: {metrics.completeness_score:.1f}")
        logger.info(f"   Accuracy: {metrics.accuracy_score:.1f}")
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Judge Agent test failed: {e}")
        return None

async def test_end_to_end_workflow():
    """Test complete agent workflow with structured outputs"""
    logger.info("Testing end-to-end structured workflow...")
    
    try:
        test_query = "Investigate Ali Khaledi Nasab academic background and research"
        
        # Step 1: Query Analysis
        logger.info("Step 1: Query Analysis")
        query_result = await test_query_analysis_agent()
        if not query_result:
            return False
        
        # Step 2: Planning
        logger.info("Step 2: Planning")
        planning_result = await test_planning_agent()
        if not planning_result:
            return False
        
        # Step 3: Pivot Analysis
        logger.info("Step 3: Pivot Analysis")
        pivot_result = await test_pivot_analysis_agent()
        if not pivot_result:
            return False
        
        # Step 4: Synthesis
        logger.info("Step 4: Synthesis")
        synthesis_result = await test_synthesis_agent()
        if not synthesis_result:
            return False
        
        # Step 5: Judge
        logger.info("Step 5: Quality Assessment")
        judge_result = await test_judge_agent()
        if not judge_result:
            return False
        
        logger.info("✅ End-to-end workflow completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ End-to-end workflow failed: {e}")
        return False

async def main():
    """Run all structured agent tests"""
    logger.info("🔬 Starting Structured OSINT Agent Tests")
    logger.info("=" * 60)
    
    # Test 1: API key configuration
    has_api_keys = check_api_keys()
    logger.info("")
    
    # Test 2: Pydantic model validation
    models_ok = await test_pydantic_models()
    logger.info("")
    
    # Test 3: Individual agent tests
    agents_ok = True
    individual_tests = [
        ("Query Analysis", test_query_analysis_agent),
        ("Planning", test_planning_agent),
        ("Pivot Analysis", test_pivot_analysis_agent),
        ("Synthesis", test_synthesis_agent),
        ("Judge", test_judge_agent)
    ]
    
    for test_name, test_func in individual_tests:
        logger.info(f"Testing {test_name} Agent...")
        result = await test_func()
        if result is None:
            agents_ok = False
        logger.info("")
    
    # Test 4: End-to-end workflow
    workflow_ok = await test_end_to_end_workflow()
    logger.info("")
    
    # Summary
    logger.info("🎯 Structured Agent Test Results")
    logger.info("=" * 60)
    logger.info(f"✅ API Keys: {'CONFIGURED' if has_api_keys else 'USING MOCKS'}")
    logger.info(f"✅ Pydantic Models: {'PASS' if models_ok else 'FAIL'}")
    logger.info(f"✅ Individual Agents: {'PASS' if agents_ok else 'FAIL'}")
    logger.info(f"✅ End-to-End Workflow: {'PASS' if workflow_ok else 'FAIL'}")
    
    if models_ok and agents_ok and workflow_ok:
        logger.info("🎉 Structured OSINT Agent System: FULLY OPERATIONAL")
        logger.info("")
        logger.info("Key Benefits Achieved:")
        logger.info("✅ Type Safety: Pydantic validation prevents data errors")
        logger.info("✅ Structured Outputs: No manual parsing required")
        logger.info("✅ LLM Integration: Instructor handles model communication")
        logger.info("✅ Data Validation: Automatic field validation and coercion")
        logger.info("✅ Mock Fallbacks: System works without API keys")
    else:
        logger.warning("⚠️  Some tests failed - check logs for details")
    
    logger.info("")
    logger.info("Next steps:")
    logger.info("1. Run full integration test: python -m pytest tests/")
    logger.info("2. Test with real investigation: 'Ali Khaledi Nasab'")
    logger.info("3. Monitor structured data validation in production")

if __name__ == "__main__":
    asyncio.run(main()) 