#!/bin/bash

# DigitalOcean Deployment Setup Script for ESG Scraper
# This script helps you set up deployment to DigitalOcean App Platform

set -e

echo "🚀 ESG Scraper - DigitalOcean Deployment Setup"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "${BLUE}📋 Checking prerequisites...${NC}"

# Check if git is available
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git is not installed. Please install Git first.${NC}"
    exit 1
fi

# Check if GitHub CLI is available (optional but recommended)
if ! command -v gh &> /dev/null; then
    echo -e "${YELLOW}⚠️  GitHub CLI not found. You'll need to create repository manually.${NC}"
    echo "   Install with: brew install gh (macOS) or apt install gh (Ubuntu)"
    USE_GH_CLI=false
else
    USE_GH_CLI=true
fi

# Check if doctl is available
if ! command -v doctl &> /dev/null; then
    echo -e "${YELLOW}⚠️  DigitalOcean CLI (doctl) not found.${NC}"
    echo "   Install with: brew install doctl (macOS) or snap install doctl (Ubuntu)"
    echo "   Or download from: https://github.com/digitalocean/doctl/releases"
    read -p "   Continue without doctl? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
    USE_DOCTL=false
else
    USE_DOCTL=true
fi

echo -e "${GREEN}✅ Prerequisites check complete${NC}"

# Collect configuration information
echo -e "${BLUE}📝 Configuration Setup${NC}"

# GitHub configuration
read -p "Enter your GitHub username: " GITHUB_USERNAME
read -p "Enter repository name [esg-scraper]: " REPO_NAME
REPO_NAME=${REPO_NAME:-esg-scraper}

# DigitalOcean configuration
if [[ $USE_DOCTL == true ]]; then
    echo "Checking DigitalOcean authentication..."
    if ! doctl account get &> /dev/null; then
        echo -e "${YELLOW}⚠️  Not authenticated with DigitalOcean${NC}"
        echo "Run: doctl auth init"
        exit 1
    fi
    
    # Get or create container registry
    echo "Setting up container registry..."
    REGISTRY_NAME=$(doctl registry get --format Name --no-header 2>/dev/null || echo "")
    if [[ -z "$REGISTRY_NAME" ]]; then
        read -p "Enter name for new container registry: " REGISTRY_NAME
        doctl registry create $REGISTRY_NAME
    fi
    echo "Using registry: $REGISTRY_NAME"
else
    read -p "Enter your DigitalOcean container registry name: " REGISTRY_NAME
fi

# JWT Secret
JWT_SECRET=$(openssl rand -base64 32 2>/dev/null || python3 -c "import secrets; print(secrets.token_urlsafe(32))")
echo -e "${GREEN}Generated JWT secret${NC}"

# Optional configurations
read -p "Enter custom domain (optional, press enter to skip): " CUSTOM_DOMAIN
read -p "Enter Stripe secret key (optional, press enter to skip): " STRIPE_KEY
read -p "Enter Slack webhook URL (optional, press enter to skip): " SLACK_WEBHOOK

# Update configuration files
echo -e "${BLUE}🔧 Updating configuration files...${NC}"

# Update app.yaml
sed -i.bak "s/YOUR_GITHUB_USERNAME/$GITHUB_USERNAME/g" deployment/app.yaml
sed -i.bak "s/YOUR_REGISTRY_NAME/$REGISTRY_NAME/g" deployment/app.yaml
sed -i.bak "s/YOUR_JWT_SECRET_CHANGE_THIS/$JWT_SECRET/g" deployment/app.yaml

if [[ ! -z "$STRIPE_KEY" ]]; then
    sed -i.bak "s/sk_test_YOUR_STRIPE_KEY/$STRIPE_KEY/g" deployment/app.yaml
fi

if [[ ! -z "$SLACK_WEBHOOK" ]]; then
    sed -i.bak "s|YOUR_SLACK_WEBHOOK_URL|$SLACK_WEBHOOK|g" deployment/app.yaml
fi

# Add domain configuration if provided
if [[ ! -z "$CUSTOM_DOMAIN" ]]; then
    cat >> deployment/app.yaml << EOF

domains:
  - domain: $CUSTOM_DOMAIN
    type: PRIMARY
  - domain: www.$CUSTOM_DOMAIN
    type: ALIAS
    minimum_tls_version: "1.2"
EOF
fi

echo -e "${GREEN}✅ Configuration files updated${NC}"

# GitHub repository setup
echo -e "${BLUE}📚 Setting up GitHub repository...${NC}"

# Initialize git if not already done
if [[ ! -d .git ]]; then
    git init
    echo -e "${GREEN}✅ Git repository initialized${NC}"
fi

# Create .gitignore if it doesn't exist
if [[ ! -f .gitignore ]]; then
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

# Models and cache
models/
bert_cache/
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

# Deployment backups
*.bak
EOF
    echo -e "${GREEN}✅ .gitignore created${NC}"
fi

# Stage files
git add .

# Create initial commit if no commits exist
if ! git rev-parse HEAD &> /dev/null; then
    git commit -m "Initial commit: ESG Scraper with DigitalOcean deployment configuration"
    echo -e "${GREEN}✅ Initial commit created${NC}"
else
    git commit -m "Update deployment configuration for DigitalOcean" || echo "No changes to commit"
fi

