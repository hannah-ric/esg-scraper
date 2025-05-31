# 🚀 Deploy ESG Scraper to DigitalOcean

This guide will help you deploy your ESG scraper to DigitalOcean App Platform with automated CI/CD through GitHub.

## 📋 What You'll Get

- **Automated Deployment**: Push to GitHub → Automatic deployment
- **Production-Ready**: Optimized Docker container with health checks
- **Framework Analysis**: Full CSRD, GRI, SASB, TCFD compliance checking
- **Scalable Infrastructure**: DigitalOcean App Platform with monitoring
- **Cost-Effective**: Starting at ~$10-17/month

## 🔧 Prerequisites

Before starting, ensure you have:

- [ ] **GitHub account** (free)
- [ ] **DigitalOcean account** with billing enabled
- [ ] **Git installed** locally
- [ ] **Basic terminal/command line** knowledge

### Optional but Recommended:
- [ ] **GitHub CLI** (`gh`) - for automated repository setup
- [ ] **DigitalOcean CLI** (`doctl`) - for streamlined deployment
- [ ] **Custom domain** - for branded URLs

## 🚀 Quick Deploy (Automated)

### Step 1: Run Setup Script

Make the setup script executable and run it:

```bash
chmod +x deployment/setup_digitalocean.sh
./deployment/setup_digitalocean.sh
```

The script will:
- ✅ Check prerequisites
- ✅ Configure deployment files
- ✅ Set up GitHub repository
- ✅ Generate security tokens
- ✅ Create deployment configuration

### Step 2: Add GitHub Secrets

Go to your repository settings:
`https://github.com/YOUR_USERNAME/esg-scraper/settings/secrets/actions`

Add these secrets:

