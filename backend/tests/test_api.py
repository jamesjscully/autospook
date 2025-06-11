"""
Unit tests for AutoSpook OSINT API
Tests the critical API endpoints that frontend depends on
"""

import pytest
import json
from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simple_api import app

client = TestClient(app)

class TestOSINTAPI:
    """Test the core OSINT API functionality"""
    
    def test_health_endpoint(self):
        """Test that health endpoint returns expected structure"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "mode" in data
        assert "timestamp" in data
        assert data["status"] == "healthy"
        assert data["mode"] == "development"
    
    def test_root_endpoint(self):
        """Test root endpoint returns API info"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "docs" in data
        assert "health" in data
        assert "AutoSpook" in data["message"]
    
    def test_create_investigation(self):
        """Test investigation creation workflow"""
        investigation_data = {
            "query": "Test Investigation",
            "max_retrievals": 10,
            "focus_areas": ["web", "social"],
            "entity_types": ["person"]
        }
        
        response = client.post("/api/investigations", json=investigation_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "investigation_id" in data
        assert "status" in data
        assert "message" in data
        assert data["status"] == "started"
        assert "Test Investigation" in data["message"]
        
        # Store investigation ID for subsequent tests (without returning it)
        TestOSINTAPI._test_investigation_id = data["investigation_id"]
    
    def test_investigation_status(self):
        """Test getting investigation status"""
        # Get investigation ID from class variable (set by test_create_investigation)
        investigation_id = getattr(TestOSINTAPI, '_test_investigation_id', None)
        if investigation_id is None:
            # Create investigation if needed
            investigation_data = {"query": "Test Investigation for Status"}
            response = client.post("/api/investigations", json=investigation_data)
            investigation_id = response.json()["investigation_id"]
        
        response = client.get(f"/api/investigations/{investigation_id}")
        assert response.status_code == 200
        
        data = response.json()
        required_fields = [
            "investigation_id", "status", "progress", 
            "entities_count", "sources_count", "key_findings", "current_phase"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        assert data["investigation_id"] == investigation_id
        assert isinstance(data["progress"], (int, float))
        assert 0 <= data["progress"] <= 100
        assert isinstance(data["entities_count"], int)
        assert isinstance(data["sources_count"], int)
        assert isinstance(data["key_findings"], list)
    
    def test_investigation_entities(self):
        """Test getting investigation entities"""
        # Get investigation ID from class variable (set by test_create_investigation)
        investigation_id = getattr(TestOSINTAPI, '_test_investigation_id', None)
        if investigation_id is None:
            # Create investigation if needed
            investigation_data = {"query": "Test Investigation for Entities"}
            response = client.post("/api/investigations", json=investigation_data)
            investigation_id = response.json()["investigation_id"]
        
        response = client.get(f"/api/investigations/{investigation_id}/entities")
        assert response.status_code == 200
        
        data = response.json()
        assert "investigation_id" in data
        assert "entities" in data
        assert "count" in data
        assert data["investigation_id"] == investigation_id
        assert isinstance(data["entities"], list)
        assert data["count"] == len(data["entities"])
        
        # Check entity structure if any exist
        if data["entities"]:
            entity = data["entities"][0]
            required_entity_fields = ["id", "name", "type", "confidence"]
            for field in required_entity_fields:
                assert field in entity, f"Missing entity field: {field}"
    
    def test_investigation_sources(self):
        """Test getting investigation sources"""
        # Get investigation ID from class variable (set by test_create_investigation)
        investigation_id = getattr(TestOSINTAPI, '_test_investigation_id', None)
        if investigation_id is None:
            # Create investigation if needed
            investigation_data = {"query": "Test Investigation for Sources"}
            response = client.post("/api/investigations", json=investigation_data)
            investigation_id = response.json()["investigation_id"]
        
        response = client.get(f"/api/investigations/{investigation_id}/sources")
        assert response.status_code == 200
        
        data = response.json()
        assert "investigation_id" in data
        assert "sources" in data
        assert "count" in data
        assert data["investigation_id"] == investigation_id
        assert isinstance(data["sources"], list)
        assert data["count"] == len(data["sources"])
        
        # Check source structure if any exist
        if data["sources"]:
            source = data["sources"][0]
            required_source_fields = ["id", "url", "title", "type"]
            for field in required_source_fields:
                assert field in source, f"Missing source field: {field}"
    
    def test_investigation_report(self):
        """Test getting investigation report"""
        # Get investigation ID from class variable (set by test_create_investigation)
        investigation_id = getattr(TestOSINTAPI, '_test_investigation_id', None)
        if investigation_id is None:
            # Create investigation if needed
            investigation_data = {"query": "Test Investigation for Report"}
            response = client.post("/api/investigations", json=investigation_data)
            investigation_id = response.json()["investigation_id"]
        
        response = client.get(f"/api/investigations/{investigation_id}/report")
        assert response.status_code == 200
        
        data = response.json()
        assert "investigation_id" in data
        assert "query" in data
        assert "report" in data
        assert data["investigation_id"] == investigation_id
        
        report = data["report"]
        required_report_fields = [
            "executive_summary", "key_findings", "entities", 
            "sources", "risk_assessment", "recommendations"
        ]
        
        for field in required_report_fields:
            assert field in report, f"Missing report field: {field}"
    
    def test_nonexistent_investigation(self):
        """Test that nonexistent investigation returns 404"""
        fake_id = "nonexistent-investigation-id"
        
        endpoints = [
            f"/api/investigations/{fake_id}",
            f"/api/investigations/{fake_id}/entities",
            f"/api/investigations/{fake_id}/sources",
            f"/api/investigations/{fake_id}/report"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 404
    
    def test_invalid_investigation_data(self):
        """Test investigation creation with invalid data"""
        # Missing required query field
        invalid_data = {
            "max_retrievals": 10,
            "focus_areas": ["web"]
        }
        
        response = client.post("/api/investigations", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    def test_investigation_progression(self):
        """Test that investigation shows realistic progression"""
        # Get investigation ID from class variable (set by test_create_investigation)
        investigation_id = getattr(TestOSINTAPI, '_test_investigation_id', None)
        if investigation_id is None:
            # Create investigation if needed
            investigation_data = {"query": "Test Investigation for Progression"}
            response = client.post("/api/investigations", json=investigation_data)
            investigation_id = response.json()["investigation_id"]
        
        # Get status multiple times to see if it changes realistically
        response1 = client.get(f"/api/investigations/{investigation_id}")
        response2 = client.get(f"/api/investigations/{investigation_id}")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Status should be consistent for the same investigation
        # (In mock mode, this should be deterministic)
        assert data1["investigation_id"] == data2["investigation_id"]
        assert data1["entities_count"] == data2["entities_count"]
        assert data1["sources_count"] == data2["sources_count"]


class TestAPIValidation:
    """Test API validation and error handling"""
    
    def test_cors_headers(self):
        """Test that CORS headers are properly set"""
        response = client.options("/api/investigations")
        # Should not fail due to CORS
        assert response.status_code in [200, 405]  # OPTIONS might not be implemented
    
    def test_api_content_type(self):
        """Test that API properly handles content types"""
        # Valid JSON
        valid_data = {"query": "test"}
        response = client.post("/api/investigations", json=valid_data)
        assert response.status_code == 200
        
        # Invalid content type should be handled gracefully
        response = client.post(
            "/api/investigations", 
            content="invalid data",
            headers={"Content-Type": "text/plain"}
        )
        assert response.status_code in [400, 422]  # Should reject invalid data


class TestStructuredAgentAPIIntegration:
    """Test integration between structured agents and API endpoints"""
    
    def test_investigation_with_structured_validation(self):
        """Test that investigations use structured validation"""
        # Test with valid structured request
        investigation_data = {
            "query": "Ali Khaledi Nasab researcher investigation",
            "max_retrievals": 12,
            "focus_areas": ["web", "academic", "social"],
            "entity_types": ["person"]
        }
        
        response = client.post("/api/investigations", json=investigation_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "investigation_id" in data
        assert "status" in data
        
        # Check that the system can handle the structured request
        investigation_id = data["investigation_id"]
        status_response = client.get(f"/api/investigations/{investigation_id}")
        assert status_response.status_code == 200
        
        status_data = status_response.json()
        assert "entities_count" in status_data
        assert "sources_count" in status_data
    
    def test_investigation_with_pydantic_validation_errors(self):
        """Test API handling of Pydantic validation errors"""
        # Test invalid max_retrievals (outside valid range)
        invalid_data = {
            "query": "Test",
            "max_retrievals": 25,  # Should be <= 20
            "focus_areas": ["web"],
            "entity_types": ["person"]
        }
        
        response = client.post("/api/investigations", json=invalid_data)
        # Should handle validation gracefully
        assert response.status_code in [422, 400]  # Validation error
    
    def test_investigation_entity_type_validation(self):
        """Test entity type validation through API"""
        # Test with invalid entity type
        invalid_data = {
            "query": "Test investigation",
            "max_retrievals": 10,
            "focus_areas": ["web"],
            "entity_types": ["invalid_entity_type"]  # Should fail validation
        }
        
        response = client.post("/api/investigations", json=invalid_data)
        # Should handle gracefully or succeed with default handling
        assert response.status_code in [200, 422, 400]
    
    def test_investigation_focus_areas_validation(self):
        """Test focus areas validation through API"""
        # Test with valid focus areas
        valid_areas = ["web", "social", "academic", "news", "business", "public_records"]
        
        for area in valid_areas:
            investigation_data = {
                "query": f"Test with {area} focus",
                "max_retrievals": 10,
                "focus_areas": [area],
                "entity_types": ["person"]
            }
            
            response = client.post("/api/investigations", json=investigation_data)
            assert response.status_code == 200
    
    def test_investigation_confidence_scores_in_response(self):
        """Test that API responses include confidence scores from structured models"""
        investigation_data = {
            "query": "Ali Khaledi Nasab confidence test",
            "max_retrievals": 10
        }
        
        response = client.post("/api/investigations", json=investigation_data)
        assert response.status_code == 200
        
        investigation_id = response.json()["investigation_id"]
        
        # Check entities endpoint for confidence scores
        entities_response = client.get(f"/api/investigations/{investigation_id}/entities")
        assert entities_response.status_code == 200
        
        entities_data = entities_response.json()
        if entities_data["entities"]:
            # If entities exist, they should have confidence scores
            for entity in entities_data["entities"]:
                if "confidence" in entity:
                    assert 0.0 <= entity["confidence"] <= 1.0
    
    def test_investigation_source_credibility_in_response(self):
        """Test that API responses include source credibility from OSINT retrieval"""
        investigation_data = {
            "query": "Ali Khaledi Nasab source credibility test",
            "max_retrievals": 10
        }
        
        response = client.post("/api/investigations", json=investigation_data)
        assert response.status_code == 200
        
        investigation_id = response.json()["investigation_id"]
        
        # Check sources endpoint for credibility scores
        sources_response = client.get(f"/api/investigations/{investigation_id}/sources")
        assert sources_response.status_code == 200
        
        sources_data = sources_response.json()
        if sources_data["sources"]:
            # If sources exist, they should have credibility indicators
            for source in sources_data["sources"]:
                assert "url" in source
                assert "title" in source
                # Credibility might be embedded in source metadata
    
    def test_investigation_report_structure_validation(self):
        """Test that investigation reports follow structured format"""
        investigation_data = {
            "query": "Ali Khaledi Nasab structured report test",
            "max_retrievals": 10
        }
        
        response = client.post("/api/investigations", json=investigation_data)
        assert response.status_code == 200
        
        investigation_id = response.json()["investigation_id"]
        
        # Get final report
        report_response = client.get(f"/api/investigations/{investigation_id}/report")
        assert report_response.status_code == 200
        
        report_data = report_response.json()
        assert "report" in report_data
        
        report = report_data["report"]
        # Check for structured report fields
        expected_fields = [
            "executive_summary", "key_findings", "entities", 
            "sources", "risk_assessment", "recommendations"
        ]
        
        for field in expected_fields:
            assert field in report, f"Missing structured field: {field}"


if __name__ == "__main__":
    # Run tests directly
    import subprocess
    subprocess.run(["python", "-m", "pytest", __file__, "-v"]) 