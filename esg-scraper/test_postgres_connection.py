#!/usr/bin/env python3
"""
PostgreSQL Connection Test Script
=================================

Tests PostgreSQL connection and basic operations
"""

import asyncio
import os
import sys
import logging
from datetime import datetime

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from postgresql_manager import PostgreSQLManager  # noqa: E402

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_connection():
    """Test PostgreSQL connection"""
    logger.info("=" * 60)
    logger.info("PostgreSQL Connection Test")
    logger.info("=" * 60)

    # Display connection parameters (without password)
    logger.info("Connection Parameters:")
    logger.info(f"  PGUSER: {os.getenv('PGUSER', 'Not set')}")
    logger.info(f"  PGHOST: {os.getenv('PGHOST', 'Not set')}")
    logger.info(f"  PGPORT: {os.getenv('PGPORT', 'Not set')}")
    logger.info(f"  PGDATABASE: {os.getenv('PGDATABASE', 'Not set')}")
    logger.info(f"  PGSSLMODE: {os.getenv('PGSSLMODE', 'Not set')}")
    logger.info(f"  PGPASSWORD: {'Set' if os.getenv('PGPASSWORD') else 'Not set'}")

    # Create manager
    manager = PostgreSQLManager()

    try:
        # Test 1: Initialize connection
        logger.info("\n📌 Test 1: Initializing connection pool...")
        await manager.initialize()
        logger.info("✅ Connection pool initialized successfully")

        # Test 2: Health check
        logger.info("\n📌 Test 2: Running health check...")
        health = await manager.health_check()
        logger.info(f"✅ Health check passed: {health}")

        # Test 3: Create test user
        logger.info("\n📌 Test 3: Creating test user...")
        test_email = f"test_{datetime.now().timestamp()}@example.com"
        user = await manager.create_user(test_email, "free")
        logger.info(f"✅ User created: ID={user['_id']}, Email={user['email']}")

        # Test 4: Save test analysis
        logger.info("\n📌 Test 4: Saving test analysis...")
        test_result = {
            "company": "Test Corp",
            "scores": {
                "environmental": 75.0,
                "social": 80.0,
                "governance": 85.0,
                "overall": 80.0,
            },
            "keywords": ["test", "ESG", "PostgreSQL"],
            "insights": ["Test successful"],
            "analysis_type": "connection_test",
            "confidence": 0.95,
            "framework_coverage": {
                "CSRD": {
                    "coverage_percentage": 75.0,
                    "requirements_found": 9,
                    "requirements_total": 12,
                }
            },
        }

        analysis_id = await manager.save_analysis(
            user["_id"], "test_connection", test_result, "Technology", "2024"
        )
        logger.info(f"✅ Analysis saved: ID={analysis_id}")

        # Test 5: Retrieve analysis
        logger.info("\n📌 Test 5: Retrieving analyses...")
        analyses = await manager.get_user_analyses(user["_id"])
        logger.info(f"✅ Retrieved {len(analyses)} analyses")

        if analyses:
            latest = analyses[0]
            logger.info(
                f"   Latest analysis: Company={latest.get('company_name')}, "
                f"Overall Score={latest['scores']['overall']}"
            )

        # Test 6: Get benchmark data
        logger.info("\n📌 Test 6: Getting benchmark data...")
        benchmarks = await manager.get_benchmark_data("Technology", "CSRD")
        logger.info(f"✅ Retrieved {len(benchmarks)} benchmark records")

        # Test 7: Database pool stats
        logger.info("\n📌 Test 7: Checking connection pool...")
        if manager.pool:
            logger.info(f"✅ Pool size: {manager.pool.get_size()}")
            logger.info(f"   Free connections: {manager.pool.get_idle_size()}")
            logger.info(
                f"   Used connections: {manager.pool.get_size() - manager.pool.get_idle_size()}"
            )

        logger.info("\n" + "=" * 60)
        logger.info("✅ ALL TESTS PASSED!")
        logger.info("PostgreSQL connection is working correctly")
        logger.info("=" * 60)

        return True

    except Exception as e:
        logger.error(f"\n❌ TEST FAILED: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback

        logger.error(f"Traceback:\n{traceback.format_exc()}")
        return False

    finally:
        # Cleanup
        logger.info("\n🧹 Cleaning up...")
        await manager.close()
        logger.info("✅ Connection pool closed")


async def main():
    """Main test runner"""
    success = await test_connection()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    # Check if we have minimum required environment variables
    if not os.getenv("PGPASSWORD"):
        logger.error("❌ PGPASSWORD environment variable not set!")
        logger.error("Please set the PostgreSQL password before running this test.")
        sys.exit(1)

    asyncio.run(main())
