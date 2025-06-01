# 📚 ESG Platform Deployment Guide

This guide covers deployment to DigitalOcean App Platform with MongoDB Atlas and Upstash Redis.

## Prerequisites

- GitHub account with repository forked
- DigitalOcean account
- MongoDB Atlas account (free M0 tier)
- Upstash account (free tier)

## Step 1: Configure External Services

### MongoDB Atlas Setup

1. Create free M0 cluster at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Configure network access (allow from anywhere: 0.0.0.0/0)
3. Create database user
4. Get connection string:
   ```
   mongodb+srv://username:password@cluster.mongodb.net/
   ```

### Upstash Redis Setup

1. Create free Redis database at [Upstash](https://upstash.com)
2. Get connection details:
   - Redis URL (with TLS): `rediss://default:password@endpoint.upstash.io:6379`

## Step 2: Prepare Repository

1. Update `deployment/app.yaml` with your app name:
   ```yaml
   name: your-app-name
   region: nyc
   ```

2. Ensure all secrets use placeholders:
   ```yaml
   envs:
   - key: MONGODB_URI
     value: ${MONGODB_URI}
     type: SECRET
   ```

## Step 3: Deploy to DigitalOcean

### Using DigitalOcean Dashboard

1. Go to [DigitalOcean App Platform](https://cloud.digitalocean.com/apps)
2. Click "Create App"
3. Connect GitHub repository
4. Select branch (usually `main`)
5. Configure environment variables:
   ```
   MONGODB_URI=mongodb+srv://...
   UPSTASH_REDIS_URL=rediss://...
   JWT_SECRET=your-secret-key
   CORS_ORIGINS=https://yourdomain.com
   ENVIRONMENT=production
   ```
6. Review and launch

### Using doctl CLI

```bash
# Install doctl
brew install doctl  # macOS
# or download from https://github.com/digitalocean/doctl

# Authenticate
doctl auth init

# Create app
doctl apps create --spec deployment/app.yaml

# Update app
doctl apps update <app-id> --spec deployment/app.yaml
```

## Step 4: Configure CI/CD

GitHub Actions workflow is already configured in `.github/workflows/deploy.yml`.

Required GitHub Secrets:
- `DIGITALOCEAN_ACCESS_TOKEN` - Your DO API token
- `DO_REGISTRY_NAME` - Your DO container registry name

## Step 5: Verify Deployment

1. Check deployment status:
   ```bash
   doctl apps get <app-id>
   ```

2. Test health endpoint:
   ```bash
   curl https://your-app.ondigitalocean.app/health
   ```

3. Check detailed health:
   ```bash
   curl https://your-app.ondigitalocean.app/health/detailed
   ```

## Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `MONGODB_URI` | MongoDB connection string | `mongodb+srv://user:pass@cluster.mongodb.net/` |
| `MONGODB_DATABASE` | Database name | `esg_platform` |
| `UPSTASH_REDIS_URL` | Redis connection URL | `rediss://default:pass@endpoint.upstash.io:6379` |
| `JWT_SECRET` | JWT signing secret | `your-random-secret` |
| `CORS_ORIGINS` | Allowed CORS origins | `https://app.com,http://localhost:3000` |
| `SENTRY_DSN` | Sentry error tracking | `https://key@sentry.io/project` |
| `ENVIRONMENT` | Environment name | `production` |

## Troubleshooting

### Memory Issues
- The app is optimized for 512MB instances
- Transformers are disabled to reduce memory usage
- Current usage: ~150MB

### Database Connection Issues
- Ensure MongoDB allows connections from any IP (0.0.0.0/0)
- Check credentials are correct
- Verify database name matches configuration

### Redis Connection Issues
- Upstash uses self-signed certificates (handled in code)
- Ensure using `rediss://` (with SSL) protocol

### Build Failures
- Check GitHub Actions logs
- Verify all environment variables are set
- Ensure flake8 passes: `flake8 . --max-line-length=120`

## Monitoring

- **Logs**: Available in DigitalOcean dashboard
- **Metrics**: Prometheus endpoint at `/metrics`
- **Alerts**: Configure in DigitalOcean or use Sentry

## Scaling

When ready to scale:

1. **Vertical Scaling**: Upgrade to Basic-S ($12/mo) or Professional plans
2. **Horizontal Scaling**: Add more instances in app spec
3. **Database Scaling**: Upgrade MongoDB to M10+ ($57/mo)
4. **Cache Scaling**: Upgrade Upstash plan as needed

## Security Checklist

- [x] Environment variables use secrets
- [x] HTTPS enforced
- [x] Security headers implemented
- [x] Rate limiting configured
- [x] Input validation active
- [x] JWT authentication required
- [x] CORS properly configured

## Cost Optimization

Current setup costs ~$20/month:
- App Platform Basic: $5/month
- MongoDB M0: $15/month (or free with limitations)
- Upstash Redis: Free tier

To reduce costs:
- Use MongoDB free tier (512MB limit)
- Keep Redis usage under 10k commands/day
- Monitor resource usage regularly 