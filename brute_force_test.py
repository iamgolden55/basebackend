import requests
import time
import random

# 🔧 Configuration
LOGIN_URL = "http://localhost:8000/api/login/"  # Updated to test the login endpoint
EMAIL = "eruwagolden55@gmail.com"  # Updated to use email instead of username

# Extended wordlist for testing rate limiting
WORDLIST = [
    "password", "123456", "phb1234", "admin123", "test@123", "letmein",
    "qwerty", "welcome", "monkey", "password1", "abc123", "football", 
    "12345678", "dragon", "sunshine", "princess", "trustno1", "iloveyou",
    "testpass", "testuser", "newpass", "secure123", "hospital", "medical123",
    "doctor123", "nurse123", "health123", "patient123", "phb2023"
]

DELAY_BETWEEN_ATTEMPTS = 0.5  # In seconds

def attempt_login(password):
    data = {
        "email": EMAIL,  # Use email instead of username
        "password": password
    }
    start_time = time.time()
    response = requests.post(LOGIN_URL, json=data)
    end_time = time.time()
    
    # Calculate response time
    response_time = round((end_time - start_time) * 1000, 2)  # Convert to milliseconds
    
    # Handle different response status codes
    status_message = "❌ Failed"
    
    # Check for rate limiting (429 status code)
    if response.status_code == 429:
        status_message = "🚫 Rate limited"
        return False, None, response_time, f"{status_message} - Too many attempts (HTTP 429)"
    
    # Check for successful login with OTP requirement
    if response.status_code == 200 and response.json().get("require_otp") == True:
        return True, "OTP required", response_time, "✅ Success (OTP required)"
    
    # Extract error message if possible
    error_detail = "Unknown error"
    try:
        error_detail = response.json().get("message", response.json().get("detail", error_detail))
    except:
        pass
        
    return False, None, response_time, f"{status_message} - {error_detail} (HTTP {response.status_code})"

def run_brute_force():
    print(f"🔐 Starting advanced brute force test on {LOGIN_URL} as {USERNAME}...")
    print(f"🔢 Testing {len(WORDLIST)} different passwords with {DELAY_BETWEEN_ATTEMPTS}s delay between attempts")
    print("="*80)
    
    successful = False
    total_attempts = 0
    rate_limits_hit = 0
    response_times = []
    
    for i, password in enumerate(WORDLIST, 1):
        total_attempts += 1
        print(f"[{i}/{len(WORDLIST)}] Trying: {password}")
        
        success, token, response_time, status = attempt_login(password)
        response_times.append(response_time)
        
        if "Rate limited" in status:
            rate_limits_hit += 1
            print(f"{status} - Response time: {response_time}ms 🐢")
        else:
            print(f"{status} - Response time: {response_time}ms")
        
        if success:
            print(f"\n✅ Successfully authenticated with password: {password}")
            print(f"🔑 JWT Token: {token[:20]}...")
            successful = True
            break
            
        time.sleep(DELAY_BETWEEN_ATTEMPTS)
    
    # Print test statistics
    print("\n" + "="*80)
    print("📊 BRUTE FORCE TEST SUMMARY")
    print("="*80)
    print(f"🔢 Total attempts: {total_attempts}")
    print(f"🚫 Rate limits encountered: {rate_limits_hit}")
    
    if response_times:
        avg_time = sum(response_times) / len(response_times)
        print(f"⏱️ Average response time: {avg_time:.2f}ms")
        print(f"⏱️ Min response time: {min(response_times):.2f}ms")
        print(f"⏱️ Max response time: {max(response_times):.2f}ms")
    
    if not successful:
        if rate_limits_hit > 0:
            print("\n🛡️ The login endpoint is protected by rate limiting!")
            print("🧠 Brute force attacks are being actively mitigated.")
        else:
            print("\n🚫 All login attempts failed, but no rate limiting was detected.")
            print("⚠️ The system might be vulnerable to sustained brute force attacks.")

if __name__ == "__main__":
    run_brute_force()
