"""
ESG Metrics Platform Database Schema
Comprehensive schema for storing scraped reports, extracted metrics, and framework alignments
"""

import sqlite3
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

METRICS_PLATFORM_SCHEMA = """
-- Companies table
CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    website TEXT,
    industry_sector TEXT,
    sub_sector TEXT,
    size TEXT,
    headquarters_country TEXT,
    stock_ticker TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Scraped reports table
CREATE TABLE IF NOT EXISTS scraped_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    report_url TEXT NOT NULL,
    report_title TEXT,
    report_type TEXT, -- 'pdf', 'webpage', 'api'
    report_year INTEGER,
    source TEXT, -- 'company_website', 'gri_database', 'cdp', etc.
    file_hash TEXT, -- To avoid duplicate processing
    content_extracted BOOLEAN DEFAULT FALSE,
    scrape_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id),
    UNIQUE(report_url, report_year)
);

-- Extracted metrics table
CREATE TABLE IF NOT EXISTS extracted_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    metric_name TEXT NOT NULL,
    metric_category TEXT NOT NULL, -- 'ghg_emissions', 'energy', 'water', etc.
    value REAL NOT NULL,
    unit TEXT NOT NULL,
    normalized_value REAL,
    normalized_unit TEXT,
    year INTEGER,
    scope TEXT, -- For emissions: 'Scope 1', 'Scope 2', 'Scope 3'
    confidence_score REAL,
    context TEXT, -- Surrounding text for validation
    page_number INTEGER,
    extraction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (report_id) REFERENCES scraped_reports(id)
);

-- Framework requirements mapping
CREATE TABLE IF NOT EXISTS framework_requirements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    framework TEXT NOT NULL, -- 'CSRD', 'GRI', 'SASB', 'TCFD'
    requirement_id TEXT NOT NULL,
    category TEXT,
    subcategory TEXT,
    description TEXT,
    metric_types TEXT, -- JSON array of applicable metric types
    is_mandatory BOOLEAN DEFAULT FALSE,
    UNIQUE(framework, requirement_id)
);

-- Metric to framework mapping
CREATE TABLE IF NOT EXISTS metric_framework_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_id INTEGER NOT NULL,
    framework TEXT NOT NULL,
    requirement_id TEXT NOT NULL,
    mapping_confidence REAL,
    FOREIGN KEY (metric_id) REFERENCES extracted_metrics(id),
    FOREIGN KEY (framework, requirement_id) REFERENCES framework_requirements(framework, requirement_id),
    UNIQUE(metric_id, framework, requirement_id)
);

-- Analysis results table
CREATE TABLE IF NOT EXISTS analysis_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reporting_years TEXT, -- JSON array of years analyzed
    total_metrics_extracted INTEGER,
    data_quality_score REAL,
    frameworks_analyzed TEXT, -- JSON array
    key_insights TEXT, -- JSON array
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- Framework coverage results
CREATE TABLE IF NOT EXISTS framework_coverage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id INTEGER NOT NULL,
    framework TEXT NOT NULL,
    coverage_percentage REAL,
    requirements_met INTEGER,
    requirements_total INTEGER,
    missing_requirements TEXT, -- JSON array
    recommendations TEXT, -- JSON array
    FOREIGN KEY (analysis_id) REFERENCES analysis_results(id)
);

-- Metric trends table (for historical tracking)
CREATE TABLE IF NOT EXISTS metric_trends (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    metric_category TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    year INTEGER NOT NULL,
    value REAL,
    normalized_value REAL,
    unit TEXT,
    normalized_unit TEXT,
    trend_direction TEXT, -- 'increasing', 'decreasing', 'stable'
    year_over_year_change REAL,
    FOREIGN KEY (company_id) REFERENCES companies(id),
    UNIQUE(company_id, metric_name, year)
);

-- Peer comparison table
CREATE TABLE IF NOT EXISTS peer_comparisons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    comparison_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    industry_sector TEXT,
    companies_compared TEXT, -- JSON array of company IDs
    metrics_compared TEXT, -- JSON array of metric categories
    comparison_results TEXT -- JSON object with detailed results
);

-- Data quality tracking
CREATE TABLE IF NOT EXISTS data_quality_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER,
    metric_id INTEGER,
    issue_type TEXT, -- 'low_confidence', 'missing_unit', 'ambiguous_year', etc.
    issue_description TEXT,
    severity TEXT, -- 'low', 'medium', 'high'
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (report_id) REFERENCES scraped_reports(id),
    FOREIGN KEY (metric_id) REFERENCES extracted_metrics(id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(name);
CREATE INDEX IF NOT EXISTS idx_reports_company ON scraped_reports(company_id);
CREATE INDEX IF NOT EXISTS idx_reports_year ON scraped_reports(report_year);
CREATE INDEX IF NOT EXISTS idx_metrics_report ON extracted_metrics(report_id);
CREATE INDEX IF NOT EXISTS idx_metrics_category ON extracted_metrics(metric_category);
CREATE INDEX IF NOT EXISTS idx_metrics_year ON extracted_metrics(year);
CREATE INDEX IF NOT EXISTS idx_mappings_metric ON metric_framework_mappings(metric_id);
CREATE INDEX IF NOT EXISTS idx_mappings_framework ON metric_framework_mappings(framework);
CREATE INDEX IF NOT EXISTS idx_coverage_analysis ON framework_coverage(analysis_id);
CREATE INDEX IF NOT EXISTS idx_trends_company ON metric_trends(company_id);
CREATE INDEX IF NOT EXISTS idx_quality_report ON data_quality_logs(report_id);
"""

