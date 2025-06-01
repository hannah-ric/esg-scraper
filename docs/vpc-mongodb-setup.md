# MongoDB VPC Network Setup for DigitalOcean App Platform

## Overview
When your app is deployed on DigitalOcean App Platform, it can connect to your Managed MongoDB database using the private network (VPC) automatically. This is more secure and doesn't count against your bandwidth.

## Step 1: Get Both Connection Strings

1. Go to your [DigitalOcean Control Panel](https://cloud.digitalocean.com/databases)
2. Click on your MongoDB cluster
3. Click "Connection Details"
4. You'll see two connection strings:
   - **Public network**: For local development
   - **Private network**: For production (App Platform)

### Example Connection Strings:

**Public (for local development):**
```
mongodb+srv://doadmin:PASSWORD@db-mongodb-nyc1-12345.mongo.ondigitalocean.com/admin?authSource=admin&tls=true
```

**Private (for App Platform):**
```
mongodb+srv://doadmin:PASSWORD@private-db-mongodb-nyc1-12345.mongo.ondigitalocean.com/admin?authSource=admin&tls=true
```

Note: The private connection string has `private-` prefix in the hostname.

## Step 2: Configure Environment Variables

### For Local Development (.env):
```bash
# Use PUBLIC connection string for local testing
MONGODB_URI=mongodb+srv://doadmin:YOUR_PASSWORD@db-mongodb-nyc1-12345.mongo.ondigitalocean.com/admin?authSource=admin&tls=true
MONGODB_DATABASE=admin
```

### For Production (GitHub Secrets):
```bash
# Use PRIVATE connection string for App Platform
MONGODB_URI=mongodb+srv://doadmin:YOUR_PASSWORD@private-db-mongodb-nyc1-12345.mongo.ondigitalocean.com/admin?authSource=admin&tls=true
MONGODB_DATABASE=admin
```

## Step 3: Update deployment/app.yaml

Your app.yaml is already configured correctly:
```yaml
envs:
  - key: MONGODB_URI
    value: ${MONGODB_URI}
    type: SECRET
    scope: RUN_TIME
  
  - key: MONGODB_DATABASE
    value: admin
    scope: RUN_TIME
```

## Step 4: Set GitHub Secrets

1. Go to your GitHub repository
2. Settings → Secrets and variables → Actions
3. Add these secrets:

```
MONGODB_URI = mongodb+srv://doadmin:PASSWORD@private-db-mongodb-nyc1-12345.mongo.ondigitalocean.com/admin?authSource=admin&tls=true
MONGODB_DATABASE = admin
DIGITALOCEAN_ACCESS_TOKEN = your_do_token
DO_REGISTRY_NAME = your_registry_name
JWT_SECRET = your_jwt_secret
UPSTASH_REDIS_URL = your_UPSTASH_REDIS_URL
STRIPE_SECRET_KEY = your_stripe_key
```

## Step 5: VPC Network Details

### Automatic VPC Assignment
- App Platform apps are automatically placed in the default VPC for your region
- Managed databases are also in the same VPC by default
- No additional configuration needed!

### Security Benefits:
1. **No public internet exposure** - Traffic stays within DigitalOcean's network
2. **No bandwidth charges** - VPC traffic is free
3. **Lower latency** - Direct private network connection
4. **Enhanced security** - No need to whitelist IPs for production

## Step 6: Testing the Connection

### Local Testing (with public URL):
```bash
# Set environment variable
export MONGODB_URI='mongodb+srv://doadmin:PASSWORD@db-mongodb-nyc1-12345.mongo.ondigitalocean.com/admin?authSource=admin&tls=true'

# Test connection
cd esg-scraper
python lean_esg_platform.py
```

### Production Testing (after deployment):
```bash
# Check your app logs in DigitalOcean
doctl apps logs YOUR_APP_ID --type=run

# Or via web console
# Go to Apps → Your App → Runtime Logs
```

## Troubleshooting

### If VPC connection fails:
1. **Check the private hostname** - Ensure it has `private-` prefix
2. **Verify same region** - App and database must be in same region
3. **Check connection string** - No spaces or special characters issues
4. **Review logs** - Look for specific connection errors

### Common Issues:
```
# Wrong: Using public URL in production
mongodb+srv://doadmin:pass@db-mongodb.mongo.ondigitalocean.com

# Right: Using private URL in production  
mongodb+srv://doadmin:pass@private-db-mongodb.mongo.ondigitalocean.com
```

## Best Practices

1. **Never expose MongoDB publicly** - Use VPC for production
2. **Use environment variables** - Don't hardcode connection strings
3. **Rotate passwords regularly** - Update in both GitHub secrets and DO
4. **Monitor connection pool** - Adjust MONGODB_POOL_SIZE if needed
5. **Enable connection encryption** - Always use `tls=true`

## Next Steps

1. Update your GitHub secrets with the private MongoDB URI
2. Push your code to trigger deployment
3. Monitor the deployment logs
4. Verify the app connects successfully via VPC

Your app will automatically use the secure VPC connection when deployed! 🚀 