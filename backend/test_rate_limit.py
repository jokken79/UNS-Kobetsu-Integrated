#!/usr/bin/env python3
"""
Test script to verify rate limiting configuration syntax
"""

import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Try to import the rate limit module
    from app.core.rate_limit import (
        limiter,
        RateLimits,
        rate_limit_exceeded_handler,
        get_rate_limit_string
    )
    print("✅ Rate limit module imported successfully")

    # Test rate limit strings
    print("\n📊 Rate Limit Configurations:")
    print(f"  AUTH_LOGIN: {RateLimits.AUTH_LOGIN}")
    print(f"  AUTH_REGISTER: {RateLimits.AUTH_REGISTER}")
    print(f"  AUTH_REFRESH: {RateLimits.AUTH_REFRESH}")
    print(f"  IMPORT_PREVIEW: {RateLimits.IMPORT_PREVIEW}")
    print(f"  IMPORT_EXECUTE: {RateLimits.IMPORT_EXECUTE}")
    print(f"  CRUD_READ: {RateLimits.CRUD_READ}")
    print(f"  CRUD_WRITE: {RateLimits.CRUD_WRITE}")

    # Test get_rate_limit_string function
    print("\n🔧 Testing get_rate_limit_string function:")
    print(f"  auth_login: {get_rate_limit_string('auth_login')}")
    print(f"  import_execute: {get_rate_limit_string('import_execute')}")
    print(f"  default: {get_rate_limit_string('unknown')}")

    print("\n✅ All rate limiting configuration tests passed!")

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\nNote: slowapi needs to be installed. Run:")
    print("pip install slowapi==0.1.9")
    sys.exit(1)

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)