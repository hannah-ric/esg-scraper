#!/usr/bin/env python3
"""
Model Download Script
Pre-downloads all required BERT models for the ESG platform
"""

import os
import sys
import logging
from transformers import (
    pipeline,
    AutoTokenizer,
    AutoModelForSequenceClassification,
    AutoModel
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Models to download
MODELS = [
    {
        'name': 'DistilBERT-ESG',
        'model_id': 'descartes100/distilBERT_ESG',
        'type': 'classification'
    },
    {
        'name': 'FinBERT-ESG-9-Categories',
        'model_id': 'yiyanghkust/finbert-esg-9-categories',
        'type': 'pipeline'
    },
    {
        'name': 'FinBERT-ESG',
        'model_id': 'yiyanghkust/finbert-esg',
        'type': 'classification'
    }
]

def download_model(model_info):
    """Download a single model"""
    name = model_info['name']
    model_id = model_info['model_id']
    model_type = model_info['type']
    
    logger.info(f"Downloading {name} ({model_id})...")
    
    try:
        if model_type == 'classification':
            # Download tokenizer and model
            tokenizer = AutoTokenizer.from_pretrained(model_id)
            model = AutoModelForSequenceClassification.from_pretrained(model_id)
            logger.info(f"✓ {name} downloaded successfully")
            
        elif model_type == 'pipeline':
            # Download via pipeline (includes both tokenizer and model)
            pipe = pipeline('text-classification', model=model_id)
            logger.info(f"✓ {name} downloaded successfully")
            
        else:
            # Generic model download
            tokenizer = AutoTokenizer.from_pretrained(model_id)
            model = AutoModel.from_pretrained(model_id)
            logger.info(f"✓ {name} downloaded successfully")
            
    except Exception as e:
        logger.error(f"✗ Failed to download {name}: {str(e)}")
        return False
    
    return True

def verify_cache():
    """Verify models are cached"""
    cache_dir = os.environ.get('TRANSFORMERS_CACHE', '/cache')
    
    if os.path.exists(cache_dir):
        files = os.listdir(cache_dir)
        logger.info(f"Cache directory contains {len(files)} items")
        
        # Check for model files
        model_files = [f for f in files if f.endswith('.bin') or f.endswith('.safetensors')]
        logger.info(f"Found {len(model_files)} model files")
        
        return len(model_files) > 0
    else:
        logger.warning("Cache directory does not exist")
        return False

def main():
    """Main download function"""
    logger.info("Starting model download process...")
    logger.info(f"Cache directory: {os.environ.get('TRANSFORMERS_CACHE', '/cache')}")
    
    # Download all models
    success_count = 0
    for model_info in MODELS:
        if download_model(model_info):
            success_count += 1
    
    logger.info(f"\nDownload complete: {success_count}/{len(MODELS)} models downloaded")
    
    # Verify cache
    if verify_cache():
        logger.info("✓ Model cache verified")
    else:
        logger.warning("⚠ Model cache verification failed")
    
    # Exit with appropriate code
    if success_count == len(MODELS):
        logger.info("✓ All models downloaded successfully!")
        sys.exit(0)
    else:
        logger.error("✗ Some models failed to download")
        sys.exit(1)

if __name__ == "__main__":
    main() 