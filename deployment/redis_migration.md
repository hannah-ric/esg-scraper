# Redis Migration to DigitalOcean Managed Redis

## 🚨 Current Issue
Redis is still running locally, causing:
- Data loss on container restart
- No persistence for cache
- Additional memory overhead (~50MB)
- No high availability

## 🚀 Migration Steps

### 1. Create Managed Redis Instance

```bash
# Create Redis database
doctl databases create esg-redis \
  --engine redis \
  --version 7 \
  --size db-s-1vcpu-1gb \
  --region nyc1
```

### 2. Get Connection Details

```bash
# Get Redis connection string
doctl databases connection esg-redis --format URI
```

Example output:
```
rediss://default:password@private-db-redis-nyc1-12345.db.ondigitalocean.com:25061
```

### 3. Update GitHub Secrets

Add to GitHub Secrets:
```
REDIS_URL=rediss://default:your-password@your-redis-host:25061
```

### 4. Enable SSL/TLS

Managed Redis requires SSL. The `rediss://` protocol handles this automatically.

### 5. Configure Connection Pool

Update Redis client initialization in `lean_esg_platform.py`:
```python
# Add SSL support for managed Redis
import ssl

# Configure Redis client with SSL
if REDIS_URL.startswith('rediss://'):
    redis_client = redis.from_url(
        REDIS_URL,
        decode_responses=True,
        ssl_cert_reqs=ssl.CERT_REQUIRED,
        ssl_ca_certs=ssl.get_default_verify_paths().cafile
    )
else:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
```

## 📊 Benefits

1. **Persistence**: Data survives restarts
2. **High Availability**: Automatic failover
3. **Backups**: Daily automated backups
4. **Monitoring**: Built-in metrics
5. **Security**: TLS encryption
6. **Memory Savings**: ~50MB freed in container

## 💰 Cost

- Basic plan: $15/month
- 1GB RAM, 1 vCPU
- Includes backups and monitoring

## 🔧 Testing

```bash
# Test connection
redis-cli -u $REDIS_URL ping
```

## ⚠️ Important Notes

1. **Connection Limits**: Managed Redis has connection limits. Use connection pooling.
2. **Eviction Policy**: Configure based on your needs (default: noeviction)
3. **Persistence**: Enable AOF for better durability
4. **Monitoring**: Set up alerts for memory usage

## 🎯 Next Steps

1. Create managed Redis instance
2. Update REDIS_URL in GitHub Secrets
3. Deploy and test
4. Monitor performance
5. Remove local Redis references 