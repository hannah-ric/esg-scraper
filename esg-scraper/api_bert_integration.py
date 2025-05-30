"""
API BERT Integration Module
Adds BERT-enhanced endpoints to the existing FastAPI application
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
import asyncio
from datetime import datetime
import logging

# Import BERT integration components
from bert_integration import (
    BERTIntegratedESGEngine,
    create_bert_engine,
    analyze_with_bert
)

# Import existing models and dependencies
from lean_esg_platform import (
    AnalyzeRequest,
    EnhancedAnalysisResponse,
    get_current_user,
    track_api_usage,
    limiter
)

logger = logging.getLogger(__name__)

# Create BERT router
bert_router = APIRouter(prefix="/api/v2/bert", tags=["BERT Enhanced Analysis"])

# Global BERT engine instance
bert_engine = None

def get_bert_engine() -> BERTIntegratedESGEngine:
    """Get or create BERT engine instance"""
    global bert_engine
    if bert_engine is None:
        bert_engine = create_bert_engine(enable_bert=True)
    return bert_engine

# Enhanced request models for BERT
class BERTAnalyzeRequest(AnalyzeRequest):
    """Enhanced analyze request with BERT options"""
    use_bert: bool = Field(True, description="Enable BERT analysis")
    bert_confidence_threshold: float = Field(0.5, description="Minimum confidence for BERT results")
    include_greenwashing_check: bool = Field(True, description="Include greenwashing risk assessment")
    analysis_depth: str = Field("standard", description="Analysis depth: quick, standard, or deep")

class BERTAnalysisResponse(EnhancedAnalysisResponse):
    """Enhanced response with BERT-specific fields"""
    bert_analysis: Optional[Dict[str, Any]] = Field(None, description="BERT analysis results")
    greenwashing_assessment: Optional[Dict[str, Any]] = Field(None, description="Greenwashing risk assessment")
    analysis_metadata: Dict[str, Any] = Field(default_factory=dict, description="Analysis performance metadata")
    confidence: float = Field(0.0, description="Overall analysis confidence")

class AnalysisComparisonRequest(BaseModel):
    """Request for comparing keyword vs BERT analysis"""
    content: str = Field(..., description="Content to analyze")
    company_name: Optional[str] = Field(None, description="Company name")
    frameworks: List[str] = Field(default_factory=lambda: ["CSRD", "TCFD"])
    industry_sector: Optional[str] = Field(None, description="Industry sector")

class PerformanceStatsResponse(BaseModel):
    """Performance statistics response"""
    keyword_stats: Dict[str, Any]
    bert_stats: Dict[str, Any]
    comparison: Dict[str, Any]

# BERT-enhanced endpoints
@bert_router.post("/analyze", response_model=BERTAnalysisResponse)
@limiter.limit("5/minute")
async def bert_analyze(
    request: BERTAnalyzeRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Perform BERT-enhanced ESG analysis
    
    This endpoint provides advanced analysis using BERT models for:
    - More accurate ESG categorization
    - Greenwashing detection
    - Sentiment analysis
    - Topic extraction
    """
    try:
        # Track API usage
        await track_api_usage(
            user_id=current_user["user_id"],
            endpoint="/api/v2/bert/analyze",
            credits_used=5 if request.use_bert else 1
        )
        
        # Get BERT engine
        engine = get_bert_engine()
        
        # Determine analysis mode
        quick_mode = request.analysis_depth == "quick"
        
        # Perform analysis
        result = await engine.analyze(
            content=request.content,
            company_name=request.company_name,
            quick_mode=quick_mode,
            frameworks=request.frameworks,
            industry_sector=request.industry_sector,
            extract_metrics=request.extract_metrics,
            use_bert=request.use_bert
        )
        
        # Convert to response model
        response = BERTAnalysisResponse(
            scores=result['scores'],
            framework_coverage=result.get('framework_coverage', []),
            requirement_findings=result.get('requirement_findings', []),
            extracted_metrics=result.get('extracted_metrics', []),
            gap_analysis=result.get('gap_analysis', []),
            insights=result.get('insights', []),
            bert_analysis=result.get('bert_analysis'),
            greenwashing_assessment=result.get('greenwashing_assessment'),
            analysis_metadata=result.get('analysis_metadata', {}),
            confidence=result.get('confidence', 0.0)
        )
        
        # Log analysis in background
        background_tasks.add_task(
            log_bert_analysis,
            user_id=current_user["user_id"],
            company_name=request.company_name,
            method=result.get('analysis_metadata', {}).get('method', 'unknown'),
            confidence=result.get('confidence', 0.0)
        )
        
        return response
        
    except Exception as e:
        logger.error(f"BERT analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@bert_router.post("/compare", response_model=Dict[str, Any])
@limiter.limit("3/minute")
async def compare_analysis_methods(
    request: AnalysisComparisonRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Compare keyword-based vs BERT-enhanced analysis
    
    Useful for:
    - Understanding the value of BERT enhancement
    - A/B testing analysis methods
    - Demonstrating improvements
    """
    try:
        # Track API usage (charge for both analyses)
        await track_api_usage(
            user_id=current_user["user_id"],
            endpoint="/api/v2/bert/compare",
            credits_used=6
        )
        
        engine = get_bert_engine()
        
        # Run both analyses in parallel
        keyword_task = engine.analyze(
            content=request.content,
            company_name=request.company_name,
            quick_mode=True,
            frameworks=request.frameworks,
            industry_sector=request.industry_sector,
            use_bert=False
        )
        
        bert_task = engine.analyze(
            content=request.content,
            company_name=request.company_name,
            quick_mode=False,
            frameworks=request.frameworks,
            industry_sector=request.industry_sector,
            use_bert=True
        )
        
        keyword_result, bert_result = await asyncio.gather(keyword_task, bert_task)
        
        # Calculate differences
        score_differences = {}
        for category in ['environmental', 'social', 'governance', 'overall']:
            keyword_score = keyword_result['scores'].get(category, 0)
            bert_score = bert_result['scores'].get(category, 0)
            score_differences[category] = {
                'keyword': keyword_score,
                'bert': bert_score,
                'difference': bert_score - keyword_score,
                'improvement_pct': ((bert_score - keyword_score) / keyword_score * 100) if keyword_score > 0 else 0
            }
        
        # Compare insights
        keyword_insights = set(keyword_result.get('insights', []))
        bert_insights = set(bert_result.get('insights', []))
        unique_bert_insights = list(bert_insights - keyword_insights)
        
        return {
            'score_comparison': score_differences,
            'keyword_analysis': {
                'scores': keyword_result['scores'],
                'insights': keyword_result.get('insights', []),
                'metrics_found': len(keyword_result.get('extracted_metrics', [])),
                'time_taken': keyword_result.get('analysis_metadata', {}).get('total_time', 0)
            },
            'bert_analysis': {
                'scores': bert_result['scores'],
                'insights': bert_result.get('insights', []),
                'metrics_found': len(bert_result.get('extracted_metrics', [])),
                'time_taken': bert_result.get('analysis_metadata', {}).get('total_time', 0),
                'confidence': bert_result.get('confidence', 0),
                'key_topics': bert_result.get('bert_analysis', {}).get('key_topics', [])
            },
            'unique_bert_insights': unique_bert_insights,
            'greenwashing_assessment': bert_result.get('greenwashing_assessment'),
            'recommendation': _generate_method_recommendation(score_differences, bert_result.get('confidence', 0))
        }
        
    except Exception as e:
        logger.error(f"Comparison error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")

@bert_router.get("/performance", response_model=PerformanceStatsResponse)
async def get_performance_stats(current_user: dict = Depends(get_current_user)):
    """
    Get performance statistics for analysis methods
    
    Returns timing and accuracy metrics
    """
    try:
        engine = get_bert_engine()
        stats = engine.get_performance_stats()
        
        # Calculate comparison metrics
        comparison = {}
        if 'keyword_time' in stats and 'bert_time' in stats:
            keyword_avg = stats['keyword_time'].get('avg', 0)
            bert_avg = stats['bert_time'].get('avg', 0)
            
            comparison = {
                'speed_ratio': bert_avg / keyword_avg if keyword_avg > 0 else 0,
                'bert_overhead_seconds': bert_avg,
                'total_analyses': stats.get('total_time', {}).get('count', 0)
            }
        
        return PerformanceStatsResponse(
            keyword_stats=stats.get('keyword_time', {}),
            bert_stats=stats.get('bert_time', {}),
            comparison=comparison
        )
        
    except Exception as e:
        logger.error(f"Performance stats error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@bert_router.post("/greenwashing-check", response_model=Dict[str, Any])
@limiter.limit("5/minute")
async def check_greenwashing(
    content: str,
    company_name: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Dedicated greenwashing detection endpoint
    
    Analyzes content specifically for:
    - Vague or unsubstantiated claims
    - Missing evidence
    - Misleading language
    """
    try:
        # Track API usage
        await track_api_usage(
            user_id=current_user["user_id"],
            endpoint="/api/v2/bert/greenwashing-check",
            credits_used=3
        )
        
        engine = get_bert_engine()
        
        # Run BERT analysis focused on greenwashing
        result = await engine.analyze(
            content=content,
            company_name=company_name,
            quick_mode=False,
            use_bert=True
        )
        
        greenwashing = result.get('greenwashing_assessment', {})
        
        # Enhanced greenwashing report
        return {
            'risk_level': greenwashing.get('risk_level', 'unknown'),
            'risk_score': greenwashing.get('risk_score', 0),
            'indicators': greenwashing.get('indicators', {}),
            'recommendation': greenwashing.get('recommendation', ''),
            'specific_concerns': _extract_greenwashing_concerns(result),
            'suggested_improvements': _generate_improvements(greenwashing),
            'confidence': result.get('confidence', 0)
        }
        
    except Exception as e:
        logger.error(f"Greenwashing check error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Check failed: {str(e)}")

# Helper functions
def _generate_method_recommendation(score_differences: Dict, confidence: float) -> str:
    """Generate recommendation on which method to use"""
    
    # Calculate average improvement
    improvements = [diff['improvement_pct'] for diff in score_differences.values()]
    avg_improvement = sum(improvements) / len(improvements) if improvements else 0
    
    if avg_improvement > 10 and confidence > 0.7:
        return "BERT analysis recommended - significant improvement in accuracy and insights"
    elif avg_improvement > 5:
        return "BERT analysis suggested for important documents requiring higher accuracy"
    else:
        return "Keyword analysis sufficient for this content - minimal benefit from BERT"

def _extract_greenwashing_concerns(result: Dict) -> List[str]:
    """Extract specific greenwashing concerns from analysis"""
    
    concerns = []
    greenwashing = result.get('greenwashing_assessment', {})
    
    indicators = greenwashing.get('indicators', {})
    if indicators.get('vague_language', 0) > 0:
        concerns.append("Uses vague sustainability terms without specific metrics")
    if indicators.get('unsubstantiated_claims', 0) > 0:
        concerns.append("Makes claims without supporting evidence or data")
    if indicators.get('future_promises_without_plans', 0) > 0:
        concerns.append("Contains future commitments without concrete action plans")
    
    return concerns

def _generate_improvements(greenwashing: Dict) -> List[str]:
    """Generate specific improvement suggestions"""
    
    improvements = []
    risk_level = greenwashing.get('risk_level', 'low')
    
    if risk_level in ['medium', 'high']:
        improvements.extend([
            "Add specific, quantifiable metrics for all ESG claims",
            "Include timelines and milestones for commitments",
            "Provide evidence of past achievements and progress",
            "Use precise language instead of vague sustainability terms"
        ])
    
    if greenwashing.get('indicators', {}).get('selective_disclosure', 0) > 0:
        improvements.append("Ensure balanced reporting of both positive and negative impacts")
    
    return improvements[:4]  # Limit to top 4

async def log_bert_analysis(user_id: str, company_name: str, method: str, confidence: float):
    """Log BERT analysis for monitoring"""
    
    logger.info(f"BERT Analysis - User: {user_id}, Company: {company_name}, "
                f"Method: {method}, Confidence: {confidence:.2f}")
    
    # Could also log to database or monitoring service
    # await db.bert_analyses.insert_one({
    #     'user_id': user_id,
    #     'company_name': company_name,
    #     'method': method,
    #     'confidence': confidence,
    #     'timestamp': datetime.utcnow()
    # })

# Integration function to add BERT routes to existing app
def integrate_bert_routes(app):
    """
    Integrate BERT routes into existing FastAPI app
    
    Usage:
        from api_bert_integration import integrate_bert_routes
        integrate_bert_routes(app)
    """
    app.include_router(bert_router)
    logger.info("BERT routes integrated successfully") 