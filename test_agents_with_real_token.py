#!/usr/bin/env python
"""
Real Token API Testing Script for Women's Health Agents

This script uses a real authentication token to test all agent endpoints.
"""

import requests
import json
import time
from datetime import datetime

class RealTokenTester:
    """API tester using real authentication token."""
    
    def __init__(self, base_url='http://localhost:8001'):
        self.base_url = base_url
        self.api_base = f"{base_url}/api"
        # Real token provided by user
        self.token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzUwOTU0NDQ4LCJpYXQiOjE3NTA5NTI2NDgsImp0aSI6IjZjZjA3MzUyZWI5YTRhNjVhNDhiMjdiZGMyYjJiYTU5IiwidXNlcl9pZCI6NH0.51ztu7bfPInN0gGFlcm0O7k56Jc2d5nHV4NVMKE5PUc"
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        self.results = []
        
    def test_endpoint(self, name, method, endpoint, data=None):
        """Test a single endpoint."""
        url = f"{self.api_base}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=self.headers)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=self.headers, json=data or {})
            else:
                response = requests.request(method, url, headers=self.headers, json=data or {})
            
            success = response.status_code in [200, 201]
            result = {
                'name': name,
                'success': success,
                'status': response.status_code,
                'endpoint': endpoint,
                'method': method
            }
            
            if success:
                try:
                    result['response'] = response.json()
                except:
                    result['response'] = response.text[:200]
                print(f"✅ PASS - {name} ({response.status_code})")
            else:
                try:
                    result['error'] = response.json()
                except:
                    result['error'] = response.text[:200]
                print(f"❌ FAIL - {name} ({response.status_code})")
                
            self.results.append(result)
            return success
            
        except Exception as e:
            print(f"❌ ERROR - {name}: {str(e)}")
            self.results.append({
                'name': name,
                'success': False,
                'error': str(e),
                'endpoint': endpoint,
                'method': method
            })
            return False
    
    def check_server(self):
        """Check if Django server is running."""
        try:
            response = requests.get(f"{self.api_base}/health-check/", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def run_all_tests(self):
        """Run comprehensive tests on all agent endpoints."""
        print("🚀 Starting Real Token API Testing")
        print("=" * 60)
        
        # Check server
        if not self.check_server():
            print("❌ Django server not accessible at", self.base_url)
            return
        print("✅ Django server is running")
        
        # Test Health Check
        print("\n🏥 Testing Health Check...")
        self.test_endpoint("Health Check", "GET", "/health-check/")
        
        # Test Agent Health Check
        print("\n🔍 Testing Agent Health Check...")
        self.test_endpoint("Agent Health Check", "GET", "/agents/health/")
        
        # Test Analytics Agent
        print("\n🧠 Testing Analytics Agent...")
        self.test_endpoint("Analytics Status", "GET", "/agents/analytics/status/")
        self.test_endpoint("Cycle Irregularities", "POST", "/agents/analytics/cycle-irregularities/", {})
        self.test_endpoint("Predict Period", "POST", "/agents/analytics/predict-period/", {})
        self.test_endpoint("Predict Fertility", "POST", "/agents/analytics/predict-fertility/", {})
        self.test_endpoint("Health Insights", "POST", "/agents/analytics/health-insights/", {})
        self.test_endpoint("Recommendations", "POST", "/agents/analytics/recommendations/", {})
        self.test_endpoint("Health Risks", "POST", "/agents/analytics/health-risks/", {})
        self.test_endpoint("Analyze Patterns", "POST", "/agents/analytics/analyze-patterns/", {})
        
        # Test Performance Agent (might need admin privileges)
        print("\n⚡ Testing Performance Agent...")
        self.test_endpoint("Performance Status", "GET", "/agents/performance/status/")
        self.test_endpoint("Optimize Database", "POST", "/agents/performance/optimize-database/", {})
        self.test_endpoint("Refresh Cache", "POST", "/agents/performance/refresh-cache/", {})
        self.test_endpoint("Monitor Performance", "GET", "/agents/performance/monitor-performance/")
        
        # Test Clinical Agent
        print("\n🏥 Testing Clinical Agent...")
        self.test_endpoint("Clinical Status", "GET", "/agents/clinical/status/")
        self.test_endpoint("Screening Recommendations", "POST", "/agents/clinical/screening-recommendations/", {})
        self.test_endpoint("Schedule Appointment", "POST", "/agents/clinical/schedule-appointment/", {})
        self.test_endpoint("Update Medical History", "POST", "/agents/clinical/update-medical-history/", {})
        self.test_endpoint("Medical History Summary", "GET", "/agents/clinical/medical-history-summary/")
        
        # Generate Report
        self.generate_report()
    
    def generate_report(self):
        """Generate test report."""
        print("\n" + "=" * 60)
        print("📊 TEST REPORT")
        print("=" * 60)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r['success'])
        failed = total - passed
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        
        if failed > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.results:
                if not result['success']:
                    print(f"  - {result['name']}: {result.get('status', 'Error')}")
        
        if passed > 0:
            print(f"\n✅ PASSED TESTS:")
            for result in self.results:
                if result['success']:
                    print(f"  - {result['name']}: {result.get('status', 'Success')}")
        
        # Save detailed report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"real_token_test_report_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'total': total,
                    'passed': passed,
                    'failed': failed,
                    'success_rate': f"{passed/total*100:.1f}%"
                },
                'results': self.results
            }, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {filename}")

if __name__ == "__main__":
    tester = RealTokenTester()
    tester.run_all_tests()