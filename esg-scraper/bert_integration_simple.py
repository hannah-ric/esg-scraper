"""
Simple BERT Integration for ESG Platform
Adds BERT capabilities to existing FastAPI application
"""

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
import logging
import os

# Import the simple BERT service
from bert_service_simple import SimpleBERTService, BERTEnhancedAnalyzer

logger = logging.getLogger(__name__)

# Request/Response models
class BERTAnalysisRequest(BaseModel):
    """Request model for BERT analysis"""
    text: str = Field(..., description="Text to analyze")
    use_bert: bool = Field(True, description="Whether to use BERT (vs keyword-only)")
    company_name: Optional[str] = Field(None, description="Company name for context")

class BERTAnalysisResponse(BaseModel):
    """Response model for BERT analysis"""
    method: str
    scores: Dict[str, float]
    insights: List[str]
    bert_analysis: Optional[Dict] = None
    keyword_scores: Optional[Dict] = None
    error: Optional[str] = None

# Global BERT service instance (lazy loaded)
_bert_service = None

def get_bert_service() -> SimpleBERTService:
    """Get or create BERT service instance"""
    global _bert_service
    if _bert_service is None:
        _bert_service = SimpleBERTService()
    return _bert_service

def integrate_bert_routes(app: FastAPI, keyword_scorer=None):
    """
    Add BERT routes to existing FastAPI application
    
    Args:
        app: FastAPI application instance
        keyword_scorer: Optional existing keyword scorer to integrate with
    """
    
    # Create enhanced analyzer
    analyzer = BERTEnhancedAnalyzer(keyword_scorer)
    
    @app.post("/api/bert/analyze", response_model=BERTAnalysisResponse)
    async def bert_analyze(request: BERTAnalysisRequest):
        """
        Analyze text using BERT for ESG classification
        
        This endpoint provides:
        - ESG category classification (Environmental, Social, Governance)
        - Sentiment analysis
        - Key topic extraction
        - Hybrid scoring (combining BERT and keywords)
        """
        try:
            # Check if BERT is enabled
            if not request.use_bert and not os.getenv("FORCE_BERT", "false").lower() == "true":
                # Use keyword-only analysis
                result = analyzer.analyze(request.text, use_bert=False)
            else:
                # Use BERT-enhanced analysis
                result = analyzer.analyze(request.text, use_bert=True)
            
            return BERTAnalysisResponse(**result)
            
        except Exception as e:
            logger.error(f"BERT analysis error: {e}")
            # Return error response
            return BERTAnalysisResponse(
                method="error",
                scores={},
                insights=[],
                error=str(e)
            )
    
    @app.get("/api/bert/status")
    async def bert_status():
        """Check BERT service status"""
        try:
            service = get_bert_service()
            
            # Try to load models if not already loaded
            if not service.models_loaded:
                service.load_models()
            
            return {
                "status": "operational",
                "models_loaded": service.models_loaded,
                "available_models": ["finbert-esg", "finbert-sentiment"],
                "device": "GPU" if service.device == 0 else "CPU"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "models_loaded": False
            }
    
    @app.post("/api/bert/compare")
    async def compare_methods(request: BERTAnalysisRequest):
        """
        Compare keyword-only vs BERT-enhanced analysis
        Useful for evaluating BERT's impact
        """
        try:
            # Run both analyses
            keyword_result = analyzer.analyze(request.text, use_bert=False)
            bert_result = analyzer.analyze(request.text, use_bert=True)
            
            # Calculate differences
            score_differences = {}
            for key in keyword_result['scores']:
                if key in bert_result['scores']:
                    diff = bert_result['scores'][key] - keyword_result['scores'][key]
                    score_differences[key] = round(diff, 1)
            
            return {
                "keyword_analysis": keyword_result,
                "bert_analysis": bert_result,
                "score_differences": score_differences,
                "bert_impact": "positive" if sum(score_differences.values()) > 0 else "negative"
            }
            
        except Exception as e:
            logger.error(f"Comparison error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/bert/batch")
    async def batch_analyze(texts: List[str], use_bert: bool = True):
        """
        Analyze multiple texts in batch
        Useful for processing multiple documents
        """
        results = []
        
        for text in texts[:10]:  # Limit to 10 texts
            try:
                result = analyzer.analyze(text, use_bert=use_bert)
                results.append(result)
            except Exception as e:
                results.append({
                    "error": str(e),
                    "method": "failed",
                    "scores": {},
                    "insights": []
                })
        
        return {"results": results, "total": len(results)}
    
    logger.info("BERT routes integrated successfully")

# Standalone function to test BERT integration
def test_bert_integration():
    """Test BERT functionality standalone"""
    from bert_service_simple import SimpleBERTService
    
    service = SimpleBERTService()
    
    test_texts = [
        "We reduced carbon emissions by 40% through renewable energy.",
        "Employee satisfaction increased with new diversity programs.",
        "Board independence improved with new governance policies."
    ]
    
    print("Testing BERT Service...")
    for text in test_texts:
        result = service.analyze_text(text)
        print(f"\nText: {text[:50]}...")
        print(f"Category: {result.esg_category}")
        print(f"Confidence: {result.confidence:.2%}")
        print(f"Sentiment: {result.sentiment}")

if __name__ == "__main__":
    test_bert_integration() 