| Secret Name | Value | Where to Get It |
|-------------|-------|-----------------|
| `DIGITALOCEAN_ACCESS_TOKEN` | Your DO API token | [DigitalOcean API](https://cloud.digitalocean.com/account/api/tokens) |
| `DO_REGISTRY_NAME` | Container registry name | From setup script output |
| `APP_URL` | Your app URL | After first deployment |

### Step 3: Deploy

Push any commit to trigger deployment:

```bash
git add .
git commit -m "Deploy to production"
git push origin main
```

## 📝 Manual Setup (Step by Step)

If you prefer manual setup or the script didn't work:

### 1. Install Required Tools

**macOS:**
```bash
# Install GitHub CLI
brew install gh

# Install DigitalOcean CLI
brew install doctl
```

**Ubuntu/Linux:**
```bash
# Install GitHub CLI
sudo apt install gh

# Install DigitalOcean CLI
sudo snap install doctl
```

### 2. Authenticate Services

**GitHub:**
```bash
gh auth login
```

**DigitalOcean:**
```bash
doctl auth init
```

### 3. Create Container Registry

```bash
# List existing registries
doctl registry list

# Create new registry (if needed)
doctl registry create your-registry-name
```

### 4. Update Configuration

Edit `deployment/app.yaml`:
```yaml
name: esg-scraper
services:
  - name: api
    github:
      repo: YOUR_USERNAME/esg-scraper  # ← Update this
    image:
      registry: YOUR_REGISTRY_NAME     # ← Update this
```

### 5. Create GitHub Repository

```bash
# Create and push repository
gh repo create esg-scraper --public --source=. --remote=origin --push
```

### 6. Add GitHub Secrets

```bash
# Add DigitalOcean token
gh secret set DIGITALOCEAN_ACCESS_TOKEN --body "YOUR_DO_TOKEN"

# Add registry name
gh secret set DO_REGISTRY_NAME --body "YOUR_REGISTRY_NAME"
```

## 🔍 Monitoring Your Deployment

### GitHub Actions
Monitor deployment progress:
- Go to: `https://github.com/YOUR_USERNAME/esg-scraper/actions`
- Watch the deployment pipeline run
- Check for any errors in the logs

### DigitalOcean Dashboard
Monitor your application:
- Go to: [DigitalOcean Apps Dashboard](https://cloud.digitalocean.com/apps)
- View logs, metrics, and performance
- Check health status and alerts

## 🌐 Accessing Your Deployed App

After successful deployment:

### API Endpoints
- **Health Check**: `https://your-app-url/health`
- **API Documentation**: `https://your-app-url/docs`
- **Framework Info**: `https://your-app-url/frameworks`

### Test Your API

1. **Register a user:**
```bash
curl -X POST "https://your-app-url/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

2. **Analyze ESG content:**
```bash
curl -X POST "https://your-app-url/analyze" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "text": "Our company is committed to achieving net zero emissions by 2030 through renewable energy investments and science-based targets.",
    "frameworks": ["CSRD", "TCFD"],
    "quick_mode": false
  }'
```

## 💰 Cost Breakdown

### DigitalOcean App Platform Costs:
- **Basic Tier**: $5/month (512MB RAM, 1 vCPU)
- **Professional**: $12/month (1GB RAM, 1 vCPU) ← Recommended
- **Container Registry**: $5/month (500MB included)

### Optional Add-ons:
- **Managed Database**: $15/month (if you want external PostgreSQL)
- **Load Balancer**: $12/month (for high traffic)
- **Custom Domain SSL**: Free (Let's Encrypt)

**Total Estimated Cost**: $10-17/month for production ready setup

## 🔧 Configuration Options

### Environment Variables

You can customize your deployment by updating `deployment/app.yaml`:

```yaml
envs:
  - key: FREE_TIER_CREDITS
    value: "1000"              # Free credits per user
  
  - key: WORKERS
    value: "2"                 # Number of worker processes
  
  - key: LOG_LEVEL
    value: "INFO"              # Logging level
  
  - key: STRIPE_SECRET_KEY
    value: "your_stripe_key"   # For payment processing
    type: SECRET
```

### Scaling Options

Update instance configuration:
```yaml
instance_count: 2            # Number of instances
instance_size_slug: professional-xs  # Instance size
```

### Custom Domain

Add to `deployment/app.yaml`:
```yaml
domains:
  - domain: your-domain.com
    type: PRIMARY
  - domain: www.your-domain.com
    type: ALIAS
```

## 🛠️ Troubleshooting

### Common Issues

**1. Deployment Fails with "Image not found"**
```bash
# Check if image was pushed successfully
doctl registry repository list-v2

# Re-run deployment
git commit --allow-empty -m "Retrigger deployment"
git push origin main
```

**2. Health Check Fails**
- Check application logs in DigitalOcean dashboard
- Ensure all required environment variables are set
- Verify Redis is starting correctly

**3. "Authorization Required" Errors**
- Check JWT_SECRET is set correctly
- Ensure DIGITALOCEAN_ACCESS_TOKEN has correct permissions

### Debug Commands

```bash
# Check deployment status
doctl apps list

# View app logs
doctl apps logs YOUR_APP_ID

# Get app info
doctl apps get YOUR_APP_ID
```

## 📊 Performance Optimization

### For High Traffic:
1. **Increase instance count**: Scale horizontally
2. **Use Professional tier**: More RAM and CPU
3. **Add managed Redis**: External caching
4. **Enable CDN**: For static assets

### For Cost Optimization:
1. **Use Basic tier**: For low traffic
2. **Optimize Docker image**: Multi-stage builds
3. **Monitor usage**: Track API calls and costs

## 🔒 Security Best Practices

### Production Security:
- [ ] Use strong JWT secrets (32+ characters)
- [ ] Enable HTTPS only (automatic with DigitalOcean)
- [ ] Set up monitoring and alerts
- [ ] Regularly update dependencies
- [ ] Use environment variables for secrets

### Monitoring:
- [ ] Set up health check alerts
- [ ] Monitor API response times
- [ ] Track error rates
- [ ] Monitor resource usage

## 📚 Additional Resources

- [DigitalOcean App Platform Docs](https://docs.digitalocean.com/products/app-platform/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

## 🆘 Getting Help

If you encounter issues:

1. **Check GitHub Actions logs** for deployment errors
2. **Review DigitalOcean app logs** for runtime issues
3. **Run health check** locally: `python health_check.py`
4. **Test components** individually

## 🎉 Success!

Your ESG scraper is now deployed with:
- ✅ **Automated CI/CD pipeline**
- ✅ **Production-grade infrastructure** 
- ✅ **Framework compliance analysis**
- ✅ **Monitoring and alerting**
- ✅ **Scalable architecture**

**Next Steps:**
- Add your custom domain
- Set up monitoring dashboards
- Create API documentation
- Scale based on usage patterns

Your enterprise-grade ESG analysis platform is now live! 🚀 