# PostgreSQL Migration Guide for ESG Scraper Platform

## Overview
This guide documents the migration from MongoDB to PostgreSQL for the ESG Scraper platform.

## Architecture Changes

### Previous Stack (MongoDB)
- **Database**: MongoDB (NoSQL document store)
- **Driver**: Motor (async MongoDB driver)
- **Connection**: Via MongoDB URI

### New Stack (PostgreSQL)
- **Database**: PostgreSQL 16 (Relational database)
- **Driver**: asyncpg (async PostgreSQL driver)
- **Connection**: Via environment variables (PGPASSWORD, PGHOST, etc.)

## Database Schema

### PostgreSQL Tables

#### 1. Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    tier VARCHAR(50) DEFAULT 'free',
    credits INTEGER DEFAULT 100,
    stripe_customer_id VARCHAR(255),
    stripe_subscription_id VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### 2. Analyses Table
```sql
CREATE TABLE analyses (
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
);
```

## Environment Variables

### Required PostgreSQL Environment Variables
```bash
# PostgreSQL Connection
PGPASSWORD=${YOUR_POSTGRESQL_PASSWORD}  # Get from DigitalOcean
PGUSER=doadmin
PGHOST=private-db-postgresql-nyc3-50809-do-user-20909316-0.l.db.ondigitalocean.com
PGPORT=25060
PGDATABASE=defaultdb
PGSSLMODE=require
```

## Code Changes Summary

1. **Database Manager**: Replaced `mongodb_manager.py` with `postgresql_manager.py`
2. **Main Application**: Updated imports and initialization
3. **Dependencies**: Replaced MongoDB drivers with PostgreSQL drivers
4. **Environment Variables**: Changed from MONGODB_URI to PostgreSQL variables
5. **Health Checks**: Updated to check PostgreSQL instead of MongoDB

## Deployment Steps

1. Set all PostgreSQL environment variables in DigitalOcean App Platform
2. Deploy the updated code
3. Database tables will be created automatically on first run
4. Monitor logs for successful initialization

## Benefits

- Better data integrity with ACID compliance
- Cleaner relational model
- Cost savings (free tier available)
- Better performance for complex queries
- Standard SQL support 