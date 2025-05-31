#!/bin/bash

# Production startup script for ESG Scraper
set -e

echo "🚀 Starting ESG Scraper in production mode..."

# Verify environment variables
echo "🔍 Checking environment configuration..."
if [ -z "$MONGODB_URI" ]; then
    echo "❌ MONGODB_URI not set!"
    exit 1
fi

if [ -z "$JWT_SECRET" ]; then
    echo "❌ JWT_SECRET not set!"
    exit 1
fi

if [ -z "$REDIS_URL" ]; then
    echo "❌ REDIS_URL not set!"
    exit 1
fi

echo "✅ Environment variables configured"

# Test MongoDB connection
echo "🗄️  Testing MongoDB connection..."
python -c "
import os
import asyncio
from mongodb_manager import get_mongodb_manager

async def test_connection():
    try:
        manager = get_mongodb_manager()
        health = await manager.health_check()
        if health['status'] == 'healthy':
            print('✅ MongoDB connection successful')
            print(f'   Version: {health.get(\"version\")}')
        else:
            print('❌ MongoDB connection failed')
            return False
        return True
    except Exception as e:
        print(f'❌ MongoDB connection error: {e}')
        return False

success = asyncio.run(test_connection())
if not success:
    exit(1)
"

# Verify critical components
echo "🔍 Verifying ESG components..."
python -c "
try:
    from esg_frameworks import ESGFrameworkManager
    manager = ESGFrameworkManager()
    frameworks = manager.get_framework_summary()
    print(f'✅ ESG Framework Manager loaded with {len(frameworks)} frameworks')
except Exception as e:
    print(f'❌ ESG Framework loading failed: {e}')
    exit(1)
"

# Set production defaults
export JWT_SECRET=${JWT_SECRET}
export MONGODB_URI=${MONGODB_URI}
export MONGODB_DATABASE=${MONGODB_DATABASE:-"admin"}
export REDIS_URL=${REDIS_URL}
export FREE_TIER_CREDITS=${FREE_TIER_CREDITS:-"100"}

echo "🌐 Starting ESG Scraper API server..."
echo "   MongoDB: Connected to managed cluster"
echo "   Redis: $REDIS_URL"
echo "   Port: 8000"
echo "   Workers: ${WORKERS:-1}"

# Start the FastAPI application with Gunicorn for production
exec python -m gunicorn lean_esg_platform:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers ${WORKERS:-1} \
    --bind 0.0.0.0:8000 \
    --timeout 300 \
    --keepalive 2 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --access-logfile - \
    --error-logfile - \
    --log-level info 