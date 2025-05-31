#!/usr/bin/env python3
"""
Test Upstash Redis Connection
=============================

Verifies that the Upstash Redis connection is working properly
"""

import os
import sys
import redis
import ssl
import time
import json

def test_upstash_connection():
    """Test connection to Upstash Redis"""
    
    # Get Redis URL from environment
    redis_url = os.getenv("UPSTASH_REDIS_URL") or os.getenv("REDIS_URL")
    
    if not redis_url:
        print("❌ No Redis URL found in environment variables")
        print("   Set either UPSTASH_REDIS_URL or REDIS_URL")
        return False
    
    print(f"🔍 Testing Upstash Redis connection...")
    print(f"   URL: {redis_url.split('@')[1] if '@' in redis_url else redis_url}")
    
    try:
        # Connect with SSL (Upstash requires SSL)
        if redis_url.startswith('rediss://'):
            client = redis.from_url(
                redis_url,
                decode_responses=True,
                ssl_cert_reqs=ssl.CERT_NONE  # Upstash uses self-signed certs
            )
        else:
            client = redis.from_url(redis_url, decode_responses=True)
        
        # Test basic operations
        print("\n1. Testing connection...")
        client.ping()
        print("   ✅ Connected successfully")
        
        # Test write
        print("\n2. Testing write operation...")
        test_key = f"test:upstash:{int(time.time())}"
        test_value = {"test": "data", "timestamp": time.time()}
        client.set(test_key, json.dumps(test_value))
        print(f"   ✅ Written test key: {test_key}")
        
        # Test read
        print("\n3. Testing read operation...")
        retrieved = client.get(test_key)
        if retrieved:
            data = json.loads(retrieved)
            print(f"   ✅ Retrieved data: {data}")
        else:
            print("   ❌ Failed to retrieve data")
            return False
        
        # Test TTL
        print("\n4. Testing TTL operation...")
        client.expire(test_key, 60)
        ttl = client.ttl(test_key)
        print(f"   ✅ TTL set to {ttl} seconds")
        
        # Test delete
        print("\n5. Testing delete operation...")
        client.delete(test_key)
        print("   ✅ Deleted test key")
        
        # Get server info
        print("\n6. Server information:")
        info = client.info()
        print(f"   - Redis version: {info.get('redis_version', 'unknown')}")
        print(f"   - Used memory: {info.get('used_memory_human', 'unknown')}")
        print(f"   - Connected clients: {info.get('connected_clients', 'unknown')}")
        print(f"   - Total commands processed: {info.get('total_commands_processed', 'unknown')}")
        
        # Test rate limiter compatibility
        print("\n7. Testing rate limiter compatibility...")
        rate_limit_key = "rate_limit:test:user"
        client.incr(rate_limit_key)
        client.expire(rate_limit_key, 60)
        count = client.get(rate_limit_key)
        print(f"   ✅ Rate limiter compatible (count: {count})")
        
        print("\n✅ All tests passed! Upstash Redis is ready for use.")
        return True
        
    except Exception as e:
        print(f"\n❌ Connection failed: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Verify the UPSTASH_REDIS_URL is correct")
        print("2. Check if the URL includes 'rediss://' for SSL")
        print("3. Ensure the token has not expired")
        print("4. Try the REST API URL if Redis protocol fails")
        return False
    
    finally:
        try:
            client.close()
        except:
            pass


def test_upstash_rest_api():
    """Test Upstash REST API as fallback"""
    rest_url = os.getenv("UPSTASH_REDIS_REST_URL")
    rest_token = os.getenv("UPSTASH_REDIS_REST_TOKEN")
    
    if not rest_url or not rest_token:
        print("\n⚠️  REST API credentials not found")
        return
    
    print("\n🔍 Testing Upstash REST API...")
    
    try:
        import httpx
        
        # Test SET command
        response = httpx.post(
            f"{rest_url}/set/test:rest/hello",
            headers={"Authorization": f"Bearer {rest_token}"}
        )
        
        if response.status_code == 200:
            print("   ✅ REST API working")
            print(f"   Response: {response.json()}")
        else:
            print(f"   ❌ REST API failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ REST API error: {e}")


if __name__ == "__main__":
    print("🚀 Upstash Redis Connection Test")
    print("=" * 50)
    
    # Test Redis protocol
    success = test_upstash_connection()
    
    # Test REST API as fallback
    if not success:
        test_upstash_rest_api()
    
    print("\n" + "=" * 50)
    
    if success:
        print("✅ Upstash Redis is properly configured and ready!")
        print("\nNext steps:")
        print("1. The REDIS_URL in app.yaml is now mapped to UPSTASH_REDIS_URL")
        print("2. No code changes needed - SSL support is already implemented")
        print("3. Deploy the application to use Upstash Redis")
        sys.exit(0)
    else:
        print("❌ Upstash Redis connection test failed")
        print("\nPlease check the configuration and try again")
        sys.exit(1) 