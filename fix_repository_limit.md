# Fix DigitalOcean Registry Repository Limit

## The Issue:
- **Error**: "quota exceeded"
- **Cause**: You've reached the 5 repository limit on Starter plan
- **NOT** a storage issue!

## Quick Fix:

### 1. Check Current Repositories
Go to: https://cloud.digitalocean.com/registry/hannahricci

You'll likely see 5 repositories already.

### 2. Delete an Unused Repository
- Click on any old/unused repository
- Click "Settings" → "Delete Repository"
- This will free up a slot for `esg-scraper`

### 3. Verify GitHub Secret
Make sure `DO_REGISTRY_NAME` is set to: `hannahricci`

### 4. Re-run Deployment
The workflow will automatically run when you push any change.

## Alternative Solutions:

### A. Upgrade to Basic Plan ($5/month)
- 25 repositories (vs 5)
- 25GB storage (vs 5GB)
- Worth it if you have multiple projects

### B. Use Docker Hub (Free)
- Unlimited public repositories
- 1 free private repository
- We can modify your workflow to use Docker Hub instead

### C. Clean Up Automatically
Add a pre-deployment step to delete old repositories programmatically.

## Recommended Action:
Delete 1-2 unused repositories manually right now at:
https://cloud.digitalocean.com/registry/hannahricci 