"""
BERT Integration Module for ESG Platform
Seamlessly integrates BERT models with existing keyword-based system
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from functools import wraps
import time

# Import existing platform components
from lean_esg_platform import (
    EnhancedESGEngine,
    KeywordScorer,
    EnhancedKeywordScorer,
    AnalyzeRequest,
    EnhancedAnalysisResponse,
    ESGScoreResponse,
    FrameworkCoverage,
    ExtractedMetric,
    GapAnalysisItem,
    RequirementFinding
)

# Import BERT components
from bert_enhanced_engine import (
    BERTEnhancedScorer,
    HybridESGAnalyzer,
    BERTAnalysisResult,
    ESGClassification
)

logger = logging.getLogger(__name__)

class BERTIntegratedESGEngine(EnhancedESGEngine):
    """
    Enhanced ESG Engine with BERT integration
    Extends the existing engine with BERT capabilities
    """
    
    def __init__(self, enable_bert: bool = True, bert_cache_dir: str = "./bert_cache"):
        super().__init__()
        self.enable_bert = enable_bert
        self.bert_cache_dir = bert_cache_dir
        
        if self.enable_bert:
            self._initialize_bert()
        
        # Initialize hybrid analyzer
        self.hybrid_analyzer = HybridESGAnalyzer(
            keyword_scorer=self.enhanced_keyword_scorer,
            bert_scorer=self.bert_scorer if self.enable_bert else None
        )
        
        # Performance tracking
        self.performance_metrics = {
            'keyword_time': [],
            'bert_time': [],
            'total_time': []
        }
    
    def _initialize_bert(self):
        """Initialize BERT models with proper error handling"""
        try:
            logger.info("Initializing BERT models...")
            
            # Create cache directory
            os.makedirs(self.bert_cache_dir, exist_ok=True)
            
            # Set transformers cache
            os.environ['TRANSFORMERS_CACHE'] = self.bert_cache_dir
            
            # Initialize BERT scorer
            self.bert_scorer = BERTEnhancedScorer(use_gpu=torch.cuda.is_available())
            
            logger.info("BERT models initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize BERT models: {str(e)}")
            logger.warning("Falling back to keyword-only mode")
            self.enable_bert = False
            self.bert_scorer = None
    
    async def analyze(self, content: str, company_name: str = None, 
                     quick_mode: bool = True, frameworks: List[str] = None,
                     industry_sector: str = None, extract_metrics: bool = True,
                     use_bert: bool = None) -> Dict[str, Any]:
        """
        Enhanced analysis with optional BERT integration
        
        Args:
            content: Text content to analyze
            company_name: Company name for context
            quick_mode: If True, use keyword-only analysis
            frameworks: List of frameworks to check
            industry_sector: Industry for sector-specific analysis
            extract_metrics: Whether to extract quantitative metrics
            use_bert: Override default BERT usage (None = use quick_mode setting)
        """
        
        start_time = time.time()
        
        # Determine analysis mode
        if use_bert is None:
            use_bert = not quick_mode and self.enable_bert
        
        # Get base keyword analysis
        keyword_start = time.time()
        base_result = await super().analyze(
            content, company_name, True,  # Always quick for base
            frameworks, industry_sector, extract_metrics
        )
        keyword_time = time.time() - keyword_start
        
        # Enhance with BERT if requested
        if use_bert and self.enable_bert:
            bert_start = time.time()
            bert_enhancements = await self._apply_bert_enhancements(
                content, base_result, frameworks, industry_sector
            )
            bert_time = time.time() - bert_start
            
            # Merge results
            enhanced_result = self._merge_results(base_result, bert_enhancements)
            
            # Add performance metrics
            enhanced_result['analysis_metadata'] = {
                'method': 'hybrid',
                'keyword_time': round(keyword_time, 3),
                'bert_time': round(bert_time, 3),
                'total_time': round(time.time() - start_time, 3),
                'bert_confidence': bert_enhancements.get('confidence', 0)
            }
            
            # Track performance
            self._track_performance(keyword_time, bert_time, time.time() - start_time)
            
            return enhanced_result
        else:
            # Keyword-only analysis
            base_result['analysis_metadata'] = {
                'method': 'keyword_only',
                'total_time': round(time.time() - start_time, 3)
            }
            return base_result
    
    async def _apply_bert_enhancements(self, content: str, base_result: Dict[str, Any],
                                     frameworks: List[str], industry_sector: str) -> Dict[str, Any]:
        """Apply BERT enhancements to base analysis"""
        
        # Run BERT analysis
        bert_result = await self.bert_scorer.analyze(content)
        
        # Enhanced categorization
        enhanced_categories = self._enhance_categories_with_bert(
            base_result.get('requirement_findings', []),
            bert_result
        )
        
        # Enhanced metric extraction
        enhanced_metrics = self._enhance_metrics_with_bert(
            base_result.get('extracted_metrics', []),
            bert_result,
            content
        )
        
        # Enhanced scoring
        enhanced_scores = self._calculate_bert_enhanced_scores(
            base_result['scores'],
            bert_result
        )
        
        # Greenwashing risk assessment
        greenwashing_risk = self._assess_greenwashing_risk(bert_result, content)
        
        # Generate BERT-based insights
        bert_insights = self._generate_bert_insights(bert_result, frameworks, industry_sector)
        
        return {
            'scores': enhanced_scores,
            'bert_analysis': {
                'classifications': [self._classification_to_dict(c) for c in bert_result.classifications],
                'key_topics': bert_result.key_topics,
                'overall_sentiment': bert_result.overall_sentiment,
                'confidence': bert_result.confidence_score
            },
            'enhanced_categories': enhanced_categories,
            'enhanced_metrics': enhanced_metrics,
            'greenwashing_risk': greenwashing_risk,
            'bert_insights': bert_insights,
            'confidence': bert_result.confidence_score
        }
    
    def _classification_to_dict(self, classification: ESGClassification) -> Dict[str, Any]:
        """Convert ESGClassification to dictionary"""
        return {
            'category': classification.category,
            'subcategory': classification.subcategory,
            'confidence': classification.confidence,
            'sentiment': classification.sentiment,
            'evidence': classification.evidence[:200] if classification.evidence else None
        }
    
    def _enhance_categories_with_bert(self, requirement_findings: List[Dict],
                                    bert_result: BERTAnalysisResult) -> List[Dict]:
        """Enhance requirement findings with BERT classifications"""
        
        enhanced_findings = []
        
        # Map BERT categories to framework requirements
        category_mapping = {
            'Climate Change': ['CSRD-E1-1', 'CSRD-E1-2', 'TCFD-MT-2'],
            'Natural Capital': ['CSRD-E4-1', 'GRI-303-3'],
            'Pollution & Waste': ['CSRD-E2-1', 'CSRD-E5-1'],
            'Human Capital': ['CSRD-S1-1', 'CSRD-S1-2', 'GRI-401-1'],
            'Product Liability': ['CSRD-S4-1', 'SASB-SC-2'],
            'Community Relations': ['CSRD-S3-1', 'GRI-413-1'],
            'Corporate Governance': ['CSRD-G1-1', 'TCFD-GOV-1'],
            'Business Ethics & Values': ['CSRD-G1-1', 'SASB-LG-1']
        }
        
        # Enhance existing findings with BERT confidence
        for finding in requirement_findings:
            enhanced_finding = finding.copy()
            
            # Find relevant BERT categories
            relevant_categories = []
            for bert_cat in bert_result.detailed_categories:
                if bert_cat['category'] in category_mapping:
                    if finding['requirement_id'] in category_mapping[bert_cat['category']]:
                        relevant_categories.append(bert_cat)
            
            if relevant_categories:
                # Boost confidence based on BERT
                bert_confidence = max(cat['confidence'] for cat in relevant_categories)
                enhanced_finding['confidence'] = min(0.95, 
                    finding['confidence'] * 0.6 + bert_confidence * 0.4)
                enhanced_finding['bert_validated'] = True
                enhanced_finding['bert_categories'] = [cat['category'] for cat in relevant_categories]
            
            enhanced_findings.append(enhanced_finding)
        
        return enhanced_findings
    
    def _enhance_metrics_with_bert(self, base_metrics: List[Dict],
                                 bert_result: BERTAnalysisResult,
                                 content: str) -> List[Dict]:
        """Enhance metric extraction using BERT context understanding"""
        
        enhanced_metrics = base_metrics.copy()
        
        # Use BERT to validate metric context
        for metric in enhanced_metrics:
            # Find evidence in BERT classifications
            relevant_evidence = []
            for classification in bert_result.classifications:
                if classification.evidence and metric.get('metric_name', '').lower() in classification.evidence.lower():
                    relevant_evidence.append(classification)
            
            if relevant_evidence:
                # Boost confidence if BERT found relevant context
                avg_bert_confidence = sum(e.confidence for e in relevant_evidence) / len(relevant_evidence)
                metric['confidence'] = min(0.95, metric.get('confidence', 0.5) * 0.7 + avg_bert_confidence * 0.3)
                metric['bert_validated'] = True
        
        return enhanced_metrics
    
    def _calculate_bert_enhanced_scores(self, keyword_scores: Dict[str, float],
                                      bert_result: BERTAnalysisResult) -> Dict[str, float]:
        """Calculate enhanced ESG scores combining keyword and BERT analysis"""
        
        # Convert BERT sentiment to scores
        bert_scores = {}
        for category, sentiment in bert_result.overall_sentiment.items():
            bert_scores[category.lower()] = sentiment * 100
        
        # Dynamic weighting based on BERT confidence
        bert_weight = min(0.7, 0.4 + bert_result.confidence_score * 0.3)
        keyword_weight = 1 - bert_weight
        
        # Combine scores
        combined_scores = {}
        for category in ['environmental', 'social', 'governance']:
            keyword_score = keyword_scores.get(category, 50)
            bert_score = bert_scores.get(category, keyword_score)  # Default to keyword if no BERT
            
            combined_scores[category] = (
                keyword_score * keyword_weight + 
                bert_score * bert_weight
            )
        
        # Calculate overall
        combined_scores['overall'] = sum(combined_scores.values()) / 3
        
        # Round scores
        return {k: round(v, 1) for k, v in combined_scores.items()}
    
    def _assess_greenwashing_risk(self, bert_result: BERTAnalysisResult, content: str) -> Dict[str, Any]:
        """Assess greenwashing risk based on BERT analysis"""
        
        risk_indicators = {
            'vague_language': 0,
            'unsubstantiated_claims': 0,
            'future_promises_without_plans': 0,
            'selective_disclosure': 0
        }
        
        # Check for vague language
        vague_terms = ['sustainable', 'green', 'eco-friendly', 'responsible']
        content_lower = content.lower()
        for term in vague_terms:
            if term in content_lower and not any(
                metric['confidence'] > 0.7 
                for metric in bert_result.detailed_categories
            ):
                risk_indicators['vague_language'] += 1
        
        # Check sentiment vs substance
        positive_sentiment = sum(
            1 for c in bert_result.classifications 
            if c.sentiment == 'Positive'
        )
        substantive_categories = sum(
            1 for c in bert_result.detailed_categories 
            if c['confidence'] > 0.7 and c['category'] != 'Non-ESG'
        )
        
        if positive_sentiment > substantive_categories * 2:
            risk_indicators['unsubstantiated_claims'] += 1
        
        # Calculate overall risk
        total_indicators = sum(risk_indicators.values())
        risk_level = 'low'
        if total_indicators >= 3:
            risk_level = 'high'
        elif total_indicators >= 2:
            risk_level = 'medium'
        
        return {
            'risk_level': risk_level,
            'risk_score': min(1.0, total_indicators / 4),
            'indicators': risk_indicators,
            'recommendation': self._get_greenwashing_recommendation(risk_level)
        }
    
    def _get_greenwashing_recommendation(self, risk_level: str) -> str:
        """Get recommendation based on greenwashing risk level"""
        recommendations = {
            'low': "ESG claims appear substantiated with concrete evidence.",
            'medium': "Some ESG claims lack specific metrics or timelines. Consider adding more concrete data.",
            'high': "Multiple ESG claims appear vague or unsubstantiated. Recommend adding specific metrics, timelines, and evidence."
        }
        return recommendations.get(risk_level, "")
    
    def _generate_bert_insights(self, bert_result: BERTAnalysisResult,
                              frameworks: List[str], industry_sector: str) -> List[str]:
        """Generate insights based on BERT analysis"""
        
        insights = []
        
        # Topic-based insights
        if bert_result.key_topics:
            insights.append(f"Key ESG focus areas identified: {', '.join(bert_result.key_topics[:3])}")
        
        # Sentiment insights
        for category, sentiment in bert_result.overall_sentiment.items():
            if sentiment > 0.7:
                insights.append(f"Strong positive {category.lower()} performance indicated")
            elif sentiment < 0.3:
                insights.append(f"{category} area shows potential concerns or negative indicators")
        
        # Industry-specific insights
        if industry_sector:
            industry_expectations = {
                'Technology': ['Data Security', 'Human Capital'],
                'Energy': ['Climate Change', 'Natural Capital'],
                'Finance': ['Corporate Governance', 'Business Ethics']
            }
            
            expected_topics = industry_expectations.get(industry_sector, [])
            missing_topics = set(expected_topics) - set(bert_result.key_topics)
            
            if missing_topics:
                insights.append(f"Consider addressing {', '.join(missing_topics)} - important for {industry_sector} sector")
        
        return insights[:5]  # Limit insights
    
    def _merge_results(self, base_result: Dict[str, Any], bert_enhancements: Dict[str, Any]) -> Dict[str, Any]:
        """Merge base and BERT-enhanced results"""
        
        merged = base_result.copy()
        
        # Update scores
        merged['scores'] = bert_enhancements['scores']
        
        # Add BERT analysis
        merged['bert_analysis'] = bert_enhancements['bert_analysis']
        
        # Enhance insights
        if 'insights' not in merged:
            merged['insights'] = []
        merged['insights'].extend(bert_enhancements['bert_insights'])
        
        # Add greenwashing assessment
        merged['greenwashing_assessment'] = bert_enhancements['greenwashing_risk']
        
        # Update confidence
        merged['confidence'] = (
            merged.get('confidence', 0.7) * 0.4 + 
            bert_enhancements['confidence'] * 0.6
        )
        
        return merged
    
    def _track_performance(self, keyword_time: float, bert_time: float, total_time: float):
        """Track performance metrics for optimization"""
        
        self.performance_metrics['keyword_time'].append(keyword_time)
        self.performance_metrics['bert_time'].append(bert_time)
        self.performance_metrics['total_time'].append(total_time)
        
        # Keep only last 100 measurements
        for key in self.performance_metrics:
            if len(self.performance_metrics[key]) > 100:
                self.performance_metrics[key] = self.performance_metrics[key][-100:]
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        
        stats = {}
        for key, values in self.performance_metrics.items():
            if values:
                stats[key] = {
                    'avg': sum(values) / len(values),
                    'min': min(values),
                    'max': max(values),
                    'count': len(values)
                }
        
        return stats


# Utility functions for integration
def create_bert_engine(enable_bert: bool = True, **kwargs) -> BERTIntegratedESGEngine:
    """Factory function to create BERT-integrated engine"""
    return BERTIntegratedESGEngine(enable_bert=enable_bert, **kwargs)


async def analyze_with_bert(text: str, company_name: str = None,
                          frameworks: List[str] = None,
                          industry_sector: str = None,
                          use_bert: bool = True) -> Dict[str, Any]:
    """Convenience function for BERT-enhanced analysis"""
    
    engine = create_bert_engine(enable_bert=use_bert)
    
    result = await engine.analyze(
        content=text,
        company_name=company_name,
        quick_mode=not use_bert,
        frameworks=frameworks or ["CSRD", "TCFD"],
        industry_sector=industry_sector,
        extract_metrics=True,
        use_bert=use_bert
    )
    
    return result


# Import guard for torch
try:
    import torch
except ImportError:
    logger.warning("PyTorch not installed. BERT features will be disabled.")
    torch = None 