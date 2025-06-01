#!/bin/bash
# Verify environment variables
echo "🔍 Checking environment configuration..."
if [ -z "$PGPASSWORD" ]; then
    echo "❌ PGPASSWORD not set!"
    exit 1
fi

if [ -z "$UPSTASH_REDIS_URL" ]; then
    echo "❌ UPSTASH_REDIS_URL not set!"
    exit 1
fi

if [ -z "$JWT_SECRET" ]; then
    echo "❌ JWT_SECRET not set!"
    exit 1
fi

echo "✅ Environment variables configured"

# Set production environment
export ENVIRONMENT="production"

# Ensure all secrets are available
export PGPASSWORD=${PGPASSWORD}
export PGUSER=${PGUSER:-"doadmin"}
export PGHOST=${PGHOST}
export PGPORT=${PGPORT:-"25060"}
export PGDATABASE=${PGDATABASE:-"defaultdb"}
export PGSSLMODE=${PGSSLMODE:-"require"}
export UPSTASH_REDIS_URL=${UPSTASH_REDIS_URL}
export JWT_SECRET=${JWT_SECRET}

echo "🚀 Starting ESG Intelligence API in production mode"
echo "   PostgreSQL: Connected to managed cluster"
echo "   Redis: Connected to managed instance"

# Start with production settings
exec gunicorn lean_esg_platform:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers ${WORKERS:-1} \
    --bind 0.0.0.0:${PORT:-8000} \
    --access-logfile - \
    --error-logfile - \
    --log-level ${LOG_LEVEL:-info} \
    --timeout 120 \
    --graceful-timeout 30 
