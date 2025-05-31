#!/usr/bin/env python3
"""
Comprehensive deployment issue checker for ESG Scraper
"""
import os
import sys
import json
import subprocess
import re
from pathlib import Path


def run_command(cmd):
    """Run a shell command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def check_flake8():
    """Check for any flake8 issues"""
    print("🔍 Running flake8 check...")
    code, stdout, stderr = run_command(
        "flake8 . --max-line-length=120 --exclude=venv,__pycache__,.git,logs,data,models"
    )
    if code == 0:
        print("✅ No flake8 issues found")
        return True
    else:
        print(f"❌ Flake8 issues found:\n{stdout}")
        return False


def check_black():
    """Check for Black formatting issues"""
    print("🔍 Running Black check...")
    code, stdout, stderr = run_command("black --check . --exclude='venv|__pycache__|.git'")
    if code == 0:
        print("✅ All files are properly formatted")
        return True
    else:
        print(f"❌ Black formatting issues found:\n{stdout}")
        return False


def check_imports():
    """Check for missing or problematic imports"""
    print("🔍 Checking imports...")
    issues = []
    
    # Check for relative imports that might cause issues
    code, stdout, _ = run_command("grep -r 'from \\.' --include='*.py' --exclude-dir=venv .")
    if stdout:
        issues.append("Found relative imports that might cause issues in production")
    
    # Check for missing __init__.py files
    for root, dirs, files in os.walk("."):
        if "venv" in root or "__pycache__" in root or ".git" in root:
            continue
        if any(f.endswith(".py") for f in files) and "__init__.py" not in files:
            if root != ".":  # Skip root directory
                issues.append(f"Missing __init__.py in {root}")
    
    if issues:
        print("❌ Import issues found:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    else:
        print("✅ No import issues found")
        return True


def check_env_vars():
    """Check for hardcoded secrets or missing env vars"""
    print("🔍 Checking for hardcoded secrets...")
    
    # Patterns that might indicate hardcoded secrets
    secret_patterns = [
        r'JWT_SECRET\s*=\s*["\'][^$][^"\']+["\']',
        r'MONGODB_URI\s*=\s*["\']mongodb://[^$][^"\']+["\']',
        r'STRIPE_SECRET_KEY\s*=\s*["\'][^$][^"\']+["\']',
        r'API_KEY\s*=\s*["\'][^$][^"\']+["\']',
    ]
    
    issues = []
    for pattern in secret_patterns:
        code, stdout, _ = run_command(f"grep -r '{pattern}' --include='*.py' --exclude-dir=venv .")
        if stdout and "os.getenv" not in stdout and "os.environ" not in stdout:
            issues.append(f"Possible hardcoded secret: {pattern}")
    
    if issues:
        print("❌ Security issues found:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    else:
        print("✅ No hardcoded secrets found")
        return True


def check_dockerfile():
    """Check Dockerfile for issues"""
    print("🔍 Checking Dockerfile...")
    
    if not os.path.exists("Dockerfile"):
        print("❌ Dockerfile not found")
        return False
    
    with open("Dockerfile", "r") as f:
        content = f.read()
    
    issues = []
    
    # Check for security issues
    if "USER root" in content and content.rindex("USER root") > content.rindex("USER appuser") if "USER appuser" in content else True:
        issues.append("Dockerfile ends with root user - should switch to non-root")
    
    if "COPY . ." in content and "requirements.txt" not in content:
        issues.append("Dockerfile copies all files before installing requirements - inefficient caching")
    
    if issues:
        print("❌ Dockerfile issues found:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    else:
        print("✅ Dockerfile looks good")
        return True


def check_deployment_files():
    """Check deployment configuration files"""
    print("🔍 Checking deployment files...")
    
    required_files = [
        "deployment/app.yaml",
        "deployment/start_production.sh",
        ".github/workflows/deploy.yml",
        "Dockerfile",
        "requirements.txt",
        ".env.example"
    ]
    
    missing = []
    for file in required_files:
        if not os.path.exists(file):
            missing.append(file)
    
    # Check if start_production.sh is executable
    if os.path.exists("deployment/start_production.sh"):
        if not os.access("deployment/start_production.sh", os.X_OK):
            missing.append("deployment/start_production.sh is not executable")
    
    if missing:
        print("❌ Missing deployment files:")
        for file in missing:
            print(f"   - {file}")
        return False
    else:
        print("✅ All deployment files present")
        return True


def check_memory_usage():
    """Check for memory-intensive operations"""
    print("🔍 Checking for memory issues...")
    
    issues = []
    
    # Check for transformer models being loaded
    code, stdout, _ = run_command("grep -r 'transformers' --include='*.py' --exclude-dir=venv . | grep -v '#'")
    if stdout and "disable_transformers" not in stdout:
        issues.append("Transformers library is imported but might cause memory issues on small instances")
    
    # Check for large in-memory operations
    code, stdout, _ = run_command("grep -r 'read()' --include='*.py' --exclude-dir=venv . | grep -v 'readline'")
    if stdout:
        issues.append("Found .read() operations that might load large files into memory")
    
    if issues:
        print("⚠️  Potential memory issues:")
        for issue in issues:
            print(f"   - {issue}")
        return True  # Warning only
    else:
        print("✅ No obvious memory issues")
        return True


def check_api_consistency():
    """Check API endpoints for consistency"""
    print("🔍 Checking API consistency...")
    
    # Check for consistent error handling
    code, stdout, _ = run_command("grep -r 'HTTPException' --include='*.py' --exclude-dir=venv .")
    if not stdout:
        print("⚠️  No HTTPException usage found - might have inconsistent error handling")
    
    # Check for proper async usage
    code, stdout, _ = run_command("grep -r 'def ' --include='*.py' --exclude-dir=venv . | grep -v 'async def' | grep '@app'")
    if stdout:
        print("⚠️  Found non-async route handlers - might cause performance issues")
    
    print("✅ API consistency check complete")
    return True


def main():
    """Run all checks"""
    print("🏥 ESG Scraper Deployment Health Check")
    print("=" * 50)
    
    checks = [
        ("Flake8 Linting", check_flake8),
        ("Black Formatting", check_black),
        ("Import Structure", check_imports),
        ("Environment Variables", check_env_vars),
        ("Dockerfile", check_dockerfile),
        ("Deployment Files", check_deployment_files),
        ("Memory Usage", check_memory_usage),
        ("API Consistency", check_api_consistency),
    ]
    
    passed = 0
    failed = 0
    
    for name, check_func in checks:
        print(f"\n📋 {name}")
        try:
            if check_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Check failed with error: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    if failed > 0:
        print("\n⚠️  Fix the above issues before deployment!")
        sys.exit(1)
    else:
        print("\n🎉 All deployment checks passed!")
        sys.exit(0)


if __name__ == "__main__":
    main() 