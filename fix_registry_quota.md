# Fix DigitalOcean Registry Quota Issue

## Quick Solutions:

### Option 1: Clean Up via Web Console (Easiest)
1. Go to: https://cloud.digitalocean.com/registry
2. Click on your registry
3. Click on "esg-scraper" repository
4. Delete old image tags (keep only "latest" and most recent)
5. This will free up space immediately

### Option 2: Upgrade Registry (If needed)
- Current plan: Likely "Starter" (5GB, 5 repositories)
- Upgrade to "Basic" ($5/month, 25GB storage)
- Go to: Registry → Settings → Change Plan

### Option 3: Use Docker Hub Instead (Free)
We can modify your workflow to use Docker Hub:
1. Create account at https://hub.docker.com
2. Create repository "esg-scraper"
3. Update GitHub secrets:
   - DOCKER_HUB_USERNAME
   - DOCKER_HUB_TOKEN
4. I'll update the workflow file

### Option 4: Auto-cleanup Old Images
Add this to your workflow to keep only last 5 images:
```yaml
- name: Clean old images
  run: |
    # This would run after successful deployment
    doctl registry repository list-tags esg-scraper --format Tag --no-header | tail -n +6 | xargs -I {} doctl registry repository delete-tag esg-scraper {} --force
```

## Immediate Fix:
Go to https://cloud.digitalocean.com/registry and delete old images manually! 