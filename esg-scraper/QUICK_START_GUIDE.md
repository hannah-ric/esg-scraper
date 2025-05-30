# Quick Start Guide: Launch ESG Analyzer

This guide will help you launch your ESG Analyzer with a beautiful UI in under 30 minutes.

## 🚀 Quick Launch Steps

### Step 1: Fork and Clone

```bash
# Fork the repository on GitHub first, then:
git clone https://github.com/YOUR_USERNAME/esg-analyzer.git
cd esg-analyzer
```

### Step 2: Set Up GitHub Repository

```bash
# Initialize git (if not already done)
git init

# Add your GitHub repository as origin
git remote add origin https://github.com/YOUR_USERNAME/esg-analyzer.git

# Create and push to main branch
git add .
git commit -m "Initial commit: ESG Analyzer with beautiful UI"
git push -u origin main
```

### Step 3: Quick DigitalOcean Setup

1. **Sign up for DigitalOcean**: [Get $200 free credit](https://m.do.co/c/your-referral-code)

2. **Create App Platform Apps**:
   ```bash
   # Install DigitalOcean CLI
   brew install doctl  # macOS
   # or
   snap install doctl  # Linux
   
   # Authenticate
   doctl auth init
   ```

3. **Deploy Frontend** (Free Static Site):
   ```bash
   # From the frontend directory
   doctl apps create --spec - <<EOF
   name: esg-analyzer-frontend
   static_sites:
   - name: frontend
     github:
       repo: YOUR_USERNAME/esg-analyzer
       branch: main
       deploy_on_push: true
     source_dir: frontend
   EOF
   ```

4. **Deploy Backend**:
   ```bash
   # From the backend directory
   doctl apps create --spec - <<EOF
   name: esg-analyzer-backend
   services:
   - name: api
     github:
       repo: YOUR_USERNAME/esg-analyzer
       branch: main
       deploy_on_push: true
     source_dir: esg-scraper
     dockerfile_path: Dockerfile.bert
     instance_size_slug: basic-xs
     instance_count: 1
     http_port: 8000
     routes:
     - path: /
   EOF
   ```

### Step 4: Configure GitHub Secrets

1. Go to your GitHub repository
2. Navigate to Settings → Secrets → Actions
3. Add these secrets:
   - `DIGITALOCEAN_ACCESS_TOKEN`: Your DO API token
   - `DO_REGISTRY_NAME`: Your DO container registry name

### Step 5: Update Frontend API URL

Edit `frontend/app.js` and update:
```javascript
const API_BASE_URL = 'https://esg-analyzer-backend-xxxxx.ondigitalocean.app';
```

### Step 6: Push and Deploy

```bash
git add .
git commit -m "Configure for deployment"
git push origin main
```

The GitHub Action will automatically deploy your app!

## 🎨 Accessing Your Beautiful UI

After deployment (usually 5-10 minutes):

1. **Frontend URL**: Check DigitalOcean dashboard for your app URL
2. **API Documentation**: `https://your-backend-url/docs`

## 🛠️ Local Development

### Run Frontend Locally
```bash
cd frontend
python -m http.server 8080
# Visit http://localhost:8080
```

### Run Backend Locally
```bash
cd esg-scraper
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements_lean.txt
uvicorn lean_esg_platform:app --reload
# API at http://localhost:8000
```

## 📊 Test the Application

### Via the Beautiful UI:
1. Open your frontend URL
2. Paste sample ESG text:
   ```
   Our company reduced carbon emissions by 35% through renewable energy.
   Employee safety improved with TRIR of 0.5. Board diversity at 40%.
   ```
3. Click "Analyze Content"
4. See beautiful visualizations!

### Via API:
```bash
curl -X POST https://your-backend-url/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "content": "ESG report text here...",
    "frameworks": ["CSRD", "TCFD"]
  }'
```

## 💰 Cost Breakdown

- **Frontend**: FREE (static site)
- **Backend**: ~$5/month (basic plan)
- **Total**: ~$5/month for basic usage

## 🔧 Customization

### Change Colors/Theme
Edit `frontend/index.html`:
```css
.gradient-bg {
    background: linear-gradient(135deg, #YOUR_COLOR_1 0%, #YOUR_COLOR_2 100%);
}
```

### Add Your Logo
Replace the SVG icon in the header with your logo:
```html
<img src="your-logo.png" alt="Your Company" class="h-8">
```

### Modify Analysis Options
Edit `frontend/index.html` to add/remove frameworks or change default options.

## 🚨 Troubleshooting

### Frontend Not Loading?
- Check if build completed in DigitalOcean dashboard
- Verify API_BASE_URL in app.js

### Backend Errors?
- Check logs: `doctl apps logs YOUR_APP_ID`
- Ensure environment variables are set
- Verify Python version compatibility

### CORS Issues?
Add to backend `lean_esg_platform.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-url"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 📈 Next Steps

1. **Add Custom Domain**: 
   - Buy domain (e.g., Namecheap)
   - Add in DigitalOcean Apps settings
   - Update DNS records

2. **Enable Authentication**:
   - Add Auth0 or Firebase Auth
   - Protect API endpoints

3. **Scale Up**:
   - Upgrade to Professional plan for more resources
   - Enable autoscaling
   - Add Redis for caching

## 🎉 Congratulations!

You now have a beautiful, modern ESG analysis platform running in the cloud!

- Frontend: Beautiful, responsive UI
- Backend: Powerful API with BERT integration
- Deployment: Automated CI/CD pipeline

Share your deployment URL and start analyzing ESG reports! 🚀 