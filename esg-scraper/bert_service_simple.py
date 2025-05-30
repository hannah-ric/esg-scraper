"""
Simplified BERT Service for ESG Analysis
Focuses on core functionality without unnecessary complexity
"""

import os
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    pipeline
)

logger = logging.getLogger(__name__)

@dataclass
class BERTResult:
    """Simple result container for BERT analysis"""
    esg_category: str  # Environmental, Social, Governance
    confidence: float
    sentiment: str  # Positive, Neutral, Negative
    key_topics: List[str]

class SimpleBERTService:
    """
    Simplified BERT service for ESG analysis
    Uses pre-trained models without complex setup
    """
    
    def __init__(self, use_gpu: bool = False):
        self.device = 0 if use_gpu and torch.cuda.is_available() else -1
        self.models_loaded = False
        self.classifiers = {}
        
    def load_models(self):
        """Load ESG-specific BERT models"""
        if self.models_loaded:
            return
            
        try:
            logger.info("Loading ESG BERT models...")
            
            # Load FinBERT-ESG for ESG classification
            self.classifiers['esg'] = pipeline(
                "text-classification",
                model="yiyanghkust/finbert-esg",
                device=self.device
            )
            
            # Load FinBERT for sentiment analysis
            self.classifiers['sentiment'] = pipeline(
                "sentiment-analysis",
                model="ProsusAI/finbert",
                device=self.device
            )
            
            self.models_loaded = True
            logger.info("Models loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            raise
    
    def analyze_text(self, text: str, max_length: int = 512) -> BERTResult:
        """
        Analyze text for ESG content
        
        Args:
            text: Input text to analyze
            max_length: Maximum text length (BERT limitation)
            
        Returns:
            BERTResult with ESG classification and sentiment
        """
        if not self.models_loaded:
            self.load_models()
        
        # Truncate text if too long
        if len(text) > max_length * 4:  # Rough character to token ratio
            text = text[:max_length * 4]
        
        try:
            # Get ESG classification
            esg_results = self.classifiers['esg'](text)
            
            # Get sentiment
            sentiment_results = self.classifiers['sentiment'](text)
            
            # Process results
            esg_category = self._map_esg_label(esg_results[0]['label'])
            confidence = esg_results[0]['score']
            sentiment = self._map_sentiment(sentiment_results[0]['label'])
            
            # Extract key topics (simplified)
            key_topics = self._extract_topics(text, esg_category)
            
            return BERTResult(
                esg_category=esg_category,
                confidence=confidence,
                sentiment=sentiment,
                key_topics=key_topics
            )
            
        except Exception as e:
            logger.error(f"Error in BERT analysis: {e}")
            # Return a default result on error
            return BERTResult(
                esg_category="Unknown",
                confidence=0.0,
                sentiment="Neutral",
                key_topics=[]
            )
    
    def _map_esg_label(self, label: str) -> str:
        """Map model labels to standard ESG categories"""
        label_lower = label.lower()
        
        if 'environmental' in label_lower or 'e' == label_lower:
            return "Environmental"
        elif 'social' in label_lower or 's' == label_lower:
            return "Social"
        elif 'governance' in label_lower or 'g' == label_lower:
            return "Governance"
        else:
            return "None"
    
    def _map_sentiment(self, label: str) -> str:
        """Map sentiment labels to standard format"""
        label_lower = label.lower()
        
        if 'positive' in label_lower:
            return "Positive"
        elif 'negative' in label_lower:
            return "Negative"
        else:
            return "Neutral"
    
    def _extract_topics(self, text: str, category: str) -> List[str]:
        """Extract key topics based on category (simplified keyword approach)"""
        topics = []
        text_lower = text.lower()
        
        # Environmental topics
        if category == "Environmental":
            env_keywords = {
                'emissions': 'Carbon Emissions',
                'renewable': 'Renewable Energy',
                'climate': 'Climate Change',
                'waste': 'Waste Management',
                'water': 'Water Usage',
                'biodiversity': 'Biodiversity'
            }
            for keyword, topic in env_keywords.items():
                if keyword in text_lower:
                    topics.append(topic)
        
        # Social topics
        elif category == "Social":
            social_keywords = {
                'diversity': 'Diversity & Inclusion',
                'employee': 'Employee Welfare',
                'safety': 'Health & Safety',
                'community': 'Community Impact',
                'human rights': 'Human Rights'
            }
            for keyword, topic in social_keywords.items():
                if keyword in text_lower:
                    topics.append(topic)
        
        # Governance topics
        elif category == "Governance":
            gov_keywords = {
                'board': 'Board Structure',
                'ethics': 'Business Ethics',
                'compliance': 'Regulatory Compliance',
                'transparency': 'Transparency',
                'risk': 'Risk Management'
            }
            for keyword, topic in gov_keywords.items():
                if keyword in text_lower:
                    topics.append(topic)
        
        return topics[:5]  # Limit to top 5 topics

class BERTEnhancedAnalyzer:
    """
    Integrates BERT with existing keyword-based analysis
    Provides a hybrid approach for better accuracy
    """
    
    def __init__(self, keyword_scorer=None):
        self.bert_service = SimpleBERTService()
        self.keyword_scorer = keyword_scorer
        
    def analyze(self, text: str, use_bert: bool = True) -> Dict:
        """
        Perform hybrid analysis combining BERT and keywords
        
        Args:
            text: Text to analyze
            use_bert: Whether to use BERT (can be disabled for speed)
            
        Returns:
            Combined analysis results
        """
        results = {
            'method': 'hybrid' if use_bert else 'keyword_only',
            'scores': {},
            'insights': []
        }
        
        # Get keyword scores if available
        if self.keyword_scorer:
            keyword_scores = self.keyword_scorer.score(text)
            results['keyword_scores'] = keyword_scores
            results['scores'] = keyword_scores.copy()
        
        # Add BERT analysis if requested
        if use_bert:
            try:
                bert_result = self.bert_service.analyze_text(text)
                
                # Add BERT results
                results['bert_analysis'] = {
                    'category': bert_result.esg_category,
                    'confidence': bert_result.confidence,
                    'sentiment': bert_result.sentiment,
                    'topics': bert_result.key_topics
                }
                
                # Enhance scores with BERT insights
                if bert_result.esg_category != "None":
                    category_key = bert_result.esg_category.lower()
                    
                    # Boost the relevant category score based on BERT confidence
                    if category_key in results['scores']:
                        current_score = results['scores'][category_key]
                        bert_boost = bert_result.confidence * 20  # Max 20 point boost
                        results['scores'][category_key] = min(100, current_score + bert_boost)
                    
                    # Add insight about BERT findings
                    results['insights'].append(
                        f"BERT identified strong {bert_result.esg_category} content "
                        f"with {bert_result.confidence:.0%} confidence"
                    )
                    
                    # Add sentiment insight
                    if bert_result.sentiment != "Neutral":
                        results['insights'].append(
                            f"{bert_result.sentiment} sentiment detected in "
                            f"{bert_result.esg_category} disclosures"
                        )
                
            except Exception as e:
                logger.warning(f"BERT analysis failed, using keyword-only: {e}")
                results['method'] = 'keyword_fallback'
                results['bert_error'] = str(e)
        
        # Recalculate overall score
        if results['scores']:
            category_scores = [
                results['scores'].get('environmental', 0),
                results['scores'].get('social', 0),
                results['scores'].get('governance', 0)
            ]
            results['scores']['overall'] = sum(category_scores) / len(category_scores)
        
        return results

# Utility function to download models in advance
def download_models():
    """Pre-download models to avoid delays on first use"""
    logger.info("Pre-downloading BERT models...")
    
    from transformers import AutoModel, AutoTokenizer
    
    models = [
        "yiyanghkust/finbert-esg",
        "ProsusAI/finbert"
    ]
    
    for model_name in models:
        logger.info(f"Downloading {model_name}...")
        try:
            AutoTokenizer.from_pretrained(model_name)
            AutoModel.from_pretrained(model_name)
            logger.info(f"✓ {model_name} downloaded successfully")
        except Exception as e:
            logger.error(f"✗ Error downloading {model_name}: {e}")

if __name__ == "__main__":
    # Test the service
    logging.basicConfig(level=logging.INFO)
    
    # Download models
    download_models()
    
    # Test analysis
    test_text = """
    Our company has reduced carbon emissions by 30% this year through 
    renewable energy initiatives. We've also improved employee diversity 
    with 45% female representation in leadership roles.
    """
    
    service = SimpleBERTService()
    result = service.analyze_text(test_text)
    
    print(f"ESG Category: {result.esg_category}")
    print(f"Confidence: {result.confidence:.2%}")
    print(f"Sentiment: {result.sentiment}")
    print(f"Key Topics: {', '.join(result.key_topics)}") 