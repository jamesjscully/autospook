#!/usr/bin/env python3
"""
AutoSpook OSINT Test Runner
Run focused tests for critical functionality
"""

import subprocess
import sys
import os
import argparse
from pathlib import Path

def install_test_dependencies():
    """Install required test dependencies"""
    print("📦 Installing test dependencies...")
    
    dependencies = [
        "pytest",
        "pytest-asyncio", 
        "httpx[test]",  # For FastAPI testing
        "requests"
    ]
    
    for dep in dependencies:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", dep],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(f"✅ {dep}")
            else:
                print(f"❌ Failed to install {dep}: {result.stderr}")
        except Exception as e:
            print(f"❌ Error installing {dep}: {e}")

def run_api_tests():
    """Run API-specific tests"""
    print("🔧 Running API Tests...")
    return subprocess.run([
        sys.executable, "-m", "pytest", 
        "backend/tests/test_api.py",
        "-v", "--tb=short"
    ]).returncode

def run_integration_tests():
    """Run integration tests"""
    print("🔗 Running Integration Tests...")
    print("⚠️  Note: These tests start a real backend server")
    return subprocess.run([
        sys.executable, "-m", "pytest", 
        "tests/test_integration.py",
        "-v", "--tb=short", "-s"
    ]).returncode

def run_dev_launcher_tests():
    """Run development launcher tests"""
    print("🚀 Running Dev Launcher Tests...")
    return subprocess.run([
        sys.executable, "-m", "pytest", 
        "tests/test_dev_launcher.py",
        "-v", "--tb=short"
    ]).returncode

def run_quick_tests():
    """Run quick unit tests only"""
    print("⚡ Running Quick Tests...")
    return subprocess.run([
        sys.executable, "-m", "pytest", 
        "backend/tests/test_api.py",
        "tests/test_dev_launcher.py",
        "-v", "--tb=short",
        "-x"  # Stop on first failure
    ]).returncode

def run_all_tests():
    """Run all tests"""
    print("🧪 Running All Tests...")
    return subprocess.run([
        sys.executable, "-m", "pytest", 
        "-v", "--tb=short"
    ]).returncode

def check_environment():
    """Check if environment is ready for testing"""
    print("🔍 Checking Environment...")
    
    # Check if backend exists
    if not Path("backend/simple_api.py").exists():
        print("❌ Backend API file not found")
        return False
    
    # Check if frontend exists
    if not Path("frontend/package.json").exists():
        print("❌ Frontend package.json not found")
        return False
    
    # Check if dev launcher exists
    if not Path("dev_launch.py").exists():
        print("❌ Development launcher not found")
        return False
    
    print("✅ Environment looks good")
    return True

def main():
    parser = argparse.ArgumentParser(description="AutoSpook OSINT Test Runner")
    parser.add_argument(
        "test_type", 
        choices=["api", "integration", "launcher", "quick", "all", "install"],
        help="Type of tests to run"
    )
    parser.add_argument(
        "--install-deps", 
        action="store_true",
        help="Install test dependencies first"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🕵️  AutoSpook OSINT Test Runner")
    print("=" * 60)
    
    if args.install_deps or args.test_type == "install":
        install_test_dependencies()
        if args.test_type == "install":
            return
    
    if not check_environment():
        print("\n❌ Environment check failed. Please ensure all files are present.")
        sys.exit(1)
    
    print(f"\n🎯 Running: {args.test_type} tests\n")
    
    # Map test types to functions
    test_functions = {
        "api": run_api_tests,
        "integration": run_integration_tests, 
        "launcher": run_dev_launcher_tests,
        "quick": run_quick_tests,
        "all": run_all_tests
    }
    
    if args.test_type in test_functions:
        exit_code = test_functions[args.test_type]()
        
        print("\n" + "=" * 60)
        if exit_code == 0:
            print("✅ All tests passed!")
        else:
            print("❌ Some tests failed!")
        print("=" * 60)
        
        sys.exit(exit_code)
    else:
        print(f"❌ Unknown test type: {args.test_type}")
        sys.exit(1)

if __name__ == "__main__":
    main() 