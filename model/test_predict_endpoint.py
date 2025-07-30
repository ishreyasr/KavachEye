#!/usr/bin/env python3
"""
Test script for the new /predict endpoint
"""

import requests
import json
from datetime import datetime

# Backend URL
BASE_URL = "http://localhost:5000"

def test_predict_endpoint():
    """Test the /predict endpoint with various scenarios"""
    
    test_cases = [
        {
            "name": "Safe daytime location",
            "data": {
                "location": "shopping mall",
                "time": "2024-01-15T14:30:00"
            }
        },
        {
            "name": "Risky nighttime location",
            "data": {
                "location": "downtown parking lot",
                "time": "2024-01-15T23:45:00"
            }
        },
        {
            "name": "Moderate evening residential",
            "data": {
                "location": "residential area",
                "time": "2024-01-15T19:30:00"
            }
        },
        {
            "name": "High risk industrial night",
            "data": {
                "location": "industrial zone",
                "time": "2024-01-15T02:15:00"
            }
        }
    ]
    
    print("Testing /predict endpoint...")
    print("=" * 50)
    
    for test_case in test_cases:
        print(f"\nTest: {test_case['name']}")
        print(f"Input: {test_case['data']}")
        
        try:
            response = requests.post(
                f"{BASE_URL}/predict",
                json=test_case['data'],
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Success!")
                print(f"Safety Level: {result['safety_level']}")
                print(f"Safety Score: {result['safety_score']}")
                print(f"Risk Factors: {result['risk_factors']}")
                print(f"Recommendations: {result['recommendations'][:2]}...")  # Show first 2 recommendations
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Connection Error: Make sure the Flask server is running on localhost:5000")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        print("-" * 30)

def test_error_cases():
    """Test error handling"""
    print("\nTesting error cases...")
    print("=" * 50)
    
    error_cases = [
        {
            "name": "Missing location",
            "data": {"time": "2024-01-15T14:30:00"}
        },
        {
            "name": "Missing time",
            "data": {"location": "downtown"}
        },
        {
            "name": "Empty request",
            "data": {}
        }
    ]
    
    for test_case in error_cases:
        print(f"\nTest: {test_case['name']}")
        print(f"Input: {test_case['data']}")
        
        try:
            response = requests.post(
                f"{BASE_URL}/predict",
                json=test_case['data'],
                headers={'Content-Type': 'application/json'}
            )
            
            print(f"Status Code: {response.status_code}")
            result = response.json()
            print(f"Response: {result}")
            
        except requests.exceptions.ConnectionError:
            print("❌ Connection Error: Make sure the Flask server is running on localhost:5000")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        print("-" * 30)

if __name__ == "__main__":
    print("Women Safety Analytics - Predict Endpoint Test")
    print("Make sure to start the Flask server first:")
    print("python complete.py")
    print()
    
    test_predict_endpoint()
    test_error_cases()
    
    print("\n" + "=" * 50)
    print("Test completed!")
    print("\nExample curl command:")
    print('curl -X POST http://localhost:5000/predict \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"location": "downtown", "time": "2024-01-15T22:30:00"}\'')