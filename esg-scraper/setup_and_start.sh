#!/bin/bash
set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}       ESG Intelligence Platform - Setup & Start        ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"

# Function to check environment variable
check_env() {
    if [ -z "${!1}" ]; then
        echo -e "${RED}❌ $1 not set!${NC}"
        return 1
    else
        echo -e "${GREEN}✓ $1 is configured${NC}"
        return 0
    fi
}

# Step 1: Verify critical environment variables
echo -e "\n${YELLOW}Step 1: Checking environment configuration...${NC}"
ERRORS=0

check_env "PGPASSWORD" || ((ERRORS++))
check_env "PGUSER" || ((ERRORS++))
check_env "PGHOST" || ((ERRORS++))
check_env "UPSTASH_REDIS_URL" || ((ERRORS++))
check_env "JWT_SECRET" || ((ERRORS++))

if [ $ERRORS -gt 0 ]; then
    echo -e "${RED}❌ Missing required environment variables!${NC}"
    exit 1
fi

# Step 2: Set production environment and defaults
echo -e "\n${YELLOW}Step 2: Setting up environment...${NC}"
export ENVIRONMENT="production"
export PGUSER=${PGUSER:-"doadmin"}
export PGPORT=${PGPORT:-"25060"}
export PGDATABASE=${PGDATABASE:-"defaultdb"}
export PGSSLMODE=${PGSSLMODE:-"require"}
export PORT=${PORT:-"8000"}
export WORKERS=${WORKERS:-"1"}
export LOG_LEVEL=${LOG_LEVEL:-"info"}

# Display connection info (without sensitive data)
echo -e "${GREEN}Environment configured:${NC}"
echo "   PostgreSQL: $PGUSER@$PGHOST:$PGPORT/$PGDATABASE"
echo "   Redis: Configured"
echo "   Port: $PORT"
echo "   Workers: $WORKERS"

# Step 3: Initialize database (first time only)
if [ "$SKIP_DB_INIT" != "true" ]; then
    echo -e "\n${YELLOW}Step 3: Checking database initialization...${NC}"
    
    # Check if we can connect to PostgreSQL
    if python -c "
import os
import asyncio
import sys
sys.path.insert(0, '/app')
from postgresql_manager import get_postgresql_manager

async def check():
    try:
        manager = get_postgresql_manager()
        await manager.initialize()
        await manager.close()
        return True
    except Exception as e:
        print(f'Database check failed: {e}')
        return False

result = asyncio.run(check())
sys.exit(0 if result else 1)
" 2>/dev/null; then
        echo -e "${GREEN}✓ Database connection successful${NC}"
        
        # Run initialization if needed
        if [ "$RUN_DB_INIT" = "true" ] || [ ! -f "/app/.db_initialized" ]; then
            echo -e "${YELLOW}Running database initialization...${NC}"
            if python /app/init_database.py; then
                echo -e "${GREEN}✓ Database initialized successfully${NC}"
                touch /app/.db_initialized
            else
                echo -e "${YELLOW}⚠ Database initialization failed (may already be initialized)${NC}"
            fi
        fi
    else
        echo -e "${RED}❌ Could not connect to database!${NC}"
        echo "Please check your PostgreSQL connection settings."
        exit 1
    fi
else
    echo -e "${YELLOW}Skipping database initialization (SKIP_DB_INIT=true)${NC}"
fi

# Step 4: Health check before starting
echo -e "\n${YELLOW}Step 4: Running pre-start health check...${NC}"
if python /app/health_check.py 2>/dev/null; then
    echo -e "${GREEN}✓ Health check passed${NC}"
else
    echo -e "${YELLOW}⚠ Health check failed, but continuing...${NC}"
fi

# Step 5: Start the application
echo -e "\n${YELLOW}Step 5: Starting ESG Intelligence API...${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🚀 Starting application on port $PORT${NC}"
echo -e "${GREEN}   PostgreSQL: Connected to managed cluster${NC}"
echo -e "${GREEN}   Redis: Connected to managed instance${NC}"
echo -e "${GREEN}   Mode: Production${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}\n"

# Start with Gunicorn
exec gunicorn lean_esg_platform:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers ${WORKERS} \
    --bind 0.0.0.0:${PORT} \
    --access-logfile - \
    --error-logfile - \
    --log-level ${LOG_LEVEL} \
    --timeout 120 \
    --graceful-timeout 30 \
    --preload