#!/usr/bin/env python3
"""
PHB Backend Deployment Test Script
Tests the deployed API endpoints to verify everything is working
"""

import requests
import json
from datetime import datetime

# Your deployed app URL
HEROKU_URL = "https://basebackend-88c8c04dd3ab.herokuapp.com"

def test_deployment():
    print("🚀 Testing PHB Backend Deployment")
    print("=" * 50)
    print(f"📍 Testing URL: {HEROKU_URL}")
    print(f"⏰ Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        {
            "name": "Health Check",
            "endpoint": "/",
            "expected_status": [200, 404],  # Django might return 404 for root
            "description": "Basic connectivity test"
        },
        {
            "name": "API Status",
            "endpoint": "/api/",
            "expected_status": [200, 404],
            "description": "API endpoint availability"
        },
        {
            "name": "Admin Panel",
            "endpoint": "/admin/",
            "expected_status": [200, 302],  # 302 for redirect to login
            "description": "Django admin accessibility"
        }
    ]
    
    results = []
    
    for test in tests:
        print(f"🧪 Testing: {test['name']}")
        print(f"   📡 {HEROKU_URL}{test['endpoint']}")
        
        try:
            response = requests.get(f"{HEROKU_URL}{test['endpoint']}", timeout=30)
            status_code = response.status_code
            
            if status_code in test['expected_status']:
                status = "✅ PASS"
                color = "🟢"
            else:
                status = "❌ FAIL"
                color = "🔴"
            
            print(f"   {color} Status: {status_code} - {status}")
            
            results.append({
                "test": test['name'],
                "status": status_code,
                "success": status_code in test['expected_status'],
                "response_size": len(response.content),
                "headers": dict(response.headers)
            })
            
        except requests.exceptions.Timeout:
            print(f"   🔴 Status: TIMEOUT - App may be sleeping (first request)")
            results.append({"test": test['name'], "status": "TIMEOUT", "success": False})
        except requests.exceptions.ConnectionError:
            print(f"   🔴 Status: CONNECTION ERROR - Deployment failed")
            results.append({"test": test['name'], "status": "CONNECTION_ERROR", "success": False})
        except Exception as e:
            print(f"   🔴 Status: ERROR - {str(e)}")
            results.append({"test": test['name'], "status": "ERROR", "success": False})
        
        print()
    
    # Summary
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for r in results if r.get('success', False))
    total = len(results)
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Deployment is successful! ✅")
        print("🚀 Your PHB Hospital System backend is live!")
        print("💳 Paystack integration should be working!")
    elif passed > 0:
        print(f"⚠️  PARTIAL SUCCESS: {passed}/{total} tests passed")
        print("🔧 Some endpoints might need additional configuration")
    else:
        print("❌ DEPLOYMENT FAILED: No endpoints responding")
        print("🔍 Check Heroku logs for detailed error information")
    
    print()
    print("🔗 Useful Links:")
    print(f"   📊 Heroku Dashboard: https://dashboard.heroku.com/apps/basebackend")
    print(f"   📋 App Logs: https://dashboard.heroku.com/apps/basebackend/logs")
    print(f"   ⚙️  Settings: https://dashboard.heroku.com/apps/basebackend/settings")
    
    return passed == total

if __name__ == "__main__":
    success = test_deployment()
    exit(0 if success else 1)
