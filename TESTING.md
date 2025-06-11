# AutoSpook OSINT Testing Guide

## 🎯 Testing Strategy

We focus on testing **critical integration points** that are likely to break as the system evolves:

1. **API Contract** - Frontend depends on exact API structure
2. **Integration Points** - Frontend-backend communication  
3. **Development Workflow** - Dev launcher and environment
4. **Core Functionality** - Key system components

## 🧪 Test Categories

### API Tests (`backend/tests/test_api.py`)
- Tests all API endpoints that frontend uses
- Validates request/response structure
- Tests error handling and validation
- **Why Critical**: Frontend breaks if API contract changes

### Integration Tests (`tests/test_integration.py`)
- Tests full frontend-backend workflow
- Starts real backend server
- Tests data consistency across endpoints  
- **Why Critical**: Catches integration issues early

### Dev Launcher Tests (`tests/test_dev_launcher.py`)
- Tests development environment setup
- Tests process management
- Tests prerequisite checking
- **Why Critical**: Keeps development workflow working

## 🚀 Running Tests

### Quick Setup
```bash
# Install test dependencies
python run_tests.py install

# Run quick tests (API + Launcher)
python run_tests.py quick
```

### Specific Test Types
```bash
# API endpoint tests
python run_tests.py api

# Integration tests (starts backend)
python run_tests.py integration

# Development launcher tests
python run_tests.py launcher

# All tests
python run_tests.py all
```

### Manual Testing
```bash
# Using pytest directly
pytest backend/tests/test_api.py -v
pytest tests/ -v
```

## 📊 Test Coverage Focus

### ✅ What We Test
- **API endpoint contracts** (critical for frontend)
- **Request/response data structures** 
- **Error handling and status codes**
- **Development environment setup**
- **Process management and cleanup**
- **Integration workflow paths**

### ❌ What We Don't Over-Test
- UI component rendering details
- Complex agent logic (mostly mock)
- Database schema validation  
- Styling and visual elements
- Performance and load testing

## 🔧 Adding New Tests

### When to Add Tests
- Adding new API endpoints
- Changing existing API contracts
- Modifying development workflow
- Adding critical system components

### Test File Structure
```
tests/
├── test_integration.py     # Frontend-backend integration
├── test_dev_launcher.py    # Development environment
backend/tests/
├── test_api.py            # API endpoint contracts
```

### Example Test Pattern
```python
def test_new_endpoint(self):
    """Test new endpoint works as expected"""
    response = client.post("/api/new-endpoint", json={"test": "data"})
    assert response.status_code == 200
    
    data = response.json()
    assert "required_field" in data
    assert isinstance(data["required_field"], str)
```

## 🛡️ Continuous Testing

### During Development
```bash
# Quick smoke test while coding
python run_tests.py quick

# Full test before committing
python run_tests.py all
```

### Before Major Changes
1. Run all tests: `python run_tests.py all`
2. Verify dev launcher works: `python dev_launch.py`
3. Manual test key workflows

## 🚨 Common Issues

### Test Failures
```bash
# Backend not starting
python run_tests.py install  # Install missing deps

# Port conflicts
pkill -f uvicorn  # Kill existing servers

# Import errors
pip install -e backend/  # Install backend in editable mode
```

### Environment Issues
```bash
# Missing files
ls backend/simple_api.py frontend/package.json  # Check files exist

# Python path issues  
export PYTHONPATH="$PWD:$PYTHONPATH"  # Add project to path
```

## 📈 Test Philosophy

> **"Test the bridges, not the islands"**

We test the **connections** between components rather than exhaustively testing individual components. This catches the issues that actually break user workflows while keeping the test suite fast and maintainable.

### Focus Areas:
1. **API contracts** that frontend depends on
2. **Integration points** between services
3. **Development workflow** that keeps productivity high
4. **Critical paths** that users actually use

### Result:
- ⚡ Fast test suite
- 🎯 Catches real issues  
- 🔧 Easy to maintain
- 🚀 Keeps development moving

Happy testing! 🧪✨ 