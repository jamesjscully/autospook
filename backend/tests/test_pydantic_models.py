"""
Tests for Pydantic model validation and edge cases
Focuses on scenarios likely to cause problems in production
"""

import pytest
from datetime import datetime
from typing import Dict, Any
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

# Import specific modules directly to avoid graph dependencies
import importlib.util
osint_models_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src', 'agent', 'osint_models.py')
spec = importlib.util.spec_from_file_location("osint_models", osint_models_path)
osint_models = importlib.util.module_from_spec(spec)
spec.loader.exec_module(osint_models)

# Import the classes we need
OSINTEntity = osint_models.OSINTEntity
EntityType = osint_models.EntityType
EntityRelationship = osint_models.EntityRelationship
QueryAnalysisResponse = osint_models.QueryAnalysisResponse
PlanningResponse = osint_models.PlanningResponse
PivotAnalysisResponse = osint_models.PivotAnalysisResponse
SynthesisResponse = osint_models.SynthesisResponse
JudgeResponse = osint_models.JudgeResponse
InvestigationReport = osint_models.InvestigationReport
RiskAssessment = osint_models.RiskAssessment
RiskLevel = osint_models.RiskLevel
KeyFinding = osint_models.KeyFinding
QualityMetrics = osint_models.QualityMetrics
RetrievalTask = osint_models.RetrievalTask
PivotStrategy = osint_models.PivotStrategy
InvestigationStartRequest = osint_models.InvestigationStartRequest
EntitySearchRequest = osint_models.EntitySearchRequest

from pydantic import ValidationError


class TestOSINTEntityValidation:
    """Test OSINTEntity model validation edge cases"""
    
    def test_valid_entity_creation(self):
        """Test creating valid entities"""
        entity = OSINTEntity(
            name="Ali Khaledi Nasab",
            entity_type=EntityType.PERSON,
            confidence=0.95,
            attributes={"profession": "researcher"},
            description="Academic researcher"
        )
        
        assert entity.name == "Ali Khaledi Nasab"
        assert entity.entity_type == EntityType.PERSON
        assert entity.confidence == 0.95
        assert entity.attributes == {"profession": "researcher"}
    
    def test_confidence_validation_edge_cases(self):
        """Test confidence field validation at boundaries"""
        # Test boundary values
        valid_confidences = [0.0, 0.5, 1.0]
        for confidence in valid_confidences:
            entity = OSINTEntity(
                name="Test",
                entity_type=EntityType.PERSON,
                confidence=confidence
            )
            assert entity.confidence == confidence
        
        # Test invalid values
        invalid_confidences = [-0.1, 1.1, 2.0, -1.0, float('inf'), float('-inf')]
        for confidence in invalid_confidences:
            with pytest.raises(ValidationError) as exc_info:
                OSINTEntity(
                    name="Test",
                    entity_type=EntityType.PERSON,
                    confidence=confidence
                )
            assert "confidence" in str(exc_info.value).lower()
    
    def test_confidence_type_coercion(self):
        """Test that confidence handles type coercion correctly"""
        # String numbers should be converted
        entity = OSINTEntity(
            name="Test",
            entity_type=EntityType.PERSON,
            confidence="0.75"  # String should be converted to float
        )
        assert entity.confidence == 0.75
        assert isinstance(entity.confidence, float)
        
        # Invalid string should fail
        with pytest.raises(ValidationError):
            OSINTEntity(
                name="Test",
                entity_type=EntityType.PERSON,
                confidence="invalid"
            )
    
    def test_required_fields(self):
        """Test that required fields are enforced"""
        # Missing name should fail
        with pytest.raises(ValidationError) as exc_info:
            OSINTEntity(entity_type=EntityType.PERSON)
        assert "name" in str(exc_info.value)
        
        # Missing entity_type should fail
        with pytest.raises(ValidationError) as exc_info:
            OSINTEntity(name="Test")
        assert "entity_type" in str(exc_info.value)
    
    def test_entity_type_validation(self):
        """Test entity type enum validation"""
        # Valid entity types
        for entity_type in EntityType:
            entity = OSINTEntity(name="Test", entity_type=entity_type)
            assert entity.entity_type == entity_type
        
        # Invalid entity type should fail
        with pytest.raises(ValidationError):
            OSINTEntity(name="Test", entity_type="invalid_type")
    
    def test_empty_and_whitespace_names(self):
        """Test handling of empty and whitespace-only names"""
        # Empty string should technically be valid (no min_length constraint)
        entity = OSINTEntity(name="", entity_type=EntityType.PERSON)
        assert entity.name == ""
        
        # Whitespace-only names
        entity = OSINTEntity(name="   ", entity_type=EntityType.PERSON)
        assert entity.name == "   "
    
    def test_complex_attributes(self):
        """Test complex attribute structures"""
        complex_attrs = {
            "nested": {"key": "value", "number": 123},
            "list": [1, 2, 3, "string"],
            "boolean": True,
            "null_value": None
        }
        
        entity = OSINTEntity(
            name="Test",
            entity_type=EntityType.ORGANIZATION,
            attributes=complex_attrs
        )
        assert entity.attributes == complex_attrs


