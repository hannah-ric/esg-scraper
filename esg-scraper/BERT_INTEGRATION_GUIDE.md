# BERT Integration Implementation Guide

## Overview

This guide provides comprehensive instructions for integrating BERT models into the ESG analysis platform. The integration follows a phased approach, starting with lightweight enhancements and progressing to advanced features.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Integration Steps](#integration-steps)
5. [API Usage](#api-usage)
6. [Testing](#testing)
7. [Performance Optimization](#performance-optimization)
8. [Monitoring](#monitoring)
9. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements
- Python 3.8+
- 8GB RAM minimum (16GB recommended for optimal performance)
- 10GB free disk space for models
- CPU with AVX support (GPU optional but recommended)

### Existing Platform Requirements
- Working ESG platform installation
- Redis server running
- SQLite database configured
- FastAPI application running

## Installation

### Step 1: Install BERT Dependencies

```bash
# Navigate to project directory
cd /Users/hannahricci/esg-scraper/esg-scraper

# Create virtual environment if not exists
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install BERT requirements
pip install -r requirements_bert.txt
```

### Step 2: Download BERT Models

The models will be automatically downloaded on first use, but you can pre-download them:

```python
# Run this script to pre-download models
python -c "
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification

# Download DistilBERT-ESG
print('Downloading DistilBERT-ESG...')
tokenizer = AutoTokenizer.from_pretrained('descartes100/distilBERT_ESG')
model = AutoModelForSequenceClassification.from_pretrained('descartes100/distilBERT_ESG')

# Download FinBERT-ESG-9
print('Downloading FinBERT-ESG-9-Categories...')
pipeline('text-classification', model='yiyanghkust/finbert-esg-9-categories')

print('Models downloaded successfully!')
"
```

## Configuration

### Step 1: Update Environment Variables

Add these to your `.env` file:

```env
# BERT Configuration
ENABLE_BERT=true
BERT_CACHE_DIR=./bert_cache
BERT_USE_GPU=false  # Set to true if GPU available
BERT_MAX_LENGTH=512
BERT_BATCH_SIZE=8
BERT_CONFIDENCE_THRESHOLD=0.5

# Performance Settings
BERT_MODEL_TIMEOUT=30
BERT_MAX_WORKERS=2
```

### Step 2: Update Main Application

Modify your `lean_esg_platform.py` to integrate BERT routes:

```python
# Add this import at the top
from api_bert_integration import integrate_bert_routes

# After creating the FastAPI app, add:
# Integrate BERT routes
if os.getenv("ENABLE_BERT", "true").lower() == "true":
    integrate_bert_routes(app)
    logger.info("BERT integration enabled")
```

## Integration Steps

### Step 1: Basic Integration

1. **Update the main application file**:

```python
# In lean_esg_platform.py, after the existing imports
from api_bert_integration import integrate_bert_routes

# After app initialization
app = FastAPI(
    title="ESG Analysis Platform",
    description="Enhanced ESG analysis with BERT integration",
    version="2.0.0"
)

# Add BERT routes
integrate_bert_routes(app)
```

2. **Test basic functionality**:

```bash
# Start the server
uvicorn lean_esg_platform:app --reload

# Test health check
curl http://localhost:8000/health
```

### Step 2: Database Schema Updates

Add BERT-specific tables to track analyses:

```sql
-- Add to your database initialization
CREATE TABLE IF NOT EXISTS bert_analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    company_name TEXT,
    method TEXT NOT NULL,
    confidence REAL,
    bert_time REAL,
    keyword_time REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_bert_user ON bert_analyses(user_id);
CREATE INDEX idx_bert_method ON bert_analyses(method);
```

### Step 3: Update Existing Endpoints

Modify existing analyze endpoint to support BERT:

```python
# In your existing analyze endpoint
@app.post("/api/analyze")
async def analyze(request: AnalyzeRequest):
    # Check if BERT is requested
    use_bert = request.dict().get('use_bert', False)
    
    if use_bert and BERT_ENABLED:
        # Use BERT-integrated engine
        from bert_integration import create_bert_engine
        engine = create_bert_engine()
    else:
        # Use standard engine
        engine = EnhancedESGEngine()
    
    # Continue with analysis...
```

## API Usage

### BERT-Enhanced Analysis

```bash
# Basic BERT analysis
curl -X POST "http://localhost:8000/api/v2/bert/analyze" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Our company reduced carbon emissions by 30% and improved employee safety records.",
    "company_name": "Example Corp",
    "frameworks": ["CSRD", "TCFD"],
    "use_bert": true,
    "analysis_depth": "standard"
  }'
```

### Compare Analysis Methods

```bash
# Compare keyword vs BERT analysis
curl -X POST "http://localhost:8000/api/v2/bert/compare" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "We are committed to sustainable practices and green initiatives.",
    "company_name": "Example Corp",
    "frameworks": ["CSRD", "GRI"]
  }'
```

### Greenwashing Detection

```bash
# Check for greenwashing
curl -X POST "http://localhost:8000/api/v2/bert/greenwashing-check" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Our eco-friendly products are sustainably sourced.",
    "company_name": "Example Corp"
  }'
```

## Testing

### Unit Tests

Create `test_bert_integration.py`:

```python
import pytest
import asyncio
from bert_integration import BERTIntegratedESGEngine

@pytest.mark.asyncio
async def test_bert_analysis():
    engine = BERTIntegratedESGEngine(enable_bert=True)
    
    result = await engine.analyze(
        content="Company reduced emissions by 25% through renewable energy adoption.",
        use_bert=True
    )
    
    assert 'bert_analysis' in result
    assert result['confidence'] > 0.5
    assert 'greenwashing_assessment' in result

@pytest.mark.asyncio
async def test_keyword_fallback():
    engine = BERTIntegratedESGEngine(enable_bert=False)
    
    result = await engine.analyze(
        content="Environmental initiatives in place.",
        use_bert=False
    )
    
    assert result['analysis_metadata']['method'] == 'keyword_only'

@pytest.mark.asyncio
async def test_performance_tracking():
    engine = BERTIntegratedESGEngine(enable_bert=True)
    
    # Run multiple analyses
    for _ in range(3):
        await engine.analyze("Test content", use_bert=True)
    
    stats = engine.get_performance_stats()
    assert 'bert_time' in stats
    assert stats['bert_time']['count'] == 3
```

Run tests:

```bash
pytest test_bert_integration.py -v
```

### Integration Tests

```python
# test_bert_api.py
from fastapi.testclient import TestClient
from lean_esg_platform import app

client = TestClient(app)

def test_bert_endpoint():
    response = client.post(
        "/api/v2/bert/analyze",
        json={
            "content": "ESG test content",
            "use_bert": True
        },
        headers={"Authorization": "Bearer test_token"}
    )
    
    assert response.status_code == 200
    assert "bert_analysis" in response.json()
```

## Performance Optimization

### 1. Model Caching

The platform automatically caches models. To optimize:

```python
# Set cache directory with sufficient space
os.environ['TRANSFORMERS_CACHE'] = '/path/to/large/cache/dir'
```

### 2. Batch Processing

For multiple documents:

```python
# Process multiple documents efficiently
async def batch_analyze(documents: List[str]):
    engine = create_bert_engine()
    
    # Process in batches
    results = []
    for i in range(0, len(documents), 8):
        batch = documents[i:i+8]
        batch_results = await asyncio.gather(*[
            engine.analyze(doc) for doc in batch
        ])
        results.extend(batch_results)
    
    return results
```

### 3. GPU Acceleration

If GPU is available:

```bash
# Install GPU support
pip install torch --index-url https://download.pytorch.org/whl/cu118

# Set environment variable
export BERT_USE_GPU=true
```

### 4. Model Quantization

For faster inference:

```python
# The platform automatically applies quantization
# To disable for higher accuracy:
os.environ['BERT_QUANTIZE'] = 'false'
```

## Monitoring

### Performance Metrics

Access performance statistics:

```bash
curl -X GET "http://localhost:8000/api/v2/bert/performance" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Logging

Monitor BERT operations in logs:

```python
# Configure logging
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# BERT logs will appear with prefix "bert_integration"
```

### Prometheus Metrics

Add to your Prometheus configuration:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'esg_bert'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

## Troubleshooting

### Common Issues

1. **Out of Memory Error**
   ```bash
   # Reduce batch size
   export BERT_BATCH_SIZE=4
   
   # Or disable BERT temporarily
   export ENABLE_BERT=false
   ```

2. **Slow First Request**
   - This is normal - models are being loaded
   - Pre-load models on startup:
   ```python
   # Add to startup event
   @app.on_event("startup")
   async def preload_models():
       if BERT_ENABLED:
           engine = get_bert_engine()
           await engine.analyze("Preload test", use_bert=True)
   ```

3. **Model Download Failures**
   ```bash
   # Use mirror if needed
   export HF_ENDPOINT=https://hf-mirror.com
   
   # Or manually download
   wget https://huggingface.co/descartes100/distilBERT_ESG/resolve/main/pytorch_model.bin
   ```

4. **GPU Not Detected**
   ```python
   # Check GPU availability
   python -c "import torch; print(torch.cuda.is_available())"
   
   # If false, install CUDA drivers
   ```

### Debug Mode

Enable detailed debugging:

```python
# In your .env file
DEBUG_BERT=true
LOG_LEVEL=DEBUG

# This will show:
# - Model loading times
# - Tokenization details
# - Inference times
# - Memory usage
```

## Best Practices

1. **Start with Keyword Analysis**
   - Use BERT only when needed
   - Default to quick mode for real-time responses

2. **Monitor Resource Usage**
   - Track memory consumption
   - Monitor response times
   - Set up alerts for anomalies

3. **Gradual Rollout**
   - Enable BERT for subset of users first
   - A/B test to measure improvements
   - Collect feedback before full deployment

4. **Regular Updates**
   - Check for model updates monthly
   - Update transformers library quarterly
   - Re-evaluate model performance

## Next Steps

After successful Phase 1 implementation:

1. **Collect Performance Data** (2 weeks)
   - Analyze accuracy improvements
   - Measure resource usage
   - Gather user feedback

2. **Fine-tune Models** (Phase 2)
   - Collect domain-specific training data
   - Fine-tune on your ESG corpus
   - Implement active learning

3. **Add Advanced Features** (Phase 3)
   - Implement cross-framework validation
   - Add multilingual support
   - Create industry-specific models

## Support

For issues or questions:
1. Check logs: `tail -f logs/bert_integration.log`
2. Review metrics: `http://localhost:8000/api/v2/bert/performance`
3. Enable debug mode for detailed diagnostics

Remember: The BERT integration is designed to enhance, not replace, the existing keyword-based system. Use it strategically for maximum benefit. 