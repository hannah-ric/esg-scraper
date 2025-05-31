"""
Enhanced Database Schema for ESG Intelligence Platform
=====================================================

This module defines the database schema supporting:
- Basic ESG analysis tracking
- Framework compliance data (CSRD, GRI, SASB, TCFD)
- Requirement findings and gap analysis
- Extracted metrics with confidence scoring
- Historical trends and company profiles
- Performance benchmarking

The schema uses SQLite for development and can be adapted for PostgreSQL in production.
"""

# Enhanced database schema with framework compliance support
ENHANCED_SCHEMA = """
-- Core analyses table (enhanced from original)
CREATE TABLE IF NOT EXISTS analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    source_url TEXT,
    company_name TEXT,
    environmental_score REAL,
    social_score REAL,
    governance_score REAL,
    overall_score REAL,
    keywords TEXT,  -- JSON array of keywords
    insights TEXT,  -- JSON array of insights
    analysis_type TEXT,  -- 'quick' or 'full'
    industry_sector TEXT,
    reporting_period TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Framework compliance tracking
CREATE TABLE IF NOT EXISTS framework_compliance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id INTEGER NOT NULL,
    framework TEXT NOT NULL,  -- CSRD, GRI, SASB, TCFD
    coverage_percentage REAL NOT NULL,
    requirements_found INTEGER NOT NULL,
    requirements_total INTEGER NOT NULL,
    mandatory_met INTEGER NOT NULL,
    mandatory_total INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (analysis_id) REFERENCES analyses(id) ON DELETE CASCADE
);

-- Individual requirement findings
CREATE TABLE IF NOT EXISTS requirement_findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id INTEGER NOT NULL,
    framework TEXT NOT NULL,
    requirement_id TEXT NOT NULL,
    category TEXT NOT NULL,
    subcategory TEXT,
    description TEXT,
    found BOOLEAN NOT NULL,
    confidence_score REAL,  -- 0.0 to 1.0
    extracted_text TEXT,  -- JSON array of matched keywords/phrases
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (analysis_id) REFERENCES analyses(id) ON DELETE CASCADE
);

-- Extracted metrics from content
CREATE TABLE IF NOT EXISTS extracted_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id INTEGER NOT NULL,
    requirement_id TEXT,  -- Links to specific requirement if applicable
    metric_name TEXT NOT NULL,
    metric_value TEXT NOT NULL,
    metric_unit TEXT,
    confidence_score REAL,
    context TEXT,  -- Surrounding text for context
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (analysis_id) REFERENCES analyses(id) ON DELETE CASCADE
);

-- Gap analysis results
CREATE TABLE IF NOT EXISTS gap_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id INTEGER NOT NULL,
    framework TEXT NOT NULL,
    requirement_id TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    severity TEXT NOT NULL,  -- critical, high, medium, low
    recommendation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (analysis_id) REFERENCES analyses(id) ON DELETE CASCADE
);

-- Company profiles for enhanced tracking
CREATE TABLE IF NOT EXISTS company_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL UNIQUE,
    industry_sector TEXT,
    market_cap_category TEXT,  -- large-cap, mid-cap, small-cap
    geographic_region TEXT,
    website_url TEXT,
    stock_symbol TEXT,
    employee_count_range TEXT,
    sustainability_commitments TEXT,  -- JSON array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Historical scores for trend analysis
CREATE TABLE IF NOT EXISTS historical_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    analysis_date DATE NOT NULL,
    environmental_score REAL,
    social_score REAL,
    governance_score REAL,
    overall_score REAL,
    framework_coverage TEXT,  -- JSON object with framework coverage data
    data_source TEXT,  -- 'analysis', 'manual', 'third_party'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Benchmarking data
CREATE TABLE IF NOT EXISTS benchmark_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    industry_sector TEXT NOT NULL,
    framework TEXT NOT NULL,
    category TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    percentile_25 REAL,
    percentile_50 REAL,
    percentile_75 REAL,
    percentile_90 REAL,
    sample_size INTEGER,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User activity tracking (enhanced)
CREATE TABLE IF NOT EXISTS user_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    activity_type TEXT NOT NULL,  -- 'analysis', 'export', 'compare', 'benchmark'
    resource_id INTEGER,  -- Reference to analysis or other resource
    credits_used INTEGER DEFAULT 0,
    metadata TEXT,  -- JSON with additional activity details
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_analyses_user_id ON analyses(user_id);
CREATE INDEX IF NOT EXISTS idx_analyses_company_name ON analyses(company_name);
CREATE INDEX IF NOT EXISTS idx_analyses_created_at ON analyses(created_at);
CREATE INDEX IF NOT EXISTS idx_analyses_industry_sector ON analyses(industry_sector);

CREATE INDEX IF NOT EXISTS idx_framework_compliance_analysis_id ON framework_compliance(analysis_id);
CREATE INDEX IF NOT EXISTS idx_framework_compliance_framework ON framework_compliance(framework);

CREATE INDEX IF NOT EXISTS idx_requirement_findings_analysis_id ON requirement_findings(analysis_id);
CREATE INDEX IF NOT EXISTS idx_requirement_findings_framework ON requirement_findings(framework);
CREATE INDEX IF NOT EXISTS idx_requirement_findings_requirement_id ON requirement_findings(requirement_id);

CREATE INDEX IF NOT EXISTS idx_extracted_metrics_analysis_id ON extracted_metrics(analysis_id);
CREATE INDEX IF NOT EXISTS idx_extracted_metrics_requirement_id ON extracted_metrics(requirement_id);

CREATE INDEX IF NOT EXISTS idx_gap_analysis_analysis_id ON gap_analysis(analysis_id);
CREATE INDEX IF NOT EXISTS idx_gap_analysis_framework ON gap_analysis(framework);
CREATE INDEX IF NOT EXISTS idx_gap_analysis_severity ON gap_analysis(severity);

CREATE INDEX IF NOT EXISTS idx_company_profiles_name ON company_profiles(company_name);
CREATE INDEX IF NOT EXISTS idx_company_profiles_industry ON company_profiles(industry_sector);

CREATE INDEX IF NOT EXISTS idx_historical_scores_company ON historical_scores(company_name);
CREATE INDEX IF NOT EXISTS idx_historical_scores_date ON historical_scores(analysis_date);

CREATE INDEX IF NOT EXISTS idx_benchmark_data_industry ON benchmark_data(industry_sector);
CREATE INDEX IF NOT EXISTS idx_benchmark_data_framework ON benchmark_data(framework);

CREATE INDEX IF NOT EXISTS idx_user_activity_user_id ON user_activity(user_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_type ON user_activity(activity_type);

-- Create triggers for automatic timestamp updates
CREATE TRIGGER IF NOT EXISTS update_analyses_timestamp
    AFTER UPDATE ON analyses
    FOR EACH ROW
    BEGIN
        UPDATE analyses SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_company_profiles_timestamp
    AFTER UPDATE ON company_profiles
    FOR EACH ROW
    BEGIN
        UPDATE company_profiles SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

-- Views for common queries
CREATE VIEW IF NOT EXISTS latest_company_scores AS
SELECT
    company_name,
    MAX(analysis_date) as latest_date,
    environmental_score,
    social_score,
    governance_score,
    overall_score,
    framework_coverage
FROM historical_scores
GROUP BY company_name;

CREATE VIEW IF NOT EXISTS framework_compliance_summary AS
SELECT
    a.company_name,
    a.industry_sector,
    fc.framework,
    fc.coverage_percentage,
    fc.mandatory_met,
    fc.mandatory_total,
    a.created_at as analysis_date
FROM analyses a
JOIN framework_compliance fc ON a.id = fc.analysis_id
WHERE a.company_name IS NOT NULL;

CREATE VIEW IF NOT EXISTS critical_gaps_summary AS
SELECT
    a.company_name,
    a.industry_sector,
    ga.framework,
    COUNT(*) as critical_gaps_count,
    a.created_at as analysis_date
FROM analyses a
JOIN gap_analysis ga ON a.id = ga.analysis_id
WHERE ga.severity = 'critical'
AND a.company_name IS NOT NULL
GROUP BY a.company_name, a.industry_sector, ga.framework, a.created_at;

-- Sample data population (optional)
INSERT OR IGNORE INTO benchmark_data
    (industry_sector, framework, category, metric_name, percentile_25,
     percentile_50, percentile_75, percentile_90, sample_size)
VALUES
('Technology', 'CSRD', 'Environmental', 'GHG Scope 1 Reduction %', 15.0, 25.0, 35.0, 50.0, 150),
('Technology', 'CSRD', 'Environmental', 'GHG Scope 2 Reduction %', 20.0, 35.0, 50.0, 70.0, 150),
('Technology', 'CSRD', 'Social', 'Women in Management %', 25.0, 35.0, 45.0, 55.0, 150),
('Technology', 'TCFD', 'Governance', 'Climate Governance Score', 60.0, 75.0, 85.0, 95.0, 150),

('Energy', 'CSRD', 'Environmental', 'GHG Scope 1 Reduction %', 10.0, 20.0, 30.0, 45.0, 80),
('Energy', 'TCFD', 'Environmental', 'Scenario Analysis Score', 50.0, 70.0, 85.0, 95.0, 80),

('Finance', 'SASB', 'Social', 'Data Privacy Score', 70.0, 80.0, 90.0, 95.0, 120),
('Finance', 'TCFD', 'Environmental', 'Climate Risk Assessment', 60.0, 75.0, 85.0, 95.0, 120),

('Manufacturing', 'CSRD', 'Environmental', 'Circular Economy Score', 30.0, 45.0, 60.0, 75.0, 100),
('Manufacturing', 'GRI', 'Social', 'Worker Safety Score', 75.0, 85.0, 92.0, 98.0, 100);
"""


