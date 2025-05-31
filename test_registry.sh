#!/bin/bash

echo "🔍 Testing DigitalOcean Registry Connection"
echo "=========================================="

# Save the auth config
mkdir -p ~/.docker
echo '{"auths":{"registry.digitalocean.com":{"auth":"aGFubmFoc3JpY2NpQGdtYWlsLmNvbTpkb3BfdjFfZjRhNGE1MDZhZjg2NWFiNGE4ZTUwOGJkMDliNTYxZTk4MDRhNjUwYjYwZDAyM2NmM2Y0ZjBhZDgyYjQzNjY4Mw=="}}}' > ~/.docker/config.json

echo "✅ Docker config saved"
echo ""

# Test login
echo "Testing registry login..."
if docker login registry.digitalocean.com; then
    echo "✅ Login successful!"
else
    echo "❌ Login failed"
    exit 1
fi

echo ""
echo "📝 Important: Make sure your GitHub secret DO_REGISTRY_NAME matches your actual registry name!"
echo ""
echo "To find your registry name:"
echo "1. Go to: https://cloud.digitalocean.com/registry"
echo "2. Look for the registry name (e.g., 'hannahricci' or similar)"
echo ""
echo "🚀 Let's try a test push to see the exact error:"

# Try to pull a small test image and tag it
docker pull alpine:latest
docker tag alpine:latest registry.digitalocean.com/YOUR_REGISTRY_NAME/test:latest

echo ""
echo "⚠️  Replace YOUR_REGISTRY_NAME above with your actual registry name and run:"
echo "docker push registry.digitalocean.com/YOUR_REGISTRY_NAME/test:latest" 