class TestInvestigationReportValidation:
    """Test InvestigationReport validation and complex nested structures"""
    
    def test_minimal_valid_report(self):
        """Test creating minimal valid report"""
        risk_assessment = RiskAssessment(
            overall_risk=RiskLevel.LOW,
            risk_factors=[],
            risk_score=0.2,
            mitigation_suggestions=[],
            confidence=0.8
        )
        
        report = InvestigationReport(
            executive_summary="Test summary",
            risk_assessment=risk_assessment,
            confidence_assessment="High confidence"
        )
        
        assert report.executive_summary == "Test summary"
        assert report.risk_assessment.overall_risk == RiskLevel.LOW
        assert len(report.key_findings) == 0  # Default empty list
    
    def test_nested_model_validation(self):
        """Test validation of nested models within report"""
        # Invalid risk score should fail validation
        with pytest.raises(ValidationError) as exc_info:
            RiskAssessment(
                overall_risk=RiskLevel.HIGH,
                risk_factors=[],
                risk_score=1.5,  # > 1.0, should fail
                mitigation_suggestions=[],
                confidence=0.8
            )
        assert "risk_score" in str(exc_info.value)
    
    def test_key_findings_validation(self):
        """Test KeyFinding model validation"""
        # Valid finding
        finding = KeyFinding(
            finding_text="Test finding",
            confidence=0.8,
            supporting_sources=["source1", "source2"],
            entities_involved=["entity1"],
            significance="Important discovery"
        )
        assert finding.finding_text == "Test finding"
        
        # Empty finding text should be allowed (no constraints)
        finding = KeyFinding(
            finding_text="",
            confidence=0.5,
            supporting_sources=[],
            entities_involved=[],
            significance=""
        )
        assert finding.finding_text == ""


class TestAgentResponseValidation:
    """Test agent response model validation"""
    
    def test_query_analysis_response_validation(self):
        """Test QueryAnalysisResponse validation"""
        entity = OSINTEntity(name="Test", entity_type=EntityType.PERSON)
        
        response = QueryAnalysisResponse(
            entities_identified=[entity],
            investigation_scope="Test scope",
            primary_objectives=["obj1", "obj2"],
            entity_priorities={"Test": 1},
            investigation_type="person"
        )
        
        assert len(response.entities_identified) == 1
        assert response.investigation_scope == "Test scope"
    
    def test_planning_response_with_invalid_task_priority(self):
        """Test RetrievalTask priority validation"""
        # Valid priority range is 1-5
        valid_task = RetrievalTask(
            task_description="Valid task",
            priority=3,  # Valid
            source_types=["web"],
            entities_of_interest=["entity"],
            search_terms=["term"]
        )
        assert valid_task.priority == 3
        
        # Invalid priorities should fail
        invalid_priorities = [0, 6, -1, 10]
        for priority in invalid_priorities:
            with pytest.raises(ValidationError) as exc_info:
                RetrievalTask(
                    task_description="Invalid task",
                    priority=priority,
                    source_types=["web"],
                    entities_of_interest=["entity"],
                    search_terms=["term"]
                )
            assert "priority" in str(exc_info.value)
    
    def test_quality_metrics_score_ranges(self):
        """Test QualityMetrics score validation (0-100 range)"""
        # Valid scores
        metrics = QualityMetrics(
            overall_score=85.5,
            completeness_score=90.0,
            accuracy_score=88.2,
            relevance_score=75.0,
            source_diversity_score=95.0,
            credibility_score=82.5
        )
        assert metrics.overall_score == 85.5
        
        # Invalid scores should fail
        invalid_scores = [-1, 100.1, 150, -50]
        for score in invalid_scores:
            with pytest.raises(ValidationError):
                QualityMetrics(
                    overall_score=score,  # Should fail validation
                    completeness_score=80,
                    accuracy_score=80,
                    relevance_score=80,
                    source_diversity_score=80,
                    credibility_score=80
                )


class TestAPIRequestValidation:
    """Test API request model validation"""
    
    def test_investigation_start_request_validation(self):
        """Test InvestigationStartRequest validation"""
        # Valid request
        request = InvestigationStartRequest(
            query="Test investigation",
            max_retrievals=10
        )
        assert request.query == "Test investigation"
        assert request.max_retrievals == 10
        
        # Query too short should fail
        with pytest.raises(ValidationError) as exc_info:
            InvestigationStartRequest(query="ab")  # Less than min_length=3
        assert "query" in str(exc_info.value)
        
        # Max retrievals out of range should fail
        with pytest.raises(ValidationError):
            InvestigationStartRequest(
                query="Valid query",
                max_retrievals=25  # > 20, should fail
            )
        
        with pytest.raises(ValidationError):
            InvestigationStartRequest(
                query="Valid query", 
                max_retrievals=5   # < 8, should fail
            )
    
    def test_entity_search_request_validation(self):
        """Test EntitySearchRequest validation"""
        # Valid request
        request = EntitySearchRequest(
            entity_name="Ali Khaledi Nasab",
            entity_type=EntityType.PERSON,
            search_depth=3
        )
        assert request.entity_name == "Ali Khaledi Nasab"
        
        # Entity name too short should fail
        with pytest.raises(ValidationError):
            EntitySearchRequest(entity_name="A")  # Less than min_length=2
        
        # Search depth out of range should fail
        with pytest.raises(ValidationError):
            EntitySearchRequest(
                entity_name="Valid name",
                search_depth=0  # < 1, should fail
            )


