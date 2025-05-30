# Enhanced ESG Intelligence Platform with Framework Compliance

## Overview

The Enhanced ESG Intelligence Platform now includes comprehensive compliance checking for major ESG reporting frameworks:
- **CSRD** (Corporate Sustainability Reporting Directive) - EU mandatory reporting
- **GRI** (Global Reporting Initiative) - Global sustainability standards
- **SASB** (Sustainability Accounting Standards Board) - Industry-specific metrics
- **TCFD** (Task Force on Climate-related Financial Disclosures) - Climate risk reporting

## Key Features

### 1. Framework Compliance Analysis
- Automated detection of framework requirements in documents
- Coverage percentage calculation for each framework
- Identification of mandatory vs. optional requirements
- Gap analysis with severity assessment

### 2. Metric Extraction
- Automated extraction of quantitative ESG metrics
- Mapping metrics to specific framework requirements
- Confidence scoring for extracted values
- Support for various units (tCO2e, cubic meters, percentages, etc.)

### 3. Industry-Specific Analysis
- Severity assessment based on industry sector
- Tailored recommendations for different industries
- Critical requirements highlighting for regulated sectors

### 4. Enhanced Database Schema
- Framework compliance tracking
- Historical ESG score tracking
- Company profiles with industry classification
- Detailed requirement findings storage

## API Endpoints

### Enhanced Analysis Endpoint
```bash
POST /analyze
{
    "url": "https://example.com/sustainability-report",
    "company_name": "Example Corp",
    "quick_mode": false,
    "frameworks": ["CSRD", "TCFD"],
    "industry_sector": "Technology",
    "reporting_period": "2023",
    "extract_metrics": true
}
```

**Response includes:**
- Traditional ESG scores (E, S, G)
- Framework coverage percentages
- Extracted metrics with confidence scores
- Gap analysis with severity levels
- Actionable recommendations
- Detailed requirement findings

### Framework Information
```bash
GET /frameworks
```
Returns available frameworks and their requirements structure.

### Company History
```bash
GET /company/{company_name}/history?days=90
```
Returns historical ESG scores and framework compliance trends.

### Gap Analysis
```bash
GET /analysis/{analysis_id}/gaps
```
Returns detailed gap analysis grouped by framework and severity.

### Company Benchmark
```bash
POST /benchmark
{
    "companies": ["Company A", "Company B", "Company C"],
    "frameworks": ["CSRD", "TCFD"]
}
```

## Framework Requirements Coverage

### CSRD (13 Requirements)
- **Environmental (E1-E5)**: Climate change, pollution, water, biodiversity, circular economy
- **Social (S1-S4)**: Workforce, value chain, communities, consumers
- **Governance (G1)**: Business conduct and culture

### GRI (12 Requirements)
- **Universal Standards**: Organization details, strategy
- **Topic Standards**: Materials, energy, water, emissions, employment, safety, training, diversity

### SASB (9 Requirements)
- **Environment**: GHG emissions, energy, water management
- **Social Capital**: Data security, product safety
- **Human Capital**: Health & safety, employee engagement
- **Business Model**: Product lifecycle
- **Governance**: Business ethics

### TCFD (11 Requirements)
- **Governance**: Board oversight, management role
- **Strategy**: Climate risks, business impact, scenario analysis
- **Risk Management**: Identification, management, integration
- **Metrics & Targets**: Climate metrics, GHG emissions, targets

## Usage Examples

### 1. Analyze a Sustainability Report
```python
import requests

# Get auth token
response = requests.post("http://localhost:8000/auth/register", 
    json={"email": "user@example.com"})
token = response.json()["token"]

# Analyze report
response = requests.post(
    "http://localhost:8000/analyze",
    json={
        "url": "https://company.com/sustainability-report.pdf",
        "company_name": "Tech Corp",
        "quick_mode": False,
        "frameworks": ["CSRD", "TCFD"],
        "industry_sector": "Technology"
    },
    headers={"Authorization": f"Bearer {token}"}
)

result = response.json()
print(f"CSRD Coverage: {result['framework_coverage']['CSRD']['coverage_percentage']}%")
print(f"Critical Gaps: {len([g for g in result['gap_analysis'] if g['severity'] == 'critical'])}")
```

### 2. Compare Companies
```python
response = requests.post(
    "http://localhost:8000/benchmark",
    json={
        "companies": ["Apple", "Microsoft", "Google"],
        "frameworks": ["CSRD", "TCFD"]
    },
    headers={"Authorization": f"Bearer {token}"}
)

benchmark = response.json()
print(f"Best Performer: {benchmark['best_performer']}")
```

## Testing

Run the comprehensive test suite:

```bash
# Basic tests
python test_esg_service.py

# Framework compliance tests
python test_framework_compliance.py

# Or use pytest
pytest test_framework_compliance.py -v
```

## Database Schema

The enhanced schema includes:

1. **analyses** - Core analysis results with industry and period
2. **framework_compliance** - Framework-specific coverage metrics
3. **requirement_findings** - Detailed findings for each requirement
4. **extracted_metrics** - Quantitative metrics with units and confidence
5. **gap_analysis** - Missing requirements with severity
6. **company_profiles** - Company metadata and classification
7. **historical_scores** - Time-series ESG and framework data

## Configuration

### Environment Variables
```bash
JWT_SECRET=your-secret-key
REDIS_URL=redis://localhost:6379
DATABASE_PATH=esg_data.db
FREE_TIER_CREDITS=100
STRIPE_SECRET_KEY=your-stripe-key  # For paid tiers
```

### Docker Deployment
```bash
docker-compose up -d
```

## Performance Considerations

1. **Quick Mode**: Fast keyword-based analysis (1 credit)
2. **Full Mode**: Comprehensive framework analysis (5 credits)
3. **Caching**: Results cached for 24 hours
4. **Rate Limiting**: 10 requests/minute per user

## Compliance Notes

- **CSRD**: Mandatory for EU companies from 2024
- **TCFD**: Mandatory in UK, recommended globally
- **GRI**: Voluntary but widely adopted
- **SASB**: US-focused, industry-specific

## Future Enhancements

1. **ML-based requirement detection** - Improve accuracy beyond keywords
2. **PDF parsing optimization** - Better extraction from complex documents
3. **Multi-language support** - Analyze reports in languages other than English
4. **API integrations** - Direct connections to reporting platforms
5. **Automated report generation** - Create compliance reports from analysis

## Support

For issues or questions:
1. Check the test files for usage examples
2. Review the API documentation at `/docs`
3. Check logs: `docker-compose logs`

## License

This enhanced platform maintains the same license as the original ESG scraper. 