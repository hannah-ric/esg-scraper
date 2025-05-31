# 🚀 Step-by-Step Deployment Guide

**Deploy your ESG Scraper to DigitalOcean in 15 minutes!**

This guide assumes zero experience with deployment and walks you through every step.

## 📋 What We're Building

You'll deploy a production-ready ESG analysis API that can:
- ✅ Analyze sustainability reports against CSRD, GRI, SASB, TCFD frameworks
- ✅ Auto-scale based on traffic
- ✅ Handle secure authentication
- ✅ Cost only ~$10-17/month

## 🛠️ Prerequisites (5 minutes)

### ✅ Step 1: Create Accounts
1. **GitHub Account** (free): [github.com](https://github.com)
2. **DigitalOcean Account**: [digitalocean.com](https://digitalocean.com) 
   - Add billing method (required for deployment)
   - You get $200 credit with referrals

### ✅ Step 2: Install Tools

**On macOS:**
```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required tools
brew install git gh doctl
```

**On Windows:**
```bash
# Install tools via Chocolatey or download directly
# Git: https://git-scm.com/download/win
# GitHub CLI: https://cli.github.com/
# DigitalOcean CLI: https://github.com/digitalocean/doctl/releases
```

**On Linux (Ubuntu/Debian):**
```bash
# Install tools
sudo apt update
sudo apt install git gh
sudo snap install doctl
```

## 🔐 Authentication Setup (3 minutes)

### ✅ Step 3: Login to Services

```bash
# Login to GitHub
gh auth login
# Follow prompts: Use web browser, authenticate

# Login to DigitalOcean
doctl auth init
# Enter your DigitalOcean API token (we'll create this next)
```

### ✅ Step 4: Create DigitalOcean API Token

1. Go to: [DigitalOcean API Tokens](https://cloud.digitalocean.com/account/api/tokens)
2. Click **"Generate New Token"**
3. Name: `ESG Scraper Deployment`
4. Scopes: **Read and Write**
5. Copy the token and paste when `doctl auth init` asks

## 📦 Repository Setup (2 minutes)

### ✅ Step 5: Create Container Registry

```bash
# Create a container registry (stores your app images)
doctl registry create your-registry-name

# Example: doctl registry create esg-scraper-registry
```

### ✅ Step 6: Verify Your Current Directory

```bash
# Make sure you're in the right place
pwd
# Should show: /Users/hannahricci/esg-scraper/esg-scraper

# If not, navigate there
cd /Users/hannahricci/esg-scraper/esg-scraper
```

## 🔧 Configuration (3 minutes)

### ✅ Step 7: Run the Setup Script

```bash
# Make sure the script is executable
chmod +x deployment/setup_digitalocean.sh

# Run the setup (this configures everything)
./deployment/setup_digitalocean.sh
```

**The script will ask you for:**
- GitHub username
- Repository name (default: esg-scraper)
- Container registry name (from Step 5)
- Custom domain (optional)
- Stripe key (optional, for payments)
- Slack webhook (optional, for notifications)

## 🌍 Environment Variables Explained

### 🔒 **Security Variables**
- **`JWT_SECRET`**: Encrypts user sessions (auto-generated, 32+ chars)
- **`DIGITALOCEAN_ACCESS_TOKEN`**: Allows deployment access

### ⚡ **App Configuration**
- **`REDIS_URL`**: Cache server location (`redis://localhost:6379`)
- **`DATABASE_PATH`**: Where to store data (`/app/data/esg_data.db`)
- **`FREE_TIER_CREDITS`**: Credits per user (`1000`)

### 🚀 **Performance Settings**
- **`WORKERS`**: Number of app processes (`2` = good for basic tier)
- **`LOG_LEVEL`**: Logging detail (`INFO` for production)
- **`ENVIRONMENT`**: App mode (`production`)

### 💳 **Optional Services**
- **`STRIPE_SECRET_KEY`**: For payment processing
- **`SLACK_WEBHOOK_URL`**: For deployment notifications

## 🎯 Deployment Process (2 minutes)

### ✅ Step 8: Add GitHub Secrets

After running the setup script, add these secrets to GitHub:

1. Go to: `https://github.com/YOUR_USERNAME/esg-scraper/settings/secrets/actions`
2. Add these secrets:

| Secret Name | Value | Example |
|-------------|-------|---------|
| `DIGITALOCEAN_ACCESS_TOKEN` | Your API token | `dop_v1_abc123...` |
| `DO_REGISTRY_NAME` | Registry name | `esg-scraper-registry` |
| `APP_URL` | *(Add after first deploy)* | `https://esg-scraper-abc.ondigitalocean.app` |

### ✅ Step 9: Deploy!

```bash
# Commit and push to trigger deployment
git add .
git commit -m "🚀 Deploy ESG Scraper to production"
git push origin main
```

## 📊 Monitor Your Deployment

### ✅ Step 10: Watch the Process

1. **GitHub Actions**: [github.com/YOUR_USERNAME/esg-scraper/actions](https://github.com)
   - Watch the build pipeline (takes ~10-15 minutes)
   - ✅ Test → ✅ Build → ✅ Deploy → ✅ Health Check

2. **DigitalOcean Dashboard**: [cloud.digitalocean.com/apps](https://cloud.digitalocean.com/apps)
   - See your app being created
   - Get the live URL

### ✅ Step 11: Add App URL Secret

Once deployment completes:
1. Copy your app URL from DigitalOcean dashboard
2. Add it as `APP_URL` secret in GitHub (Step 8 location)

## 🧪 Test Your Deployment

### ✅ Step 12: Verify Everything Works

```bash
# Replace YOUR_APP_URL with your actual URL
APP_URL="https://your-app-url.ondigitalocean.app"

# Test health check
curl $APP_URL/health

# Test framework info
curl $APP_URL/frameworks

# Register a test user
curl -X POST "$APP_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'

# Save the token and test analysis
TOKEN="your_token_here"
curl -X POST "$APP_URL/analyze" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "text": "Our company commits to net zero emissions by 2030",
    "frameworks": ["CSRD", "TCFD"],
    "quick_mode": false
  }'
```

## 🔧 Best Practices

### 🔒 **Security Best Practices**

1. **Strong Secrets**: Use auto-generated JWT secrets (done automatically)
2. **Environment Variables**: Never commit secrets to Git
3. **HTTPS Only**: DigitalOcean provides free SSL
4. **Regular Updates**: Keep dependencies updated

### 💰 **Cost Optimization**

1. **Start Small**: Use `basic-xxs` tier ($5/month)
2. **Monitor Usage**: Check DigitalOcean dashboard
3. **Scale When Needed**: Upgrade to `professional-xs` ($12/month) for more traffic

### 📊 **Performance Best Practices**

1. **Health Monitoring**: Set up alerts for downtime
2. **Log Monitoring**: Check application logs regularly
3. **Database Backups**: DigitalOcean handles this automatically
4. **CDN**: Add if you have global users

## 🛠️ Troubleshooting

### ❌ **Common Issues & Solutions**

**"Deployment Failed" in GitHub Actions:**
```bash
# Check the logs in GitHub Actions tab
# Common fix: Re-run the deployment
git commit --allow-empty -m "Retry deployment"
git push origin main
```

**"Health Check Failed":**
- Wait 2-3 minutes for app to start
- Check DigitalOcean app logs
- Verify environment variables are set

**"Image Not Found":**
- Check container registry exists
- Verify `DO_REGISTRY_NAME` secret is correct

**"Authorization Failed":**
- Verify `DIGITALOCEAN_ACCESS_TOKEN` has Read/Write permissions
- Check token hasn't expired

### 🆘 **Get Help**

```bash
# Check deployment status
doctl apps list

# View app logs
doctl apps logs YOUR_APP_ID

# Test locally first
python health_check.py
```

## 🎉 Success Checklist

After deployment, you should have:

- [ ] ✅ Live API at `https://your-app.ondigitalocean.app`
- [ ] ✅ Health check passes: `/health`
- [ ] ✅ API documentation: `/docs`
- [ ] ✅ Framework analysis working: `/frameworks`
- [ ] ✅ User registration working: `/auth/register`
- [ ] ✅ ESG analysis working: `/analyze`
- [ ] ✅ Monitoring dashboard in DigitalOcean
- [ ] ✅ Auto-deployment on GitHub pushes

## 💰 **Cost Summary**

**Monthly Costs:**
- **Basic App**: $5/month (512MB RAM, 1 vCPU)
- **Container Registry**: $5/month (500MB included)
- **Total**: $10/month

**Optional Upgrades:**
- **Professional App**: $12/month (1GB RAM, faster)
- **Managed Database**: $15/month (external PostgreSQL)
- **Load Balancer**: $12/month (high traffic)

## 🚀 **Next Steps**

1. **Custom Domain**: Add your own domain in DigitalOcean dashboard
2. **Monitoring**: Set up alerts for CPU/memory usage
3. **Scaling**: Increase instance count for more traffic
4. **Features**: Add more ESG frameworks or analysis features

## 📞 **Support**

Need help? Check:
1. **Logs**: DigitalOcean app dashboard
2. **Actions**: GitHub Actions tab for deployment issues
3. **Health**: Run `python health_check.py` locally
4. **Documentation**: `/docs` endpoint on your deployed app

**Your ESG analysis platform is now live and production-ready! 🎉**

**API URL**: `https://your-app.ondigitalocean.app` 