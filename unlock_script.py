from django.core.cache import cache

# Email to unlock
email = "eruwagolden55@gmail.com"

# Clear all lockout-related cache entries
cache_keys = [
    f"account_lockout:{email}",
    f"account_lockout_expiry:{email}",
    f"account_attempts:{email}",
    f"login_attempts:{email}"
]

for key in cache_keys:
    cache.delete(key)

# Set the verified reset flag to bypass future checks
verified_key = f"verified_reset:{email}"
cache.set(verified_key, True, 86400)  # 24 hours

print(f"Account {email} has been successfully unlocked")
