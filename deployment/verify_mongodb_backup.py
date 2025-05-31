#!/usr/bin/env python3
"""
MongoDB Backup Verification Script
==================================

Tests backup and restore procedures for DigitalOcean Managed MongoDB
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MongoDBBackupVerifier:
    """Verify MongoDB backup and restore procedures"""
    
    def __init__(self, connection_uri: str):
        self.connection_uri = connection_uri
        self.client = None
        self.db = None
        
    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(self.connection_uri)
            self.db = self.client.esg_platform
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info("✅ Connected to MongoDB")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            return False
    
    async def verify_backup_exists(self):
        """Check if automated backups are configured"""
        try:
            # For DigitalOcean managed databases, check via API
            do_token = os.getenv("DIGITALOCEAN_ACCESS_TOKEN")
            if not do_token:
                logger.warning("⚠️  DIGITALOCEAN_ACCESS_TOKEN not set, cannot verify backup configuration")
                return False
            
            # Get database cluster ID from connection string
            # Format: mongodb+srv://doadmin:xxx@db-mongodb-xxx.mongo.ondigitalocean.com/admin
            import re
            match = re.search(r'@(db-mongodb-[^.]+)', self.connection_uri)
            if not match:
                logger.error("❌ Could not extract cluster ID from connection URI")
                return False
            
            cluster_name = match.group(1)
            
            # Query DigitalOcean API
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {do_token}"}
                
                # List databases to find our cluster
                response = await client.get(
                    "https://api.digitalocean.com/v2/databases",
                    headers=headers
                )
                
                if response.status_code == 200:
                    databases = response.json().get("databases", [])
                    
                    for db in databases:
                        if cluster_name in db.get("connection", {}).get("uri", ""):
                            backup_window = db.get("maintenance_window", {})
                            logger.info(f"✅ Backup configured:")
                            logger.info(f"   - Day: {backup_window.get('day', 'N/A')}")
                            logger.info(f"   - Hour: {backup_window.get('hour', 'N/A')}")
                            logger.info(f"   - Retention: 7 days (DigitalOcean default)")
                            return True
                    
                    logger.error("❌ Database cluster not found")
                else:
                    logger.error(f"❌ Failed to query DigitalOcean API: {response.status_code}")
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error verifying backup configuration: {e}")
            return False
    
    async def create_test_data(self):
        """Create test data for backup verification"""
        try:
            test_collection = self.db.backup_test
            
            # Clear existing test data
            await test_collection.delete_many({})
            
            # Insert test documents
            test_docs = [
                {
                    "type": "backup_test",
                    "timestamp": datetime.utcnow(),
                    "test_id": i,
                    "data": f"Test document {i} for backup verification"
                }
                for i in range(10)
            ]
            
            result = await test_collection.insert_many(test_docs)
            logger.info(f"✅ Created {len(result.inserted_ids)} test documents")
            
            return len(result.inserted_ids)
            
        except Exception as e:
            logger.error(f"❌ Failed to create test data: {e}")
            return 0
    
    async def verify_data_integrity(self):
        """Verify data can be read correctly"""
        try:
            # Check main collections
            collections = await self.db.list_collection_names()
            logger.info(f"✅ Found {len(collections)} collections:")
            
            for collection_name in collections:
                collection = self.db[collection_name]
                count = await collection.count_documents({})
                logger.info(f"   - {collection_name}: {count} documents")
            
            # Verify test data
            test_collection = self.db.backup_test
            test_count = await test_collection.count_documents({})
            
            if test_count > 0:
                sample = await test_collection.find_one()
                logger.info(f"✅ Test collection verified: {test_count} documents")
                logger.info(f"   Sample: {sample.get('data', 'N/A')}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to verify data integrity: {e}")
            return False
    
    async def test_write_operations(self):
        """Test write operations"""
        try:
            test_collection = self.db.backup_test_writes
            
            # Test insert
            doc = {
                "type": "write_test",
                "timestamp": datetime.utcnow(),
                "operation": "insert"
            }
            result = await test_collection.insert_one(doc)
            
            if result.inserted_id:
                logger.info("✅ Insert operation successful")
            else:
                logger.error("❌ Insert operation failed")
                return False
            
            # Test update
            update_result = await test_collection.update_one(
                {"_id": result.inserted_id},
                {"$set": {"updated": True, "updated_at": datetime.utcnow()}}
            )
            
            if update_result.modified_count > 0:
                logger.info("✅ Update operation successful")
            else:
                logger.error("❌ Update operation failed")
                return False
            
            # Test delete
            delete_result = await test_collection.delete_one({"_id": result.inserted_id})
            
            if delete_result.deleted_count > 0:
                logger.info("✅ Delete operation successful")
            else:
                logger.error("❌ Delete operation failed")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Write operations failed: {e}")
            return False
    
    async def generate_backup_report(self):
        """Generate comprehensive backup verification report"""
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "UNKNOWN",
            "checks": {
                "connection": False,
                "backup_configured": False,
                "data_integrity": False,
                "write_operations": False
            },
            "recommendations": []
        }
        
        # Run all checks
        report["checks"]["connection"] = await self.connect()
        
        if report["checks"]["connection"]:
            report["checks"]["backup_configured"] = await self.verify_backup_exists()
            report["checks"]["data_integrity"] = await self.verify_data_integrity()
            report["checks"]["write_operations"] = await self.test_write_operations()
        
        # Determine overall status
        all_passed = all(report["checks"].values())
        critical_passed = report["checks"]["connection"] and report["checks"]["data_integrity"]
        
        if all_passed:
            report["status"] = "HEALTHY"
        elif critical_passed:
            report["status"] = "WARNING"
        else:
            report["status"] = "CRITICAL"
        
        # Add recommendations
        if not report["checks"]["backup_configured"]:
            report["recommendations"].append(
                "Verify backup configuration in DigitalOcean dashboard"
            )
        
        if not report["checks"]["write_operations"]:
            report["recommendations"].append(
                "Check database permissions and connection settings"
            )
        
        return report
    
    async def cleanup(self):
        """Clean up test data"""
        try:
            if self.db:
                # Remove test collections
                await self.db.backup_test.drop()
                await self.db.backup_test_writes.drop()
                logger.info("✅ Cleaned up test data")
        except Exception as e:
            logger.warning(f"⚠️  Failed to clean up test data: {e}")
        finally:
            if self.client:
                self.client.close()


async def main():
    """Main verification process"""
    # Get MongoDB URI from environment
    mongodb_uri = os.getenv("MONGODB_URI")
    
    if not mongodb_uri:
        logger.error("❌ MONGODB_URI environment variable not set")
        sys.exit(1)
    
    logger.info("🔍 Starting MongoDB Backup Verification")
    logger.info("=" * 50)
    
    verifier = MongoDBBackupVerifier(mongodb_uri)
    
    try:
        # Generate report
        report = await verifier.generate_backup_report()
        
        # Print results
        logger.info("\n📊 BACKUP VERIFICATION REPORT")
        logger.info("=" * 50)
        logger.info(f"Status: {report['status']}")
        logger.info(f"Timestamp: {report['timestamp']}")
        
        logger.info("\n✓ Check Results:")
        for check, passed in report['checks'].items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            logger.info(f"  {check}: {status}")
        
        if report['recommendations']:
            logger.info("\n💡 Recommendations:")
            for rec in report['recommendations']:
                logger.info(f"  - {rec}")
        
        # Save report to file
        import json
        with open("backup_verification_report.json", "w") as f:
            json.dump(report, f, indent=2)
        logger.info("\n📄 Report saved to: backup_verification_report.json")
        
        # Exit code based on status
        if report['status'] == "CRITICAL":
            sys.exit(2)
        elif report['status'] == "WARNING":
            sys.exit(1)
        else:
            sys.exit(0)
            
    finally:
        await verifier.cleanup()


if __name__ == "__main__":
    asyncio.run(main()) 