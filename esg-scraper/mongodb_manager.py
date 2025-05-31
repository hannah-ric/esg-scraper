"""
MongoDB Manager for ESG Intelligence Platform
============================================

Provides async MongoDB operations with:
- Connection pooling
- Retry logic
- Error handling
- Query optimization
- Index management
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

import motor.motor_asyncio
from pymongo import ASCENDING, DESCENDING, IndexModel
from pymongo.errors import ConnectionFailure, OperationFailure, DuplicateKeyError
import asyncio
from functools import wraps

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
                except (ConnectionFailure, OperationFailure) as e:
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


class MongoDBManager:
    """Async MongoDB manager with connection pooling and optimization"""

    def __init__(self, connection_string: str = None):
        """Initialize MongoDB connection with optimal settings"""
        # Get connection string from environment or parameter
        self.connection_string = connection_string or os.getenv(
            "MONGODB_URI", "mongodb://localhost:27017/esg_scraper"
        )

        # Parse database name from connection string
        self.db_name = os.getenv("MONGODB_DATABASE", "admin")

        # Connection pool settings
        self.max_pool_size = int(os.getenv("MONGODB_POOL_SIZE", "100"))
        self.min_pool_size = int(os.getenv("MONGODB_MIN_POOL_SIZE", "10"))

        # Initialize async client with optimized settings
        self.client = motor.motor_asyncio.AsyncIOMotorClient(
            self.connection_string,
            maxPoolSize=self.max_pool_size,
            minPoolSize=self.min_pool_size,
            connectTimeoutMS=5000,
            serverSelectionTimeoutMS=5000,
            retryWrites=True,
            w="majority",
        )

        self.db = self.client[self.db_name]

        # Collections
        self.analyses = self.db.analyses
        self.users = self.db.users
        self.companies = self.db.companies
        self.user_activity = self.db.user_activity
        self.benchmark_data = self.db.benchmark_data

        # Initialize indexes on startup
        asyncio.create_task(self._create_indexes())

    async def _create_indexes(self):
        """Create optimized indexes for common queries"""
        try:
            # Analyses indexes
            await self.analyses.create_indexes(
                [
                    IndexModel([("user_id", ASCENDING), ("created_at", DESCENDING)]),
                    IndexModel(
                        [("company_name", ASCENDING), ("created_at", DESCENDING)]
                    ),
                    IndexModel(
                        [("industry_sector", ASCENDING), ("overall_score", DESCENDING)]
                    ),
                    IndexModel([("created_at", DESCENDING)]),
                    IndexModel(
                        [("_id", ASCENDING), ("user_id", ASCENDING)]
                    ),  # Compound for security
                ]
            )

            # Users indexes
            await self.users.create_indexes(
                [
                    IndexModel([("email", ASCENDING)], unique=True),
                    IndexModel([("stripe_customer_id", ASCENDING)], sparse=True),
                ]
            )

            # Companies indexes
            await self.companies.create_indexes(
                [
                    IndexModel([("company_name", ASCENDING)], unique=True),
                    IndexModel([("industry_sector", ASCENDING)]),
                    IndexModel([("stock_symbol", ASCENDING)], sparse=True),
                ]
            )

            # User activity indexes
            await self.user_activity.create_indexes(
                [
                    IndexModel([("user_id", ASCENDING), ("created_at", DESCENDING)]),
                    IndexModel([("activity_type", ASCENDING)]),
                ]
            )

            logger.info("MongoDB indexes created successfully")

        except Exception as e:
            logger.error(f"Error creating indexes: {e}")

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
            # Prepare document with embedded data
            doc = {
                "user_id": user_id,
                "source_url": source,
                "company_name": result.get("company"),
                "scores": {
                    "environmental": result["scores"].get("environmental", 0),
                    "social": result["scores"].get("social", 0),
                    "governance": result["scores"].get("governance", 0),
                    "overall": result["scores"].get("overall", 0),
                },
                "keywords": result.get("keywords", []),
                "insights": result.get("insights", []),
                "analysis_type": result.get("analysis_type", "unknown"),
                "industry_sector": industry_sector,
                "reporting_period": reporting_period,
                "confidence": result.get("confidence", 0.7),
                "sentiment": result.get("sentiment"),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }

            # Add framework data if present
            if result.get("framework_coverage"):
                doc["framework_coverage"] = result["framework_coverage"]

            if result.get("extracted_metrics"):
                doc["extracted_metrics"] = result["extracted_metrics"]

            if result.get("gap_analysis"):
                doc["gap_analysis"] = result["gap_analysis"]

            if result.get("requirement_findings"):
                doc["requirement_findings"] = result["requirement_findings"]

            if result.get("recommendations"):
                doc["recommendations"] = result["recommendations"]

            # Insert document
            result = await self.analyses.insert_one(doc)
            analysis_id = str(result.inserted_id)

            # Update company profile if needed
            if doc["company_name"] and industry_sector:
                await self._update_company_profile(
                    doc["company_name"], industry_sector, doc["scores"]
                )

            # Log user activity
            await self._log_activity(
                user_id,
                "analysis",
                analysis_id,
                {"source": source, "company": doc["company_name"]},
            )

            return analysis_id

        except Exception as e:
            logger.error(f"Error saving analysis: {e}")
            raise

    @with_retry()
    async def get_user_analyses(
        self, user_id: str, limit: int = 10, skip: int = 0, company_name: str = None
    ) -> List[Dict[str, Any]]:
        """Get user analyses with pagination"""
        try:
            # Build query
            query = {"user_id": user_id}
            if company_name:
                query["company_name"] = company_name

            # Execute query with projection for performance
            cursor = (
                self.analyses.find(
                    query,
                    {
                        "_id": 1,
                        "company_name": 1,
                        "scores": 1,
                        "analysis_type": 1,
                        "created_at": 1,
                        "source_url": 1,
                        "framework_coverage": 1,
                    },
                )
                .sort("created_at", -1)
                .skip(skip)
                .limit(limit)
            )

            # Convert to list
            analyses = []
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])
                analyses.append(doc)

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

            # Aggregation pipeline for efficient querying
            pipeline = [
                {
                    "$match": {
                        "company_name": company_name,
                        "created_at": {"$gte": cutoff_date},
                    }
                },
                {
                    "$project": {
                        "analysis_date": "$created_at",
                        "scores": 1,
                        "framework_coverage": 1,
                        "analysis_type": 1,
                    }
                },
                {"$sort": {"analysis_date": -1}},
            ]

            cursor = self.analyses.aggregate(pipeline)
            history = []
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])
                history.append(doc)

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
            # Security check - ensure user owns the analysis
            analysis = await self.analyses.find_one(
                {"_id": analysis_id, "user_id": user_id}, {"gap_analysis": 1}
            )

            if not analysis:
                return []

            return analysis.get("gap_analysis", [])

        except Exception as e:
            logger.error(f"Error getting framework gaps: {e}")
            raise

    @with_retry()
    async def create_user(self, email: str, tier: str = "free") -> Dict[str, Any]:
        """Create new user"""
        try:
            user_doc = {
                "email": email,
                "tier": tier,
                "credits": 100 if tier == "free" else 1000,
                "created_at": datetime.utcnow(),
                "last_login": datetime.utcnow(),
            }

            result = await self.users.insert_one(user_doc)
            user_doc["_id"] = str(result.inserted_id)

            return user_doc

        except DuplicateKeyError:
            # User already exists
            existing = await self.users.find_one({"email": email})
            existing["_id"] = str(existing["_id"])
            return existing
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise

    @with_retry()
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            user = await self.users.find_one({"_id": user_id})
            if user:
                user["_id"] = str(user["_id"])
            return user
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
            update_doc = {
                "$set": {
                    "tier": tier,
                    "credits": credits,
                    "updated_at": datetime.utcnow(),
                }
            }

            if stripe_customer_id:
                update_doc["$set"]["stripe_customer_id"] = stripe_customer_id

            if stripe_subscription_id:
                update_doc["$set"]["stripe_subscription_id"] = stripe_subscription_id

            result = await self.users.update_one({"_id": user_id}, update_doc)

            return result.modified_count > 0

        except Exception as e:
            logger.error(f"Error updating subscription: {e}")
            raise

    @with_retry()
    async def get_benchmark_data(
        self, industry_sector: str, framework: str
    ) -> List[Dict[str, Any]]:
        """Get benchmark data for industry and framework"""
        try:
            cursor = self.benchmark_data.find(
                {"industry_sector": industry_sector, "framework": framework}
            )

            benchmarks = []
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])
                benchmarks.append(doc)

            return benchmarks

        except Exception as e:
            logger.error(f"Error getting benchmark data: {e}")
            raise

    async def _update_company_profile(
        self, company_name: str, industry_sector: str, latest_scores: Dict[str, float]
    ):
        """Update or create company profile"""
        try:
            await self.companies.update_one(
                {"company_name": company_name},
                {
                    "$set": {
                        "industry_sector": industry_sector,
                        "latest_scores": latest_scores,
                        "updated_at": datetime.utcnow(),
                    },
                    "$setOnInsert": {"created_at": datetime.utcnow()},
                },
                upsert=True,
            )
        except Exception as e:
            logger.warning(f"Error updating company profile: {e}")

    async def _log_activity(
        self,
        user_id: str,
        activity_type: str,
        resource_id: str = None,
        metadata: Dict[str, Any] = None,
    ):
        """Log user activity"""
        try:
            await self.user_activity.insert_one(
                {
                    "user_id": user_id,
                    "activity_type": activity_type,
                    "resource_id": resource_id,
                    "metadata": metadata or {},
                    "created_at": datetime.utcnow(),
                }
            )
        except Exception as e:
            logger.warning(f"Error logging activity: {e}")

    async def health_check(self) -> Dict[str, Any]:
        """Check MongoDB connection health"""
        try:
            # Ping the server
            await self.client.admin.command("ping")

            # Get server info
            info = await self.client.server_info()

            return {
                "status": "healthy",
                "version": info.get("version"),
                "uptime": info.get("uptime"),
                "connections": {
                    "current": info.get("connections", {}).get("current"),
                    "available": info.get("connections", {}).get("available"),
                },
            }
        except Exception as e:
            logger.error(f"MongoDB health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    async def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")


# Create singleton instance
_mongodb_manager = None


def get_mongodb_manager() -> MongoDBManager:
    """Get or create MongoDB manager instance"""
    global _mongodb_manager
    if _mongodb_manager is None:
        _mongodb_manager = MongoDBManager()
    return _mongodb_manager
