# Complete Deployment Guide: GitHub + DigitalOcean

This guide will walk you through deploying your ESG Analyzer with a beautiful modern UI to DigitalOcean using GitHub for version control and CI/CD.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [GitHub Setup](#github-setup)
3. [DigitalOcean Setup](#digitalocean-setup)
4. [Frontend Deployment](#frontend-deployment)
5. [Backend Deployment](#backend-deployment)
6. [CI/CD Pipeline](#cicd-pipeline)
7. [Domain & SSL Setup](#domain--ssl-setup)
8. [Monitoring & Maintenance](#monitoring--maintenance)

## Prerequisites

- GitHub account
- DigitalOcean account with billing enabled
- Domain name (optional but recommended)
- Local development environment set up

## GitHub Setup

### 1. Create GitHub Repository

```bash
# Initialize git in your project
cd /Users/hannahricci/esg-scraper
git init

# Create .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# Environment
.env
.env.local
.env.*.local

# Database
*.db
*.sqlite3

# Logs
logs/
*.log

# BERT models
bert_cache/
models/
*.bin
*.safetensors

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Dependencies
node_modules/
dist/
build/

# Secrets
*.pem
*.key
*.crt
EOF

# Add all files
git add .
git commit -m "Initial commit: ESG Analyzer with BERT integration"

# Create repository on GitHub (using GitHub CLI)
gh repo create esg-analyzer --public --source=. --remote=origin --push
```

### 2. Organize Repository Structure

```bash
# Create proper structure
mkdir -p .github/workflows
mkdir -p frontend
mkdir -p backend
mkdir -p deployment

# Move backend files
mv *.py backend/
mv requirements*.txt backend/
mv esg-scraper/* backend/

# Move frontend files (already created)
# frontend/index.html
# frontend/app.js

# Create README for GitHub
cat > README.md << 'EOF'
# ESG Analyzer

AI-powered ESG (Environmental, Social, Governance) analysis platform with BERT integration.

![ESG Analyzer Demo](https://img.shields.io/badge/demo-live-green)
![License](https://img.shields.io/badge/license-MIT-blue)

## Features

- 🤖 **AI-Powered Analysis**: Advanced BERT models for ESG categorization
- 📊 **Framework Compliance**: CSRD, TCFD, GRI, and SASB checking
- 🔍 **Greenwashing Detection**: Identify vague sustainability claims
- 📈 **Beautiful Dashboard**: Modern, responsive UI
- 🚀 **Fast & Scalable**: Deployed on DigitalOcean

## Demo

[Live Demo](https://esg-analyzer.com)

## Quick Start

### Using the Web Interface

1. Visit [esg-analyzer.com](https://esg-analyzer.com)
2. Paste your ESG report content
3. Select frameworks to check
4. Click "Analyze"

### Using the API

```bash
curl -X POST https://api.esg-analyzer.com/api/v2/bert/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Your ESG report text...",
    "frameworks": ["CSRD", "TCFD"],
    "use_bert": true
  }'
```

## Documentation

- [API Documentation](https://api.esg-analyzer.com/docs)
- [Deployment Guide](./DIGITALOCEAN_DEPLOYMENT_GUIDE.md)
- [BERT Integration Guide](./backend/BERT_INTEGRATION_GUIDE.md)

## Tech Stack

- **Backend**: FastAPI, Python, BERT (DistilBERT-ESG, FinBERT)
- **Frontend**: HTML5, TailwindCSS, Vanilla JavaScript
- **Database**: SQLite + Redis
- **Deployment**: DigitalOcean App Platform / Kubernetes

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md)

## License

MIT License - see [LICENSE](./LICENSE)
EOF

# Commit changes
git add .
git commit -m "Organize repository structure"
git push
```

## DigitalOcean Setup

### 1. Create DigitalOcean Account

1. Sign up at [digitalocean.com](https://digitalocean.com)
2. Add billing information
3. Get $200 credit with referral (optional)

### 2. Choose Deployment Method

We'll use **DigitalOcean App Platform** for simplicity, with option for Kubernetes later.

## Frontend Deployment

### 1. Prepare Frontend for Deployment

```bash
# Create frontend build script
cat > frontend/build.sh << 'EOF'
#!/bin/bash
# Frontend build script

# Copy files to dist
mkdir -p dist
cp index.html dist/
cp app.js dist/

# Update API URL for production
sed -i '' "s|http://localhost:8000|https://api.esg-analyzer.com|g" dist/app.js

echo "Frontend build complete!"
EOF

chmod +x frontend/build.sh

# Create static.json for buildpack
cat > frontend/static.json << 'EOF'
{
  "root": "dist/",
  "clean_urls": true,
  "https_only": true,
  "headers": {
    "/**": {
      "Cache-Control": "public, max-age=3600"
    }
  }
}
EOF
```

### 2. Deploy Frontend to DigitalOcean App Platform

```yaml
# Create app spec for frontend
cat > frontend/app.yaml << 'EOF'
name: esg-analyzer-frontend
region: nyc
static_sites:
  - name: frontend
    github:
      repo: yourusername/esg-analyzer
      branch: main
      deploy_on_push: true
    source_dir: frontend
    build_command: ./build.sh
    output_dir: dist
    routes:
      - path: /
    cors:
      allow_origins:
        - prefix: https://api.esg-analyzer.com
      allow_methods:
        - GET
        - POST
        - PUT
        - DELETE
        - OPTIONS
      allow_headers:
        - Content-Type
        - Authorization
EOF
```

## Backend Deployment

### 1. Prepare Backend for Production

```bash
# Create production Dockerfile
cat > backend/Dockerfile.prod << 'EOF'
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc g++ curl git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements
COPY requirements_lean.txt requirements_bert.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements_lean.txt && \
    pip install --no-cache-dir -r requirements_bert.txt && \
    pip install gunicorn

# Copy application
COPY . .

# Create directories
RUN mkdir -p data logs bert_cache

# Download models at build time
RUN python download_models.py || true

# Environment
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Run with gunicorn
CMD gunicorn lean_esg_platform:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers 2 \
    --bind 0.0.0.0:$PORT \
    --timeout 120
EOF

# Create app.yaml for backend
cat > backend/app.yaml << 'EOF'
name: esg-analyzer-backend
region: nyc
services:
  - name: api
    github:
      repo: yourusername/esg-analyzer
      branch: main
      deploy_on_push: true
    source_dir: backend
    dockerfile_path: Dockerfile.prod
    instance_size_slug: professional-xs
    instance_count: 1
    routes:
      - path: /api
    envs:
      - key: ENABLE_BERT
        value: "true"
      - key: REDIS_URL
        scope: RUN_TIME
        value: ${redis.REDIS_URL}
      - key: JWT_SECRET
        scope: RUN_TIME
        type: SECRET
      - key: DATABASE_URL
        scope: RUN_TIME
        value: ${db.DATABASE_URL}
    health_check:
      http_path: /health
      initial_delay_seconds: 30
      period_seconds: 10

databases:
  - name: db
    engine: PG
    version: "14"
    size: db-s-1vcpu-1gb

  - name: redis
    engine: REDIS
    version: "7"
    size: db-s-1vcpu-1gb
EOF
```

### 2. Deploy Using DigitalOcean CLI

```bash
# Install doctl
brew install doctl

# Authenticate
doctl auth init

# Create app
doctl apps create --spec backend/app.yaml

# Get app ID
APP_ID=$(doctl apps list --format ID --no-header)

# Deploy
doctl apps create-deployment $APP_ID
```

## CI/CD Pipeline

### 1. GitHub Actions for Automated Deployment

```yaml
# Create .github/workflows/deploy.yml
cat > .github/workflows/deploy.yml << 'EOF'
name: Deploy to DigitalOcean

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements_lean.txt
          pip install -r requirements_bert.txt
          pip install pytest
      
      - name: Run tests
        run: |
          cd backend
          pytest test_bert_integration.py -v

  deploy-frontend:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to DigitalOcean App Platform
        uses: digitalocean/app_action@v1.1.5
        with:
          app_name: esg-analyzer-frontend
          token: ${{ secrets.DIGITALOCEAN_ACCESS_TOKEN }}

  deploy-backend:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to DigitalOcean App Platform
        uses: digitalocean/app_action@v1.1.5
        with:
          app_name: esg-analyzer-backend
          token: ${{ secrets.DIGITALOCEAN_ACCESS_TOKEN }}
EOF

# Add secrets to GitHub
# Go to Settings > Secrets > Actions
# Add DIGITALOCEAN_ACCESS_TOKEN
```

## Domain & SSL Setup

### 1. Add Custom Domain

```bash
# Add domain to frontend app
doctl apps update $FRONTEND_APP_ID --spec - << 'EOF'
domains:
  - domain: esg-analyzer.com
    type: PRIMARY
EOF

# Add domain to backend app
doctl apps update $BACKEND_APP_ID --spec - << 'EOF'
domains:
  - domain: api.esg-analyzer.com
    type: PRIMARY
EOF
```

### 2. Configure DNS

Add these records to your domain:

```
Type    Name    Value
A       @       <FRONTEND_APP_IP>
A       api     <BACKEND_APP_IP>
CNAME   www     esg-analyzer.com
```

### 3. SSL Certificates

DigitalOcean App Platform automatically provisions Let's Encrypt SSL certificates.

## Monitoring & Maintenance

### 1. Set Up Monitoring

```bash
# Create monitoring dashboard
cat > deployment/monitoring.yaml << 'EOF'
alerts:
  - name: high-error-rate
    condition: error_rate > 0.05
    notification: email
    
  - name: high-response-time
    condition: response_time_p95 > 2000
    notification: slack
    
  - name: low-availability
    condition: availability < 0.99
    notification: pagerduty

metrics:
  - api_requests_total
  - api_request_duration_seconds
  - bert_analysis_duration_seconds
  - active_users_total
EOF
```

### 2. Enable Application Insights

```bash
# In DigitalOcean dashboard
# Apps > Your App > Insights > Enable

# Or via CLI
doctl apps update $APP_ID --spec - << 'EOF'
alerts:
  - rule: CPU_UTILIZATION
    value: 80
    operator: GREATER_THAN
    window: FIVE_MINUTES
EOF
```

### 3. Set Up Backups

```bash
# Database backups (automatic with DigitalOcean managed databases)
doctl databases backups list $DB_ID

# Application state backups
cat > deployment/backup.sh << 'EOF'
#!/bin/bash
# Backup script

# Backup database
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Upload to Spaces
s3cmd put backup_*.sql s3://esg-analyzer-backups/

# Clean old backups
find . -name "backup_*.sql" -mtime +7 -delete
EOF
```

## Quick Deployment Commands

```bash
# One-command deployment (after initial setup)
git add .
git commit -m "Update application"
git push origin main

# The GitHub Action will automatically:
# 1. Run tests
# 2. Build Docker images
# 3. Deploy to DigitalOcean
# 4. Update SSL certificates
# 5. Run health checks
```

## Cost Estimation

- **Frontend (Static Site)**: Free
- **Backend (App Platform)**: ~$12/month (Professional-XS)
- **Database (PostgreSQL)**: ~$15/month
- **Redis**: ~$15/month
- **Total**: ~$42/month

For higher traffic, consider:
- **Kubernetes Cluster**: Starting at $36/month
- **Load Balancer**: $12/month
- **CDN**: $5/month

## Troubleshooting

### Common Issues

1. **BERT Models Not Loading**
   ```bash
   # Increase instance size
   doctl apps update $APP_ID --spec app.yaml
   # Change instance_size_slug to professional-s
   ```

2. **CORS Errors**
   ```javascript
   // Update frontend app.js
   const API_BASE_URL = 'https://api.esg-analyzer.com';
   ```

3. **Database Connection Issues**
   ```bash
   # Check connection string
   doctl databases connection $DB_ID
   ```

## Next Steps

1. **Enable Authentication**: Add Auth0 or similar
2. **Add CDN**: CloudFlare for frontend assets
3. **Scale Backend**: Move to Kubernetes for auto-scaling
4. **Add Analytics**: Google Analytics or Plausible
5. **API Rate Limiting**: Implement usage tiers

Your ESG Analyzer is now live with a beautiful UI at `https://esg-analyzer.com`! 