"""
Test script to demonstrate BERT functionality
Shows various use cases and capabilities
"""

import requests
import json

# API base URL
BASE_URL = "http://localhost:8001"

def test_bert_status():
    """Test BERT service status"""
    print("=== Testing BERT Status ===")
    response = requests.get(f"{BASE_URL}/api/bert/status")
    print(json.dumps(response.json(), indent=2))
    print()

def test_bert_analysis():
    """Test basic BERT analysis"""
    print("=== Testing BERT Analysis ===")
    
    test_texts = [
        {
            "text": "We achieved carbon neutrality through 100% renewable energy adoption and forest conservation projects.",
            "description": "Environmental - Positive"
        },
        {
            "text": "Employee turnover increased by 20% due to workplace safety incidents and low satisfaction scores.",
            "description": "Social - Negative"
        },
        {
            "text": "The board established new ethics policies and improved transparency in executive compensation.",
            "description": "Governance - Positive"
        }
    ]
    
    for test in test_texts:
        print(f"\nAnalyzing: {test['description']}")
        print(f"Text: {test['text'][:80]}...")
        
        response = requests.post(
            f"{BASE_URL}/api/bert/analyze",
            json={"text": test["text"], "use_bert": True}
        )
        
        result = response.json()
        if "bert_analysis" in result:
            bert = result["bert_analysis"]
            print(f"  Category: {bert['category']}")
            print(f"  Confidence: {bert['confidence']:.2%}")
            print(f"  Sentiment: {bert['sentiment']}")
            print(f"  Topics: {', '.join(bert['topics'])}")

def test_comparison():
    """Test keyword vs BERT comparison"""
    print("\n=== Testing Keyword vs BERT Comparison ===")
    
    text = "Our sustainable practices include reducing emissions and improving diversity."
    
    response = requests.post(
        f"{BASE_URL}/api/bert/compare",
        json={"text": text}
    )
    
    result = response.json()
    print(f"Text: {text}")
    print("\nScore Differences:")
    for key, diff in result.get("score_differences", {}).items():
        print(f"  {key}: {diff:+.1f} points")
    print(f"\nBERT Impact: {result.get('bert_impact', 'unknown')}")

def test_enhanced_analysis():
    """Test enhanced analysis with metrics extraction"""
    print("\n=== Testing Enhanced Analysis ===")
    
    text = """
    In fiscal year 2023, our sustainability achievements include:
    - Reduced Scope 1 emissions by 30% to 50,000 tCO2e
    - Achieved 45% renewable energy usage
    - Improved water efficiency by 20%, saving 1.2 million gallons
    - Increased employee diversity with 38% women in leadership roles
    - Zero workplace accidents for 365 consecutive days
    """
    
    response = requests.post(
        f"{BASE_URL}/analyze-enhanced",
        json={
            "text": text,
            "company_name": "Demo Company",
            "use_bert": True,
            "extract_metrics": True,
            "frameworks": ["CSRD", "GRI"]
        }
    )
    
    result = response.json()
    print(f"Company: {result.get('company_name')}")
    print(f"\nMetrics Extracted: {len(result.get('metrics', []))}")
    
    if result.get("bert_analysis"):
        bert = result["bert_analysis"].get("bert_analysis", {})
        print(f"\nBERT Analysis:")
        print(f"  Primary Category: {bert.get('category')}")
        print(f"  Confidence: {bert.get('confidence', 0):.2%}")
        print(f"  Sentiment: {bert.get('sentiment')}")
    
    print(f"\nInsights:")
    for insight in result.get("insights", [])[:5]:
        print(f"  - {insight}")

def test_batch_analysis():
    """Test batch analysis capability"""
    print("\n=== Testing Batch Analysis ===")
    
    texts = [
        "Carbon emissions reduced through renewable energy",
        "Employee wellness programs improved satisfaction",
        "Board governance strengthened with new policies"
    ]
    
    response = requests.post(
        f"{BASE_URL}/api/bert/batch",
        json=texts
    )
    
    result = response.json()
    print(f"Analyzed {result.get('total', 0)} texts")
    
    for i, analysis in enumerate(result.get("results", [])):
        if "bert_analysis" in analysis:
            bert = analysis["bert_analysis"]
            print(f"\nText {i+1}: {bert.get('category')} ({bert.get('confidence', 0):.0%})")

def main():
    """Run all tests"""
    print("ESG BERT Functionality Test Suite")
    print("=" * 50)
    
    try:
        # Check if API is running
        response = requests.get(f"{BASE_URL}/health")
        health = response.json()
        print(f"API Status: {health['status']}")
        print(f"BERT Status: {health['bert_status']}")
        print(f"Version: {health['version']}")
        print()
        
        # Run tests
        test_bert_status()
        test_bert_analysis()
        test_comparison()
        test_enhanced_analysis()
        test_batch_analysis()
        
        print("\n✅ All tests completed successfully!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to API. Make sure the server is running on port 8001")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 