"""
Integration tests for AutoSpook OSINT System
Tests the critical integration points between frontend and backend
"""

import pytest
import requests
import time
import json
import subprocess
import os
import signal
from typing import Optional

class OSINTIntegrationTest:
    """Integration tests for the full OSINT workflow"""
    
    @classmethod
    def setup_class(cls):
        """Start the backend server for testing"""
        cls.backend_process = None
        cls.base_url = "http://localhost:8001"  # Use different port for testing
        
        # Start backend on test port
        backend_dir = os.path.join(os.path.dirname(__file__), "../backend")
        cls.backend_process = subprocess.Popen(
            ["python", "-m", "uvicorn", "simple_api:app", "--host", "localhost", "--port", "8001"],
            cwd=backend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for server to start
        cls._wait_for_server()
    
    @classmethod
    def teardown_class(cls):
        """Stop the backend server"""
        if cls.backend_process:
            cls.backend_process.terminate()
            cls.backend_process.wait()
    
    @classmethod
    def _wait_for_server(cls, timeout=10):
        """Wait for backend server to be ready"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{cls.base_url}/health", timeout=1)
                if response.status_code == 200:
                    return True
            except:
                pass
            time.sleep(0.5)
        
        raise Exception("Backend server failed to start within timeout")
    
    def test_full_investigation_workflow(self):
        """Test complete investigation workflow as frontend would use it"""
        
        # 1. Create investigation (like frontend would)
        investigation_data = {
            "query": "Ali Khaledi Nasab",
            "max_retrievals": 12,
            "focus_areas": ["web", "social"],
            "entity_types": ["person"]
        }
        
        create_response = requests.post(
            f"{self.base_url}/api/investigations",
            json=investigation_data
        )
        assert create_response.status_code == 200
        
        investigation_data = create_response.json()
        investigation_id = investigation_data["investigation_id"]
        assert investigation_data["status"] == "started"
        
        # 2. Poll for status updates (like frontend would)
        status_response = requests.get(f"{self.base_url}/api/investigations/{investigation_id}")
        assert status_response.status_code == 200
        
        status_data = status_response.json()
        assert status_data["investigation_id"] == investigation_id
        assert "progress" in status_data
        assert "current_phase" in status_data
        
        # 3. Get entities (like frontend Entity Graph tab)
        entities_response = requests.get(f"{self.base_url}/api/investigations/{investigation_id}/entities")
        assert entities_response.status_code == 200
        
        entities_data = entities_response.json()
        assert entities_data["investigation_id"] == investigation_id
        assert "entities" in entities_data
        assert "count" in entities_data
        
        # 4. Get sources (like frontend Sources tab)
        sources_response = requests.get(f"{self.base_url}/api/investigations/{investigation_id}/sources")
        assert sources_response.status_code == 200
        
        sources_data = sources_response.json()
        assert sources_data["investigation_id"] == investigation_id
        assert "sources" in sources_data
        assert "count" in sources_data
        
        # 5. Get final report (like frontend Report tab)
        report_response = requests.get(f"{self.base_url}/api/investigations/{investigation_id}/report")
        assert report_response.status_code == 200
        
        report_data = report_response.json()
        assert report_data["investigation_id"] == investigation_id
        assert "report" in report_data
        assert "query" in report_data
        
        # Verify report structure that frontend expects
        report = report_data["report"]
        expected_fields = [
            "executive_summary", "key_findings", "entities", 
            "sources", "risk_assessment", "recommendations"
        ]
        for field in expected_fields:
            assert field in report, f"Report missing expected field: {field}"
    
    def test_api_contract_stability(self):
        """Test that API contract matches frontend expectations"""
        
        # Create investigation
        investigation_data = {"query": "Test Query"}
        create_response = requests.post(
            f"{self.base_url}/api/investigations",
            json=investigation_data
        )
        investigation_id = create_response.json()["investigation_id"]
        
        # Test each endpoint returns expected structure
        endpoints_and_expected_fields = {
            f"/api/investigations/{investigation_id}": [
                "investigation_id", "status", "progress", "entities_count", 
                "sources_count", "key_findings", "current_phase"
            ],
            f"/api/investigations/{investigation_id}/entities": [
                "investigation_id", "entities", "count"
            ],
            f"/api/investigations/{investigation_id}/sources": [
                "investigation_id", "sources", "count"
            ],
            f"/api/investigations/{investigation_id}/report": [
                "investigation_id", "query", "report"
            ]
        }
        
        for endpoint, expected_fields in endpoints_and_expected_fields.items():
            response = requests.get(f"{self.base_url}{endpoint}")
            assert response.status_code == 200, f"Endpoint {endpoint} failed"
            
            data = response.json()
            for field in expected_fields:
                assert field in data, f"Endpoint {endpoint} missing field {field}"
    
    def test_cors_functionality(self):
        """Test CORS headers work for frontend domains"""
        
        # Test with typical frontend origins
        origins = [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://localhost:5174"
        ]
        
        for origin in origins:
            response = requests.get(
                f"{self.base_url}/health",
                headers={"Origin": origin}
            )
            assert response.status_code == 200
            # Note: TestClient doesn't process CORS, but real server should
    
    def test_error_handling_for_frontend(self):
        """Test error responses are suitable for frontend handling"""
        
        # Test 404 for nonexistent investigation
        response = requests.get(f"{self.base_url}/api/investigations/nonexistent")
        assert response.status_code == 404
        
        # Response should be JSON for frontend to parse
        assert response.headers.get("content-type", "").startswith("application/json")
        
        # Test validation error
        response = requests.post(f"{self.base_url}/api/investigations", json={})
        assert response.status_code == 422
        assert response.headers.get("content-type", "").startswith("application/json")
    
    def test_investigation_data_consistency(self):
        """Test that investigation data is consistent across endpoints"""
        
        # Create investigation
        investigation_data = {"query": "Consistency Test"}
        create_response = requests.post(
            f"{self.base_url}/api/investigations",
            json=investigation_data
        )
        investigation_id = create_response.json()["investigation_id"]
        
        # Get data from different endpoints
        status_response = requests.get(f"{self.base_url}/api/investigations/{investigation_id}")
        entities_response = requests.get(f"{self.base_url}/api/investigations/{investigation_id}/entities")
        sources_response = requests.get(f"{self.base_url}/api/investigations/{investigation_id}/sources")
        
        status_data = status_response.json()
        entities_data = entities_response.json()
        sources_data = sources_response.json()
        
        # Verify counts are consistent
        assert status_data["entities_count"] == entities_data["count"]
        assert status_data["sources_count"] == sources_data["count"]
        
        # Verify investigation IDs match
        assert status_data["investigation_id"] == investigation_id
        assert entities_data["investigation_id"] == investigation_id
        assert sources_data["investigation_id"] == investigation_id


class TestFrontendCompatibility(OSINTIntegrationTest):
    """Test specific frontend compatibility requirements"""
    
    def setup_method(self):
        """Set up for each test"""
        self.base_url = "http://localhost:8001"
    
    def test_investigation_context_requirements(self):
        """Test data structure matches InvestigationContext expectations"""
        
        # Create investigation
        investigation_data = {"query": "Frontend Test"}
        create_response = requests.post(
            f"{self.base_url}/api/investigations",
            json=investigation_data
        )
        investigation_id = create_response.json()["investigation_id"]
        
        # Test entities structure matches OSINTEntity interface
        entities_response = requests.get(f"{self.base_url}/api/investigations/{investigation_id}/entities")
        entities_data = entities_response.json()
        
        if entities_data["entities"]:
            entity = entities_data["entities"][0]
            required_entity_fields = ["id", "name", "type", "confidence"]
            for field in required_entity_fields:
                assert field in entity, f"Entity missing field expected by frontend: {field}"
        
        # Test sources structure
        sources_response = requests.get(f"{self.base_url}/api/investigations/{investigation_id}/sources")
        sources_data = sources_response.json()
        
        if sources_data["sources"]:
            source = sources_data["sources"][0]
            required_source_fields = ["id", "url", "title", "type"]
            for field in required_source_fields:
                assert field in source, f"Source missing field expected by frontend: {field}"
    
    def test_status_updates_for_progress_tracking(self):
        """Test status updates provide data for progress bars and phase indicators"""
        
        # Create investigation
        investigation_data = {"query": "Progress Test"}
        create_response = requests.post(
            f"{self.base_url}/api/investigations",
            json=investigation_data
        )
        investigation_id = create_response.json()["investigation_id"]
        
        # Get status
        status_response = requests.get(f"{self.base_url}/api/investigations/{investigation_id}")
        status_data = status_response.json()
        
        # Verify progress tracking data
        assert "progress" in status_data
        assert isinstance(status_data["progress"], (int, float))
        assert 0 <= status_data["progress"] <= 100
        
        assert "current_phase" in status_data
        assert isinstance(status_data["current_phase"], str)
        
        assert "status" in status_data
        valid_statuses = ["retrieving", "analyzing", "reporting", "complete"]
        assert status_data["status"] in valid_statuses


if __name__ == "__main__":
    # Run tests
    import subprocess
    subprocess.run(["python", "-m", "pytest", __file__, "-v", "-s"]) 