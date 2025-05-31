# Production Monitoring Setup

## 🔍 Overview

Complete monitoring stack for ESG Scraper platform including:
- Application Performance Monitoring (APM)
- Error Tracking
- Infrastructure Monitoring
- Business Metrics
- Alerting

## 1. Sentry Error Tracking

### Installation
```bash
pip install sentry-sdk[fastapi]
```

### Configuration
```python
# Add to lean_esg_platform.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

# Initialize Sentry
sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    environment=os.getenv("ENVIRONMENT", "production"),
    integrations=[
        FastApiIntegration(transaction_style="endpoint"),
        RedisIntegration(),
        LoggingIntegration(level=logging.INFO),
    ],
    traces_sample_rate=0.1,  # 10% of transactions
    profiles_sample_rate=0.1,  # 10% profiling
    attach_stacktrace=True,
    send_default_pii=False,  # GDPR compliance
)

# Add to app startup
@app.on_event("startup")
async def startup_event():
    sentry_sdk.set_tag("app.version", "1.0.0")
    sentry_sdk.set_context("app", {
        "name": "ESG Scraper",
        "instance": os.getenv("HOSTNAME", "unknown")
    })
```

### Custom Error Context
```python
# In analyze endpoint
with sentry_sdk.push_scope() as scope:
    scope.set_tag("analysis.type", request.quick_mode and "quick" or "full")
    scope.set_context("analysis", {
        "company": request.company_name,
        "frameworks": request.frameworks,
        "user_id": user_id
    })
    # ... perform analysis
```

## 2. Prometheus Metrics Enhancement

### Additional Metrics
```python
# Business metrics
analysis_by_framework = Counter(
    "esg_analysis_by_framework_total",
    "Analyses by framework",
    ["framework", "user_tier"]
)

metrics_extracted = Histogram(
    "esg_metrics_extracted_count",
    "Number of metrics extracted per analysis",
    buckets=[0, 5, 10, 20, 50, 100, 200]
)

cache_operations = Counter(
    "esg_cache_operations_total",
    "Cache operations",
    ["operation", "status"]  # get/set, hit/miss
)

subscription_revenue = Gauge(
    "esg_subscription_revenue_usd",
    "Monthly recurring revenue",
    ["tier"]
)

# Track in endpoints
analysis_by_framework.labels(
    framework="CSRD",
    user_tier=user.get("tier", "free")
).inc()

# Cache tracking
if cached:
    cache_operations.labels(operation="get", status="hit").inc()
else:
    cache_operations.labels(operation="get", status="miss").inc()
```

### Grafana Dashboard JSON
```json
{
  "dashboard": {
    "title": "ESG Scraper Monitoring",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [{
          "expr": "rate(esg_api_requests_total[5m])"
        }]
      },
      {
        "title": "Error Rate",
        "targets": [{
          "expr": "rate(esg_api_requests_total{status=~'5..'}[5m])"
        }]
      },
      {
        "title": "P95 Latency",
        "targets": [{
          "expr": "histogram_quantile(0.95, rate(esg_api_request_duration_seconds_bucket[5m]))"
        }]
      },
      {
        "title": "Cache Hit Rate",
        "targets": [{
          "expr": "rate(esg_cache_operations_total{status='hit'}[5m]) / rate(esg_cache_operations_total{operation='get'}[5m])"
        }]
      }
    ]
  }
}
```

## 3. DigitalOcean Monitoring

### App Platform Metrics
```yaml
# Add to app.yaml
alerts:
  - rule: CPU_UTILIZATION_HIGH
    threshold: 80
    window: 5m
    
  - rule: MEMORY_UTILIZATION_HIGH
    threshold: 90
    window: 5m
    
  - rule: RESTART_COUNT_HIGH
    threshold: 3
    window: 10m
```

### Custom Health Checks
```python
@app.get("/health/detailed")
async def detailed_health():
    """Detailed health check for monitoring"""
    checks = {
        "mongodb": "unknown",
        "redis": "unknown",
        "memory": "unknown",
        "disk": "unknown"
    }
    
    # MongoDB check
    try:
        mongo_health = await db_manager.health_check()
        checks["mongodb"] = mongo_health["status"]
    except:
        checks["mongodb"] = "unhealthy"
    
    # Redis check
    try:
        redis_client.ping()
        checks["redis"] = "healthy"
    except:
        checks["redis"] = "unhealthy"
    
    # Memory check
    import psutil
    memory = psutil.virtual_memory()
    checks["memory"] = "healthy" if memory.percent < 80 else "warning"
    
    # Overall status
    overall = "healthy"
    if any(v == "unhealthy" for v in checks.values()):
        overall = "unhealthy"
    elif any(v == "warning" for v in checks.values()):
        overall = "degraded"
    
    return {
        "status": overall,
        "checks": checks,
        "metrics": {
            "memory_percent": memory.percent,
            "memory_available_mb": memory.available / 1024 / 1024
        }
    }
```

## 4. Log Aggregation

### Structured Logging
```python
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Usage
logger.info(
    "analysis_completed",
    user_id=user_id,
    company=company_name,
    duration_ms=duration * 1000,
    frameworks=frameworks,
    metrics_count=len(metrics)
)
```

