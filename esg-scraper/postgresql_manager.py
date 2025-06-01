"""
PostgreSQL Manager for ESG Intelligence Platform
===============================================

Provides async PostgreSQL operations with:
- Connection pooling
- Retry logic
- Error handling
- Query optimization
- Schema management
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import asyncio
from functools import wraps
from contextlib import asynccontextmanager

import asyncpg
from asyncpg.exceptions import PostgresError

logger = logging.getLogger(__name__)


def with_retry(retries: int = 3, delay: float = 1.0):
    """Decorator for retrying database operations"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(retries):
                try:
                    return await func(*args, **kwargs)
                except PostgresError as e:
                    last_error = e
                    if attempt < retries - 1:
                        await asyncio.sleep(delay * (attempt + 1))
                        logger.warning(
                            f"Retry {attempt + 1}/{retries} for {func.__name__}: {e}"
                        )
                    else:
                        logger.error(f"Failed after {retries} attempts: {e}")
            raise last_error

        return wrapper

    return decorator


class PostgreSQLManager:
    """Async PostgreSQL manager with connection pooling and optimization"""

    def __init__(self, connection_string: str = None):
        """Initialize PostgreSQL connection with optimal settings"""
        # Parse connection string from environment
        if connection_string:
            self.connection_string = connection_string
        else:
            # Build connection string from components
            pg_password = os.getenv("PGPASSWORD", "")
            pg_user = os.getenv("PGUSER", "doadmin")
            pg_host = os.getenv("PGHOST", "localhost")
            pg_port = os.getenv("PGPORT", "25060")
            pg_database = os.getenv("PGDATABASE", "defaultdb")
            pg_sslmode = os.getenv("PGSSLMODE", "require")

            self.connection_string = (
                f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_database}"
                f"?sslmode={pg_sslmode}"
            )

        # Connection pool settings
        self.max_pool_size = int(os.getenv("PG_POOL_SIZE", "50"))
        self.min_pool_size = int(os.getenv("PG_MIN_POOL_SIZE", "5"))

        self.pool = None

    async def initialize(self):
        """Initialize connection pool and create tables"""
        try:
            self.pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=self.min_pool_size,
                max_size=self.max_pool_size,
                command_timeout=10,
                ssl="require",
            )

            # Create tables if they don't exist
            await self._create_tables()
            logger.info("PostgreSQL connection pool initialized")

        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL: {e}")
            raise

    async def _create_tables(self):
        """Create database tables if they don't exist"""
        async with self.pool.acquire() as conn:
            # Enable UUID extension
            await conn.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

            # Users table
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    email VARCHAR(255) UNIQUE NOT NULL,
                    tier VARCHAR(50) DEFAULT 'free',
                    credits INTEGER DEFAULT 100,
                    stripe_customer_id VARCHAR(255),
                    stripe_subscription_id VARCHAR(255),
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    last_login TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
            """
            )

            # Companies table
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS companies (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    company_name VARCHAR(255) UNIQUE NOT NULL,
                    industry_sector VARCHAR(100),
                    stock_symbol VARCHAR(20),
                    latest_scores JSONB,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
            """
            )

            # Analyses table
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS analyses (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                    source_url TEXT,
                    company_name VARCHAR(255),
                    environmental_score DECIMAL(5,2),
                    social_score DECIMAL(5,2),
                    governance_score DECIMAL(5,2),
                    overall_score DECIMAL(5,2),
                    keywords TEXT[],
                    insights TEXT[],
                    analysis_type VARCHAR(50),
                    industry_sector VARCHAR(100),
                    reporting_period VARCHAR(50),
                    confidence DECIMAL(3,2),
                    sentiment JSONB,
                    framework_coverage JSONB,
                    extracted_metrics JSONB,
                    gap_analysis JSONB,
                    requirement_findings JSONB,
                    recommendations TEXT[],
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
            """
            )

            # User activity table
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_activity (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                    activity_type VARCHAR(50),
                    resource_id VARCHAR(255),
                    metadata JSONB,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """
            )

            # Benchmark data table
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS benchmark_data (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    industry_sector VARCHAR(100),
                    framework VARCHAR(50),
                    percentile_50 DECIMAL(5,2),
                    percentile_75 DECIMAL(5,2),
                    percentile_90 DECIMAL(5,2),
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
            """
            )

            # Create indexes
            await self._create_indexes(conn)

    async def _create_indexes(self, conn):
        """Create database indexes for performance"""
        # Analyses indexes
        await conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_analyses_user_created
            ON analyses(user_id, created_at DESC)
        """
        )
        await conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_analyses_company_created
            ON analyses(company_name, created_at DESC)
        """
        )
        await conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_analyses_sector_score
            ON analyses(industry_sector, overall_score DESC)
        """
        )

        # User activity indexes
        await conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_activity_user_created
            ON user_activity(user_id, created_at DESC)
        """
        )
        await conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_activity_type
            ON user_activity(activity_type)
        """
        )

        # Companies indexes
        await conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_companies_sector
            ON companies(industry_sector)
        """
        )

        logger.info("PostgreSQL indexes created successfully")

    @asynccontextmanager
    async def acquire(self):
        """Acquire a connection from the pool"""
        async with self.pool.acquire() as conn:
            yield conn

    @with_retry()
    async def save_analysis(
        self,
        user_id: str,
        source: str,
        result: Dict[str, Any],
        industry_sector: str = None,
        reporting_period: str = None,
    ) -> str:
        """Save analysis with all framework data"""
        try:
            async with self.acquire() as conn:
                # Insert analysis record
                analysis_id = await conn.fetchval(
                    """
                    INSERT INTO analyses (
                        user_id, source_url, company_name,
                        environmental_score, social_score, governance_score, overall_score,
                        keywords, insights, analysis_type,
                        industry_sector, reporting_period, confidence, sentiment,
                        framework_coverage, extracted_metrics, gap_analysis,
                        requirement_findings, recommendations
                    ) VALUES (
                        $1::uuid, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14,
                        $15, $16, $17, $18, $19
                    ) RETURNING id
                """,
                    user_id,
                    source,
                    result.get("company"),
                    result["scores"].get("environmental", 0),
                    result["scores"].get("social", 0),
                    result["scores"].get("governance", 0),
                    result["scores"].get("overall", 0),
                    result.get("keywords", []),
                    result.get("insights", []),
                    result.get("analysis_type", "unknown"),
                    industry_sector,
                    reporting_period,
                    result.get("confidence", 0.7),
                    (
                        json.dumps(result.get("sentiment"))
                        if result.get("sentiment")
                        else None
                    ),
                    (
                        json.dumps(result.get("framework_coverage"))
                        if result.get("framework_coverage")
                        else None
                    ),
                    (
                        json.dumps(result.get("extracted_metrics"))
                        if result.get("extracted_metrics")
                        else None
                    ),
                    (
                        json.dumps(result.get("gap_analysis"))
                        if result.get("gap_analysis")
                        else None
                    ),
                    (
                        json.dumps(result.get("requirement_findings"))
                        if result.get("requirement_findings")
                        else None
                    ),
                    result.get("recommendations", []),
                )

                # Update company profile if needed
                if result.get("company") and industry_sector:
                    await self._update_company_profile(
                        conn, result["company"], industry_sector, result["scores"]
                    )

                # Log user activity
                await self._log_activity(
                    conn,
                    user_id,
                    "analysis",
                    str(analysis_id),
                    {"source": source, "company": result.get("company")},
                )

                return str(analysis_id)

        except Exception as e:
            logger.error(f"Error saving analysis: {e}")
            raise

    @with_retry()
    async def get_user_analyses(
        self, user_id: str, limit: int = 10, skip: int = 0, company_name: str = None
    ) -> List[Dict[str, Any]]:
        """Get user analyses with pagination"""
        try:
            async with self.acquire() as conn:
                query = """
                    SELECT
                        id, company_name,
                        environmental_score, social_score, governance_score, overall_score,
                        analysis_type, created_at, source_url, framework_coverage
                    FROM analyses
                    WHERE user_id = $1::uuid
                """
                params = [user_id]

                if company_name:
                    query += " AND company_name = $2"
                    params.append(company_name)

                query += " ORDER BY created_at DESC LIMIT $%d OFFSET $%d" % (
                    len(params) + 1,
                    len(params) + 2,
                )
                params.extend([limit, skip])

                rows = await conn.fetch(query, *params)

                analyses = []
                for row in rows:
                    analysis = dict(row)
                    analysis["_id"] = str(analysis.pop("id"))
                    analysis["scores"] = {
                        "environmental": float(analysis.pop("environmental_score", 0)),
                        "social": float(analysis.pop("social_score", 0)),
                        "governance": float(analysis.pop("governance_score", 0)),
                        "overall": float(analysis.pop("overall_score", 0)),
                    }
                    if analysis.get("framework_coverage"):
                        analysis["framework_coverage"] = json.loads(
                            analysis["framework_coverage"]
                        )
                    analyses.append(analysis)

                return analyses

        except Exception as e:
            logger.error(f"Error getting user analyses: {e}")
            raise

    @with_retry()
    async def get_company_history(
        self, company_name: str, days: int = 90
    ) -> List[Dict[str, Any]]:
        """Get company ESG history"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            async with self.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT
                        id, created_at as analysis_date,
                        environmental_score, social_score, governance_score, overall_score,
                        framework_coverage, analysis_type
                    FROM analyses
                    WHERE company_name = $1 AND created_at >= $2
                    ORDER BY created_at DESC
                """,
                    company_name,
                    cutoff_date,
                )

                history = []
                for row in rows:
                    record = dict(row)
                    record["_id"] = str(record.pop("id"))
                    record["scores"] = {
                        "environmental": float(record.pop("environmental_score", 0)),
                        "social": float(record.pop("social_score", 0)),
                        "governance": float(record.pop("governance_score", 0)),
                        "overall": float(record.pop("overall_score", 0)),
                    }
                    if record.get("framework_coverage"):
                        record["framework_coverage"] = json.loads(
                            record["framework_coverage"]
                        )
                    history.append(record)

                return history

        except Exception as e:
            logger.error(f"Error getting company history: {e}")
            raise

    @with_retry()
    async def get_framework_gaps(
        self, analysis_id: str, user_id: str
    ) -> List[Dict[str, Any]]:
        """Get gap analysis for specific analysis"""
        try:
            async with self.acquire() as conn:
                gap_analysis = await conn.fetchval(
                    """
                    SELECT gap_analysis
                    FROM analyses
                    WHERE id = $1::uuid AND user_id = $2::uuid
                """,
                    analysis_id,
                    user_id,
                )

                if gap_analysis:
                    return json.loads(gap_analysis)
                return []

        except Exception as e:
            logger.error(f"Error getting framework gaps: {e}")
            raise

    @with_retry()
    async def create_user(self, email: str, tier: str = "free") -> Dict[str, Any]:
        """Create new user"""
        try:
            async with self.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO users (email, tier, credits)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (email) DO UPDATE
                    SET last_login = NOW()
                    RETURNING id, email, tier, credits, created_at, last_login
                """,
                    email,
                    tier,
                    100 if tier == "free" else 1000,
                )

                user = dict(row)
                user["_id"] = str(user.pop("id"))
                return user

        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise

    @with_retry()
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            async with self.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT id, email, tier, credits, stripe_customer_id,
                           stripe_subscription_id, created_at, last_login
                    FROM users
                    WHERE id = $1::uuid
                """,
                    user_id,
                )

                if row:
                    user = dict(row)
                    user["_id"] = str(user.pop("id"))
                    return user
                return None

        except Exception as e:
            logger.error(f"Error getting user: {e}")
            raise

    @with_retry()
    async def update_user_subscription(
        self,
        user_id: str,
        tier: str,
        credits: int,
        stripe_customer_id: str = None,
        stripe_subscription_id: str = None,
    ) -> bool:
        """Update user subscription"""
        try:
            async with self.acquire() as conn:
                query = """
                    UPDATE users
                    SET tier = $2, credits = $3, updated_at = NOW()
                """
                params = [user_id, tier, credits]

                if stripe_customer_id:
                    query += ", stripe_customer_id = $4"
                    params.append(stripe_customer_id)

                if stripe_subscription_id:
                    query += f", stripe_subscription_id = ${len(params) + 1}"
                    params.append(stripe_subscription_id)

                query += " WHERE id = $1::uuid"

                result = await conn.execute(query, *params)
                return result.split()[-1] != "0"

        except Exception as e:
            logger.error(f"Error updating subscription: {e}")
            raise

    @with_retry()
    async def get_benchmark_data(
        self, industry_sector: str, framework: str
    ) -> List[Dict[str, Any]]:
        """Get benchmark data for industry and framework"""
        try:
            async with self.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT id, industry_sector, framework,
                           percentile_50, percentile_75, percentile_90
                    FROM benchmark_data
                    WHERE industry_sector = $1 AND framework = $2
                """,
                    industry_sector,
                    framework,
                )

                benchmarks = []
                for row in rows:
                    benchmark = dict(row)
                    benchmark["_id"] = str(benchmark.pop("id"))
                    benchmarks.append(benchmark)

                return benchmarks

        except Exception as e:
            logger.error(f"Error getting benchmark data: {e}")
            raise

    async def _update_company_profile(
        self,
        conn,
        company_name: str,
        industry_sector: str,
        latest_scores: Dict[str, float],
    ):
        """Update or create company profile"""
        try:
            await conn.execute(
                """
                INSERT INTO companies (company_name, industry_sector, latest_scores)
                VALUES ($1, $2, $3)
                ON CONFLICT (company_name) DO UPDATE
                SET industry_sector = $2, latest_scores = $3, updated_at = NOW()
            """,
                company_name,
                industry_sector,
                json.dumps(latest_scores),
            )
        except Exception as e:
            logger.warning(f"Error updating company profile: {e}")

    async def _log_activity(
        self,
        conn,
        user_id: str,
        activity_type: str,
        resource_id: str = None,
        metadata: Dict[str, Any] = None,
    ):
        """Log user activity"""
        try:
            await conn.execute(
                """
                INSERT INTO user_activity (user_id, activity_type, resource_id, metadata)
                VALUES ($1::uuid, $2, $3, $4)
            """,
                user_id,
                activity_type,
                resource_id,
                json.dumps(metadata) if metadata else None,
            )
        except Exception as e:
            logger.warning(f"Error logging activity: {e}")

    async def health_check(self) -> Dict[str, Any]:
        """Check PostgreSQL connection health"""
        try:
            async with self.acquire() as conn:
                # Test connection
                version = await conn.fetchval("SELECT version()")

                # Get connection stats
                stats = await conn.fetchrow(
                    """
                    SELECT
                        count(*) as active_connections,
                        max_connections
                    FROM pg_stat_activity, pg_settings
                    WHERE name = 'max_connections'
                    GROUP BY max_connections
                """
                )

                return {
                    "status": "healthy",
                    "version": version.split()[1] if version else "unknown",
                    "connections": (
                        {
                            "current": stats["active_connections"] if stats else 0,
                            "available": stats["max_connections"] if stats else 0,
                        }
                        if stats
                        else {}
                    ),
                }
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    async def close(self):
        """Close PostgreSQL connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("PostgreSQL connection pool closed")


# Create singleton instance
_postgresql_manager = None


def get_postgresql_manager() -> PostgreSQLManager:
    """Get or create PostgreSQL manager instance"""
    global _postgresql_manager
    if _postgresql_manager is None:
        _postgresql_manager = PostgreSQLManager()
    return _postgresql_manager
