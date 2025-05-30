#!/usr/bin/env python3
"""
Simple test script to verify the ESG Intelligence Platform API is working
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_api():
    """Run basic API tests"""
    print("Testing ESG Intelligence Platform API...")
    print("=" * 50)
    
    # Test 1: Root endpoint
    print("\n1. Testing root endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("✓ Root endpoint is accessible")
            data = response.json()
            print(f"  - Platform: {data.get('name')}")
            print(f"  - Version: {data.get('version')}")
        else:
            print(f"✗ Root endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Could not connect to API: {e}")
        print("\nMake sure the API is running on port 8000")
        sys.exit(1)
    
    # Test 2: Health check
    print("\n2. Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✓ Health check passed")
            health = response.json()
            print(f"  - Status: {health.get('status')}")
            for service, status in health.get('services', {}).items():
                print(f"  - {service}: {status}")
        else:
            print(f"✗ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Health check error: {e}")
    
    # Test 3: Register user
    print("\n3. Testing user registration...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={"email": "test@example.com"}
        )
        if response.status_code == 200:
            print("✓ User registration successful")
            data = response.json()
            token = data.get('token')
            print(f"  - User ID: {data.get('user_id')}")
            print(f"  - Credits: {data.get('credits')}")
            print(f"  - Token: {token[:20]}...")
            return token
        else:
            print(f"✗ Registration failed: {response.status_code}")
            print(f"  - Error: {response.text}")
    except Exception as e:
        print(f"✗ Registration error: {e}")
    
    return None

def test_analysis(token):
    """Test analysis endpoint with authentication"""
    print("\n4. Testing analysis endpoint...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test with sample text
    test_data = {
        "text": "Our company reduced carbon emissions by 30% in 2023 through renewable energy initiatives. We also improved employee diversity with 45% female representation in leadership roles.",
        "company_name": "Test Corp",
        "quick_mode": True,
        "frameworks": ["CSRD", "GRI"]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/analyze",
            json=test_data,
            headers=headers
        )
        
        if response.status_code == 200:
            print("✓ Analysis successful")
            result = response.json()
            
            # Display scores
            if 'scores' in result:
                print("\n  ESG Scores:")
                scores = result['scores']
                print(f"    - Environmental: {scores.get('environmental', 0):.1f}")
                print(f"    - Social: {scores.get('social', 0):.1f}")
                print(f"    - Governance: {scores.get('governance', 0):.1f}")
                print(f"    - Overall: {scores.get('overall', 0):.1f}")
            
            # Display insights
            if 'insights' in result:
                print("\n  Insights:")
                for insight in result['insights'][:3]:
                    print(f"    - {insight}")
            
            # Display usage
            print(f"\n  Credits used: {result.get('credits_used', 0)}")
            print(f"  Credits remaining: {result.get('credits_remaining', 0)}")
            
        else:
            print(f"✗ Analysis failed: {response.status_code}")
            print(f"  - Error: {response.text}")
    
    except Exception as e:
        print(f"✗ Analysis error: {e}")

def test_frameworks():
    """Test frameworks endpoint"""
    print("\n5. Testing frameworks endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/frameworks")
        if response.status_code == 200:
            print("✓ Frameworks endpoint accessible")
            data = response.json()
            frameworks = data.get('frameworks', [])
            print(f"  - Available frameworks: {len(frameworks)}")
            for fw in frameworks:
                print(f"    - {fw['name']}: {fw['full_name']}")
        else:
            print(f"✗ Frameworks endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Frameworks error: {e}")

def main():
    """Run all tests"""
    # Test basic endpoints
    token = test_api()
    
    # Test authenticated endpoints if registration succeeded
    if token:
        test_analysis(token)
    
    # Test public endpoints
    test_frameworks()
    
    print("\n" + "=" * 50)
    print("Testing complete!")

if __name__ == "__main__":
    main() 