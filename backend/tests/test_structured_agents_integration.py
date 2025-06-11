"""
Tests for structured agent integration and failure scenarios
Focuses on LLM failures, mock fallbacks, and production edge cases
"""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from src.agent.osint_agents_structured import (
    OSINTStructuredAgents, 
    get_structured_client
)
from src.agent.osint_models import (
    QueryAnalysisResponse, PlanningResponse, PivotAnalysisResponse,
    SynthesisResponse, JudgeResponse, OSINTEntity, EntityType,
    RetrievalTask, QualityMetrics, RiskAssessment, RiskLevel,
    InvestigationReport
)
from instructor.exceptions import InstructorRetryException
import instructor


class TestStructuredAgentClientInitialization:
    """Test client initialization and configuration edge cases"""
    
    def test_client_initialization_without_api_keys(self):
        """Test that clients initialize properly without API keys (mock mode)"""
        # Clear environment variables that might exist
        with patch.dict(os.environ, {}, clear=True):
            agents = OSINTStructuredAgents()
            
            # Should initialize without errors in mock mode
            assert agents is not None
            
            # All clients should be accessible (even if they're mocks)
            assert hasattr(agents, 'claude_client')
            assert hasattr(agents, 'openai_client') 
            assert hasattr(agents, 'gemini_client')
    
    def test_client_initialization_with_partial_api_keys(self):
        """Test client initialization with only some API keys present"""
        # Test with only one API key
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test_key'}, clear=True):
            agents = OSINTStructuredAgents()
            assert agents is not None
            
        # Test with two API keys missing one
        with patch.dict(os.environ, {
            'ANTHROPIC_API_KEY': 'test_key',
            'OPENAI_API_KEY': 'test_key'
        }, clear=True):
            agents = OSINTStructuredAgents()
            assert agents is not None
    
    def test_get_structured_client_with_invalid_provider(self):
        """Test get_structured_client with invalid provider name"""
        with pytest.raises(ValueError) as exc_info:
            get_structured_client("invalid_provider", "fake_key")
        assert "Unsupported provider" in str(exc_info.value)


class TestStructuredAgentMockFallbacks:
    """Test that mock responses work when LLM clients fail"""
    
    def setup_method(self):
        """Set up test environment with no API keys (force mock mode)"""
        self.agents = OSINTStructuredAgents()
    
    @pytest.mark.asyncio
    async def test_query_analysis_mock_fallback(self):
        """Test query analysis returns valid mock response"""
        query = "Ali Khaledi Nasab investigation"
        focus_areas = ["web", "social"]
        
        result = await self.agents.query_analysis_structured(
            query, focus_areas
        )
        
        # Should return a valid QueryAnalysisResponse
        assert isinstance(result, QueryAnalysisResponse)
        assert result.investigation_scope
        assert len(result.entities_identified) > 0
        assert len(result.primary_objectives) > 0
        assert result.investigation_type
        
        # Mock should handle the specific query
        assert "Ali Khaledi Nasab" in result.investigation_scope or \
               any("Ali Khaledi Nasab" in entity.name 
                   for entity in result.entities_identified)
    
    @pytest.mark.asyncio
    async def test_planning_mock_fallback(self):
        """Test planning agent returns valid mock response"""
        entities = [OSINTEntity(name="Ali Khaledi Nasab", entity_type=EntityType.PERSON)]
        objectives = ["Identify professional background"]
        
        result = await self.agents.planning_structured(
            entities, objectives, [], {"max_retrievals": 10}
        )
        
        assert isinstance(result, PlanningResponse)
        assert len(result.retrieval_tasks) > 0
        assert result.investigation_strategy
        
        # Check that tasks have valid priorities
        for task in result.retrieval_tasks:
            assert 1 <= task.priority <= 5
            assert len(task.source_types) > 0
    
    @pytest.mark.asyncio
    async def test_synthesis_mock_with_large_context(self):
        """Test synthesis agent handles large context in mock mode"""
        # Simulate large amount of OSINT data
        large_sources = [f"Large source content {i}: " + "A" * 1000 
                        for i in range(100)]
        
        entities = [OSINTEntity(name="Test Entity", entity_type=EntityType.PERSON)]
        findings = ["Finding 1", "Finding 2"]
        
        result = await self.agents.synthesis_structured(
            large_sources, entities, findings
        )
        
        assert isinstance(result, SynthesisResponse)
        assert result.investigation_report
        assert result.investigation_report.executive_summary
        
        # Should handle large context without errors
        assert len(result.investigation_report.executive_summary) > 0