# Additional utility functions for database operations
def get_table_creation_statements():
    """Return individual table creation statements for programmatic use"""
    statements = []

    # Split the schema into individual statements
    schema_parts = ENHANCED_SCHEMA.split(";")

    for part in schema_parts:
        part = part.strip()
        if part and (
            part.startswith("CREATE TABLE")
            or part.startswith("CREATE INDEX")
            or part.startswith("CREATE TRIGGER")
            or part.startswith("CREATE VIEW")
            or part.startswith("INSERT OR IGNORE")
        ):
            statements.append(part + ";")

    return statements


def get_framework_compliance_query():
    """SQL query to get framework compliance summary"""
    return """
    SELECT
        a.company_name,
        a.industry_sector,
        a.overall_score,
        fc.framework,
        fc.coverage_percentage,
        fc.mandatory_met,
        fc.mandatory_total,
        ROUND(fc.mandatory_met * 100.0 / fc.mandatory_total, 1) as mandatory_compliance_pct,
        COUNT(ga.id) as total_gaps,
        COUNT(CASE WHEN ga.severity = 'critical' THEN 1 END) as critical_gaps,
        a.created_at
    FROM analyses a
    LEFT JOIN framework_compliance fc ON a.id = fc.analysis_id
    LEFT JOIN gap_analysis ga ON a.id = ga.analysis_id AND ga.framework = fc.framework
    WHERE a.company_name IS NOT NULL
    GROUP BY a.id, fc.framework
    ORDER BY a.created_at DESC, fc.coverage_percentage DESC;
    """


