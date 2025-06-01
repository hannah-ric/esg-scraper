#!/bin/bash

# Production startup script for ESG Scraper
set -e

echo "🚀 Starting ESG Scraper in production mode..."

# Verify environment variables
echo "🔍 Checking environment configuration..."
if [ -z "$PGPASSWORD" ]; then
    echo "❌ PGPASSWORD not set!"
    exit 1
fi

if [ -z "$JWT_SECRET" ]; then
    echo "❌ JWT_SECRET not set!"
    exit 1
fi

if [ -z "$UPSTASH_REDIS_URL" ]; then
    echo "❌ UPSTASH_REDIS_URL not set!"
    exit 1
fi

echo "✅ Environment variables configured"

# Test PostgreSQL connection
echo "🗄️  Testing PostgreSQL connection..."
python -c "
import os
import asyncio
from postgresql_manager import get_postgresql_manager

async def test_connection():
    try:
        manager = get_postgresql_manager()
        await manager.initialize()
        health = await manager.health_check()
        if health['status'] == 'healthy':
            print('✅ PostgreSQL connection successful')
            print(f'   Version: {health.get(\"version\")}')
        else:
            print('❌ PostgreSQL connection failed')
            return False
        return True
    except Exception as e:
        print(f'❌ PostgreSQL connection error: {e}')
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

# Set production environment
export ENVIRONMENT="production"
export PGPASSWORD=${PGPASSWORD}
export PGUSER=${PGUSER:-"doadmin"}
export PGHOST=${PGHOST}
export PGPORT=${PGPORT:-"25060"}
export PGDATABASE=${PGDATABASE:-"defaultdb"}
export PGSSLMODE=${PGSSLMODE:-"require"}
export UPSTASH_REDIS_URL=${UPSTASH_REDIS_URL}
export JWT_SECRET=${JWT_SECRET}

echo "🌐 Starting ESG Scraper API server..."
echo "   PostgreSQL: Connected to managed cluster"
echo "   Redis: Connected to managed instance"
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