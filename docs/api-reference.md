# 📖 ESG Platform API Reference

Base URL: `https://your-app.ondigitalocean.app`

## Authentication

All endpoints (except health checks) require JWT authentication.

### Register User
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com"
}
```

Response:
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "tier": "free",
  "credits": 100
}
```

### Using Authentication
Include the JWT token in the Authorization header:
```http
Authorization: Bearer YOUR_JWT_TOKEN
```

## Core Endpoints

### Analyze ESG Performance

Analyzes ESG performance from a URL or text content.

```http
POST /analyze
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json

{
  "url": "https://company.com/sustainability-report",
  "company_name": "Example Corp",
  "quick_mode": false,
  "frameworks": ["CSRD", "TCFD"],
  "industry_sector": "Technology",
  "reporting_period": "2023",
  "extract_metrics": true
}
```

Parameters:
- `url` (string, optional): URL to analyze
- `text` (string, optional): Direct text content (max 100k chars)
- `company_name` (string, optional): Company name for context
- `quick_mode` (boolean): Fast analysis (true) or comprehensive (false)
- `frameworks` (array): Frameworks to check ["CSRD", "GRI", "SASB", "TCFD"]
- `industry_sector` (string, optional): Industry for context
- `reporting_period` (string, optional): Reporting year
- `extract_metrics` (boolean): Extract standardized metrics

Response:
```json
{
  "scores": {
    "environmental": 75.5,
    "social": 82.3,
    "governance": 79.1,
    "overall": 78.9
  },
  "keywords": ["sustainability", "carbon neutral", "diversity"],
  "insights": [
    "Strong environmental performance detected",
    "Net-zero commitment identified"
  ],
  "analysis_type": "full",
  "confidence": 0.85,
  "framework_coverage": {
    "CSRD": {
      "coverage_percentage": 65.5,
      "requirements_found": 42,
      "requirements_total": 64,
      "mandatory_met": 18,
      "mandatory_total": 25
    }
  },
  "extracted_metrics": [
    {
      "metric_name": "Scope 1 GHG Emissions",
      "metric_value": 1250.5,
      "metric_unit": "tCO2e",
      "confidence": 0.9,
      "framework": "CSRD"
    }
  ],
  "gap_analysis": [
    {
      "framework": "CSRD",
      "requirement_id": "E1-1",
      "category": "Climate Change",
      "description": "Transition plan for climate change mitigation",
      "severity": "critical"
    }
  ],
  "recommendations": [
    "Critical gap in Climate Change: Immediate action required",
    "Improve CSRD disclosure: Currently at 65.5% coverage"
  ],
  "credits_used": 5,
  "credits_remaining": 95
}
```

### Compare Companies

Compare ESG performance of multiple companies.

```http
POST /compare
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json

{
  "companies": ["Company A", "Company B", "Company C"]
}
```

Response:
```json
{
  "companies": {
    "Company A": {
      "scores": {
        "environmental": 75.0,
        "social": 80.0,
        "governance": 85.0,
        "overall": 80.0
      },
      "trend": "improving",
      "last_updated": "2024-01-15T10:30:00"
    }
  },
  "benchmark": {
    "environmental": 65,
    "social": 70,
    "governance": 72
  }
}
```

### Export Data

Export analysis data in JSON or CSV format.

```http
POST /export
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json

{
  "format": "csv"
}
```

Parameters:
- `format` (string): "json" or "csv"

### Get Available Frameworks

List all available ESG frameworks and their requirements.

```http
GET /frameworks
Authorization: Bearer YOUR_JWT_TOKEN
```

Response:
```json
{
  "frameworks": {
    "CSRD": {
      "name": "CSRD",
      "total_requirements": 64,
      "mandatory_requirements": 25,
      "categories": ["Environmental", "Social", "Governance"]
    },
    "TCFD": {
      "name": "TCFD",
      "total_requirements": 11,
      "mandatory_requirements": 11,
      "categories": ["Governance", "Strategy", "Risk Management", "Metrics"]
    }
  }
}
```

### Company History

Get historical ESG data for a company.

```http
GET /company/{company_name}/history?days=90
Authorization: Bearer YOUR_JWT_TOKEN
```

Parameters:
- `days` (integer): Number of days of history (default: 90)

### Gap Analysis Details

Get detailed gap analysis for a specific analysis.

```http
GET /analysis/{analysis_id}/gaps
Authorization: Bearer YOUR_JWT_TOKEN
```

### Benchmark Companies

Benchmark multiple companies against ESG frameworks.

```http
POST /benchmark
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json

{
  "companies": ["Company A", "Company B"],
  "frameworks": ["CSRD", "TCFD"]
}
```

## Usage & Billing

### Check Usage

Get current usage statistics.

```http
GET /usage
Authorization: Bearer YOUR_JWT_TOKEN
```

Response:
```json
{
  "current_usage": 250,
  "limit": 1000,
  "percentage": 25.0,
  "reset_date": "2024-02-01"
}
```

### Subscribe to Tier

Subscribe to a paid tier.

```http
POST /subscribe
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json

{
  "tier": "starter",
  "payment_method": "pm_1234567890"
}
```

Tiers:
- `starter`: $49/month, 1,000 credits
- `growth`: $199/month, 5,000 credits
- `enterprise`: $999/month, 50,000 credits

## Health & Monitoring

### Basic Health Check

```http
GET /health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "services": {
    "mongodb": {
      "status": "healthy"
    },
    "redis": "healthy"
  }
}
```

### Detailed Health Check

```http
GET /health/detailed
```

Response includes system metrics:
```json
{
  "status": "healthy",
  "checks": {
    "mongodb": "healthy",
    "redis": "healthy",
    "memory": "healthy",
    "cpu": "healthy",
    "disk": "healthy"
  },
  "metrics": {
    "memory_percent": 45.2,
    "memory_available_mb": 278.5,
    "cpu_percent": 23.5,
    "disk_percent": 62.1
  }
}
```

### Prometheus Metrics

```http
GET /metrics
```

Returns Prometheus-formatted metrics for monitoring.

## Rate Limits

Rate limits are tier-based and per endpoint:

| Endpoint | Anonymous | Free | Starter | Growth | Enterprise |
|----------|-----------|------|---------|--------|------------|
| /analyze | 5/hour | 20/hour | 100/hour | 500/hour | 2000/hour |
| /compare | 5/hour | 10/hour | 50/hour | 200/hour | 1000/hour |
| /export | 1/day | 5/day | 20/day | 100/day | 1000/day |

Rate limit headers:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Unix timestamp when limit resets
- `Retry-After`: Seconds until retry (on 429 errors)

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid input: Either URL or text must be provided"
}
```

### 401 Unauthorized
```json
{
  "detail": "Invalid token"
}
```

### 429 Too Many Requests
```json
{
  "error": "Rate limit exceeded",
  "message": "Rate limit exceeded for tier: free",
  "retry_after": "60",
  "upgrade_url": "https://blueprintbuddy.io/pricing"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Analysis failed: Internal server error"
}
```

## Credit Costs

Operations consume credits based on complexity:

| Operation | Credits |
|-----------|---------|
| Quick analysis | 1 |
| Full analysis | 5 |
| Web scraping | 2 |
| Data export | 10 |
| Company comparison | 1 per company | 