# Create GitHub repository
if [[ $USE_GH_CLI == true ]]; then
    echo "Creating GitHub repository..."
    gh repo create $REPO_NAME --public --source=. --remote=origin --push || {
        echo -e "${YELLOW}⚠️  Repository might already exist. Adding remote...${NC}"
        git remote add origin https://github.com/$GITHUB_USERNAME/$REPO_NAME.git 2>/dev/null || true
        git push -u origin main
    }
    echo -e "${GREEN}✅ GitHub repository set up${NC}"
else
    echo -e "${YELLOW}📋 Manual GitHub setup required:${NC}"
    echo "1. Create repository: https://github.com/new"
    echo "2. Repository name: $REPO_NAME"
    echo "3. Make it public"
    echo "4. Add remote and push:"
    echo "   git remote add origin https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"
    echo "   git push -u origin main"
    read -p "Press enter after creating GitHub repository..."
fi

# GitHub Secrets setup
echo -e "${BLUE}🔐 GitHub Secrets Setup${NC}"
echo "You need to add these secrets to your GitHub repository:"
echo "Go to: https://github.com/$GITHUB_USERNAME/$REPO_NAME/settings/secrets/actions"
echo ""
echo -e "${YELLOW}Required Secrets:${NC}"
echo "DIGITALOCEAN_ACCESS_TOKEN  - Your DigitalOcean API token"
echo "DO_REGISTRY_NAME           - $REGISTRY_NAME"
echo "APP_URL                    - Will be provided after first deployment"
echo ""
echo -e "${YELLOW}Optional Secrets:${NC}"
if [[ ! -z "$SLACK_WEBHOOK" ]]; then
    echo "SLACK_WEBHOOK_URL          - $SLACK_WEBHOOK"
fi

# Generate DigitalOcean API token instructions
echo ""
echo -e "${BLUE}📋 DigitalOcean API Token Instructions:${NC}"
echo "1. Go to: https://cloud.digitalocean.com/account/api/tokens"
echo "2. Click 'Generate New Token'"
echo "3. Name: 'ESG Scraper Deployment'"
echo "4. Select: Read and Write"
echo "5. Copy the token and add it as DIGITALOCEAN_ACCESS_TOKEN secret"

# Create environment file for local development
echo -e "${BLUE}📄 Creating local environment file...${NC}"
cat > .env.example << EOF
# ESG Scraper Environment Configuration
# Copy this to .env and update with your values

# Required
JWT_SECRET=$JWT_SECRET
UPSTASH_REDIS_URL=redis://localhost:6379
DATABASE_PATH=esg_data.db
FREE_TIER_CREDITS=1000

# Optional
STRIPE_SECRET_KEY=$STRIPE_KEY
SLACK_WEBHOOK_URL=$SLACK_WEBHOOK

# Production settings (for deployment)
ENVIRONMENT=production
LOG_LEVEL=INFO
WORKERS=2
EOF

echo -e "${GREEN}✅ Environment template created (.env.example)${NC}"

# Create deployment summary
echo -e "${BLUE}📋 Creating deployment summary...${NC}"
cat > DEPLOYMENT_SUMMARY.md << EOF
# ESG Scraper Deployment Summary

## Configuration
- **GitHub Repository**: https://github.com/$GITHUB_USERNAME/$REPO_NAME
- **Container Registry**: $REGISTRY_NAME
- **JWT Secret**: Generated automatically

## Next Steps

### 1. Add GitHub Secrets
Go to: https://github.com/$GITHUB_USERNAME/$REPO_NAME/settings/secrets/actions"

Add these secrets:
- \`DIGITALOCEAN_ACCESS_TOKEN\` - Your DigitalOcean API token
- \`DO_REGISTRY_NAME\` - $REGISTRY_NAME
- \`APP_URL\` - Add after first deployment (e.g., https://esg-scraper-xxx.ondigitalocean.app)

### 2. Deploy
Push any commit to main branch to trigger deployment:
\`\`\`bash
git add .
git commit -m "Trigger deployment"
git push origin main
\`\`\`

### 3. Monitor Deployment
- Check GitHub Actions: https://github.com/$GITHUB_USERNAME/$REPO_NAME/actions
- Check DigitalOcean Apps: https://cloud.digitalocean.com/apps

### 4. Access Your App
After deployment, your app will be available at:
- App URL: (provided by DigitalOcean)
- API Documentation: YOUR_APP_URL/docs
- Health Check: YOUR_APP_URL/health

## Cost Estimation
- **Basic Instance**: \$5-12/month
- **Container Registry**: \$5/month (500MB included)
- **Total**: ~\$10-17/month

## Support
- Check logs in DigitalOcean dashboard
- Monitor GitHub Actions for deployment status
- Review health checks and alerts
EOF

echo -e "${GREEN}✅ Deployment summary created (DEPLOYMENT_SUMMARY.md)${NC}"

# Final instructions
echo ""
echo -e "${GREEN}🎉 Deployment setup complete!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. 📝 Add GitHub secrets (see DEPLOYMENT_SUMMARY.md)"
echo "2. 🚀 Push to main branch to trigger deployment"
echo "3. 📊 Monitor deployment in GitHub Actions"
echo "4. 🌐 Access your app at the provided URL"
echo ""
echo -e "${YELLOW}Files created/updated:${NC}"
echo "- deployment/app.yaml (configured)"
echo "- .env.example (environment template)"
echo "- DEPLOYMENT_SUMMARY.md (next steps)"
echo "- .gitignore (if needed)"
echo ""
echo -e "${GREEN}Your ESG scraper is ready for deployment! 🚀${NC}" 