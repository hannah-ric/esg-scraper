#!/bin/bash

# Production startup script for ESG Scraper
set -e

echo "🚀 Starting ESG Scraper in production mode..."

# Start Redis in the background
echo "📦 Starting Redis server..."
redis-server --daemonize yes --bind 0.0.0.0 --port 6379

# Wait for Redis to start
sleep 2

# Check Redis connection
redis-cli ping || {
    echo "❌ Redis connection failed"
    exit 1
}

echo "✅ Redis server started successfully"

# Initialize database if it doesn't exist
echo "🗄️  Initializing database..."
python -c "
import os
from database_schema import EnhancedDatabaseManager

# Create database manager and initialize schema
db_path = os.getenv('DATABASE_PATH', '/app/data/esg_data.db')
print(f'Initializing database at: {db_path}')

try:
    db_manager = EnhancedDatabaseManager(db_path)
    print('✅ Database initialized successfully')
except Exception as e:
    print(f'❌ Database initialization failed: {e}')
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
export JWT_SECRET=${JWT_SECRET:-"production-secret-change-me-in-env"}
export DATABASE_PATH=${DATABASE_PATH:-"/app/data/esg_data.db"}
export REDIS_URL=${REDIS_URL:-"redis://localhost:6379"}
export FREE_TIER_CREDITS=${FREE_TIER_CREDITS:-"1000"}

echo "🌐 Starting ESG Scraper API server..."
echo "   Database: $DATABASE_PATH"
echo "   Redis: $REDIS_URL"
echo "   Port: 8000"

# Start the FastAPI application with Gunicorn for production
exec python -m gunicorn lean_esg_platform:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers ${WORKERS:-2} \
    --bind 0.0.0.0:8000 \
    --timeout 300 \
    --keepalive 2 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --access-logfile - \
    --error-logfile - \
    --log-level info 