class TestDataTypeConversion:
    """Test data type conversion scenarios that might occur in production"""
    
    def test_numeric_string_conversion(self):
        """Test conversion of numeric strings to proper types"""
        # Confidence as string
        entity = OSINTEntity(
            name="Test",
            entity_type=EntityType.PERSON,
            confidence="0.85"  # String should convert to float
        )
        assert entity.confidence == 0.85
        assert isinstance(entity.confidence, float)
        
        # Priority as string
        task = RetrievalTask(
            task_description="Test task",
            priority="3",  # String should convert to int
            source_types=["web"],
            entities_of_interest=["entity"],
            search_terms=["term"]
        )
        assert task.priority == 3
        assert isinstance(task.priority, int)
    
    def test_enum_conversion(self):
        """Test enum conversion from strings"""
        # Entity type from string
        entity = OSINTEntity(
            name="Test",
            entity_type="person",  # String should convert to enum
        )
        assert entity.entity_type == EntityType.PERSON
        
        # Risk level from string
        risk = RiskAssessment(
            overall_risk="medium",  # String should convert to enum
            risk_factors=[],
            risk_score=0.5,
            mitigation_suggestions=[],
            confidence=0.8
        )
        assert risk.overall_risk == RiskLevel.MEDIUM
    
    def test_boolean_conversion(self):
        """Test boolean conversion scenarios"""
        # This would be used in validation results
        judge_response = JudgeResponse(
            quality_metrics=QualityMetrics(
                overall_score=85,
                completeness_score=80,
                accuracy_score=90,
                relevance_score=85,
                source_diversity_score=88,
                credibility_score=87
            ),
            approval_status="APPROVED",
            required_improvements=[],
            validation_results={
                "source_diversity": "true",  # String should convert to bool
                "credibility_check": 1,      # Int should convert to bool
                "completeness": 0            # Int should convert to bool
            },
            final_recommendations=[]
        )
        assert judge_response.validation_results["source_diversity"] is True
        assert judge_response.validation_results["credibility_check"] is True
        assert judge_response.validation_results["completeness"] is False


class TestEdgeCasesAndProductionScenarios:
    """Test edge cases likely to occur in production"""
    
    def test_unicode_and_special_characters(self):
        """Test handling of unicode and special characters"""
        unicode_name = "Алексей Кулешов"  # Cyrillic
        special_chars = "O'Neil & Associates (Test)"
        emoji_name = "Test Entity 🔍"
        
        entities = [
            OSINTEntity(name=unicode_name, entity_type=EntityType.PERSON),
            OSINTEntity(name=special_chars, entity_type=EntityType.ORGANIZATION),
            OSINTEntity(name=emoji_name, entity_type=EntityType.PERSON)
        ]
        
        for entity in entities:
            assert entity.name  # Should handle all these cases
    
    def test_very_long_strings(self):
        """Test handling of very long strings"""
        long_description = "A" * 10000  # Very long description
        long_finding = "F" * 5000       # Very long finding text
        
        # Should handle long strings without issues
        entity = OSINTEntity(
            name="Test",
            entity_type=EntityType.PERSON,
            description=long_description
        )
        assert len(entity.description) == 10000
        
        finding = KeyFinding(
            finding_text=long_finding,
            confidence=0.8,
            supporting_sources=[],
            entities_involved=[],
            significance="Test"
        )
        assert len(finding.finding_text) == 5000
    
    def test_null_and_none_handling(self):
        """Test handling of null/None values"""
        # Optional fields can be None
        entity = OSINTEntity(
            name="Test",
            entity_type=EntityType.PERSON,
            description=None  # Should be allowed
        )
        assert entity.description is None
        
        # But required fields cannot be None
        with pytest.raises(ValidationError):
            OSINTEntity(
                name=None,  # Required field cannot be None
                entity_type=EntityType.PERSON
            )
    
    def test_empty_collections(self):
        """Test handling of empty lists and dictionaries"""
        # Empty collections should be allowed
        report = InvestigationReport(
            executive_summary="Test",
            key_findings=[],           # Empty list
            entities_discovered=[],    # Empty list
            entity_relationships=[],   # Empty list
            risk_assessment=RiskAssessment(
                overall_risk=RiskLevel.LOW,
                risk_factors=[],       # Empty list
                risk_score=0.1,
                mitigation_suggestions=[], # Empty list
                confidence=0.8
            ),
            source_summary={},         # Empty dict
            recommendations=[],        # Empty list
            confidence_assessment="Test",
            limitations=[],            # Empty list
            next_steps=[]              # Empty list
        )
        
        assert len(report.key_findings) == 0
        assert len(report.source_summary) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 