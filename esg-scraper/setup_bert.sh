#!/bin/bash
# BERT Integration Setup Script

set -e

echo "=== ESG Platform BERT Integration Setup ==="
echo

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running from correct directory
if [ ! -f "lean_esg_platform.py" ]; then
    echo -e "${RED}Error: Please run this script from the esg-scraper directory${NC}"
    exit 1
fi

# Function to check command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "Checking prerequisites..."

if ! command_exists python3; then
    echo -e "${RED}Python 3 is not installed${NC}"
    exit 1
fi

if ! command_exists pip; then
    echo -e "${RED}pip is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites satisfied${NC}"
echo

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing base requirements..."
pip install -r requirements_lean.txt

echo "Installing BERT requirements..."
pip install -r requirements_bert.txt

echo -e "${GREEN}✓ Dependencies installed${NC}"
echo

# Create necessary directories
echo "Creating directories..."
mkdir -p data logs bert_cache models
echo -e "${GREEN}✓ Directories created${NC}"
echo

# Download models (optional)
read -p "Do you want to pre-download BERT models now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Downloading BERT models..."
    python download_models.py
    echo -e "${GREEN}✓ Models downloaded${NC}"
fi
echo

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << EOF
# BERT Configuration
ENABLE_BERT=true
BERT_CACHE_DIR=./bert_cache
BERT_USE_GPU=false
BERT_MAX_LENGTH=512
BERT_BATCH_SIZE=8
BERT_CONFIDENCE_THRESHOLD=0.5

# Performance Settings
BERT_MODEL_TIMEOUT=30
BERT_MAX_WORKERS=2

# Other settings
JWT_SECRET=$(openssl rand -hex 32)
REDIS_URL=redis://localhost:6379
DATABASE_URL=sqlite:///./esg_analysis.db
LOG_LEVEL=INFO
EOF
    echo -e "${GREEN}✓ .env file created${NC}"
else
    echo -e "${YELLOW}.env file already exists${NC}"
fi

# Update main application to include BERT routes
echo "Checking main application integration..."
if ! grep -q "api_bert_integration" lean_esg_platform.py; then
    echo -e "${YELLOW}Note: You need to manually add BERT integration to lean_esg_platform.py${NC}"
    echo "Add these lines after creating the FastAPI app:"
    echo
    echo "from api_bert_integration import integrate_bert_routes"
    echo "if os.getenv('ENABLE_BERT', 'true').lower() == 'true':"
    echo "    integrate_bert_routes(app)"
    echo
fi

# Run tests
read -p "Do you want to run BERT integration tests? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Running tests..."
    pytest test_bert_integration.py -v
    echo -e "${GREEN}✓ Tests completed${NC}"
fi
echo

# Start services
echo -e "${GREEN}Setup complete!${NC}"
echo
echo "To start the BERT-enhanced platform:"
echo "1. With Docker:    docker-compose -f docker-compose.bert.yml up"
echo "2. Without Docker: uvicorn lean_esg_platform:app --reload"
echo
echo "API Documentation will be available at:"
echo "- http://localhost:8000/docs (Swagger UI)"
echo "- http://localhost:8000/redoc (ReDoc)"
echo
echo "BERT endpoints:"
echo "- POST /api/v2/bert/analyze - BERT-enhanced analysis"
echo "- POST /api/v2/bert/compare - Compare keyword vs BERT"
echo "- POST /api/v2/bert/greenwashing-check - Greenwashing detection"
echo "- GET  /api/v2/bert/performance - Performance statistics" 