### Log Shipping
```yaml
# Add to deployment
- name: LOG_FORMAT
  value: json
  
- name: LOG_LEVEL
  value: INFO

# Ship to external service
- name: LOGDNA_KEY
  value: ${LOGDNA_KEY}
  type: SECRET
```

## 5. Business Metrics Dashboard

### Key Metrics SQL
```sql
-- Daily Active Users
SELECT DATE(created_at) as date, 
       COUNT(DISTINCT user_id) as dau
FROM user_activity
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at);

-- Revenue by Tier
SELECT tier,
       COUNT(*) as customers,
       SUM(CASE 
         WHEN tier = 'starter' THEN 49
         WHEN tier = 'growth' THEN 199
         WHEN tier = 'enterprise' THEN 999
         ELSE 0
       END) as mrr
FROM users
WHERE tier != 'free'
GROUP BY tier;

-- Framework Usage
SELECT framework,
       COUNT(*) as usage_count,
       AVG(coverage_percentage) as avg_coverage
FROM framework_compliance
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY framework;
```

## 6. Alerting Rules

### PagerDuty Integration
```python
# alerts.py
import httpx

class AlertManager:
    def __init__(self):
        self.pagerduty_key = os.getenv("PAGERDUTY_KEY")
        self.slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
    
    async def send_alert(self, severity: str, title: str, details: dict):
        # PagerDuty for critical
        if severity == "critical":
            await self._pagerduty_alert(title, details)
        
        # Slack for all alerts
        await self._slack_alert(severity, title, details)
    
    async def _pagerduty_alert(self, title: str, details: dict):
        async with httpx.AsyncClient() as client:
            await client.post(
                "https://events.pagerduty.com/v2/enqueue",
                json={
                    "routing_key": self.pagerduty_key,
                    "event_action": "trigger",
                    "payload": {
                        "summary": title,
                        "severity": "error",
                        "source": "esg-scraper",
                        "custom_details": details
                    }
                }
            )
```

### Alert Conditions
```python
# Check critical conditions
async def check_alerts():
    alerts = []
    
    # Database connection pool exhaustion
    if db_manager.client.nodes[0].pool.size >= 45:  # 90% of max
        alerts.append({
            "severity": "warning",
            "title": "MongoDB connection pool high",
            "details": {"connections": db_manager.client.nodes[0].pool.size}
        })
    
    # High error rate
    error_rate = await calculate_error_rate()
    if error_rate > 0.05:  # 5%
        alerts.append({
            "severity": "critical",
            "title": "High error rate detected",
            "details": {"error_rate": error_rate}
        })
    
    # Memory usage
    import psutil
    if psutil.virtual_memory().percent > 85:
        alerts.append({
            "severity": "warning",
            "title": "High memory usage",
            "details": {"memory_percent": psutil.virtual_memory().percent}
        })
    
    # Send alerts
    alert_manager = AlertManager()
    for alert in alerts:
        await alert_manager.send_alert(**alert)
```

## 7. Performance Monitoring

### APM with DataDog
```python
from ddtrace import patch_all, tracer

# Patch all supported libraries
patch_all()

# Custom spans
@tracer.wrap("esg.analysis.framework")
async def analyze_frameworks(content: str, frameworks: List[str]):
    span = tracer.current_span()
    span.set_tag("frameworks.count", len(frameworks))
    span.set_tag("content.length", len(content))
    # ... perform analysis
```

## 8. Uptime Monitoring

### External Monitoring
- **UptimeRobot**: Monitor `/health` endpoint
- **Pingdom**: Full transaction monitoring
- **StatusPage**: Public status page

### Configuration
```yaml
monitors:
  - name: "API Health"
    url: "https://api.blueprintbuddy.io/health"
    interval: 60
    locations: ["us-east", "eu-west"]
    
  - name: "Analysis Endpoint"
    url: "https://api.blueprintbuddy.io/analyze"
    method: POST
    headers:
      Authorization: "Bearer ${MONITOR_TOKEN}"
    body:
      text: "Test ESG analysis"
      quick_mode: true
    interval: 300
    timeout: 30
```

## 9. Cost Monitoring

### DigitalOcean Billing Alerts
```bash
# Set up billing alerts
doctl billing-history alerts create \
  --amount 100 \
  --email alerts@company.com
```

### Resource Usage Tracking
```python
@app.on_event("startup")
async def track_costs():
    """Track resource usage for cost allocation"""
    while True:
        await asyncio.sleep(3600)  # Hourly
        
        # Track by user tier
        usage_by_tier = await db_manager.get_usage_by_tier()
        
        for tier, usage in usage_by_tier.items():
            cost_metrics.labels(tier=tier).set(usage["cost_estimate"])
```

## 10. Dashboard Links

### Production Dashboards
- **Grafana**: `https://monitoring.blueprintbuddy.io/grafana`
- **Sentry**: `https://sentry.io/organizations/esg-scraper`
- **DataDog**: `https://app.datadoghq.com/dashboard/esg-scraper`
- **StatusPage**: `https://status.blueprintbuddy.io`

### Alert Channels
- **Critical**: PagerDuty → On-call engineer
- **Warning**: Slack #alerts channel
- **Info**: Slack #monitoring channel

## 🎯 Implementation Priority

1. **Week 1**: Sentry + Basic Prometheus
2. **Week 2**: Grafana Dashboards + Alerts
3. **Week 3**: APM + Business Metrics
4. **Month 2**: Full observability stack 