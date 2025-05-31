# 🌱 ESG Intelligence Platform

**Production-Ready ESG Analysis Platform with Framework Compliance**

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-green)](https://fastapi.tiangolo.com)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-green)](https://www.mongodb.com)
[![Redis](https://img.shields.io/badge/Redis-Upstash-red)](https://upstash.com)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

## 📊 Overview

The ESG Intelligence Platform is a production-ready API service that analyzes Environmental, Social, and Governance (ESG) performance from company reports and websites. It provides comprehensive framework compliance checking against CSRD, GRI, SASB, and TCFD standards.

### ✨ Key Features

- **ESG Analysis**: Automated scoring and insights extraction
- **Framework Compliance**: CSRD, GRI, SASB, TCFD requirement checking
- **Metric Extraction**: Standardized ESG metrics with unit conversion
- **Gap Analysis**: Identify missing disclosures and compliance gaps
- **Multi-Company Comparison**: Benchmark multiple companies
- **Tiered Rate Limiting**: Usage-based API access control
- **Production Ready**: Deployed on DigitalOcean with MongoDB and Redis

## 🚀 Quick Start

### Local Development

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/esg-scraper.git
   cd esg-scraper
   ```

2. **Set up environment**:
   ```bash
   cd esg-scraper
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run the application**:
   ```bash
   python lean_esg_platform.py
   ```

5. **Access the API**:
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs

## 📁 Project Structure

```
esg-scraper/
├── esg-scraper/                    # Main application directory
│   ├── lean_esg_platform.py        # Main FastAPI application
│   ├── esg_frameworks.py           # ESG framework definitions
│   ├── mongodb_manager.py          # MongoDB async operations
│   ├── metrics_standardizer.py     # Metric standardization
│   ├── api_versioning.py           # API versioning framework
│   └── requirements.txt            # Python dependencies
├── deployment/                     # Deployment configurations
│   ├── app.yaml                    # DigitalOcean App Platform config
│   ├── verify_implementation.sh    # Implementation verification
│   └── migrate_redis.py            # Redis migration tool
├── .github/workflows/              # CI/CD pipelines
│   └── deploy.yml                  # GitHub Actions deployment
└── docs/                          # Consolidated documentation
    ├── deployment-guide.md         # Deployment instructions
    ├── api-reference.md            # API documentation
    └── monitoring-setup.md         # Monitoring configuration
```

## 🔧 Configuration

### Environment Variables

```bash
# MongoDB
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/
MONGODB_DATABASE=esg_platform

# Redis (Upstash)
REDIS_URL=rediss://default:password@endpoint.upstash.io:6379

# Security
JWT_SECRET=your-secret-key
CORS_ORIGINS=https://yourdomain.com,http://localhost:3000

# Monitoring (Optional)
SENTRY_DSN=https://key@sentry.io/project

# API Keys
STRIPE_SECRET_KEY=sk_test_xxx  # For subscription management
```

## 📚 API Endpoints

### Core Endpoints

- **POST /analyze** - Analyze ESG performance from URL or text
- **POST /compare** - Compare multiple companies
- **GET /frameworks** - List available ESG frameworks
- **GET /health** - Basic health check
- **GET /health/detailed** - Detailed system metrics

### Authentication

All endpoints (except /health) require JWT authentication:

```bash
curl -X POST http://api.example.com/analyze \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://company.com/sustainability-report"}'
```

## 🚀 Deployment

### DigitalOcean App Platform

1. **Fork this repository**

2. **Create DigitalOcean App**:
   - Go to DigitalOcean App Platform
   - Connect your GitHub repository
   - Select the deployment branch

3. **Configure environment variables** in DigitalOcean dashboard

4. **Deploy**: Push to your main branch to trigger deployment

### Production Architecture

- **App Platform**: DigitalOcean (Basic plan: $5/month)
- **Database**: MongoDB Atlas (M0 Shared: $15/month)
- **Cache**: Upstash Redis (Free tier: 10k commands/day)
- **Monitoring**: Sentry (Optional)

Total cost: ~$20/month for starter setup

## 🔒 Security

- JWT-based authentication
- Rate limiting by user tier
- Security headers (HSTS, CSP, etc.)
- Input validation and sanitization
- CORS configuration
- SSL/TLS encryption

## 📊 Monitoring

- **Health Checks**: `/health` and `/health/detailed`
- **Metrics**: Prometheus-compatible metrics at `/metrics`
- **Error Tracking**: Sentry integration (optional)
- **Logging**: Structured JSON logging

## 🧪 Testing

```bash
# Run tests
pytest test_framework_compliance.py -v

# Check code quality
flake8 . --max-line-length=120 --exclude=venv,__pycache__
black . --check
```

## 📈 Performance

- **Memory Usage**: ~150MB (optimized from 1350MB)
- **Response Time**: <500ms average
- **Concurrent Users**: 100+ supported
- **Rate Limits**: 5-2000 requests/hour (tier-based)

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🛟 Support

- **Documentation**: See `/docs` directory
- **Issues**: GitHub Issues
- **Email**: support@example.com

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- DigitalOcean for hosting infrastructure
- MongoDB and Upstash for database services

---

**Status**: 🟢 Production Ready | **Version**: 1.0.0 | **Last Updated**: December 2024 