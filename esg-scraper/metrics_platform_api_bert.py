"""
ESG Metrics Platform API with BERT Integration
Enhanced version with BERT capabilities
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, Field
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

# Import existing modules
from metrics_extractor import MetricsExtractor, ExtractedMetric, MetricCategory
from esg_report_scraper import ESGReportScraper
from esg_frameworks import ESGFrameworkManager
from metrics_database_schema import MetricsDatabaseManager

# Import BERT integration
from bert_integration_simple import integrate_bert_routes
from bert_service_simple import BERTEnhancedAnalyzer

# Import keyword scorer from lean platform if available
try:
    from lean_esg_platform import KeywordScorer
    keyword_scorer = KeywordScorer()
except ImportError:
    keyword_scorer = None

logger = logging.getLogger(__name__)

app = FastAPI(
    title="ESG Metrics Platform API with BERT",
    description="Extract, standardize, and align ESG metrics with BERT enhancement",
    version="2.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
metrics_extractor = MetricsExtractor()
framework_manager = ESGFrameworkManager()
db_manager = MetricsDatabaseManager()

# Integrate BERT routes
integrate_bert_routes(app, keyword_scorer)

# Enhanced request model with BERT option
class EnhancedAnalyzeRequest(BaseModel):
    """Request model for enhanced analysis with BERT option"""
    url: Optional[HttpUrl] = None
    text: Optional[str] = None
    company_name: Optional[str] = None
    frameworks: List[str] = ["CSRD", "GRI", "SASB", "TCFD"]
    use_bert: bool = Field(False, description="Use BERT for enhanced analysis")
    extract_metrics: bool = True

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "ESG Metrics Platform API with BERT v2.1",
        "endpoints": {
            "/scrape": "Scrape ESG reports for a company",
            "/extract-metrics": "Extract metrics from text",
            "/analyze-enhanced": "Enhanced analysis with BERT option",
            "/api/bert/analyze": "BERT-specific analysis",
            "/api/bert/status": "Check BERT service status",
            "/api/bert/compare": "Compare keyword vs BERT analysis",
            "/frameworks": "List supported frameworks",
            "/health": "Health check"
        }
    }

@app.post("/analyze-enhanced")
async def analyze_enhanced(request: EnhancedAnalyzeRequest):
    """
    Enhanced analysis endpoint that combines metrics extraction with BERT
    """
    try:
        # Get content
        if request.text:
            content = request.text
        elif request.url:
            async with ESGReportScraper() as scraper:
                if str(request.url).endswith('.pdf'):
                    content = await scraper._extract_pdf_content(str(request.url))
                else:
                    content = await scraper._extract_webpage_content(str(request.url))
        else:
            raise HTTPException(status_code=400, detail="Either text or URL must be provided")
        
        result = {
            'company_name': request.company_name,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Extract metrics if requested
        if request.extract_metrics:
            metrics = metrics_extractor.extract_metrics(content)
            result['metrics'] = [
                {
                    'metric_name': m.metric_name,
                    'value': m.value,
                    'unit': m.unit,
                    'category': m.category.value,
                    'confidence': m.confidence
                }
                for m in metrics
            ]
            
            # Framework mapping
            framework_mappings = metrics_extractor.map_to_frameworks(metrics, request.frameworks)
            result['framework_mappings'] = framework_mappings
        
        # Add BERT analysis if requested
        if request.use_bert:
            analyzer = BERTEnhancedAnalyzer(keyword_scorer)
            bert_result = analyzer.analyze(content, use_bert=True)
            result['bert_analysis'] = bert_result
            
            # Combine insights
            insights = []
            if 'insights' in bert_result:
                insights.extend(bert_result['insights'])
            
            # Add metric-based insights
            if request.extract_metrics and metrics:
                insights.append(f"Extracted {len(metrics)} quantitative metrics")
                
                # Category breakdown
                category_counts = {}
                for m in metrics:
                    cat = m.category.value
                    category_counts[cat] = category_counts.get(cat, 0) + 1
                
                for cat, count in category_counts.items():
                    insights.append(f"{count} {cat} metrics identified")
            
            result['insights'] = insights
        
        return result
        
    except Exception as e:
        logger.error(f"Enhanced analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scrape")
async def scrape_reports(company_name: str, website: Optional[str] = None, years: Optional[List[int]] = None):
    """Scrape ESG reports for a company"""
    try:
        async with ESGReportScraper() as scraper:
            if years:
                all_results = []
                for year in years:
                    result = await scraper.scrape_company_esg_data(company_name, website, year)
                    all_results.append(result)
                
                combined = {
                    'company_name': company_name,
                    'reports': []
                }
                
                for result in all_results:
                    combined['reports'].extend(result['reports'][:3])
                
                return combined
            else:
                return await scraper.scrape_company_esg_data(company_name, website)
    
    except Exception as e:
        logger.error(f"Scraping error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/extract-metrics")
async def extract_metrics(text: str, year: Optional[int] = None):
    """Extract metrics from text"""
    try:
        metrics = metrics_extractor.extract_metrics(text, year)
        
        return {
            'total_metrics': len(metrics),
            'metrics': [
                {
                    'metric_name': m.metric_name,
                    'value': m.value,
                    'unit': m.unit,
                    'normalized_value': m.normalized_value,
                    'normalized_unit': m.normalized_unit,
                    'category': m.category.value,
                    'confidence': m.confidence,
                    'year': m.year,
                    'scope': m.scope
                }
                for m in metrics
            ]
        }
    
    except Exception as e:
        logger.error(f"Extraction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/frameworks")
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

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    
    # Check BERT status
    bert_status = "unknown"
    try:
        from bert_service_simple import SimpleBERTService
        service = SimpleBERTService()
        if service:
            bert_status = "available"
    except:
        bert_status = "unavailable"
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.1.0",
        "database": "connected",
        "bert_status": bert_status
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 