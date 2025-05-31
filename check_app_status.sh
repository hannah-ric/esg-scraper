#!/bin/bash

echo "🔍 Checking DigitalOcean App Status..."
echo ""

# Check if doctl is installed
if ! command -v doctl &> /dev/null; then
    echo "❌ doctl is not installed. Please install it first:"
    echo "   brew install doctl"
    exit 1
fi

# Check if authenticated
if ! doctl auth list &> /dev/null; then
    echo "❌ Not authenticated with DigitalOcean. Please run:"
    echo "   doctl auth init"
    exit 1
fi

# List all apps
echo "📱 Your DigitalOcean Apps:"
doctl apps list

# Check for esg-scraper app
if doctl apps list | grep -q "esg-scraper"; then
    APP_ID=$(doctl apps list --format ID,Spec.Name --no-header | grep esg-scraper | awk '{print $1}')
    echo ""
    echo "✅ Found ESG Scraper app: $APP_ID"
    echo ""
    
    # Get detailed app info
    echo "📊 App Details:"
    doctl apps get $APP_ID --format json > app_details.json
    
    # Extract URLs
    LIVE_URL=$(cat app_details.json | jq -r '.live_url // empty')
    DEFAULT_DOMAIN=$(cat app_details.json | jq -r '.default_ingress // empty')
    
    echo "Live URL: ${LIVE_URL:-Not available yet}"
    echo "Default Domain: ${DEFAULT_DOMAIN:-Not available yet}"
    
    # Construct URL if needed
    if [ -z "$LIVE_URL" ] && [ -n "$DEFAULT_DOMAIN" ]; then
        LIVE_URL="https://$DEFAULT_DOMAIN"
        echo "Constructed URL: $LIVE_URL"
    fi
    
    # Show deployment status
    echo ""
    echo "🚀 Latest Deployment:"
    PHASE=$(cat app_details.json | jq -r '.in_progress_deployment.phase // .last_deployment_active_at // "No deployment info"')
    echo "Status: $PHASE"
    
    # Test the app if URL is available
    if [ -n "$LIVE_URL" ] && [ "$LIVE_URL" != "null" ]; then
        echo ""
        echo "🧪 Testing app health..."
        HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$LIVE_URL/health" 2>/dev/null || echo "Failed")
        
        if [ "$HEALTH_STATUS" = "200" ]; then
            echo "✅ Health check passed! App is running at: $LIVE_URL"
        else
            echo "⚠️  Health check returned status: $HEALTH_STATUS"
            echo "   The app might still be deploying..."
        fi
    else
        echo ""
        echo "⚠️  App URL not available yet. The app might still be creating..."
    fi
    
    # Clean up
    rm -f app_details.json
else
    echo ""
    echo "❌ ESG Scraper app not found in your DigitalOcean account"
    echo ""
    echo "To create the app, run:"
    echo "  doctl apps create --spec deployment/app.yaml"
fi

echo ""
echo "📝 To view deployment logs:"
echo "   doctl apps logs esg-scraper --type=deploy" 