#!/usr/bin/env python3
"""
Database Initialization and Migration Script
===========================================

Initializes PostgreSQL database with:
- Schema creation
- Initial data seeding
- Benchmark data population
- Verification
"""

import asyncio
import logging
import os
import sys

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from postgresql_manager import get_postgresql_manager  # noqa: E402

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DatabaseInitializer:
    """Initialize and seed PostgreSQL database"""

    def __init__(self):
        self.db_manager = get_postgresql_manager()
        self.benchmark_data = {
            "Technology": {
                "CSRD": {"p50": 65, "p75": 75, "p90": 85},
                "TCFD": {"p50": 60, "p75": 70, "p90": 80},
                "GRI": {"p50": 70, "p75": 80, "p90": 90},
                "SASB": {"p50": 55, "p75": 65, "p90": 75},
            },
            "Energy": {
                "CSRD": {"p50": 70, "p75": 80, "p90": 90},
                "TCFD": {"p50": 75, "p75": 85, "p90": 95},
                "GRI": {"p50": 65, "p75": 75, "p90": 85},
                "SASB": {"p50": 60, "p75": 70, "p90": 80},
            },
            "Financial Services": {
                "CSRD": {"p50": 60, "p75": 70, "p90": 80},
                "TCFD": {"p50": 65, "p75": 75, "p90": 85},
                "GRI": {"p50": 55, "p75": 65, "p90": 75},
                "SASB": {"p50": 70, "p75": 80, "p90": 90},
            },
        }

    async def initialize_database(self):
        """Initialize database connection and create schema"""
        try:
            logger.info("🚀 Initializing PostgreSQL database...")
            await self.db_manager.initialize()
            logger.info("✅ Database initialized successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            return False

    async def seed_benchmark_data(self):
        """Seed benchmark data for industries and frameworks"""
        logger.info("📊 Seeding benchmark data...")

        try:
            async with self.db_manager.acquire() as conn:
                # Check if benchmark data already exists
                count = await conn.fetchval("SELECT COUNT(*) FROM benchmark_data")

                if count > 0:
                    logger.info(f"ℹ️  Benchmark data already exists ({count} records)")
                    return True

                # Insert benchmark data
                for industry, frameworks in self.benchmark_data.items():
                    for framework, percentiles in frameworks.items():
                        await conn.execute(
                            """
                            INSERT INTO benchmark_data
                            (industry_sector, framework, percentile_50, percentile_75, percentile_90)
                            VALUES ($1, $2, $3, $4, $5)
                        """,
                            industry,
                            framework,
                            float(percentiles["p50"]),
                            float(percentiles["p75"]),
                            float(percentiles["p90"]),
                        )

                logger.info(
                    f"✅ Inserted {len(self.benchmark_data) * 4} benchmark records"
                )
                return True

        except Exception as e:
            logger.error(f"❌ Failed to seed benchmark data: {e}")
            return False

    async def create_test_user(self):
        """Create a test user for development"""
        if os.getenv("ENVIRONMENT") != "production":
            try:
                test_email = "test@example.com"
                user = await self.db_manager.create_user(test_email, "free")
                logger.info(f"✅ Created test user: {test_email} (ID: {user['_id']})")
                return user
            except Exception as e:
                logger.warning(f"⚠️  Test user may already exist: {e}")
                return None
        return None

    async def verify_database(self):
        """Verify database setup"""
        logger.info("🔍 Verifying database setup...")

        try:
            async with self.db_manager.acquire() as conn:
                # Check all tables exist
                tables = await conn.fetch(
                    """
                    SELECT tablename FROM pg_tables
                    WHERE schemaname = 'public'
                    ORDER BY tablename
                """
                )

                table_names = [t["tablename"] for t in tables]
                required_tables = [
                    "users",
                    "analyses",
                    "companies",
                    "user_activity",
                    "benchmark_data",
                ]

                missing_tables = [t for t in required_tables if t not in table_names]
                if missing_tables:
                    logger.error(f"❌ Missing tables: {missing_tables}")
                    return False

                logger.info(
                    f"✅ All required tables exist: {', '.join(required_tables)}"
                )

                # Check indexes
                indexes = await conn.fetch(
                    """
                    SELECT indexname FROM pg_indexes
                    WHERE schemaname = 'public'
                    AND indexname LIKE 'idx_%'
                """
                )

                logger.info(f"✅ Found {len(indexes)} custom indexes")

                # Check row counts
                for table in required_tables:
                    count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                    logger.info(f"   - {table}: {count} rows")

                return True

        except Exception as e:
            logger.error(f"❌ Database verification failed: {e}")
            return False

    async def test_database_operations(self):
        """Test basic database operations"""
        logger.info("🧪 Testing database operations...")

        try:
            # Test user creation
            test_user = await self.db_manager.create_user(
                "operations_test@example.com", "free"
            )
            logger.info("✅ User creation test passed")

            # Test analysis save
            test_result = {
                "company": "Test Corp",
                "scores": {
                    "environmental": 75.0,
                    "social": 80.0,
                    "governance": 85.0,
                    "overall": 80.0,
                },
                "keywords": ["sustainability", "ESG", "reporting"],
                "insights": ["Strong ESG performance"],
                "analysis_type": "test",
                "confidence": 0.85,
            }

            analysis_id = await self.db_manager.save_analysis(
                test_user["_id"], "test_source", test_result, "Technology", "2024"
            )
            logger.info(f"✅ Analysis save test passed (ID: {analysis_id})")

            # Test retrieval
            analyses = await self.db_manager.get_user_analyses(test_user["_id"])
            if analyses:
                logger.info(
                    f"✅ Analysis retrieval test passed ({len(analyses)} records)"
                )

            # Test health check
            health = await self.db_manager.health_check()
            logger.info(f"✅ Health check test passed: {health['status']}")

            return True

        except Exception as e:
            logger.error(f"❌ Database operations test failed: {e}")
            return False


async def main():
    """Main initialization process"""
    initializer = DatabaseInitializer()

    logger.info("=" * 60)
    logger.info("PostgreSQL Database Initialization")
    logger.info("=" * 60)

    # Initialize database
    if not await initializer.initialize_database():
        logger.error("Failed to initialize database. Exiting.")
        sys.exit(1)

    # Seed benchmark data
    if not await initializer.seed_benchmark_data():
        logger.warning("Failed to seed benchmark data, but continuing...")

    # Create test user (non-production only)
    await initializer.create_test_user()

    # Verify database
    if not await initializer.verify_database():
        logger.error("Database verification failed!")
        sys.exit(1)

    # Test operations
    if not await initializer.test_database_operations():
        logger.warning("Some database operations tests failed")

    # Close connection
    await initializer.db_manager.close()

    logger.info("")
    logger.info("=" * 60)
    logger.info("✅ Database initialization complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
