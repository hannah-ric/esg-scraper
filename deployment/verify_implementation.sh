#!/bin/bash

# ESG Scraper Implementation Verification Script
# ==============================================

echo "🔍 ESG Scraper Implementation Verification"
echo "=========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track overall status
ISSUES_FOUND=0

# Function to check implementation
check_item() {
    local item=$1
    local status=$2
    local details=$3
    
    if [ "$status" = "PASS" ]; then
        echo -e "${GREEN}✅ $item${NC}"
        if [ -n "$details" ]; then
            echo "   $details"
        fi
    elif [ "$status" = "WARN" ]; then
        echo -e "${YELLOW}⚠️  $item${NC}"
        echo "   $details"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
    else
        echo -e "${RED}❌ $item${NC}"
        echo "   $details"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
    fi
    echo ""
}

echo "1. Sentry Monitoring Integration"
echo "--------------------------------"

# Check if sentry-sdk is in requirements.txt
if grep -q "sentry-sdk" esg-scraper/requirements.txt; then
    check_item "Sentry SDK in requirements.txt" "PASS" "Version: $(grep sentry-sdk esg-scraper/requirements.txt)"
else
    check_item "Sentry SDK in requirements.txt" "FAIL" "Not found in requirements.txt"
fi

# Check if Sentry is initialized in the code
if grep -q "sentry_sdk.init" esg-scraper/lean_esg_platform.py; then
    check_item "Sentry initialization in code" "PASS"
else
    check_item "Sentry initialization in code" "FAIL" "Sentry SDK not initialized"
fi

# Check if SENTRY_DSN is in app.yaml
if grep -q "SENTRY_DSN" deployment/app.yaml; then
    check_item "SENTRY_DSN in app.yaml" "PASS"
else
    check_item "SENTRY_DSN in app.yaml" "FAIL" "Environment variable not configured"
fi

echo "2. API Rate Limiting"
echo "-------------------"

# Check if slowapi is in requirements.txt
if grep -q "slowapi" esg-scraper/requirements.txt; then
    check_item "Slowapi in requirements.txt" "PASS"
else
    check_item "Slowapi in requirements.txt" "FAIL" "Not found in requirements.txt"
fi

# Check if rate limiter is configured
if grep -q "limiter = Limiter" esg-scraper/lean_esg_platform.py; then
    check_item "Rate limiter configured" "PASS"
else
    check_item "Rate limiter configured" "FAIL" "Rate limiter not initialized"
fi

# Check if rate limiting is applied to endpoints
if grep -q "@limiter.limit" esg-scraper/lean_esg_platform.py; then
    check_item "Rate limiting decorators" "PASS" "Applied to endpoints"
else
    check_item "Rate limiting decorators" "FAIL" "No rate limiting decorators found"
fi

echo "3. Security Headers"
echo "------------------"

# Check for security headers middleware
if grep -q "add_security_headers" esg-scraper/lean_esg_platform.py; then
    check_item "Security headers middleware" "PASS"
else
    check_item "Security headers middleware" "FAIL" "Security headers not implemented"
fi

echo "4. Health Check Endpoints"
echo "------------------------"

# Check for enhanced health check
if grep -q "/health/detailed" esg-scraper/lean_esg_platform.py; then
    check_item "Detailed health check endpoint" "PASS"
else
    check_item "Detailed health check endpoint" "FAIL" "Enhanced health check not found"
fi

# Check if psutil is in requirements.txt
if grep -q "psutil" esg-scraper/requirements.txt; then
    check_item "System monitoring (psutil)" "PASS"
else
    check_item "System monitoring (psutil)" "FAIL" "psutil not in requirements.txt"
fi

echo "5. PostgreSQL Configuration"
echo "----------------------"

# Check if PostgreSQL environment variables are in app.yaml
if grep -q "PGPASSWORD" deployment/app.yaml; then
    check_item "PGPASSWORD in app.yaml" "PASS"
else
    check_item "PGPASSWORD in app.yaml" "FAIL" "PostgreSQL password not configured"
fi

if grep -q "PGHOST" deployment/app.yaml; then
    check_item "PGHOST in app.yaml" "PASS"
else
    check_item "PGHOST in app.yaml" "FAIL" "PostgreSQL host not configured"
fi

echo "6. Redis Configuration"
echo "---------------------"

# Check if Redis SSL support is implemented
if grep -q "rediss://" esg-scraper/lean_esg_platform.py; then
    check_item "Redis SSL support" "PASS"
else
    check_item "Redis SSL support" "FAIL" "SSL support not implemented"
fi

# Check if UPSTASH_REDIS_URL uses secret
if grep -A2 "key: UPSTASH_REDIS_URL" deployment/app.yaml | grep -q "type: SECRET"; then
    check_item "UPSTASH_REDIS_URL as secret" "PASS"
else
    check_item "UPSTASH_REDIS_URL as secret" "WARN" "Should be configured as SECRET"
fi

echo "7. Error Handling"
echo "----------------"

# Check for Sentry error context
if grep -q "sentry_sdk.push_scope" esg-scraper/lean_esg_platform.py; then
    check_item "Sentry error context" "PASS" "Enhanced error tracking implemented"
else
    check_item "Sentry error context" "FAIL" "No Sentry context found"
fi

echo "8. Verification Scripts"
echo "---------------------"

# Check if Redis migration script exists
if [ -f "deployment/migrate_redis.py" ]; then
    check_item "Redis migration script" "PASS"
else
    check_item "Redis migration script" "FAIL" "Script not found"
fi

echo "9. API Versioning"
echo "-----------------"

# Check if API versioning is implemented
if [ -f "esg-scraper/api_versioning.py" ]; then
    check_item "API versioning module" "PASS"
else
    check_item "API versioning module" "FAIL" "Module not found"
fi

echo "10. Documentation"
echo "----------------"

# Check for critical documentation
docs=(
    "DEPLOYMENT_READINESS_CHECKLIST.md"
    "FINAL_DEPLOYMENT_GUIDE.md"
    "deployment/monitoring_setup.md"
    "deployment/redis_migration.md"
)

for doc in "${docs[@]}"; do
    if [ -f "$doc" ]; then
        check_item "Documentation: $doc" "PASS"
    else
        check_item "Documentation: $doc" "FAIL" "File not found"
    fi
done

echo "=========================================="
echo "SUMMARY"
echo "=========================================="

if [ $ISSUES_FOUND -eq 0 ]; then
    echo -e "${GREEN}✅ All immediate recommendations implemented!${NC}"
    echo "The platform is ready for the next phase of deployment."
else
    echo -e "${RED}❌ Found $ISSUES_FOUND issues that need attention${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Review the failed items above"
    echo "2. Run the deployment readiness checklist"
    echo "3. Complete Redis migration to managed service"
    echo "4. Configure Sentry DSN in GitHub Secrets"
fi

echo ""
echo "To run specific verifications:"
echo "  python deployment/migrate_redis.py"

exit $ISSUES_FOUND 