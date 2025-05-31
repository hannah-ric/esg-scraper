#!/bin/bash

echo "🔍 Debugging DigitalOcean Registry Issue"
echo "======================================="
echo ""

# Your registry name from app.yaml
REGISTRY_NAME="hannahricci"
echo "📦 Registry Name: $REGISTRY_NAME"
echo ""

# Save Docker config
mkdir -p ~/.docker
echo '{"auths":{"registry.digitalocean.com":{"auth":"aGFubmFoc3JpY2NpQGdtYWlsLmNvbTpkb3BfdjFfZjRhNGE1MDZhZjg2NWFiNGE4ZTUwOGJkMDliNTYxZTk4MDRhNjUwYjYwZDAyM2NmM2Y0ZjBhZDgyYjQzNjY4Mw=="}}}' > ~/.docker/config.json

# Test with a tiny image
echo "1️⃣ Testing registry access with a minimal image..."
docker pull busybox:latest
docker tag busybox:latest registry.digitalocean.com/$REGISTRY_NAME/test-quota:latest

echo ""
echo "2️⃣ Attempting push to test quota..."
if docker push registry.digitalocean.com/$REGISTRY_NAME/test-quota:latest; then
    echo "✅ Push successful! Registry is working."
    echo ""
    echo "3️⃣ Cleaning up test image..."
    # Note: This would need doctl auth to work
    echo "You can delete 'test-quota' from https://cloud.digitalocean.com/registry"
else
    echo "❌ Push failed. Checking possible causes..."
    echo ""
    echo "Possible issues:"
    echo "1. Repository limit reached (not storage)"
    echo "2. Registry name mismatch"
    echo "3. Token permissions"
fi

echo ""
echo "📋 GitHub Secret Check:"
echo "Make sure DO_REGISTRY_NAME is set to: $REGISTRY_NAME"
echo ""
echo "🔍 Registry Limits:"
echo "- Starter Plan: 5 repositories, 5GB storage"
echo "- Basic Plan: 25 repositories, 25GB storage"
echo ""
echo "💡 If you have 5 repositories already, delete unused ones at:"
echo "https://cloud.digitalocean.com/registry/$REGISTRY_NAME" 