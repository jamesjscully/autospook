#!/usr/bin/env python3
"""
Deployment test script to verify core functionality without external API dependencies.
"""

import requests
import json
import time

# Test configuration
BASE_URL = "http://localhost:5000"
TEST_TOKEN = "e3797c07596ee872cdd0cabd5220827f0a3a7c4579643a5450487f32b2acc119ede9377ec5e79b01947ed058000edeb0feb8da598f59e816b0c0d40c7a656ebe"

def test_health_check():
    """Test the health check endpoint"""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_auth_validation():
    """Test token validation endpoint"""
    print("🔍 Testing authentication...")
    try:
        # Test valid token
        response = requests.post(
            f"{BASE_URL}/auth/validate",
            json={"token": TEST_TOKEN},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("valid"):
                print(f"✅ Authentication passed: {data['message']}")
                return True
            else:
                print(f"❌ Token validation failed: {data}")
                return False
        else:
            print(f"❌ Auth endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Auth test error: {e}")
        return False

def test_unauthorized_access():
    """Test that protected endpoints require authentication"""
    print("🔍 Testing unauthorized access protection...")
    try:
        # Test without token
        response = requests.post(
            f"{BASE_URL}/submit",
            data={"target_name": "test", "target_context": "test"},
            timeout=5
        )
        if response.status_code == 401:
            print("✅ Unauthorized access properly blocked")
            return True
        else:
            print(f"❌ Should have returned 401, got: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Unauthorized access test error: {e}")
        return False

def test_frontend_access():
    """Test that frontend loads properly"""
    print("🔍 Testing frontend access...")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200 and "AutoSpook" in response.text:
            print("✅ Frontend loads successfully")
            return True
        else:
            print(f"❌ Frontend test failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend test error: {e}")
        return False

def run_deployment_tests():
    """Run all deployment tests"""
    print("🚀 Starting AutoSpook Deployment Tests\n")
    
    tests = [
        ("Health Check", test_health_check),
        ("Authentication", test_auth_validation),
        ("Unauthorized Access Protection", test_unauthorized_access),
        ("Frontend Access", test_frontend_access),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        if test_func():
            passed += 1
        time.sleep(1)  # Small delay between tests
    
    print(f"\n🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All deployment tests PASSED! System is ready for production.")
        return True
    else:
        print("⚠️  Some tests failed. Please review before deployment.")
        return False

if __name__ == "__main__":
    success = run_deployment_tests()
    exit(0 if success else 1)