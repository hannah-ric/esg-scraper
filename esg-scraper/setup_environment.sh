#!/bin/bash

# ESG Scraper Environment Setup Script
# This script resolves dependency conflicts and sets up a clean environment

set -e  # Exit on any error

echo "🚀 Setting up ESG Scraper environment..."

# Detect system architecture
ARCH=$(uname -m)
OS=$(uname -s)

echo "🔍 Detected system: $OS $ARCH"

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment detected: $VIRTUAL_ENV"
else
    echo "⚠️  Warning: Not in a virtual environment. Consider creating one:"
    echo "   python -m venv venv"
    echo "   source venv/bin/activate  # On macOS/Linux"
    echo "   # or venv\\Scripts\\activate on Windows"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Upgrade pip first
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Uninstall conflicting packages first
echo "🧹 Removing conflicting packages..."
pip uninstall -y celery billiard click-didyoumean click-plugins click-repl kombu vine || true
pip uninstall -y trafilatura lxml courlan htmldate || true
pip uninstall -y pillow || true

# Install packages in specific order to avoid conflicts
echo "📦 Installing core dependencies..."
pip install wheel setuptools

echo "📦 Installing data processing packages..."
pip install numpy>=1.26.0
pip install pandas==2.1.4
pip install scipy>=1.11.0

echo "📦 Installing web scraping packages with Apple Silicon optimizations..."

# Special handling for lxml on Apple Silicon
if [[ "$OS" == "Darwin" && "$ARCH" == "arm64" ]]; then
    echo "🍎 Detected Apple Silicon Mac - using optimized installation..."
    
    # Try installing lxml via conda if available, otherwise use binary wheel
    if command -v conda &> /dev/null; then
        echo "📦 Installing lxml via conda for better compatibility..."
        conda install -c conda-forge lxml -y || {
            echo "⚠️  Conda installation failed, trying pip with binary wheel..."
            pip install --only-binary=lxml lxml>=4.9.3
        }
    else
        echo "📦 Installing lxml binary wheel..."
        pip install --only-binary=lxml lxml>=4.9.3
    fi
else
    echo "📦 Installing lxml for $OS $ARCH..."
    pip install lxml>=4.9.3
fi

echo "📦 Installing other scraping dependencies..."
pip install beautifulsoup4==4.12.2

# Try installing trafilatura - handle gracefully if it fails
echo "📦 Installing trafilatura..."
pip install trafilatura==1.6.2 || {
    echo "⚠️  Trafilatura installation failed, trying alternative..."
    pip install --no-deps trafilatura==1.6.2
    pip install courlan htmldate justext
}

echo "📦 Installing Celery and dependencies..."
pip install billiard>=4.1.0,\<5.0
pip install click-didyoumean>=0.3.0
pip install click-plugins>=1.1.1
pip install click-repl>=0.2.0
pip install kombu>=5.3.2,\<6.0
pip install vine>=5.0.0,\<6.0
pip install celery==5.3.4

echo "📦 Installing remaining dependencies..."
pip install -r requirements.txt || {
    echo "⚠️  Some packages failed to install, continuing with manual installation..."
    
    # Install critical packages individually
    pip install fastapi==0.104.1 || echo "⚠️  FastAPI installation failed"
    pip install uvicorn[standard]==0.24.0 || echo "⚠️  Uvicorn installation failed"
    pip install redis==5.0.1 || echo "⚠️  Redis installation failed"
    pip install transformers==4.36.0 || echo "⚠️  Transformers installation failed"
    pip install sqlalchemy==2.0.23 || echo "⚠️  SQLAlchemy installation failed"
    pip install httpx==0.25.2 || echo "⚠️  HTTPX installation failed"
    pip install python-dotenv==1.0.0 || echo "⚠️  python-dotenv installation failed"
}

# Verify critical imports
echo "🔍 Verifying installations..."
python -c "
import sys
import subprocess

def check_import(module, package_name=None):
    try:
        __import__(module)
        print(f'✅ {package_name or module} - OK')
        return True
    except ImportError as e:
        print(f'❌ {package_name or module} - FAILED: {e}')
        return False

# Critical imports for ESG scraper
imports_to_check = [
    ('fastapi', 'FastAPI'),
    ('uvicorn', 'Uvicorn'),
    ('lxml', 'LXML'),
    ('bs4', 'BeautifulSoup'),
    ('redis', 'Redis'),
    ('celery', 'Celery'),
    ('sqlalchemy', 'SQLAlchemy'),
    ('httpx', 'HTTPX'),
    ('pandas', 'Pandas'),
    ('numpy', 'NumPy')
]

# Optional imports
optional_imports = [
    ('trafilatura', 'Trafilatura'),
    ('transformers', 'Transformers'),
    ('prometheus_client', 'Prometheus Client')
]

failed_imports = []
failed_optional = []

print('\\n📋 Checking critical imports:')
for module, name in imports_to_check:
    if not check_import(module, name):
        failed_imports.append(name)

print('\\n📋 Checking optional imports:')
for module, name in optional_imports:
    if not check_import(module, name):
        failed_optional.append(name)

if failed_imports:
    print(f'\\n❌ Failed critical imports: {\"\\,\\ \".join(failed_imports)}')
    print('Please install these manually before continuing.')
    sys.exit(1)

