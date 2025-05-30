# ESG Intelligence Platform

A production-ready, AI-powered ESG (Environmental, Social, and Governance) analysis platform that scrapes web content and PDFs to provide instant ESG scoring and insights.

## 🚀 Features

- **Web Scraping**: Analyze any website for ESG content
- **PDF Analysis**: Upload and analyze sustainability reports
- **AI-Powered Scoring**: ML-based ESG scoring using FinBERT
- **Real-time Analysis**: Get instant ESG scores and insights
- **API-First Design**: RESTful API with comprehensive documentation
- **Usage-Based Billing**: Flexible pricing with Stripe integration
- **Enterprise Ready**: Rate limiting, monitoring, and security features

## 📊 Architecture

- **Backend**: FastAPI (Python 3.11)
- **Database**: SQLite (upgradeable to PostgreSQL)
- **Cache**: Redis
- **ML Model**: FinBERT for sentiment analysis
- **Monitoring**: Prometheus + Grafana
- **Container**: Docker + Docker Compose
- **CI/CD**: GitHub Actions

## 🛠️ Quick Start

### Prerequisites

- Docker & Docker Compose
- OpenSSL (for SSL certificates)
- 4GB RAM minimum
- 10GB disk space

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/esg-scraper.git
cd esg-scraper
```

2. Create environment file:
```bash
cp esg-scraper/.env.example .env
# Edit .env with your configuration
```

3. Deploy the platform:
```bash
chmod +x deploy.sh
./deploy.sh
```

The platform will be available at:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Metrics: http://localhost:8000/metrics
- Grafana: http://localhost:3000 (admin/admin)

## 🔑 API Usage

### 1. Register (Free Tier)

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'
```

### 2. Analyze URL

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/sustainability-report",
    "company_name": "Example Corp",
    "quick_mode": true
  }'
```

### 3. Compare Companies

```bash
curl -X POST http://localhost:8000/compare \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "companies": ["Apple", "Microsoft", "Google"]
  }'
```

## 💰 Pricing Tiers

| Tier | Price | Credits/Month | Features |
|------|-------|---------------|----------|
| Free | $0 | 100 | Basic analysis, Email support |
| Starter | $49 | 1,000 | Full analysis, Priority support |
| Growth | $199 | 5,000 | Bulk operations, Custom integration |
| Enterprise | $999 | 50,000 | Dedicated support, SLA |

## 🔒 Security Features

- JWT-based authentication
- Rate limiting per endpoint
- SSRF protection
- Input validation with Pydantic
- HTTPS support with nginx
- Environment-based secrets

## 📈 Monitoring

The platform includes comprehensive monitoring:

- **Prometheus**: Metrics collection
- **Grafana**: Visualization dashboards
- **Health Checks**: Automated health monitoring
- **Logging**: Structured JSON logging

Access Grafana at http://localhost:3000 with default credentials (admin/admin).

## 🧪 Testing

Run the test suite:

```bash
cd esg-scraper
docker-compose exec api python test_esg_service.py
```

Or run with pytest:

```bash
docker-compose exec api pytest test_esg_service.py -v
```

## 🚀 Production Deployment

### Environment Variables

Required for production:

```bash
JWT_SECRET=<strong-random-secret>
STRIPE_SECRET_KEY=<your-stripe-key>
DATABASE_PATH=/data/esg_data.db
ENVIRONMENT=production
```

### SSL Certificates

For production, replace self-signed certificates:

```bash
cp /path/to/cert.pem ssl/
cp /path/to/key.pem ssl/
```

### Database Migration

To migrate to PostgreSQL:

1. Update `DATABASE_URL` in `.env`
2. Run migration scripts (coming soon)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 API Documentation

Full API documentation is available at http://localhost:8000/docs when running locally.

Key endpoints:

- `POST /auth/register` - Register new user
- `POST /analyze` - Analyze URL or text
- `POST /compare` - Compare multiple companies
- `GET /usage` - Check usage statistics
- `POST /export` - Export analysis data
- `GET /health` - Health check

## 🐛 Troubleshooting

### Common Issues

1. **Port conflicts**: Change ports in `docker-compose.yml`
2. **Memory issues**: Increase Docker memory allocation
3. **SSL errors**: Regenerate certificates with `deploy.sh`

### Logs

View logs:
```bash
docker-compose logs -f api
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- FinBERT model by ProsusAI
- Trafilatura for web extraction
- FastAPI framework
- All open-source contributors 