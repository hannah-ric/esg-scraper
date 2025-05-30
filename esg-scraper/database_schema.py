"""
Enhanced database schema for ESG framework compliance
"""

ENHANCED_SCHEMA = """
-- Main analyses table (existing, but enhanced)
CREATE TABLE IF NOT EXISTS analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    source_url TEXT,
    company_name TEXT,
    environmental_score REAL,
    social_score REAL,
    governance_score REAL,
    overall_score REAL,
    keywords TEXT,
    insights TEXT,
    analysis_type TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- New fields
    industry_sector TEXT,
    company_size TEXT,
    reporting_period TEXT,
    document_type TEXT,
    language TEXT DEFAULT 'en'
);

-- Framework compliance tracking
CREATE TABLE IF NOT EXISTS framework_compliance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id INTEGER NOT NULL,
    framework TEXT NOT NULL,
    coverage_percentage REAL,
    requirements_found INTEGER,
    requirements_total INTEGER,
    mandatory_met INTEGER,
    mandatory_total INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (analysis_id) REFERENCES analyses(id)
);

-- Detailed requirement findings
CREATE TABLE IF NOT EXISTS requirement_findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id INTEGER NOT NULL,
    framework TEXT NOT NULL,
    requirement_id TEXT NOT NULL,
    category TEXT,
    subcategory TEXT,
    description TEXT,
    found BOOLEAN,
    confidence_score REAL,
    extracted_text TEXT,
    page_numbers TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (analysis_id) REFERENCES analyses(id)
);

-- Extracted metrics
CREATE TABLE IF NOT EXISTS extracted_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id INTEGER NOT NULL,
    requirement_id TEXT,
    metric_name TEXT,
    metric_value TEXT,
    metric_unit TEXT,
    metric_year INTEGER,
    confidence_score REAL,
    source_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (analysis_id) REFERENCES analyses(id)
);

-- Gap analysis results
CREATE TABLE IF NOT EXISTS gap_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id INTEGER NOT NULL,
    framework TEXT NOT NULL,
    requirement_id TEXT NOT NULL,
    category TEXT,
    description TEXT,
    severity TEXT, -- 'critical', 'high', 'medium', 'low'
    recommendation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (analysis_id) REFERENCES analyses(id)
);

-- Company profiles for better context
CREATE TABLE IF NOT EXISTS company_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT UNIQUE NOT NULL,
    industry_sector TEXT,
    sub_sector TEXT,
    company_size TEXT,
    headquarters_country TEXT,
    stock_ticker TEXT,
    website TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Historical tracking
CREATE TABLE IF NOT EXISTS historical_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    analysis_date DATE,
    environmental_score REAL,
    social_score REAL,
    governance_score REAL,
    overall_score REAL,
    framework_coverage TEXT, -- JSON with coverage per framework
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_analyses_company ON analyses(company_name);
CREATE INDEX IF NOT EXISTS idx_analyses_created ON analyses(created_at);
CREATE INDEX IF NOT EXISTS idx_framework_compliance_analysis ON framework_compliance(analysis_id);
CREATE INDEX IF NOT EXISTS idx_requirement_findings_analysis ON requirement_findings(analysis_id);
CREATE INDEX IF NOT EXISTS idx_metrics_analysis ON extracted_metrics(analysis_id);
CREATE INDEX IF NOT EXISTS idx_historical_company ON historical_scores(company_name);
CREATE INDEX IF NOT EXISTS idx_gap_analysis ON gap_analysis(analysis_id);
CREATE INDEX IF NOT EXISTS idx_company_profiles_name ON company_profiles(company_name);
""" 