if failed_optional:
    print(f'\\n⚠️  Failed optional imports: {\"\\,\\ \".join(failed_optional)}')
    print('These can be installed later if needed.')

print('\\n🎉 All critical dependencies installed successfully!')
"

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs
mkdir -p data
mkdir -p models

# Create .env template if it doesn't exist
if [ ! -f .env ]; then
    echo "📄 Creating .env template..."
    cat > .env << EOF
# ESG Scraper Configuration
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
UPSTASH_REDIS_URL=redis://localhost:6379
DATABASE_PATH=esg_data.db
STRIPE_SECRET_KEY=sk_test_your_stripe_key_here
FREE_TIER_CREDITS=100

# Optional: Production settings
# ENVIRONMENT=production
# LOG_LEVEL=INFO
# MAX_WORKERS=4
EOF
    echo "⚠️  Please update the .env file with your actual configuration values!"
fi

# Create an enhanced health check script
cat > health_check.py << 'EOF'
#!/usr/bin/env python3
"""
Quick health check for ESG Scraper dependencies
"""
import sys
import os

def main():
    print("🏥 ESG Scraper Health Check")
    print("=" * 40)
    
    # Check Python version
    python_version = sys.version_info
    print(f"Python Version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 9):
        print("❌ Python 3.9+ required")
        return False
    else:
        print("✅ Python version OK")
    
    # Check critical files
    required_files = [
        'lean_esg_platform.py',
        'esg_frameworks.py', 
        'database_schema.py',
        'requirements.txt'
    ]
    
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - Missing")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n⚠️  Missing files: {', '.join(missing_files)}")
        return False
    
    # Test imports
    print("\n🔍 Testing imports...")
    
    critical_imports = [
        ('fastapi', 'FastAPI'),
        ('uvicorn', 'Uvicorn'),
        ('lxml', 'LXML'),
        ('bs4', 'BeautifulSoup'),
        ('redis', 'Redis'),
        ('celery', 'Celery'),
        ('sqlalchemy', 'SQLAlchemy'),
        ('httpx', 'HTTPX'),
        ('pandas', 'Pandas'),
        ('numpy', 'NumPy')
    ]
    
    optional_imports = [
        ('trafilatura', 'Trafilatura'),
        ('transformers', 'Transformers'),
        ('prometheus_client', 'Prometheus Client')
    ]
    
    # Check critical imports
    critical_passed = True
    for module, name in critical_imports:
        try:
            __import__(module)
            print(f"✅ {name}")
        except ImportError as e:
            print(f"❌ {name} - {e}")
            critical_passed = False
    
    # Check optional imports
    optional_passed = 0
    for module, name in optional_imports:
        try:
            __import__(module)
            print(f"✅ {name} (optional)")
            optional_passed += 1
        except ImportError:
            print(f"⚠️  {name} (optional) - Not available")
    
    if not critical_passed:
        print("\n❌ Critical import failures detected!")
        return False
    
    # Test basic functionality
    try:
        from esg_frameworks import ESGFrameworkManager
        manager = ESGFrameworkManager()
        print("✅ ESG Framework Manager loaded")
        
        # Test framework loading
        frameworks = manager.get_framework_summary()
        print(f"✅ Loaded {len(frameworks)} ESG frameworks")
        
    except Exception as e:
        print(f"❌ ESG Framework Manager failed: {e}")
        return False
    
    print(f"\n🎉 Health check passed!")
    print(f"📊 {len(critical_imports)} critical imports OK")
    print(f"📊 {optional_passed}/{len(optional_imports)} optional imports available")
    print("\n🚀 Ready to run ESG Scraper!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
EOF

chmod +x health_check.py

# Create a simple fallback scraper for cases where trafilatura fails
cat > simple_scraper.py << 'EOF'
"""
Simple fallback web scraper using only BeautifulSoup
"""
import requests
from bs4 import BeautifulSoup
import time

def simple_scrape(url: str, timeout: int = 10) -> str:
    """Simple web scraping fallback"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text[:50000]  # Limit content size
        
    except Exception as e:
        raise Exception(f"Scraping failed: {e}")

if __name__ == "__main__":
    # Test the simple scraper
    test_url = "https://httpbin.org/html"
    try:
        content = simple_scrape(test_url)
        print(f"✅ Simple scraper works! Extracted {len(content)} characters")
    except Exception as e:
        print(f"❌ Simple scraper failed: {e}")
EOF

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env file with your configuration"
echo "2. Run health check: python health_check.py"
echo "3. Start Redis server: redis-server"
echo "4. Run the application: python lean_esg_platform.py"
echo ""
echo "📝 Additional files created:"
echo "   - health_check.py: System verification"
echo "   - simple_scraper.py: Fallback web scraper"
echo ""
if [[ "$OS" == "Darwin" && "$ARCH" == "arm64" ]]; then
    echo "🍎 Apple Silicon Notes:"
    echo "   - If you encounter lxml issues, try: conda install -c conda-forge lxml"
    echo "   - Alternative: brew install libxml2 libxslt && pip install lxml"
fi
echo ""
echo "For more details, check the logs in the logs/ directory" 