def get_industry_benchmark_query():
    """SQL query to get industry benchmarking data"""
    return """
    SELECT
        industry_sector,
        framework,
        category,
        metric_name,
        percentile_25,
        percentile_50 as median,
        percentile_75,
        percentile_90,
        sample_size,
        last_updated
    FROM benchmark_data
    WHERE industry_sector = ? AND framework = ?
    ORDER BY category, metric_name;
    """


def get_company_trend_query():
    """SQL query to get company ESG score trends"""
    return """
    SELECT
        analysis_date,
        environmental_score,
        social_score,
        governance_score,
        overall_score,
        framework_coverage
    FROM historical_scores
    WHERE company_name = ?
    AND analysis_date >= date('now', '-' || ? || ' days')
    ORDER BY analysis_date DESC;
    """


def get_top_performers_query():
    """SQL query to get top ESG performers by industry"""
    return """
    SELECT
        a.company_name,
        a.industry_sector,
        a.overall_score,
        AVG(fc.coverage_percentage) as avg_framework_coverage,
        COUNT(DISTINCT fc.framework) as frameworks_covered,
        a.created_at
    FROM analyses a
    JOIN framework_compliance fc ON a.id = fc.analysis_id
    WHERE a.industry_sector = ?
    AND a.created_at >= date('now', '-30 days')
    GROUP BY a.company_name, a.industry_sector, a.overall_score, a.created_at
    HAVING frameworks_covered >= 2
    ORDER BY a.overall_score DESC, avg_framework_coverage DESC
    LIMIT ?;
    """


# Database migration utilities
MIGRATION_SCRIPTS = {
    "v1_to_v2": """
        -- Add new columns to existing analyses table
        ALTER TABLE analyses ADD COLUMN industry_sector TEXT;
        ALTER TABLE analyses ADD COLUMN reporting_period TEXT;
        ALTER TABLE analyses ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
    """,
    "v2_to_v3": """
        -- Add framework compliance and related tables
        -- (This would be the full enhanced schema for existing basic setups)
    """,
}


def get_migration_script(from_version: str, to_version: str) -> str:
    """Get migration script between versions"""
    migration_key = f"{from_version}_to_{to_version}"
    return MIGRATION_SCRIPTS.get(migration_key, "")


if __name__ == "__main__":
    # Print schema for verification
    print("Enhanced ESG Database Schema")
    print("=" * 50)
    print(ENHANCED_SCHEMA)

    print("\nTable Creation Statements:")
    print("-" * 30)
    for i, statement in enumerate(get_table_creation_statements(), 1):
        if statement.startswith("CREATE TABLE"):
            table_name = (
                statement.split("(")[0]
                .replace("CREATE TABLE IF NOT EXISTS ", "")
                .strip()
            )
            print(f"{i}. {table_name}")

    print(f"\nTotal statements: {len(get_table_creation_statements())}")
