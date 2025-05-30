"""
Comprehensive Test Suite for BERT Integration
Tests all aspects of the BERT-enhanced ESG analysis platform
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch
import json
from typing import Dict, List, Any

# Import components to test
from bert_integration import (
    BERTIntegratedESGEngine,
    create_bert_engine,
    analyze_with_bert
)
from bert_enhanced_engine import (
    SmartDocumentChunker,
    BERTEnhancedScorer,
    HybridESGAnalyzer,
    BERTAnalysisResult,
    ESGClassification
)

# Test data
SAMPLE_ESG_TEXTS = {
    "environmental_positive": """
        Our company has achieved a 40% reduction in carbon emissions over the past three years 
        through renewable energy adoption. We've installed 500MW of solar capacity and 
        transitioned 80% of our fleet to electric vehicles. Water consumption decreased by 25%.
    """,
    
    "social_negative": """
        Recent workplace incidents have increased by 15%. Employee turnover reached 30% this year.
        Several discrimination lawsuits are pending. Community relations remain strained after 
        the factory closure last quarter.
    """,
    
    "governance_mixed": """
        The board has improved diversity with 40% female directors and established an independent 
        audit committee. However, executive compensation increased 50% while company performance 
        declined. No clawback provisions exist for executive bonuses.
    """,
    
    "greenwashing_high": """
        We are committed to sustainability and green practices. Our eco-friendly approach ensures 
        responsible operations. We strive to be environmentally conscious in all our activities.
        Sustainability is at the heart of everything we do.
    """,
    
    "comprehensive": """
        2023 ESG Report: Emissions reduced by 35% (Scope 1: 10,000 tCO2e, Scope 2: 15,000 tCO2e).
        Employee safety: 0.5 TRIR, down from 1.2. Board composition: 5/12 independent directors.
        $2M invested in community programs. 100% suppliers audited for human rights compliance.
        Target: Net zero by 2040 with science-based targets approved by SBTi.
    """
}

class TestSmartDocumentChunker:
    """Test document chunking functionality"""
    
    def test_basic_chunking(self):
        chunker = SmartDocumentChunker(chunk_size=100, overlap=10)
        text = "This is a test. " * 50  # ~800 characters
        
        chunks = chunker.chunk_document(text)
        
        assert len(chunks) > 1
        assert all('text' in chunk for chunk in chunks)
        assert all('type' in chunk for chunk in chunks)
        assert all('token_count' in chunk for chunk in chunks)
    
    def test_section_type_detection(self):
        chunker = SmartDocumentChunker()
        
        env_text = "Carbon emissions and climate change initiatives"
        social_text = "Employee diversity and workplace safety"
        gov_text = "Board governance and ethics policies"
        
        assert chunker._detect_section_type(env_text) == 'environmental'
        assert chunker._detect_section_type(social_text) == 'social'
        assert chunker._detect_section_type(gov_text) == 'governance'
    
    def test_large_document_handling(self):
        chunker = SmartDocumentChunker(chunk_size=450)
        large_text = " ".join([SAMPLE_ESG_TEXTS["comprehensive"]] * 10)
        
        chunks = chunker.chunk_document(large_text)
        
        # Verify no chunk exceeds size limit
        for chunk in chunks:
            assert chunk['token_count'] <= 450 * 1.5  # Allow some margin

@pytest.mark.asyncio
class TestBERTEnhancedScorer:
    """Test BERT scoring functionality"""
    
    async def test_initialization(self):
        """Test BERT scorer initialization"""
        scorer = BERTEnhancedScorer(use_gpu=False)
        
        assert scorer.device.type == "cpu"
        assert hasattr(scorer, 'distilbert_tokenizer')
        assert hasattr(scorer, 'distilbert_model')
        assert hasattr(scorer, 'finbert_pipeline')
    
    async def test_analyze_positive_environmental(self):
        """Test analysis of positive environmental content"""
        scorer = BERTEnhancedScorer(use_gpu=False)
        
        result = await scorer.analyze(SAMPLE_ESG_TEXTS["environmental_positive"])
        
        assert isinstance(result, BERTAnalysisResult)
        assert len(result.classifications) > 0
        assert 'Environmental' in [c.category for c in result.classifications]
        assert result.overall_sentiment['Environmental'] > 0.6
        assert result.confidence_score > 0.5
    
    async def test_analyze_negative_social(self):
        """Test analysis of negative social content"""
        scorer = BERTEnhancedScorer(use_gpu=False)
        
        result = await scorer.analyze(SAMPLE_ESG_TEXTS["social_negative"])
        
        assert 'Social' in [c.category for c in result.classifications]
        assert result.overall_sentiment['Social'] < 0.4
        assert any(c.sentiment == 'Negative' for c in result.classifications if c.category == 'Social')
    
    async def test_confidence_threshold(self):
        """Test confidence threshold filtering"""
        scorer = BERTEnhancedScorer(use_gpu=False)
        
        result = await scorer.analyze(
            SAMPLE_ESG_TEXTS["governance_mixed"],
            min_confidence=0.7
        )
        
        # All classifications should meet threshold
        assert all(c.confidence >= 0.7 for c in result.classifications)

@pytest.mark.asyncio
class TestBERTIntegratedEngine:
    """Test integrated ESG engine with BERT"""
    
    async def test_engine_initialization(self):
        """Test engine initialization with and without BERT"""
        # With BERT
        engine_bert = BERTIntegratedESGEngine(enable_bert=True)
        assert engine_bert.enable_bert
        assert hasattr(engine_bert, 'bert_scorer')
        
        # Without BERT
        engine_no_bert = BERTIntegratedESGEngine(enable_bert=False)
        assert not engine_no_bert.enable_bert
    
    async def test_keyword_only_analysis(self):
        """Test keyword-only analysis mode"""
        engine = BERTIntegratedESGEngine(enable_bert=True)
        
        result = await engine.analyze(
            content=SAMPLE_ESG_TEXTS["environmental_positive"],
            quick_mode=True,
            use_bert=False
        )
        
        assert result['analysis_metadata']['method'] == 'keyword_only'
        assert 'bert_analysis' not in result
        assert 'scores' in result
    
    async def test_bert_enhanced_analysis(self):
        """Test BERT-enhanced analysis mode"""
        engine = BERTIntegratedESGEngine(enable_bert=True)
        
        result = await engine.analyze(
            content=SAMPLE_ESG_TEXTS["comprehensive"],
            quick_mode=False,
            use_bert=True,
            frameworks=["CSRD", "TCFD"]
        )
        
        assert result['analysis_metadata']['method'] == 'hybrid'
        assert 'bert_analysis' in result
        assert 'greenwashing_assessment' in result
        assert result['analysis_metadata']['bert_time'] > 0
        assert result['confidence'] > 0
    
    async def test_greenwashing_detection(self):
        """Test greenwashing risk assessment"""
        engine = BERTIntegratedESGEngine(enable_bert=True)
        
        result = await engine.analyze(
            content=SAMPLE_ESG_TEXTS["greenwashing_high"],
            use_bert=True
        )
        
        assert 'greenwashing_assessment' in result
        greenwashing = result['greenwashing_assessment']
        assert greenwashing['risk_level'] in ['medium', 'high']
        assert greenwashing['risk_score'] > 0.5
        assert len(greenwashing['indicators']) > 0
    
    async def test_framework_enhancement(self):
        """Test framework requirement enhancement with BERT"""
        engine = BERTIntegratedESGEngine(enable_bert=True)
        
        result = await engine.analyze(
            content=SAMPLE_ESG_TEXTS["comprehensive"],
            frameworks=["CSRD", "TCFD"],
            use_bert=True
        )
        
        # Check if requirements were enhanced
        if 'requirement_findings' in result:
            bert_validated = [f for f in result['requirement_findings'] if f.get('bert_validated')]
            assert len(bert_validated) > 0
    
    async def test_performance_tracking(self):
        """Test performance metrics tracking"""
        engine = BERTIntegratedESGEngine(enable_bert=True)
        
        # Run multiple analyses
        for i in range(3):
            await engine.analyze(
                content=f"Test content {i}",
                use_bert=True
            )
        
        stats = engine.get_performance_stats()
        
        assert 'keyword_time' in stats
        assert 'bert_time' in stats
        assert stats['bert_time']['count'] == 3
        assert stats['bert_time']['avg'] > 0

@pytest.mark.asyncio
class TestHybridAnalyzer:
    """Test hybrid analysis functionality"""
    
    async def test_hybrid_mode(self):
        """Test hybrid analysis mode"""
        from lean_esg_platform import EnhancedKeywordScorer
        
        keyword_scorer = EnhancedKeywordScorer()
        bert_scorer = BERTEnhancedScorer(use_gpu=False)
        analyzer = HybridESGAnalyzer(keyword_scorer, bert_scorer)
        
        result = await analyzer.analyze(
            SAMPLE_ESG_TEXTS["environmental_positive"],
            mode="hybrid"
        )
        
        assert result['method'] == 'hybrid'
        assert result['credits_used'] == 6
        assert 'keyword_scores' in result
        assert 'bert_analysis' in result
        assert 'scores' in result
    
    async def test_score_combination(self):
        """Test score combination logic"""
        from lean_esg_platform import EnhancedKeywordScorer
        
        keyword_scorer = EnhancedKeywordScorer()
        bert_scorer = BERTEnhancedScorer(use_gpu=False)
        analyzer = HybridESGAnalyzer(keyword_scorer, bert_scorer)
        
        # Mock scores for testing
        keyword_scores = {'environmental': 60, 'social': 50, 'governance': 70}
        
        bert_result = Mock(spec=BERTAnalysisResult)
        bert_result.overall_sentiment = {
            'Environmental': 0.8,  # 80
            'Social': 0.3,         # 30
            'Governance': 0.9      # 90
        }
        bert_result.confidence_score = 0.85
        
        combined = analyzer._combine_scores(keyword_scores, bert_result)
        
        # With high confidence, BERT should have more weight
        assert combined['environmental'] > keyword_scores['environmental']
        assert combined['social'] < keyword_scores['social']
        assert combined['governance'] > keyword_scores['governance']

class TestIntegrationScenarios:
    """Test real-world integration scenarios"""
    
    @pytest.mark.asyncio
    async def test_batch_processing(self):
        """Test processing multiple documents"""
        engine = create_bert_engine(enable_bert=True)
        
        documents = list(SAMPLE_ESG_TEXTS.values())
        results = []
        
        start_time = time.time()
        for doc in documents:
            result = await engine.analyze(doc, use_bert=True)
            results.append(result)
        
        total_time = time.time() - start_time
        
        assert len(results) == len(documents)
        assert all('scores' in r for r in results)
        assert total_time < 30  # Should complete in reasonable time
    
    @pytest.mark.asyncio
    async def test_fallback_on_error(self):
        """Test fallback to keyword analysis on BERT error"""
        engine = BERTIntegratedESGEngine(enable_bert=True)
        
        # Mock BERT scorer to raise error
        with patch.object(engine.bert_scorer, 'analyze', side_effect=Exception("Model error")):
            result = await engine.analyze(
                content="Test content",
                use_bert=True
            )
            
            # Should fallback gracefully
            assert 'scores' in result
            assert result['analysis_metadata']['method'] == 'keyword_only'
    
    @pytest.mark.asyncio
    async def test_memory_efficiency(self):
        """Test memory efficiency with large documents"""
        engine = create_bert_engine(enable_bert=True)
        
        # Create a large document
        large_doc = " ".join([SAMPLE_ESG_TEXTS["comprehensive"]] * 20)
        
        result = await engine.analyze(large_doc, use_bert=True)
        
        assert 'scores' in result
        assert 'bert_analysis' in result
        # Should handle large docs without memory issues

# Performance benchmarks
@pytest.mark.benchmark
class TestPerformanceBenchmarks:
    """Performance benchmarking tests"""
    
    @pytest.mark.asyncio
    async def test_keyword_vs_bert_speed(self):
        """Benchmark keyword vs BERT analysis speed"""
        engine = create_bert_engine(enable_bert=True)
        test_content = SAMPLE_ESG_TEXTS["comprehensive"]
        
        # Keyword analysis
        keyword_start = time.time()
        keyword_result = await engine.analyze(test_content, use_bert=False)
        keyword_time = time.time() - keyword_start
        
        # BERT analysis
        bert_start = time.time()
        bert_result = await engine.analyze(test_content, use_bert=True)
        bert_time = time.time() - bert_start
        
        print(f"\nKeyword analysis: {keyword_time:.3f}s")
        print(f"BERT analysis: {bert_time:.3f}s")
        print(f"BERT overhead: {bert_time - keyword_time:.3f}s")
        
        assert bert_time < 10  # Should complete within 10 seconds
        assert keyword_time < 1  # Keyword should be very fast

# Utility function for running specific test groups
def run_tests(test_group=None):
    """Run specific test groups or all tests"""
    if test_group:
        pytest.main(["-v", "-k", test_group, __file__])
    else:
        pytest.main(["-v", __file__])

if __name__ == "__main__":
    # Run all tests
    run_tests() 