"""
Tests for the development launcher
Tests critical functionality that keeps development workflow working
"""

import pytest
import os
import sys
import tempfile
import shutil
import subprocess
import time
import requests
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestDevLauncherPrerequisites:
    """Test prerequisite checking functionality"""
    
    def setup_method(self):
        """Create temporary test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
    
    def teardown_method(self):
        """Clean up test environment"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)
    
    def create_file_structure(self, include_backend=True, include_frontend=True, include_api=True, include_package=True):
        """Create test file structure"""
        if include_backend:
            os.makedirs("backend", exist_ok=True)
            if include_api:
                with open("backend/simple_api.py", "w") as f:
                    f.write("# Mock API file")
        
        if include_frontend:
            os.makedirs("frontend", exist_ok=True)
            if include_package:
                with open("frontend/package.json", "w") as f:
                    f.write('{"name": "frontend", "scripts": {"dev": "vite"}}')
    
    def test_prerequisite_checking_success(self):
        """Test that prerequisite checking works when all files exist"""
        from dev_launch import DevLauncher
        
        self.create_file_structure()
        launcher = DevLauncher()
        
        assert launcher.check_prerequisites() is True
    
    def test_prerequisite_checking_missing_backend(self):
        """Test prerequisite checking fails when backend directory missing"""
        from dev_launch import DevLauncher
        
        self.create_file_structure(include_backend=False)
        launcher = DevLauncher()
        
        assert launcher.check_prerequisites() is False
    
    def test_prerequisite_checking_missing_frontend(self):
        """Test prerequisite checking fails when frontend directory missing"""
        from dev_launch import DevLauncher
        
        self.create_file_structure(include_frontend=False)
        launcher = DevLauncher()
        
        assert launcher.check_prerequisites() is False
    
    def test_prerequisite_checking_missing_api_file(self):
        """Test prerequisite checking fails when API file missing"""
        from dev_launch import DevLauncher
        
        self.create_file_structure(include_api=False)
        launcher = DevLauncher()
        
        assert launcher.check_prerequisites() is False
    
    def test_prerequisite_checking_missing_package_json(self):
        """Test prerequisite checking fails when package.json missing"""
        from dev_launch import DevLauncher
        
        self.create_file_structure(include_package=False)
        launcher = DevLauncher()
        
        assert launcher.check_prerequisites() is False


class TestDevLauncherLogging:
    """Test logging functionality"""
    
    def test_log_formatting(self):
        """Test that logs are formatted correctly"""
        from dev_launch import DevLauncher, Colors
        
        launcher = DevLauncher()
        
        # Add a log message
        launcher.log("TEST", "Test message", Colors.GREEN)
        
        # Get the message from queue
        assert not launcher.log_queue.empty()
        message = launcher.log_queue.get()
        
        # Verify format: [timestamp] SERVICE | message
        assert "TEST" in message
        assert "Test message" in message
        assert "[" in message  # timestamp brackets
        assert "]" in message
        assert "|" in message
    
    def test_log_coloring(self):
        """Test that log coloring works"""
        from dev_launch import DevLauncher, Colors
        
        launcher = DevLauncher()
        
        # Test different colors
        launcher.log("TEST", "Green message", Colors.GREEN)
        launcher.log("TEST", "Red message", Colors.RED)
        
        green_message = launcher.log_queue.get()
        red_message = launcher.log_queue.get()
        
        # Messages should contain color codes
        assert Colors.GREEN in green_message
        assert Colors.RED in red_message


class TestDevLauncherProcessManagement:
    """Test process management functionality"""
    
    @patch('subprocess.Popen')
    def test_process_creation(self, mock_popen):
        """Test that processes are created correctly"""
        from dev_launch import DevLauncher, Colors
        
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Process still running
        mock_process.stdout.readline.return_value = "Test output\n"
        mock_process.stderr.readline.return_value = ""
        mock_popen.return_value = mock_process
        
        launcher = DevLauncher()
        
        # Test backend process creation
        process = launcher.run_process(
            ["python", "-m", "uvicorn", "simple_api:app"],
            "backend",
            "BACKEND",
            Colors.BLUE
        )
        
        assert process is not None
        assert process in launcher.processes
        mock_popen.assert_called_once()
    
    def test_cleanup_functionality(self):
        """Test that cleanup properly terminates processes"""
        from dev_launch import DevLauncher
        
        launcher = DevLauncher()
        
        # Add mock processes
        mock_process1 = MagicMock()
        mock_process2 = MagicMock()
        launcher.processes = [mock_process1, mock_process2]
        
        # Run cleanup
        launcher.cleanup()
        
        # Verify processes were terminated
        mock_process1.terminate.assert_called_once()
        mock_process2.terminate.assert_called_once()


class TestSystemIntegration:
    """Test system-level integration points"""
    
    def test_python_environment(self):
        """Test that Python environment has required packages"""
        try:
            import fastapi
            import uvicorn
            import requests
            assert True
        except ImportError as e:
            pytest.fail(f"Required package missing: {e}")
    
    def test_file_structure_integrity(self):
        """Test that required files exist in project"""
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        required_files = [
            "backend/simple_api.py",
            "frontend/package.json",
            "dev_launch.py"
        ]
        
        for file_path in required_files:
            full_path = os.path.join(project_root, file_path)
            assert os.path.exists(full_path), f"Required file missing: {file_path}"
    
    def test_port_availability_checking(self):
        """Test port availability checking works"""
        import socket
        
        # Test with a port that should be available
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            # Try to bind to a random high port
            sock.bind(('localhost', 0))
            port = sock.getsockname()[1]
            
            # Port should be available now
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as test_sock:
                result = test_sock.connect_ex(('localhost', port))
                assert result != 0  # Should fail to connect (port not listening)


class TestCriticalWorkflow:
    """Test the critical parts of the development workflow"""
    
    def test_backend_startup_sequence(self):
        """Test that backend can start without errors"""
        backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
        
        if not os.path.exists(os.path.join(backend_dir, "simple_api.py")):
            pytest.skip("Backend not available for testing")
        
        # Try to start backend on test port
        process = subprocess.Popen(
            ["python", "-m", "uvicorn", "simple_api:app", "--host", "localhost", "--port", "8002"],
            cwd=backend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        try:
            # Wait a moment for startup
            time.sleep(2)
            
            # Check if it's responding
            try:
                response = requests.get("http://localhost:8002/health", timeout=5)
                assert response.status_code == 200
                
                data = response.json()
                assert "status" in data
                assert data["status"] == "healthy"
                
            except requests.exceptions.RequestException:
                pytest.fail("Backend failed to start or respond")
            
        finally:
            # Clean up
            process.terminate()
            process.wait(timeout=5)
    
    def test_api_endpoint_availability(self):
        """Test that all critical API endpoints are defined"""
        from backend.simple_api import app
        
        # Get all routes
        routes = [route.path for route in app.routes]
        
        critical_endpoints = [
            "/health",
            "/",
            "/api/investigations",
            "/api/investigations/{investigation_id}",
            "/api/investigations/{investigation_id}/entities",
            "/api/investigations/{investigation_id}/sources", 
            "/api/investigations/{investigation_id}/report"
        ]
        
        for endpoint in critical_endpoints:
            assert endpoint in routes, f"Critical endpoint missing: {endpoint}"


if __name__ == "__main__":
    # Run tests
    subprocess.run(["python", "-m", "pytest", __file__, "-v"]) 