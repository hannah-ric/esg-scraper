# ESG Intelligence Platform

A comprehensive, production-ready platform for ESG (Environmental, Social, Governance) analysis with BERT enhancement, metrics extraction, and framework compliance checking.

## Features

- **ESG Analysis**: Keyword-based and BERT-enhanced analysis of ESG content
- **Web Scraping**: Automated extraction of ESG reports from company websites
- **Metrics Extraction**: Automatic extraction of quantitative ESG metrics
- **Framework Compliance**: Check compliance with CSRD, GRI, SASB, and TCFD frameworks
- **BERT Integration**: Optional state-of-the-art NLP for enhanced accuracy
- **API-First Design**: RESTful API with comprehensive documentation
- **Authentication**: JWT-based authentication with usage tracking
- **Rate Limiting**: Built-in rate limiting for API protection
- **Monitoring**: Prometheus metrics and health checks

## Quick Start

### Prerequisites

- Python 3.8+
- Redis (optional, for caching)
- 2GB+ RAM (4GB+ recommended for BERT)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd esg-scraper
```

2. Set environment variables:
```bash
export JWT_SECRET=your-secret-key-here-change-in-production
export UPSTASH_REDIS_URL=redis://localhost:6379  # Optional
```

3. Run the application:
```bash
chmod +x start.sh
./start.sh
```

The API will be available at `http://localhost:8000`

### Docker Deployment

```bash
docker-compose up -d
```

## API Usage

### Authentication

First, register to get an API token:

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'
```

### Analyze ESG Content

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/sustainability-report",
    "company_name": "Example Corp",
    "use_bert": true,
    "frameworks": ["CSRD", "TCFD"]
  }'
```

### Extract Metrics

```bash
curl -X POST http://localhost:8000/api/extract-metrics \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "We reduced Scope 1 emissions by 30% to 50,000 tCO2e in 2023."
  }'
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `JWT_SECRET` | Secret key for JWT tokens | **Required** |
| `PORT` | Application port | 8000 |
| `ENABLE_BERT` | Enable BERT analysis | true |
| `ENABLE_METRICS` | Enable metrics extraction | true |
| `UPSTASH_REDIS_URL` | Redis connection URL | redis://localhost:6379 |
| `DATABASE_URL` | Database connection URL | sqlite:///./esg_data.db |
| `ENV` | Environment (development/production) | production |

### Feature Flags

- **BERT Analysis**: Set `ENABLE_BERT=false` to disable BERT and use keyword-only analysis
- **Metrics Extraction**: Set `ENABLE_METRICS=false` to disable metrics extraction

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   FastAPI App   │────▶│  Core Services  │────▶│    Database     │
│   (main.py)     │     │                 │     │   (SQLite)      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                        │
         ▼                       ▼                        ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ BERT Service    │     │ Metrics Extract │     │     Redis       │
│  (Optional)     │     │    Service      │     │   (Optional)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Core Components

1. **main.py**: Unified application entry point
2. **lean_esg_platform.py**: Core ESG analysis engine
3. **bert_service_simple.py**: BERT integration for enhanced analysis
4. **metrics_extractor.py**: Quantitative metrics extraction
5. **esg_frameworks.py**: Framework compliance checking
6. **esg_report_scraper.py**: Web scraping functionality

## Performance Optimization

- **Caching**: Redis caching for repeated analyses
- **Lazy Loading**: BERT models loaded only when needed
- **Rate Limiting**: Prevents API abuse
- **Database Indexing**: Optimized queries for fast retrieval
- **Async Operations**: Non-blocking I/O for better concurrency

## Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

### Prometheus Metrics
```bash
curl http://localhost:8000/metrics
```

## Development

### Running Tests
```bash
pytest tests/
```

### Code Quality
```bash
# Format code
black .

# Lint
flake8 .

# Type checking
mypy .
```

## Deployment

### DigitalOcean Kubernetes

See `DIGITALOCEAN_DEPLOYMENT_GUIDE.md` for detailed instructions.

### Production Checklist

- [ ] Set strong `JWT_SECRET`
- [ ] Configure Redis for caching
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Configure rate limiting
- [ ] Enable HTTPS
- [ ] Set up backup strategy
- [ ] Configure log aggregation

## API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Credits and Usage Limits

- **Free Tier**: 100 credits
- **Quick Analysis**: 1 credit
- **Full Analysis**: 5 credits
- **BERT Analysis**: +5 credits
- **Web Scraping**: 2 credits

## Troubleshooting

### Common Issues

1. **JWT_SECRET not set**
   ```bash
   export JWT_SECRET=your-secret-key-here
   ```

2. **Redis connection failed**
   - Application works without Redis but with limited caching
   - To install Redis: `sudo apt-get install redis-server`

3. **BERT models not loading**
   - Ensure 2GB+ free RAM
   - Models download automatically on first use
   - Pre-download: `./start.sh --download-models`

4. **Port already in use**
   ```bash
   export PORT=8001  # Use different port
   ```

## License

[Your License Here]

## Support

For issues and questions:
- GitHub Issues: [repository-url]/issues
- Documentation: See `/docs` endpoint 