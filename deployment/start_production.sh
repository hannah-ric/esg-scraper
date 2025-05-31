# Verify environment variables
echo "🔍 Checking environment configuration..."
if [ -z "$MONGODB_URI" ]; then
    echo "❌ MONGODB_URI not set!"
    exit 1
fi

if [ -z "$JWT_SECRET" ]; then
    echo "❌ JWT_SECRET not set!"
    exit 1
fi

if [ -z "$UPSTASH_REDIS_URL" ]; then
    echo "❌ UPSTASH_REDIS_URL not set!"
    exit 1
fi

echo "✅ Environment variables configured"

# Set production defaults
export JWT_SECRET=${JWT_SECRET}
export MONGODB_URI=${MONGODB_URI}
export MONGODB_DATABASE=${MONGODB_DATABASE:-"admin"}
export UPSTASH_REDIS_URL=${UPSTASH_REDIS_URL}
export FREE_TIER_CREDITS=${FREE_TIER_CREDITS:-"100"}

echo "🌐 Starting ESG Scraper API server..."
echo "   MongoDB: Connected to managed cluster"
echo "   Redis: Using Upstash Redis"
echo "   Port: 8000"
echo "   Workers: ${WORKERS:-1}" 