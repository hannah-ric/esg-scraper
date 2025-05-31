# ESG Scraper Secure Configuration

## 🔐 GitHub Secrets Required

Add these secrets to your GitHub repository (Settings → Secrets and variables → Actions):

### 1. **JWT_SECRET**
Generate a secure random secret:
```bash
openssl rand -base64 32
```
Example: `yBz5K8pN2fQ3XwR7mA9vC6hJ4tL1sE0dGnU8iO5qWe0=`

### 2. **MONGODB_URI**
Your DigitalOcean MongoDB connection string:
```
mongodb+srv://dbadmin:8Lpj41o605fSD97r@dbaas-db-5313098-ad381704.mongo.ondigitalocean.com/admin?authSource=admin&tls=true
```

### 3. **REDIS_URL**
For local Redis (temporary):
```
redis://localhost:6379
```

For DigitalOcean Managed Redis (recommended):
```
rediss://default:YOUR_REDIS_PASSWORD@YOUR_REDIS_HOST:25061
```

### 4. **STRIPE_SECRET_KEY**
Your Stripe secret key (starts with `sk_`):
```
sk_live_YOUR_ACTUAL_STRIPE_SECRET_KEY
```

### 5. **SLACK_WEBHOOK_URL** (Optional)
Your Slack webhook for notifications:
```
https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

## 📝 MongoDB Connection Details

**Connection String Components:**
- Protocol: `mongodb+srv://`
- Username: `dbadmin`
- Password: `8Lpj41o605fSD97r`
- Host: `dbaas-db-5313098-ad381704.mongo.ondigitalocean.com`
- Database: `admin`
- Options: `?authSource=admin&tls=true`

**Important:** The password contains special characters. The connection string above is properly URL-encoded.

## 🚀 Setting GitHub Secrets

1. Go to your repository: https://github.com/hannah-ric/esg-scraper
2. Click Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Add each secret with the exact name and value

## 🔒 Security Best Practices

1. **Never commit secrets to code**
2. **Rotate secrets regularly**
3. **Use different secrets for dev/staging/production**
4. **Enable GitHub secret scanning**
5. **Limit secret access to required workflows**

## 🎯 Quick Setup Commands

```bash
# Generate JWT secret
export JWT_SECRET=$(openssl rand -base64 32)

# Set MongoDB URI (already formatted correctly)
export MONGODB_URI="mongodb+srv://dbadmin:8Lpj41o605fSD97r@dbaas-db-5313098-ad381704.mongo.ondigitalocean.com/admin?authSource=admin&tls=true"

# For testing locally
export REDIS_URL="redis://localhost:6379"

echo "JWT_SECRET=$JWT_SECRET"
echo "MONGODB_URI=$MONGODB_URI"
echo "REDIS_URL=$REDIS_URL"
```

## ⚠️ Critical Security Notes

1. **Change default passwords immediately**
2. **Enable IP whitelisting on MongoDB**
3. **Use read-only credentials where possible**
4. **Monitor access logs regularly**
5. **Set up alerts for unauthorized access**

## 📊 MongoDB Best Practices

1. **Create application-specific database:**
   ```javascript
   use esg_scraper
   db.createUser({
     user: "esg_app",
     pwd: "GENERATE_STRONG_PASSWORD",
     roles: [{ role: "readWrite", db: "esg_scraper" }]
   })
   ```

2. **Enable authentication**
3. **Configure backup retention**
4. **Set up monitoring alerts**
5. **Review slow query logs**

## 🆘 Troubleshooting

### MongoDB Connection Issues:
- Verify IP whitelist includes your app's IP
- Check SSL/TLS certificate
- Ensure correct auth database (`authSource=admin`)
- Test with `mongosh` command line tool

### Redis Connection Issues:
- Check if Redis is running: `redis-cli ping`
- Verify port is open (6379 for standard, 25061 for managed)
- Check authentication if using managed Redis

### JWT Issues:
- Ensure secret is at least 32 characters
- Use the same secret across all instances
- Don't include spaces or newlines 