#!/usr/bin/env python3
"""
Redis Migration Script
======================

Migrates data from local to managed Redis
"""

import os
import sys
import redis
import ssl
import logging
import json
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RedisMigrator:
    """Migrate Redis data from local to managed instance"""
    
    def __init__(self, source_url: str, target_url: str):
        self.source_url = source_url
        self.target_url = target_url
        self.source_client = None
        self.target_client = None
        self.migration_stats = {
            "keys_scanned": 0,
            "keys_migrated": 0,
            "keys_failed": 0,
            "data_size_bytes": 0
        }
    
    def connect_source(self):
        """Connect to source Redis (local)"""
        try:
            self.source_client = redis.from_url(
                self.source_url,
                decode_responses=True
            )
            self.source_client.ping()
            logger.info(f"✅ Connected to source Redis: {self.source_url}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to source Redis: {e}")
            return False
    
    def connect_target(self):
        """Connect to target Redis (managed with SSL)"""
        try:
            if self.target_url.startswith('rediss://'):
                # Managed Redis with SSL
                # Check if it's Upstash (they use self-signed certs)
                if 'upstash.io' in self.target_url:
                    self.target_client = redis.from_url(
                        self.target_url,
                        decode_responses=True,
                        ssl_cert_reqs=ssl.CERT_NONE  # Upstash uses self-signed certs
                    )
                else:
                    self.target_client = redis.from_url(
                        self.target_url,
                        decode_responses=True,
                        ssl_cert_reqs=ssl.CERT_REQUIRED,
                        ssl_ca_certs=ssl.get_default_verify_paths().cafile
                    )
            else:
                # Regular Redis without SSL (for testing)
                self.target_client = redis.from_url(
                    self.target_url,
                    decode_responses=True
                )
            
            self.target_client.ping()
            logger.info(f"✅ Connected to target Redis: {self.target_url}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to target Redis: {e}")
            return False
    
    def analyze_source(self) -> Dict[str, Any]:
        """Analyze source Redis data"""
        try:
            info = self.source_client.info()
            dbsize = self.source_client.dbsize()
            
            # Sample keys to understand patterns
            sample_keys = []
            for key in self.source_client.scan_iter(count=100):
                sample_keys.append(key)
                if len(sample_keys) >= 20:
                    break
            
            # Analyze key patterns
            patterns = {}
            for key in sample_keys:
                prefix = key.split(':')[0] if ':' in key else 'no_prefix'
                patterns[prefix] = patterns.get(prefix, 0) + 1
            
            analysis = {
                "total_keys": dbsize,
                "memory_used_mb": info.get('used_memory', 0) / 1024 / 1024,
                "memory_peak_mb": info.get('used_memory_peak', 0) / 1024 / 1024,
                "key_patterns": patterns,
                "sample_keys": sample_keys[:10]
            }
            
            logger.info(f"📊 Source Redis Analysis:")
            logger.info(f"   - Total keys: {analysis['total_keys']}")
            logger.info(f"   - Memory used: {analysis['memory_used_mb']:.2f} MB")
            logger.info(f"   - Key patterns: {analysis['key_patterns']}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Failed to analyze source: {e}")
            return {}
    
    def migrate_key(self, key: str) -> bool:
        """Migrate a single key"""
        try:
            # Get key type
            key_type = self.source_client.type(key)
            
            # Get TTL
            ttl = self.source_client.ttl(key)
            
            # Migrate based on type
            if key_type == 'string':
                value = self.source_client.get(key)
                self.target_client.set(key, value)
                if ttl > 0:
                    self.target_client.expire(key, ttl)
                    
            elif key_type == 'hash':
                value = self.source_client.hgetall(key)
                if value:
                    self.target_client.hset(key, mapping=value)
                    if ttl > 0:
                        self.target_client.expire(key, ttl)
                        
            elif key_type == 'list':
                values = self.source_client.lrange(key, 0, -1)
                if values:
                    self.target_client.rpush(key, *values)
                    if ttl > 0:
                        self.target_client.expire(key, ttl)
                        
            elif key_type == 'set':
                values = self.source_client.smembers(key)
                if values:
                    self.target_client.sadd(key, *values)
                    if ttl > 0:
                        self.target_client.expire(key, ttl)
                        
            elif key_type == 'zset':
                values = self.source_client.zrange(key, 0, -1, withscores=True)
                if values:
                    self.target_client.zadd(key, {v: s for v, s in values})
                    if ttl > 0:
                        self.target_client.expire(key, ttl)
            
            else:
                logger.warning(f"⚠️  Unknown key type '{key_type}' for key: {key}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to migrate key '{key}': {e}")
            return False
    
    def migrate_data(self, batch_size: int = 100) -> Dict[str, Any]:
        """Migrate all data in batches"""
        logger.info("🚀 Starting data migration...")
        
        batch = []
        
        for key in self.source_client.scan_iter():
            self.migration_stats["keys_scanned"] += 1
            batch.append(key)
            
            # Process batch
            if len(batch) >= batch_size:
                self._process_batch(batch)
                batch = []
            
            # Progress update every 1000 keys
            if self.migration_stats["keys_scanned"] % 1000 == 0:
                logger.info(
                    f"   Progress: {self.migration_stats['keys_scanned']} scanned, "
                    f"{self.migration_stats['keys_migrated']} migrated"
                )
        
        # Process remaining keys
        if batch:
            self._process_batch(batch)
        
        return self.migration_stats
    
    def _process_batch(self, batch: List[str]):
        """Process a batch of keys"""
        for key in batch:
            if self.migrate_key(key):
                self.migration_stats["keys_migrated"] += 1
            else:
                self.migration_stats["keys_failed"] += 1
    
    def verify_migration(self) -> Dict[str, Any]:
        """Verify migration completed successfully"""
        logger.info("🔍 Verifying migration...")
        
        source_dbsize = self.source_client.dbsize()
        target_dbsize = self.target_client.dbsize()
        
        verification = {
            "source_keys": source_dbsize,
            "target_keys": target_dbsize,
            "match": source_dbsize == target_dbsize,
            "difference": abs(source_dbsize - target_dbsize)
        }
        
        # Sample key verification
        sample_verified = 0
        sample_failed = 0
        
        for key in self.source_client.scan_iter(count=100):
            source_type = self.source_client.type(key)
            target_type = self.target_client.type(key)
            
            if source_type == target_type:
                sample_verified += 1
            else:
                sample_failed += 1
                logger.warning(f"⚠️  Key type mismatch: {key}")
            
            if sample_verified + sample_failed >= 100:
                break
        
        verification["sample_verified"] = sample_verified
        verification["sample_failed"] = sample_failed
        
        logger.info(f"✅ Verification Results:")
        logger.info(f"   - Source keys: {verification['source_keys']}")
        logger.info(f"   - Target keys: {verification['target_keys']}")
        logger.info(f"   - Match: {verification['match']}")
        logger.info(f"   - Sample verified: {sample_verified}/100")
        
        return verification
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate migration report"""
        report = {
            "source_url": self.source_url.split('@')[1] if '@' in self.source_url else self.source_url,
            "target_url": self.target_url.split('@')[1] if '@' in self.target_url else self.target_url,
            "migration_stats": self.migration_stats,
            "status": "UNKNOWN"
        }
        
        # Determine status
        if self.migration_stats["keys_failed"] == 0:
            if self.migration_stats["keys_migrated"] == self.migration_stats["keys_scanned"]:
                report["status"] = "SUCCESS"
            else:
                report["status"] = "PARTIAL"
        else:
            if self.migration_stats["keys_migrated"] > 0:
                report["status"] = "WARNING"
            else:
                report["status"] = "FAILED"
        
        return report
    
    def cleanup(self):
        """Close connections"""
        if self.source_client:
            self.source_client.close()
        if self.target_client:
            self.target_client.close()


def main():
    """Main migration process"""
    # Get Redis URLs from environment or arguments
    source_url = os.getenv("REDIS_SOURCE_URL", "redis://localhost:6379")
    target_url = os.getenv("REDIS_TARGET_URL", os.getenv("REDIS_URL"))
    
    if not target_url:
        logger.error("❌ REDIS_TARGET_URL or REDIS_URL environment variable not set")
        sys.exit(1)
    
    # Confirm migration
    logger.info("🔄 Redis Migration Tool")
    logger.info("=" * 50)
    logger.info(f"Source: {source_url}")
    logger.info(f"Target: {target_url}")
    logger.info("")
    
    if "--no-confirm" not in sys.argv:
        confirm = input("⚠️  This will migrate all data. Continue? (yes/no): ")
        if confirm.lower() != "yes":
            logger.info("Migration cancelled.")
            sys.exit(0)
    
    migrator = RedisMigrator(source_url, target_url)
    
    try:
        # Connect to both instances
        if not migrator.connect_source():
            sys.exit(1)
        
        if not migrator.connect_target():
            sys.exit(1)
        
        # Analyze source
        analysis = migrator.analyze_source()
        
        if analysis.get("total_keys", 0) == 0:
            logger.info("ℹ️  No data to migrate.")
            sys.exit(0)
        
        # Perform migration
        stats = migrator.migrate_data()
        
        # Verify migration
        verification = migrator.verify_migration()
        
        # Generate report
        report = migrator.generate_report()
        report["analysis"] = analysis
        report["verification"] = verification
        
        # Save report
        with open("redis_migration_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        logger.info("")
        logger.info("📊 MIGRATION COMPLETE")
        logger.info("=" * 50)
        logger.info(f"Status: {report['status']}")
        logger.info(f"Keys migrated: {stats['keys_migrated']}")
        logger.info(f"Keys failed: {stats['keys_failed']}")
        logger.info(f"Report saved to: redis_migration_report.json")
        
        # Exit code based on status
        if report["status"] == "SUCCESS":
            sys.exit(0)
        elif report["status"] in ["PARTIAL", "WARNING"]:
            sys.exit(1)
        else:
            sys.exit(2)
            
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        sys.exit(2)
        
    finally:
        migrator.cleanup()


if __name__ == "__main__":
    main() 