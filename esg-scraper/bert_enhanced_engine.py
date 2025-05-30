"""
BERT-Enhanced ESG Analysis Engine
Phase 1 Implementation: Lightweight BERT Integration
"""

import torch
from transformers import (
    DistilBertTokenizer, 
    DistilBertForSequenceClassification,
    pipeline,
    AutoTokenizer,
    AutoModelForSequenceClassification
)
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import asyncio
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

@dataclass
class ESGClassification:
    """ESG classification result with confidence scores"""
    category: str
    subcategory: Optional[str]
    confidence: float
    sentiment: Optional[str]
    evidence: Optional[str]

@dataclass
class BERTAnalysisResult:
    """Complete BERT analysis result"""
    classifications: List[ESGClassification]
    detailed_categories: List[Dict[str, Any]]
    overall_sentiment: Dict[str, float]
    key_topics: List[str]
    confidence_score: float

class SmartDocumentChunker:
    """Intelligent document chunking for BERT processing"""
    
    def __init__(self, chunk_size: int = 450, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap
        
    def chunk_document(self, text: str) -> List[Dict[str, Any]]:
        """Split document into semantic chunks"""
        # Split by paragraphs
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        chunks = []
        current_chunk = ""
        current_tokens = 0
        
        for para in paragraphs:
            # Rough token estimation (avg 1.3 tokens per word)
            para_tokens = len(para.split()) * 1.3
            
            if current_tokens + para_tokens <= self.chunk_size:
                current_chunk += para + "\n\n"
                current_tokens += para_tokens
            else:
                if current_chunk:
                    chunks.append({
                        'text': current_chunk.strip(),
                        'type': self._detect_section_type(current_chunk),
                        'token_count': int(current_tokens)
                    })
                
                # Start new chunk with overlap
                if len(para.split()) * 1.3 <= self.chunk_size:
                    current_chunk = para + "\n\n"
                    current_tokens = para_tokens
                else:
                    # Split large paragraph
                    sentences = para.split('. ')
                    for sent in sentences:
                        if len(current_chunk.split()) * 1.3 + len(sent.split()) * 1.3 <= self.chunk_size:
                            current_chunk += sent + ". "
                        else:
                            chunks.append({
                                'text': current_chunk.strip(),
                                'type': self._detect_section_type(current_chunk),
                                'token_count': int(len(current_chunk.split()) * 1.3)
                            })
                            current_chunk = sent + ". "
        
        # Add final chunk
        if current_chunk:
            chunks.append({
                'text': current_chunk.strip(),
                'type': self._detect_section_type(current_chunk),
                'token_count': int(len(current_chunk.split()) * 1.3)
            })
        
        return chunks
    
    def _detect_section_type(self, text: str) -> str:
        """Detect the type of content in the chunk"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['emission', 'carbon', 'climate', 'energy']):
            return 'environmental'
        elif any(word in text_lower for word in ['employee', 'diversity', 'safety', 'community']):
            return 'social'
        elif any(word in text_lower for word in ['governance', 'board', 'ethics', 'compliance']):
            return 'governance'
        else:
            return 'general'

class BERTEnhancedScorer:
    """BERT-enhanced ESG scoring system"""
    
    def __init__(self, use_gpu: bool = False):
        self.device = torch.device("cuda" if use_gpu and torch.cuda.is_available() else "cpu")
        self._load_models()
        self.chunker = SmartDocumentChunker()
        
    @lru_cache(maxsize=1)
    def _load_models(self):
        """Load and cache BERT models"""
        logger.info("Loading BERT models...")
        
        # DistilBERT-ESG for multi-label classification
        self.distilbert_tokenizer = DistilBertTokenizer.from_pretrained('descartes100/distilBERT_ESG')
        self.distilbert_model = DistilBertForSequenceClassification.from_pretrained(
            'descartes100/distilBERT_ESG'
        ).to(self.device)
        self.distilbert_model.eval()
        
        # FinBERT-ESG-9 for detailed categorization
        self.finbert_pipeline = pipeline(
            "text-classification",
            model="yiyanghkust/finbert-esg-9-categories",
            device=0 if self.device.type == "cuda" else -1
        )
        
        # Label mappings for DistilBERT-ESG
        self.label_map = {
            0: ('Environmental', 'Negative'),
            1: ('Environmental', 'Neutral'),
            2: ('Environmental', 'Positive'),
            3: ('Social', 'Negative'),
            4: ('Social', 'Neutral'),
            5: ('Social', 'Positive'),
            6: ('Governance', 'Negative'),
            7: ('Governance', 'Neutral'),
            8: ('Governance', 'Positive')
        }
        
        logger.info("Models loaded successfully")
    
    async def analyze(self, text: str, min_confidence: float = 0.5) -> BERTAnalysisResult:
        """Perform comprehensive BERT-based ESG analysis"""
        # Chunk the document
        chunks = self.chunker.chunk_document(text)
        
        # Analyze each chunk
        chunk_results = []
        for chunk in chunks:
            chunk_result = await self._analyze_chunk(chunk['text'], chunk['type'])
            chunk_results.append(chunk_result)
        
        # Aggregate results
        aggregated_result = self._aggregate_results(chunk_results, min_confidence)
        
        return aggregated_result
    
    async def _analyze_chunk(self, text: str, chunk_type: str) -> Dict[str, Any]:
        """Analyze a single text chunk"""
        # DistilBERT multi-label classification
        distilbert_results = self._run_distilbert(text)
        
        # FinBERT detailed categorization
        finbert_results = self._run_finbert(text)
        
        return {
            'text': text[:100] + "..." if len(text) > 100 else text,
            'chunk_type': chunk_type,
            'distilbert': distilbert_results,
            'finbert': finbert_results
        }
    
    def _run_distilbert(self, text: str) -> Dict[str, Any]:
        """Run DistilBERT-ESG analysis"""
        # Tokenize
        encoding = self.distilbert_tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        )
        
        # Move to device
        encoding = {k: v.to(self.device) for k, v in encoding.items()}
        
        # Get predictions
        with torch.no_grad():
            outputs = self.distilbert_model(**encoding)
            logits = outputs.logits
            
        # Apply sigmoid for multi-label
        sigmoid = torch.nn.Sigmoid()
        probs = sigmoid(logits.squeeze()).cpu().numpy()
        
        # Get classifications above threshold
        classifications = []
        for idx, prob in enumerate(probs):
            if prob > 0.5:
                category, sentiment = self.label_map[idx]
                classifications.append({
                    'category': category,
                    'sentiment': sentiment,
                    'confidence': float(prob)
                })
        
        return {
            'classifications': classifications,
            'raw_probs': probs.tolist()
        }
    
    def _run_finbert(self, text: str) -> List[Dict[str, Any]]:
        """Run FinBERT-ESG-9 analysis"""
        # Get top 3 predictions
        results = self.finbert_pipeline(text, top_k=3)
        
        # Process results
        processed_results = []
        for result in results:
            processed_results.append({
                'category': result['label'],
                'confidence': result['score']
            })
        
        return processed_results
    
    def _aggregate_results(self, chunk_results: List[Dict], min_confidence: float) -> BERTAnalysisResult:
        """Aggregate results from all chunks"""
        all_classifications = []
        all_categories = []
        sentiment_scores = {'Environmental': [], 'Social': [], 'Governance': []}
        
        for chunk in chunk_results:
            # Process DistilBERT results
            for classification in chunk['distilbert']['classifications']:
                if classification['confidence'] >= min_confidence:
                    all_classifications.append(ESGClassification(
                        category=classification['category'],
                        subcategory=None,
                        confidence=classification['confidence'],
                        sentiment=classification['sentiment'],
                        evidence=chunk['text']
                    ))
                    
                    # Track sentiment scores
                    if classification['sentiment'] == 'Positive':
                        sentiment_scores[classification['category']].append(1.0)
                    elif classification['sentiment'] == 'Neutral':
                        sentiment_scores[classification['category']].append(0.5)
                    else:
                        sentiment_scores[classification['category']].append(0.0)
            
            # Process FinBERT results
            for category in chunk['finbert']:
                if category['confidence'] >= min_confidence:
                    all_categories.append(category)
        
        # Calculate overall sentiment
        overall_sentiment = {}
        for category, scores in sentiment_scores.items():
            if scores:
                overall_sentiment[category] = np.mean(scores)
            else:
                overall_sentiment[category] = 0.5  # Neutral default
        
        # Extract key topics from categories
        category_counts = {}
        for cat in all_categories:
            category_counts[cat['category']] = category_counts.get(cat['category'], 0) + 1
        
        key_topics = sorted(category_counts.keys(), key=lambda x: category_counts[x], reverse=True)[:5]
        
        # Calculate overall confidence
        all_confidences = [c.confidence for c in all_classifications] + [c['confidence'] for c in all_categories]
        overall_confidence = np.mean(all_confidences) if all_confidences else 0.0
        
        return BERTAnalysisResult(
            classifications=all_classifications,
            detailed_categories=all_categories,
            overall_sentiment=overall_sentiment,
            key_topics=key_topics,
            confidence_score=overall_confidence
        )

class HybridESGAnalyzer:
    """Hybrid analyzer combining keyword and BERT approaches"""
    
    def __init__(self, keyword_scorer, bert_scorer: Optional[BERTEnhancedScorer] = None):
        self.keyword_scorer = keyword_scorer
        self.bert_scorer = bert_scorer or BERTEnhancedScorer()
        
    async def analyze(self, text: str, mode: str = "hybrid", **kwargs) -> Dict[str, Any]:
        """Perform hybrid ESG analysis"""
        
        if mode == "keyword_only":
            # Fast keyword-based analysis
            return {
                'scores': self.keyword_scorer.score(text),
                'method': 'keyword',
                'credits_used': 1
            }
            
        elif mode == "bert_only":
            # BERT-only analysis
            bert_result = await self.bert_scorer.analyze(text)
            return {
                'bert_analysis': bert_result,
                'method': 'bert',
                'credits_used': 5
            }
            
        else:  # hybrid mode
            # Run both analyses
            keyword_scores = self.keyword_scorer.score(text)
            bert_result = await self.bert_scorer.analyze(text)
            
            # Combine scores
            combined_scores = self._combine_scores(keyword_scores, bert_result)
            
            return {
                'scores': combined_scores,
                'keyword_scores': keyword_scores,
                'bert_analysis': bert_result,
                'method': 'hybrid',
                'credits_used': 6
            }
    
    def _combine_scores(self, keyword_scores: Dict[str, float], 
                       bert_result: BERTAnalysisResult) -> Dict[str, float]:
        """Combine keyword and BERT scores intelligently"""
        
        # Convert BERT sentiment to scores
        bert_scores = {}
        for category, sentiment in bert_result.overall_sentiment.items():
            bert_scores[category.lower()] = sentiment * 100
        
        # Weighted combination (60% BERT, 40% keyword)
        combined = {}
        for category in ['environmental', 'social', 'governance']:
            keyword_score = keyword_scores.get(category, 50)
            bert_score = bert_scores.get(category, 50)
            
            # If BERT has high confidence, weight it more
            if bert_result.confidence_score > 0.8:
                combined[category] = bert_score * 0.7 + keyword_score * 0.3
            else:
                combined[category] = bert_score * 0.6 + keyword_score * 0.4
        
        # Calculate overall
        combined['overall'] = np.mean([combined['environmental'], 
                                      combined['social'], 
                                      combined['governance']])
        
        return {k: round(v, 1) for k, v in combined.items()}

# Example usage
if __name__ == "__main__":
    # Test the BERT-enhanced scorer
    test_text = """
    Our company is committed to achieving net zero emissions by 2050. We have reduced 
    our Scope 1 and 2 emissions by 30% since 2020. Employee safety is our top priority, 
    with zero workplace accidents this year. Our board has established strong governance 
    practices with 40% independent directors.
    """
    
    async def test():
        scorer = BERTEnhancedScorer()
        result = await scorer.analyze(test_text)
        
        print("BERT Analysis Results:")
        print(f"Key Topics: {result.key_topics}")
        print(f"Overall Sentiment: {result.overall_sentiment}")
        print(f"Confidence: {result.confidence_score:.2f}")
        print(f"\nClassifications:")
        for classification in result.classifications:
            print(f"  - {classification.category} ({classification.sentiment}): "
                  f"{classification.confidence:.2f}")
    
    asyncio.run(test()) 