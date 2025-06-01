#!/bin/bash

# ESG Intelligence Platform - Startup Script
# Optimized for production deployment

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting ESG Intelligence Platform...${NC}"

# Check environment
if [ -z "$JWT_SECRET" ]; then
    echo -e "${RED}ERROR: JWT_SECRET environment variable is not set!${NC}"
    echo "Please set it using: export JWT_SECRET=your-secret-key-here"
    exit 1
fi

# Set default environment variables
export PORT=${PORT:-8000}
export ENABLE_BERT=${ENABLE_BERT:-true}
export ENABLE_METRICS=${ENABLE_METRICS:-true}
export UPSTASH_REDIS_URL=${UPSTASH_REDIS_URL:-redis://localhost:6379}
export DATABASE_URL=${DATABASE_URL:-sqlite:///./esg_data.db}
export ENV=${ENV:-production}

# Check if Redis is running (optional)
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        echo -e "${GREEN}✓ Redis is running${NC}"
    else
        echo -e "${YELLOW}⚠ Redis is not running. Some features may be limited.${NC}"
    fi
fi

# Install dependencies if needed
if [ ! -d "venv" ] && [ "$1" != "--no-venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip install -r requirements.txt
elif [ -d "venv" ] && [ "$1" != "--no-venv" ]; then
    source venv/bin/activate
fi

# Pre-download BERT models if enabled (optional)
if [ "$ENABLE_BERT" = "true" ] && [ "$1" = "--download-models" ]; then
    echo -e "${YELLOW}Pre-downloading BERT models...${NC}"
    python -c "from bert_service_simple import download_models; download_models()"
fi

# Start the application
echo -e "${GREEN}Starting application on port $PORT...${NC}"
echo -e "${GREEN}Features enabled:${NC}"
echo -e "  - BERT Analysis: $ENABLE_BERT"
echo -e "  - Metrics Extraction: $ENABLE_METRICS"
echo -e "  - Environment: $ENV"

if [ "$ENV" = "development" ]; then
    # Development mode with auto-reload
    python -m uvicorn main:app --host 0.0.0.0 --port $PORT --reload
else
    # Production mode with workers
    python -m uvicorn main:app --host 0.0.0.0 --port $PORT --workers 4
fi 