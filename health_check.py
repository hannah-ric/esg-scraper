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
    print(
        f"Python Version: {python_version.major}.{python_version.minor}.{python_version.micro}"
    )

    if python_version < (3, 9):
        print("❌ Python 3.9+ required")
        return False
    else:
        print("✅ Python version OK")

    # Check critical files
    required_files = [
        "lean_esg_platform.py",
        "esg_frameworks.py",
        "metrics_standardizer.py",
        "api_versioning.py",
        "requirements.txt",
        "deployment_readiness_checklist.md",
        "monitoring_setup.md",
        "redis_migration.md",
        "postgresql_manager.py",
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
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("lxml", "LXML"),
        ("bs4", "BeautifulSoup"),
        ("redis", "Redis"),
        ("celery", "Celery"),
        ("asyncpg", "AsyncPG (PostgreSQL)"),
        ("httpx", "HTTPX"),
        ("pandas", "Pandas"),
        ("numpy", "NumPy"),
        ("yake", "YAKE"),
        ("jwt", "PyJWT"),
        ("slowapi", "SlowAPI"),
    ]

    optional_imports = [
        ("trafilatura", "Trafilatura"),
        ("transformers", "Transformers"),
        ("prometheus_client", "Prometheus Client"),
        ("sentry_sdk", "Sentry SDK"),
        ("psutil", "PSUtil"),
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

    # Test PostgreSQL manager
    try:
        __import__("postgresql_manager")
        print("✅ PostgreSQL Manager module loaded")
    except Exception as e:
        print(f"⚠️  PostgreSQL Manager failed to import: {e}")

    print("\n🎉 Health check passed!")
    print(f"📊 {len(critical_imports)} critical imports OK")
    print(f"📊 {optional_passed}/{len(optional_imports)} optional imports available")
    print("\n🚀 Ready to run ESG Scraper!")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