class MetricsDatabaseManager:
    """Manager for the metrics platform database"""
    
    def __init__(self, db_path: str = "metrics_platform.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with schema"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.executescript(METRICS_PLATFORM_SCHEMA)
                logger.info("Metrics database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def insert_company(self, name: str, website: str = None, **kwargs) -> int:
        """Insert or update company record"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if company exists
            cursor.execute("SELECT id FROM companies WHERE name = ?", (name,))
            result = cursor.fetchone()
            
            if result:
                # Update existing
                company_id = result[0]
                update_fields = []
                update_values = []
                
                for field, value in kwargs.items():
                    if value is not None:
                        update_fields.append(f"{field} = ?")
                        update_values.append(value)
                
                if update_fields:
                    update_values.append(company_id)
                    cursor.execute(
                        f"UPDATE companies SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                        update_values
                    )
            else:
                # Insert new
                fields = ['name', 'website'] + list(kwargs.keys())
                values = [name, website] + list(kwargs.values())
                placeholders = ', '.join(['?' for _ in values])
                
                cursor.execute(
                    f"INSERT INTO companies ({', '.join(fields)}) VALUES ({placeholders})",
                    values
                )
                company_id = cursor.lastrowid
            
            return company_id
    
    def insert_report(self, company_id: int, report_url: str, **kwargs) -> int:
        """Insert scraped report"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check for duplicate
            cursor.execute(
                "SELECT id FROM scraped_reports WHERE report_url = ? AND report_year = ?",
                (report_url, kwargs.get('report_year'))
            )
            
            existing = cursor.fetchone()
            if existing:
                return existing[0]
            
            # Insert new report
            fields = ['company_id', 'report_url'] + list(kwargs.keys())
            values = [company_id, report_url] + list(kwargs.values())
            placeholders = ', '.join(['?' for _ in values])
            
            cursor.execute(
                f"INSERT INTO scraped_reports ({', '.join(fields)}) VALUES ({placeholders})",
                values
            )
            
            return cursor.lastrowid
    
    def insert_metric(self, report_id: int, metric_data: dict) -> int:
        """Insert extracted metric"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            required_fields = ['metric_name', 'metric_category', 'value', 'unit']
            for field in required_fields:
                if field not in metric_data:
                    raise ValueError(f"Missing required field: {field}")
            
            fields = ['report_id'] + list(metric_data.keys())
            values = [report_id] + list(metric_data.values())
            placeholders = ', '.join(['?' for _ in values])
            
            cursor.execute(
                f"INSERT INTO extracted_metrics ({', '.join(fields)}) VALUES ({placeholders})",
                values
            )
            
            return cursor.lastrowid
    
    def insert_framework_mapping(self, metric_id: int, framework: str, 
                                requirement_id: str, confidence: float = 0.8):
        """Insert metric to framework mapping"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute(
                    """INSERT INTO metric_framework_mappings 
                       (metric_id, framework, requirement_id, mapping_confidence) 
                       VALUES (?, ?, ?, ?)""",
                    (metric_id, framework, requirement_id, confidence)
                )
            except sqlite3.IntegrityError:
                # Mapping already exists
                pass
    
    def get_company_metrics(self, company_name: str, year: int = None) -> list:
        """Get all metrics for a company"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = """
                SELECT em.*, sr.report_year, sr.report_title
                FROM extracted_metrics em
                JOIN scraped_reports sr ON em.report_id = sr.id
                JOIN companies c ON sr.company_id = c.id
                WHERE c.name = ?
            """
            params = [company_name]
            
            if year:
                query += " AND em.year = ?"
                params.append(year)
            
            query += " ORDER BY em.year DESC, em.metric_category"
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_framework_coverage(self, company_name: str, framework: str) -> dict:
        """Get framework coverage for a company"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get total requirements
            cursor.execute(
                "SELECT COUNT(*) as total FROM framework_requirements WHERE framework = ?",
                (framework,)
            )
            total_requirements = cursor.fetchone()['total']
            
            # Get covered requirements
            cursor.execute("""
                SELECT COUNT(DISTINCT mfm.requirement_id) as covered
                FROM metric_framework_mappings mfm
                JOIN extracted_metrics em ON mfm.metric_id = em.id
                JOIN scraped_reports sr ON em.report_id = sr.id
                JOIN companies c ON sr.company_id = c.id
                WHERE c.name = ? AND mfm.framework = ?
            """, (company_name, framework))
            
            covered_requirements = cursor.fetchone()['covered']
            
            coverage_percentage = (covered_requirements / total_requirements * 100) if total_requirements > 0 else 0
            
            return {
                'framework': framework,
                'total_requirements': total_requirements,
                'covered_requirements': covered_requirements,
                'coverage_percentage': round(coverage_percentage, 1)
            }
    
    def insert_analysis_result(self, company_id: int, analysis_data: dict) -> int:
        """Insert analysis result"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Convert lists to JSON
            if 'reporting_years' in analysis_data and isinstance(analysis_data['reporting_years'], list):
                analysis_data['reporting_years'] = json.dumps(analysis_data['reporting_years'])
            if 'frameworks_analyzed' in analysis_data and isinstance(analysis_data['frameworks_analyzed'], list):
                analysis_data['frameworks_analyzed'] = json.dumps(analysis_data['frameworks_analyzed'])
            if 'key_insights' in analysis_data and isinstance(analysis_data['key_insights'], list):
                analysis_data['key_insights'] = json.dumps(analysis_data['key_insights'])
            
            fields = ['company_id'] + list(analysis_data.keys())
            values = [company_id] + list(analysis_data.values())
            placeholders = ', '.join(['?' for _ in values])
            
            cursor.execute(
                f"INSERT INTO analysis_results ({', '.join(fields)}) VALUES ({placeholders})",
                values
            )
            
            return cursor.lastrowid
    
    def populate_framework_requirements(self):
        """Populate framework requirements table with predefined requirements"""
        requirements = [
            # CSRD Requirements
            ('CSRD', 'E1-1', 'Environmental', 'Climate', 'Scope 1 GHG emissions', '["ghg_emissions"]', True),
            ('CSRD', 'E1-2', 'Environmental', 'Climate', 'Scope 2 GHG emissions', '["ghg_emissions"]', True),
            ('CSRD', 'E1-3', 'Environmental', 'Climate', 'Scope 3 GHG emissions', '["ghg_emissions"]', True),
            ('CSRD', 'E1-5', 'Environmental', 'Climate', 'Energy consumption and mix', '["energy"]', True),
            ('CSRD', 'E3-1', 'Environmental', 'Water', 'Water consumption', '["water"]', True),
            ('CSRD', 'E5-1', 'Environmental', 'Waste', 'Waste generation', '["waste"]', True),
            
            # GRI Requirements
            ('GRI', '305-1', 'Environmental', 'Emissions', 'Direct (Scope 1) GHG emissions', '["ghg_emissions"]', True),
            ('GRI', '305-2', 'Environmental', 'Emissions', 'Energy indirect (Scope 2) GHG emissions', '["ghg_emissions"]', True),
            ('GRI', '305-3', 'Environmental', 'Emissions', 'Other indirect (Scope 3) GHG emissions', '["ghg_emissions"]', False),
            ('GRI', '302-1', 'Environmental', 'Energy', 'Energy consumption within the organization', '["energy"]', True),
            ('GRI', '303-3', 'Environmental', 'Water', 'Water withdrawal', '["water"]', True),
            ('GRI', '306-3', 'Environmental', 'Waste', 'Waste generated', '["waste"]', True),
            
            # Add more requirements as needed
        ]
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for req in requirements:
                try:
                    cursor.execute(
                        """INSERT INTO framework_requirements 
                           (framework, requirement_id, category, subcategory, description, metric_types, is_mandatory)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        req
                    )
                except sqlite3.IntegrityError:
                    # Requirement already exists
                    pass


# Initialize database when module is imported
if __name__ == "__main__":
    db_manager = MetricsDatabaseManager()
    db_manager.populate_framework_requirements()
    print("Metrics database initialized with framework requirements") 