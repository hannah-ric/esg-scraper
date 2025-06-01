# Deployment Checklist for VPC Setup

## ✅ Already Done:
- [x] MongoDB private VPC connection string configured
- [x] App Platform configuration ready (app.yaml)
- [x] Code formatted with Black
- [x] All environment variables aligned

## 📋 To Do:

### 1. Add GitHub Secrets:
Go to: https://github.com/hannah-ric/esg-scraper/settings/secrets/actions

Add these secrets:
- [ ] MONGODB_URI (private VPC string)
- [ ] MONGODB_DATABASE (set to: admin)
- [ ] JWT_SECRET (use generated one above)
- [ ] DIGITALOCEAN_ACCESS_TOKEN
- [ ] DO_REGISTRY_NAME
- [ ] UPSTASH_REDIS_URL
- [ ] UPSTASH_REDIS_REST_URL
- [ ] UPSTASH_REDIS_REST_TOKEN
- [ ] STRIPE_SECRET_KEY

### 2. Verify VPC Setup:
- [ ] MongoDB cluster is in same region as App Platform (nyc1)
- [ ] Using private- prefix in production MongoDB URI
- [ ] No IP whitelisting needed for production (VPC handles it)

### 3. Deploy:
```bash
git add -A
git commit -m "feat: configure VPC MongoDB connection"
git push origin main
```

### 4. Monitor Deployment:
- [ ] Check GitHub Actions: https://github.com/hannah-ric/esg-scraper/actions
- [ ] View App Platform logs in DigitalOcean
- [ ] Verify MongoDB connects via VPC (no public access needed)

## 🎉 Benefits of VPC:
- No bandwidth charges between app and database
- Enhanced security (no public exposure)
- Lower latency
- Automatic failover support 