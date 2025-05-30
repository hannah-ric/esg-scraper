"""
ESG Intelligence Platform - Main Application
Optimized and consolidated version combining all features
"""

import os
import logging
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Depends, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from prometheus_client import make_asgi_app
import uvicorn
from pydantic import BaseModel, HttpUrl, EmailStr
import jwt
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
class Config:
    """Application configuration"""
    APP_NAME = "ESG Intelligence Platform"
    VERSION = "3.0.0"
    ENABLE_BERT = os.getenv("ENABLE_BERT", "true").lower() == "true"
    ENABLE_METRICS = os.getenv("ENABLE_METRICS", "true").lower() == "true"
    JWT_SECRET = os.getenv("JWT_SECRET", None)
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./esg_data.db")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.JWT_SECRET:
            raise ValueError("JWT_SECRET environment variable is required")

# Validate configuration on import
Config.validate()

# Security
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token and return user ID"""
    try:
        payload = jwt.decode(credentials.credentials, Config.JWT_SECRET, algorithms=["HS256"])
        return payload.get("user_id")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Request Models
class UnifiedAnalyzeRequest(BaseModel):
    """Unified request model for all analysis types"""
    url: Optional[HttpUrl] = None
    text: Optional[str] = None
    company_name: Optional[str] = None
    use_bert: bool = False
    extract_metrics: bool = True
    frameworks: List[str] = ["CSRD", "GRI", "SASB", "TCFD"]
    quick_mode: bool = True
    industry_sector: Optional[str] = None

class UserRegistration(BaseModel):
    """User registration model"""
    email: EmailStr

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info(f"Starting {Config.APP_NAME} v{Config.VERSION}")
    
    # Initialize components
    try:
        # Initialize database
        from database_schema import init_db
        init_db()
        logger.info("Database initialized")
        
        # Initialize enhanced database if available
        from lean_esg_platform import EnhancedDatabaseManager
        global db_manager
        db_manager = EnhancedDatabaseManager()
        db_manager.init_db()
        logger.info("Enhanced database initialized")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
    
    # Pre-load BERT models if enabled
    if Config.ENABLE_BERT:
        try:
            from bert_service_simple import SimpleBERTService
            service = SimpleBERTService()
            service.load_models()
            logger.info("BERT models pre-loaded")
        except Exception as e:
            logger.warning(f"BERT model loading failed: {e}")
    
    yield
    
    # Cleanup
    logger.info("Shutting down application")

# Create FastAPI app
app = FastAPI(
    title=Config.APP_NAME,
    version=Config.VERSION,
    description="Unified ESG analysis platform with BERT enhancement and metrics extraction",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Initialize components
db_manager = None  # Will be initialized in lifespan

# Import and initialize core components
from lean_esg_platform import (
    LeanESGEngine, 
    EnhancedESGEngine,
    LeanScraper,
    UsageTracker,
    RateLimiter,
    KeywordScorer
)
from metrics_extractor import MetricsExtractor
from esg_frameworks import ESGFrameworkManager
from esg_report_scraper import ESGReportScraper

# Initialize services
engine = EnhancedESGEngine()
scraper = LeanScraper()
usage_tracker = UsageTracker()
rate_limiter = RateLimiter()
metrics_extractor = MetricsExtractor()
framework_manager = ESGFrameworkManager()

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": Config.APP_NAME,
        "version": Config.VERSION,
        "features": {
            "keyword_analysis": True,
            "bert_analysis": Config.ENABLE_BERT,
            "metrics_extraction": Config.ENABLE_METRICS,
            "framework_compliance": True,
            "web_scraping": True
        },
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "metrics": "/metrics",
            "api": {
                "analyze": "/api/analyze",
                "register": "/api/auth/register",
                "scrape": "/api/scrape",
                "extract-metrics": "/api/extract-metrics",
                "frameworks": "/api/frameworks",
                "bert": "/api/bert/*" if Config.ENABLE_BERT else None
            }
        }
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    health_status = {
        "status": "healthy",
        "version": Config.VERSION,
        "services": {
            "database": "unknown",
            "redis": "unknown",
            "bert": "disabled"
        }
    }
    
    # Check database
    try:
        if db_manager:
            # Simple check - in production would do actual query
            health_status["services"]["database"] = "healthy"
    except Exception as e:
        health_status["services"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Redis
    try:
        import redis
        r = redis.from_url(Config.REDIS_URL)
        r.ping()
        health_status["services"]["redis"] = "healthy"
    except Exception as e:
        health_status["services"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check BERT
    if Config.ENABLE_BERT:
        try:
            from bert_service_simple import SimpleBERTService
            service = SimpleBERTService()
            health_status["services"]["bert"] = "enabled" if service else "error"
        except Exception as e:
            health_status["services"]["bert"] = f"error: {str(e)}"
    
    return health_status

# Authentication endpoints
@app.post("/api/auth/register")
async def register(registration: UserRegistration):
    """Register a new user"""
    try:
        # Generate user ID
        user_id = f"user_{datetime.utcnow().timestamp()}"
        
        # Create JWT token
        token = jwt.encode(
            {"user_id": user_id, "email": registration.email},
            Config.JWT_SECRET,
            algorithm="HS256"
        )
        
        # Initialize user credits
        await usage_tracker.track_usage(user_id, "registration", 0)
        
        return {
            "user_id": user_id,
            "token": token,
            "credits": 100  # Free tier credits
        }
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

# Main analysis endpoint
@app.post("/api/analyze")
async def analyze(
    request: UnifiedAnalyzeRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user)
):
    """Unified analysis endpoint combining all platform capabilities"""
    try:
        # Check rate limit
        if not rate_limiter.is_allowed(f"analyze:{user_id}"):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        # Check usage limits
        remaining = await usage_tracker.get_user_limit(user_id)
        if remaining <= 0:
            raise HTTPException(status_code=402, detail="No credits remaining")
        
        # Get content
        content = request.text
        if request.url and not request.text:
            content = await scraper.scrape(str(request.url))
        
        if not content:
            raise HTTPException(status_code=400, detail="No content to analyze")
        
        # Perform analysis
        result = await engine.analyze(
            content=content,
            company_name=request.company_name,
            quick_mode=request.quick_mode,
            frameworks=request.frameworks,
            industry_sector=request.industry_sector,
            extract_metrics=request.extract_metrics
        )
        
        # Add BERT analysis if requested and enabled
        if request.use_bert and Config.ENABLE_BERT:
            from bert_service_simple import BERTEnhancedAnalyzer
            analyzer = BERTEnhancedAnalyzer(engine.keyword_scorer)
            bert_result = analyzer.analyze(content, use_bert=True)
            result["bert_analysis"] = bert_result
        
        # Track usage
        credits_used = 1 if request.quick_mode else 5
        if request.use_bert:
            credits_used += 5
        
        await usage_tracker.track_usage(user_id, "analyze", credits_used)
        
        # Save to database
        if db_manager:
            background_tasks.add_task(
                db_manager.save_analysis,
                user_id,
                str(request.url) if request.url else "text",
                result,
                request.industry_sector
            )
        
        # Add metadata
        result["credits_used"] = credits_used
        result["credits_remaining"] = remaining - credits_used
        result["timestamp"] = datetime.utcnow().isoformat()
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Metrics extraction endpoint
@app.post("/api/extract-metrics")
async def extract_metrics(
    text: str,
    year: Optional[int] = None,
    user_id: str = Depends(get_current_user)
):
    """Extract metrics from text"""
    if not Config.ENABLE_METRICS:
        raise HTTPException(status_code=404, detail="Metrics extraction not enabled")
    
    try:
        metrics = metrics_extractor.extract_metrics(text, year)
        
        return {
            'total_metrics': len(metrics),
            'metrics': [
                {
                    'metric_name': m.metric_name,
                    'value': m.value,
                    'unit': m.unit,
                    'category': m.category.value,
                    'confidence': m.confidence
                }
                for m in metrics[:50]  # Limit response size
            ]
        }
    except Exception as e:
        logger.error(f"Metrics extraction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Frameworks endpoint
@app.get("/api/frameworks")
async def list_frameworks():
    """List all supported ESG frameworks"""
    frameworks = []
    for framework in framework_manager.frameworks:
        frameworks.append({
            'name': framework.name,
            'full_name': framework.full_name,
            'description': framework.description,
            'total_requirements': len(framework.requirements)
        })
    
    return {'frameworks': frameworks}

# Scraping endpoint
@app.post("/api/scrape")
async def scrape_reports(
    company_name: str,
    website: Optional[str] = None,
    years: Optional[List[int]] = None,
    user_id: str = Depends(get_current_user)
):
    """Scrape ESG reports for a company"""
    try:
        # Check rate limit
        if not rate_limiter.is_allowed(f"scrape:{user_id}"):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        async with ESGReportScraper() as report_scraper:
            if years:
                all_results = []
                for year in years:
                    result = await report_scraper.scrape_company_esg_data(company_name, website, year)
                    all_results.append(result)
                
                combined = {
                    'company_name': company_name,
                    'reports': []
                }
                
                for result in all_results:
                    combined['reports'].extend(result['reports'][:3])
                
                return combined
            else:
                return await report_scraper.scrape_company_esg_data(company_name, website)
    
    except Exception as e:
        logger.error(f"Scraping error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Add BERT routes if enabled
if Config.ENABLE_BERT:
    from bert_integration_simple import integrate_bert_routes
    keyword_scorer = KeywordScorer()
    integrate_bert_routes(app, keyword_scorer)

# Usage tracking endpoint
@app.get("/api/usage")
async def get_usage(user_id: str = Depends(get_current_user)):
    """Get user's usage statistics"""
    try:
        remaining = await usage_tracker.get_user_limit(user_id)
        
        return {
            "user_id": user_id,
            "credits_remaining": remaining,
            "subscription_tier": "free"  # Would fetch from database
        }
    except Exception as e:
        logger.error(f"Usage check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("ENV", "production") == "development",
        log_level="info"
    ) 