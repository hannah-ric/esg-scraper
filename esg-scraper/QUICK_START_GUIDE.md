# ESG Scraper Quick Start Guide

## ✅ System Status: Ready!

Your ESG scraper is now fully set up and working! All dependency conflicts have been resolved.

## 🚀 Quick Start

### 1. Verify Everything is Working
```bash
python health_check.py
```
This should show all green checkmarks ✅.

### 2. Start Required Services

**Start Redis (in a separate terminal):**
```bash
# macOS with Homebrew
brew services start redis
# OR manually
redis-server

# Ubuntu/Debian
sudo systemctl start redis-server

# Windows
# Download and install Redis for Windows
```

### 3. Configure Environment
Edit the `.env` file with your settings:
```bash
nano .env
```

**Important settings to update:**
```env
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
REDIS_URL=redis://localhost:6379
DATABASE_PATH=esg_data.db
```

### 4. Run the ESG Scraper
```bash
python lean_esg_platform.py
```

The API will be available at: `http://localhost:8000`

## 📊 What's Working Now

### ✅ Fixed Dependencies
- **lxml**: Now works on Apple Silicon Macs
- **trafilatura**: Web scraping with BeautifulSoup fallback
- **Celery**: Background tasks with all dependencies
- **Framework compatibility**: All version conflicts resolved

### ✅ ESG Framework Analysis
- **CSRD**: 14 comprehensive requirements
- **GRI**: 10 universal and topic-specific standards  
- **SASB**: 7 industry-focused requirements
- **TCFD**: 11 climate disclosure requirements

### ✅ Advanced Features
- Framework compliance percentage calculation
- Automated metrics extraction (emissions, financial, social)
- Gap analysis with severity levels (critical, high, medium, low)
- Industry-specific recommendations
- Historical trend tracking
- Company benchmarking

## 🔧 API Usage Examples

### Analyze a URL
```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "url": "https://example.com/sustainability-report",
    "company_name": "Example Corp",
    "frameworks": ["CSRD", "TCFD"],
    "industry_sector": "Technology",
    "quick_mode": false
  }'
```

### Analyze Text Content
```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "text": "Our company committed to net zero emissions by 2030...",
    "company_name": "Green Corp",
    "frameworks": ["CSRD", "GRI", "SASB", "TCFD"]
  }'
```

### Get Framework Information
```bash
curl -X GET "http://localhost:8000/frameworks" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Compare Companies
```bash
curl -X POST "http://localhost:8000/compare" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "companies": ["Apple Inc", "Microsoft", "Google"]
  }'
```

## 🔑 Getting an API Token

1. Register a user:
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "your@email.com"}'
```

2. Use the returned token in the `Authorization: Bearer <token>` header.

## 📈 Enhanced Analysis Features

### Framework Compliance Analysis
- **Coverage Percentage**: How much of each framework is addressed
- **Mandatory vs Optional**: Compliance with required vs recommended disclosures
- **Gap Analysis**: What's missing with severity assessment

### Metrics Extraction
- **Emissions Data**: CO2, scope 1/2/3 emissions
- **Financial Metrics**: Revenue impacts, investment amounts
- **Social Metrics**: Diversity percentages, safety incidents
- **Governance Indicators**: Board composition, ethics training

### Industry Intelligence
- **Sector-Specific Analysis**: Tailored recommendations by industry
- **Benchmarking**: Compare against industry averages
- **Trend Analysis**: Historical performance tracking

## 🛠️ Troubleshooting

### If Redis Connection Fails
```bash
# Check if Redis is running
redis-cli ping
# Should return "PONG"

# Start Redis if not running
brew services start redis  # macOS
sudo systemctl start redis-server  # Linux
```

### If Web Scraping Fails
The system automatically falls back to BeautifulSoup if trafilatura fails. You can also use the manual scraper:
```bash
python simple_scraper.py
```

### If Framework Analysis is Slow
Use `quick_mode: true` for faster analysis:
```json
{
  "text": "Your ESG content...",
  "quick_mode": true,
  "frameworks": ["CSRD"]
}
```

## 📚 API Documentation

Once running, visit these URLs for documentation:
- **Interactive API Docs**: http://localhost:8000/docs
- **OpenAPI Schema**: http://localhost:8000/openapi.json
- **Redoc Documentation**: http://localhost:8000/redoc

## 🎯 Key Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/auth/register` | POST | Register new user |
| `/analyze` | POST | Analyze ESG content |
| `/frameworks` | GET | List available frameworks |
| `/compare` | POST | Compare multiple companies |
| `/export` | POST | Export analysis data |
| `/health` | GET | System health check |
| `/metrics` | GET | Prometheus metrics |

## 🔍 Framework Details

### CSRD (Corporate Sustainability Reporting Directive)
- **Mandatory in EU** starting 2024
- Covers Environmental, Social, Governance
- **Double materiality** approach
- 14 detailed requirements implemented

### TCFD (Task Force on Climate-related Financial Disclosures)
- **Climate risk** focus
- Governance, Strategy, Risk Management, Metrics & Targets
- **Scenario analysis** requirements
- 11 comprehensive requirements

### GRI (Global Reporting Initiative)
- **Universal standards** + topic-specific
- Stakeholder impact focus
- **Material topics** identification
- 10 key standards implemented

### SASB (Sustainability Accounting Standards Board)
- **Industry-specific** materiality
- Financial impact focus
- **Investor-oriented** disclosures
- 7 cross-sector requirements

## 🚨 Production Deployment

For production use:

1. **Set Strong JWT Secret**:
   ```env
   JWT_SECRET=your-cryptographically-secure-secret-key
   ```

2. **Use Production Database**:
   ```env
   DATABASE_PATH=/data/esg_production.db
   ```

3. **Configure Redis with Auth**:
   ```env
   REDIS_URL=redis://username:password@redis-host:6379
   ```

4. **Set Resource Limits**:
   ```env
   MAX_WORKERS=4
   MEMORY_LIMIT=2GB
   ```

5. **Enable Monitoring**:
   ```env
   LOG_LEVEL=INFO
   ENVIRONMENT=production
   ```

## 📞 Support

If you encounter issues:

1. **Run Health Check**: `python health_check.py`
2. **Check Logs**: Look in the `logs/` directory
3. **Verify Dependencies**: Ensure all packages are installed correctly
4. **Test Components**: Use the individual test scripts

Your ESG scraper is now production-ready with enterprise-grade framework analysis capabilities! 🎉 