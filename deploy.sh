#!/bin/bash

# ESG Platform Deployment Script
# This script handles the deployment of the ESG scraping service

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p ssl
mkdir -p logs
mkdir -p data

# Check for environment file
if [ ! -f ".env" ]; then
    print_warning ".env file not found. Creating from example..."
    if [ -f "esg-scraper/.env.example" ]; then
        cp esg-scraper/.env.example .env
        print_warning "Please edit .env file with your configuration before running again."
        exit 1
    else
        print_error ".env.example file not found. Please create .env file manually."
        exit 1
    fi
fi

# Generate self-signed SSL certificates if they don't exist
if [ ! -f "ssl/cert.pem" ] || [ ! -f "ssl/key.pem" ]; then
    print_status "Generating self-signed SSL certificates..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout ssl/key.pem \
        -out ssl/cert.pem \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
fi

# Build or rebuild services
print_status "Building Docker images..."
cd esg-scraper
docker-compose build --no-cache

# Stop existing containers
print_status "Stopping existing containers..."
docker-compose down

# Start services
print_status "Starting services..."
docker-compose up -d

# Wait for services to be healthy
print_status "Waiting for services to be healthy..."
sleep 10

# Check service health
print_status "Checking service health..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    print_status "API service is healthy!"
else
    print_error "API service health check failed!"
    docker-compose logs api
    exit 1
fi

# Run database migrations (if needed)
print_status "Initializing database..."
docker-compose exec -T api python -c "
from lean_esg_platform import db_manager
print('Database initialized successfully!')
"

# Display service information
print_status "Deployment completed successfully!"
echo ""
echo "Service URLs:"
echo "  - API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - Metrics: http://localhost:8000/metrics"
echo "  - Grafana: http://localhost:3000 (admin/admin)"
echo "  - Prometheus: http://localhost:9090"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""
echo "To stop services:"
echo "  docker-compose down"
echo ""

# Optional: Run tests
read -p "Do you want to run tests? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Running tests..."
    docker-compose exec api python test_esg_service.py
fi 