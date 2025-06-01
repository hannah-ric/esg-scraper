# Deployment Checklist for ESG Scraper Platform

## 🔐 Secrets Configuration (via DigitalOcean App Platform)
- [x] PostgreSQL private VPC connection configured
- [ ] Redis connection string (use Upstash or DigitalOcean Managed Redis)
- [ ] JWT_SECRET generated and stored
- [ ] Stripe API keys configured (if using payments)
- [ ] Sentry DSN configured (for error tracking)

## 📝 Environment Variables to Set in App Platform

### Required:
- [ ] PGPASSWORD (from DigitalOcean PostgreSQL)
- [ ] PGUSER (default: doadmin)
- [ ] PGHOST (private-db-postgresql-*.db.ondigitalocean.com)
- [ ] PGPORT (default: 25060)
- [ ] PGDATABASE (default: defaultdb)
- [ ] PGSSLMODE (set to: require)
- [ ] UPSTASH_UPSTASH_REDIS_URL (Redis connection string)
- [ ] JWT_SECRET (generate secure random string)

### Optional:
- [ ] SENTRY_DSN (for error tracking)
- [ ] STRIPE_SECRET_KEY (for payments)
- [ ] CORS_ORIGINS (comma-separated list of allowed origins)

## 🔍 Pre-deployment Verification
- [ ] PostgreSQL cluster is in same region as App Platform (nyc3)
- [ ] Using private- prefix in production PostgreSQL URI
- [ ] Redis instance is configured and accessible
- [ ] All secrets are stored in App Platform environment variables

## 🚀 Deployment Steps
1. Push code to main branch
2. Deploy via DigitalOcean App Platform
3. Verify logs for successful startup
4. Test health endpoint: `curl https://your-app.ondigitalocean.app/health`

## ✅ Post-deployment Verification
- [ ] Health check endpoint returns 200
- [ ] Verify PostgreSQL connects via VPC (no public access needed)
- [ ] Check Redis connectivity
- [ ] Test authentication endpoints
- [ ] Monitor Sentry for any errors

## 🔧 Rollback Plan
- [ ] Previous deployment can be restored via App Platform
- [ ] Database backups are automated by DigitalOcean
- [ ] Redis data can be restored from snapshots 