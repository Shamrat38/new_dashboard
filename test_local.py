#!/usr/bin/env python
"""
Test script to verify Django configuration works locally
Run this before deploying to server
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(project_dir))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')

def test_django_setup():
    """Test Django setup"""
    print("Testing Django setup...")
    try:
        django.setup()
        print("✓ Django setup successful")
        return True
    except Exception as e:
        print(f"✗ Django setup failed: {e}")
        return False

def test_database():
    """Test database connection"""
    print("Testing database connection...")
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result:
                print("✓ Database connection successful")
                return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

def test_imports():
    """Test critical imports"""
    print("Testing critical imports...")
    try:
        from authentication.models import MyUser, Company
        from authentication.views import UserLoginView, UserRegistrationView
        from pilgrims.models import *
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_urls():
    """Test URL configuration"""
    print("Testing URL configuration...")
    try:
        from django.urls import reverse
        from django.test import Client
        
        client = Client()
        # Test a simple URL
        response = client.get('/api/schema/')
        if response.status_code in [200, 401, 403]:  # Any of these is fine
            print("✓ URL configuration working")
            return True
        else:
            print(f"⚠ Unexpected response code: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ URL test failed: {e}")
        return False

def main():
    """Main test function"""
    print("Django Local Configuration Test")
    print("=" * 40)
    
    tests = [
        test_django_setup,
        test_database,
        test_imports,
        test_urls
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed! Your configuration looks good.")
    else:
        print("⚠ Some tests failed. Check the errors above.")

if __name__ == '__main__':
    main()