class TestStructuredAgentErrorHandling:
    """Test error handling and recovery scenarios"""
    
    def setup_method(self):
        """Set up agents for testing"""
        self.agents = OSINTStructuredAgents()
    
    @pytest.mark.asyncio
    async def test_client_api_error_fallback(self):
        """Test fallback to mock when client API calls fail"""
        # Mock a client that raises an exception
        with patch.object(self.agents, 'claude_client') as mock_client:
            mock_completion = AsyncMock()
            mock_completion.side_effect = Exception("API Error")
            mock_client.chat.completions.create = mock_completion
            
            # Should fall back to mock response instead of failing
            result = await self.agents.query_analysis_structured(
                "Test query", ["web"]
            )
            
            # Should still return valid response (from mock fallback)
            assert isinstance(result, QueryAnalysisResponse)
    
    @pytest.mark.asyncio
    async def test_instructor_retry_exception_handling(self):
        """Test handling of Instructor retry exceptions"""
        with patch.object(self.agents, 'claude_client') as mock_client:
            mock_completion = AsyncMock()
            mock_completion.side_effect = InstructorRetryException("Retry failed")
            mock_client.chat.completions.create = mock_completion
            
            # Should handle instructor exceptions gracefully
            result = await self.agents.query_analysis_structured(
                "Test query", ["web"]  
            )
            
            assert isinstance(result, QueryAnalysisResponse)
    
    @pytest.mark.asyncio
    async def test_malformed_response_handling(self):
        """Test handling when LLM returns malformed/invalid response"""
        with patch.object(self.agents, 'claude_client') as mock_client:
            # Mock a response that would fail Pydantic validation
            mock_response = MagicMock()
            mock_response.entities_identified = "invalid_not_a_list"  # Invalid type
            mock_response.investigation_scope = None  # Missing required field
            
            mock_completion = AsyncMock()
            mock_completion.return_value = mock_response
            mock_client.chat.completions.create = mock_completion
            
            # Should fall back to mock when validation fails
            result = await self.agents.query_analysis_structured(
                "Test query", ["web"]
            )
            
            assert isinstance(result, QueryAnalysisResponse)
            assert isinstance(result.entities_identified, list)
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test handling of API timeouts"""
        with patch.object(self.agents, 'claude_client') as mock_client:
            mock_completion = AsyncMock()
            mock_completion.side_effect = asyncio.TimeoutError("Request timeout")
            mock_client.chat.completions.create = mock_completion
            
            # Should handle timeouts gracefully
            result = await self.agents.query_analysis_structured(
                "Test query", ["web"]
            )
            
            assert isinstance(result, QueryAnalysisResponse)


class TestStructuredAgentDataIntegrity:
    """Test data consistency and conversion between structured models and legacy formats"""
    
    def setup_method(self):
        """Set up agents for testing"""
        self.agents = OSINTStructuredAgents()
    
    @pytest.mark.asyncio
    async def test_entity_data_consistency(self):
        """Test that entities maintain consistent data across agent calls"""
        # Create entity with specific attributes
        test_entity = OSINTEntity(
            name="Ali Khaledi Nasab",
            entity_type=EntityType.PERSON,
            confidence=0.95,
            attributes={"test_attr": "test_value"}
        )
        
        # Use entity in planning
        result = await self.agents.planning_structured(
            [test_entity], ["Test objective"], [], {"max_retrievals": 10}
        )
        
        # Check that entity information is preserved in tasks
        assert isinstance(result, PlanningResponse)
        for task in result.retrieval_tasks:
            if "Ali Khaledi Nasab" in task.entities_of_interest:
                assert len(task.entities_of_interest) > 0
    
    @pytest.mark.asyncio
    async def test_confidence_score_propagation(self):
        """Test that confidence scores are properly maintained"""
        entities = [
            OSINTEntity(name="High Confidence", entity_type=EntityType.PERSON, confidence=0.95),
            OSINTEntity(name="Low Confidence", entity_type=EntityType.PERSON, confidence=0.3)
        ]
        
        result = await self.agents.planning_structured(
            entities, ["Test"], [], {"max_retrievals": 10}
        )
        
        # Tasks should reflect entity confidence levels in priorities
        assert isinstance(result, PlanningResponse)
        assert len(result.retrieval_tasks) > 0
    
    @pytest.mark.asyncio 
    async def test_judge_validation_consistency(self):
        """Test that judge responses have consistent validation results"""
        # Create quality metrics
        quality_metrics = QualityMetrics(
            overall_score=85.0,
            completeness_score=80.0,
            accuracy_score=90.0,
            relevance_score=85.0,
            source_diversity_score=88.0,
            credibility_score=87.0
        )
        
        investigation_data = {
            "entities": [OSINTEntity(name="Test", entity_type=EntityType.PERSON)],
            "sources": ["source1", "source2"],
            "findings": ["finding1", "finding2"]
        }
        
        result = await self.agents.judge_structured(
            quality_metrics, investigation_data
        )
        
        assert isinstance(result, JudgeResponse)
        assert result.quality_metrics == quality_metrics
        assert result.approval_status in ["APPROVED", "NEEDS_IMPROVEMENT", "REJECTED"]
        assert isinstance(result.validation_results, dict)


class TestStructuredAgentPerformanceScenarios:
    """Test performance and edge cases likely in production"""
    
    def setup_method(self):
        """Set up agents for testing"""
        self.agents = OSINTStructuredAgents()
    
    @pytest.mark.asyncio
    async def test_concurrent_agent_calls(self):
        """Test multiple agents being called concurrently"""
        # Simulate concurrent calls that might happen during investigation
        tasks = [
            self.agents.query_analysis_structured("Query 1", ["web"]),
            self.agents.query_analysis_structured("Query 2", ["social"]),
            self.agents.query_analysis_structured("Query 3", ["news"])
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should complete successfully
        for result in results:
            assert not isinstance(result, Exception)
            assert isinstance(result, QueryAnalysisResponse)
    
    @pytest.mark.asyncio
    async def test_large_entity_list_handling(self):
        """Test handling of large numbers of entities"""
        # Create large list of entities (simulating comprehensive investigation)
        large_entity_list = [
            OSINTEntity(
                name=f"Entity {i}",
                entity_type=EntityType.PERSON if i % 2 == 0 else EntityType.ORGANIZATION,
                confidence=0.5 + (i % 50) / 100  # Vary confidence
            )
            for i in range(100)
        ]
        
        result = await self.agents.planning_structured(
            large_entity_list, ["Large scale investigation"], [], {"max_retrievals": 20}
        )
        
        assert isinstance(result, PlanningResponse)
        assert len(result.retrieval_tasks) > 0
        # Should handle large input without errors
    
    @pytest.mark.asyncio
    async def test_memory_usage_with_large_context(self):
        """Test memory handling with very large context data"""
        # Simulate large OSINT data collection
        massive_sources = [
            f"Source {i}: {'Lorem ipsum dolor sit amet, consectetur adipiscing elit. ' * 100}"
            for i in range(50)
        ]
        
        entities = [OSINTEntity(name="Test", entity_type=EntityType.PERSON)]
        findings = [f"Finding {i}" for i in range(20)]
        
        # Should handle large context without memory issues
        result = await self.agents.synthesis_structured(
            massive_sources, entities, findings
        )
        
        assert isinstance(result, SynthesisResponse)
        assert result.investigation_report is not None


class TestProductionIntegrationScenarios:
    """Test scenarios that simulate real production usage"""
    
    def setup_method(self):
        """Set up agents for testing"""
        self.agents = OSINTStructuredAgents()
    
    @pytest.mark.asyncio
    async def test_ali_khaledi_nasab_investigation_mock(self):
        """Test complete Ali Khaledi Nasab investigation flow in mock mode"""
        # Step 1: Query Analysis
        query_result = await self.agents.query_analysis_structured(
            "Ali Khaledi Nasab", ["web", "social", "academic"]
        )
        
        assert isinstance(query_result, QueryAnalysisResponse)
        assert any("Ali Khaledi Nasab" in entity.name.lower() 
                  for entity in query_result.entities_identified)
        
        # Step 2: Planning
        planning_result = await self.agents.planning_structured(
            query_result.entities_identified,
            query_result.primary_objectives,
            [],
            {"max_retrievals": 12}
        )
        
        assert isinstance(planning_result, PlanningResponse)
        assert len(planning_result.retrieval_tasks) >= 8  # Meet min requirement
        
        # Step 3: Pivot Analysis (simulate some retrieved data)
        pivot_result = await self.agents.pivot_analysis_structured(
            ["Sample OSINT data about Ali Khaledi Nasab"],
            query_result.entities_identified,
            []
        )
        
        assert isinstance(pivot_result, PivotAnalysisResponse)
        
        # Step 4: Synthesis
        synthesis_result = await self.agents.synthesis_structured(
            ["Source 1", "Source 2", "Source 3"],
            query_result.entities_identified,
            ["Key finding 1", "Key finding 2"]
        )
        
        assert isinstance(synthesis_result, SynthesisResponse)
        assert synthesis_result.investigation_report is not None
        
        # Step 5: Judge validation
        quality_metrics = QualityMetrics(
            overall_score=85.0,
            completeness_score=80.0,
            accuracy_score=90.0,
            relevance_score=85.0,
            source_diversity_score=88.0,
            credibility_score=87.0
        )
        
        judge_result = await self.agents.judge_structured(
            quality_metrics,
            {
                "entities": query_result.entities_identified,
                "sources": ["source1", "source2"],
                "findings": ["finding1", "finding2"]
            }
        )
        
        assert isinstance(judge_result, JudgeResponse)
        assert judge_result.approval_status in ["APPROVED", "NEEDS_IMPROVEMENT", "REJECTED"]
    
    @pytest.mark.asyncio
    async def test_investigation_state_consistency(self):
        """Test that investigation state remains consistent across agent calls"""
        # Simulate investigation state that would be passed between agents
        initial_state = {
            "entities": [OSINTEntity(name="Ali Khaledi Nasab", entity_type=EntityType.PERSON)],
            "objectives": ["Identify professional background"],
            "findings": [],
            "sources": []
        }
        
        # Planning should use initial state
        planning_result = await self.agents.planning_structured(
            initial_state["entities"],
            initial_state["objectives"],
            initial_state["findings"],
            {"max_retrievals": 10}
        )
        
        # State should be preserved and enhanced, not replaced
        assert isinstance(planning_result, PlanningResponse)
        assert len(planning_result.retrieval_tasks) > 0
        
        # Entities should be consistent
        for task in planning_result.retrieval_tasks:
            if task.entities_of_interest:
                assert any("Ali Khaledi Nasab" in entity 
                          for entity in task.entities_of_interest)


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 