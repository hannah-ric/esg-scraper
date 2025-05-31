#!/usr/bin/env python3
"""
Test suite for ESG Framework Compliance features
Tests CSRD, GRI, SASB, and TCFD compliance checking
"""

import os
import sys
import json
import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any

# Set test environment
os.environ["JWT_SECRET"] = "test-secret-key"
os.environ["REDIS_URL"] = "redis://localhost:6379"
os.environ["DATABASE_PATH"] = "test_esg_frameworks.db"

# Import after setting environment
from lean_esg_platform import app, create_token, EnhancedESGEngine, ESGFrameworkManager
from fastapi.testclient import TestClient
from esg_frameworks import Framework, DisclosureRequirement

# Create test client
client = TestClient(app)

# Test data
TEST_SUSTAINABILITY_REPORT = """
Our company is committed to achieving net zero emissions by 2050. In 2023, our Scope 1 emissions 
were 50,000 metric tons CO2e, Scope 2 emissions were 30,000 metric tons CO2e, and Scope 3 emissions 
totaled 200,000 metric tons CO2e. We have implemented a comprehensive climate transition plan aligned 
with the Paris Agreement.

Our board of directors has established a Climate Committee to oversee climate-related risks and 
opportunities. The committee meets quarterly and reports directly to the full board. Management has 
integrated climate risk assessment into our enterprise risk management framework.

We conducted scenario analysis using both 2°C and 1.5°C scenarios to assess physical and transition 
risks. Our water consumption was 2.5 million cubic meters, with 80% recycled. We have zero tolerance 
for child labor in our supply chain and conduct regular supplier audits.

Employee safety is paramount - our LTIFR was 0.5 in 2023. We achieved 40% gender diversity in 
management positions and provide comprehensive training programs averaging 40 hours per employee 
annually. Our code of conduct includes strong anti-corruption policies and whistleblower protections.
"""

TEST_USER_TOKEN = create_token("test_user")


class TestFrameworkCompliance:
    """Test ESG framework compliance features"""

    def test_framework_manager_initialization(self):
        """Test that framework manager loads all requirements correctly"""
        manager = ESGFrameworkManager()

        # Check all frameworks are loaded
        assert len(manager.requirements) == 4
        assert Framework.CSRD in manager.requirements
        assert Framework.GRI in manager.requirements
        assert Framework.SASB in manager.requirements
        assert Framework.TCFD in manager.requirements

        # Check CSRD has correct number of requirements
        csrd_reqs = manager.requirements[Framework.CSRD]
        assert len(csrd_reqs) >= 12  # We defined 12 CSRD requirements

        # Check all CSRD requirements are mandatory
        assert all(req.mandatory for req in csrd_reqs)

    def test_keyword_detection(self):
        """Test keyword-based requirement detection"""
        manager = ESGFrameworkManager()

        test_text = (
            "Our company has net zero targets and scope 1 emissions of 50,000 tCO2e"
        )
        found_reqs = manager.find_relevant_requirements(test_text)

        # Should find CSRD climate requirements
        assert Framework.CSRD in found_reqs
        csrd_found = found_reqs[Framework.CSRD]
        assert any(
            req.requirement_id == "CSRD-E1-1" for req in csrd_found
        )  # GHG emissions
        assert any(
            req.requirement_id == "CSRD-E1-2" for req in csrd_found
        )  # Climate transition

    def test_metric_extraction(self):
        """Test quantitative metric extraction"""
        manager = ESGFrameworkManager()

        test_text = "Scope 1 emissions: 50,000 metric tons CO2e, water usage: 2.5 million cubic meters"
        found_reqs = manager.find_relevant_requirements(test_text)

        # Extract metrics
        all_reqs = []
        for reqs in found_reqs.values():
            all_reqs.extend(reqs)

        metrics = manager.extract_metrics(test_text, all_reqs)
        assert len(metrics) > 0

        # Check if CO2 metrics were extracted
        co2_found = False
        for req_id, req_metrics in metrics.items():
            if any("CO2" in unit for unit in req_metrics.keys()):
                co2_found = True
                break
        assert co2_found

    def test_coverage_calculation(self):
        """Test framework coverage percentage calculation"""
        manager = ESGFrameworkManager()

        # Test with comprehensive report
        found_reqs = manager.find_relevant_requirements(TEST_SUSTAINABILITY_REPORT)
        coverage = manager.calculate_framework_coverage(found_reqs)

        # Should have some coverage for each framework
        assert coverage[Framework.CSRD] > 0
        assert coverage[Framework.TCFD] > 0
        assert coverage[Framework.GRI] >= 0  # May be 0 if only mandatory checked
        assert coverage[Framework.SASB] >= 0

    def test_gap_analysis(self):
        """Test gap analysis generation"""
        manager = ESGFrameworkManager()

        # Test with partial report
        partial_report = "We have net zero targets and measure our carbon emissions."
        found_reqs = manager.find_relevant_requirements(partial_report)
        gaps = manager.generate_gap_analysis(found_reqs)

        # Should identify gaps in CSRD (many mandatory requirements)
        assert Framework.CSRD in gaps
        assert len(gaps[Framework.CSRD]) > 5  # Should be missing many requirements

    @pytest.mark.asyncio
    async def test_enhanced_analysis_endpoint(self):
        """Test the enhanced analysis endpoint with framework compliance"""
        response = client.post(
            "/analyze",
            json={
                "text": TEST_SUSTAINABILITY_REPORT,
                "company_name": "Test Corp",
                "quick_mode": False,
                "frameworks": ["CSRD", "TCFD"],
                "industry_sector": "Technology",
                "extract_metrics": True,
            },
            headers={"Authorization": f"Bearer {TEST_USER_TOKEN}"},
        )

        assert response.status_code == 200
        data = response.json()

        # Check basic ESG scores
        assert "scores" in data
        assert data["scores"]["environmental"] > 0
        assert data["scores"]["social"] > 0
        assert data["scores"]["governance"] > 0

        # Check framework coverage
        assert "framework_coverage" in data
        assert "CSRD" in data["framework_coverage"]
        assert "TCFD" in data["framework_coverage"]

        # Check coverage details
        csrd_coverage = data["framework_coverage"]["CSRD"]
        assert "coverage_percentage" in csrd_coverage
        assert "requirements_found" in csrd_coverage
        assert "mandatory_met" in csrd_coverage

        # Check extracted metrics
        assert "extracted_metrics" in data
        assert len(data["extracted_metrics"]) > 0

        # Check gap analysis
        assert "gap_analysis" in data

        # Check recommendations
        assert "recommendations" in data
        assert len(data["recommendations"]) > 0

    def test_frameworks_info_endpoint(self):
        """Test the frameworks information endpoint"""
        response = client.get("/frameworks")

        assert response.status_code == 200
        data = response.json()

        assert "frameworks" in data
        assert "CSRD" in data["frameworks"]
        assert "TCFD" in data["frameworks"]

        # Check CSRD info
        csrd_info = data["frameworks"]["CSRD"]
        assert csrd_info["total_requirements"] >= 12
        assert csrd_info["mandatory_requirements"] >= 12
        assert "Environmental" in csrd_info["categories"]
        assert "Social" in csrd_info["categories"]
        assert "Governance" in csrd_info["categories"]

    def test_severity_determination(self):
        """Test severity determination for gaps"""
        engine = EnhancedESGEngine()

        # Test CSRD mandatory requirement
        csrd_req = DisclosureRequirement(
            framework=Framework.CSRD,
            category="Environmental",
            subcategory="Climate",
            requirement_id="CSRD-E1-1",
            description="GHG emissions",
            keywords=["ghg", "emissions"],
            mandatory=True,
        )

        severity = engine._determine_severity(csrd_req, Framework.CSRD, "Energy")
        assert severity == "critical"  # CSRD mandatory + energy sector + emissions

    def test_benchmark_endpoint(self):
        """Test the company benchmark endpoint"""
        response = client.post(
            "/benchmark",
            json={
                "companies": ["Company A", "Company B", "Company C"],
                "frameworks": ["CSRD", "TCFD"],
            },
            headers={"Authorization": f"Bearer {TEST_USER_TOKEN}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "companies" in data
        assert len(data["companies"]) == 3
        assert "average_scores" in data
        assert "best_performer" in data
        assert "frameworks_analyzed" in data

    def test_enhanced_keyword_scorer(self):
        """Test the enhanced keyword scorer with framework-specific terms"""
        from lean_esg_platform import EnhancedKeywordScorer

        scorer = EnhancedKeywordScorer()

        # Test with framework-specific keywords
        csrd_text = "We conduct double materiality assessment and have taxonomy alignment of 75%"
        scores = scorer.score(csrd_text)

        # Should boost environmental score due to CSRD keywords
        assert scores["environmental"] > 0

        # Test TCFD keywords
        tcfd_text = "Our scenario analysis covers physical risks and transition risks"
        scores = scorer.score(tcfd_text)
        assert scores["environmental"] > 0

    def test_requirement_findings(self):
        """Test detailed requirement findings"""
        engine = EnhancedESGEngine()

        # Create mock framework results
        framework_results = {
            "requirements": {
                Framework.CSRD: [
                    DisclosureRequirement(
                        framework=Framework.CSRD,
                        category="Environmental",
                        subcategory="Climate",
                        requirement_id="CSRD-E1-1",
                        description="GHG emissions",
                        keywords=["scope 1", "scope 2", "ghg emissions"],
                        mandatory=True,
                    )
                ]
            }
        }

        findings = engine._get_requirement_findings(
            framework_results, TEST_SUSTAINABILITY_REPORT
        )

        assert len(findings) > 0
        finding = findings[0]
        assert finding["requirement_id"] == "CSRD-E1-1"
        assert finding["found"] == True
        assert len(finding["keywords_matched"]) > 0
        assert finding["confidence"] > 0.5


class TestDatabaseIntegration:
    """Test database integration for framework compliance"""

    @pytest.mark.asyncio
    async def test_save_framework_analysis(self):
        """Test saving framework analysis to database"""
        from lean_esg_platform import db_manager

        # Create test result with framework data
        test_result = {
            "scores": {
                "environmental": 75.0,
                "social": 80.0,
                "governance": 85.0,
                "overall": 80.0,
            },
            "framework_coverage": {
                "CSRD": {
                    "framework": "CSRD",
                    "coverage_percentage": 75.0,
                    "requirements_found": 9,
                    "requirements_total": 12,
                    "mandatory_met": 9,
                    "mandatory_total": 12,
                }
            },
            "extracted_metrics": [
                {
                    "metric_name": "Scope 1 emissions",
                    "metric_value": "50000",
                    "metric_unit": "tCO2e",
                    "confidence": 0.9,
                    "requirement_id": "CSRD-E1-1",
                    "framework": "CSRD",
                }
            ],
            "gap_analysis": [
                {
                    "framework": "CSRD",
                    "requirement_id": "CSRD-E4-1",
                    "category": "Environmental",
                    "description": "Biodiversity impact",
                    "severity": "high",
                }
            ],
            "company": "Test Corp",
        }

        # Save to database
        await db_manager.save_analysis(
            "test_user", "test_source", test_result, "Technology", "2023"
        )

        # Verify saved correctly
        analyses = await db_manager.get_user_analyses("test_user", 1)
        assert len(analyses) > 0

        latest = analyses[0]
        assert latest["company_name"] == "Test Corp"
        assert latest["industry_sector"] == "Technology"
        assert "framework_scores" in latest  # Should have framework data


def test_integration_flow():
    """Test complete integration flow from analysis to gap retrieval"""
    # 1. Analyze a document
    response = client.post(
        "/analyze",
        json={
            "text": TEST_SUSTAINABILITY_REPORT,
            "company_name": "Integration Test Corp",
            "quick_mode": False,
            "frameworks": ["CSRD", "TCFD", "GRI", "SASB"],
            "industry_sector": "Technology",
            "reporting_period": "2023",
            "extract_metrics": True,
        },
        headers={"Authorization": f"Bearer {TEST_USER_TOKEN}"},
    )

    assert response.status_code == 200
    analysis_data = response.json()

    # 2. Check framework coverage is reasonable
    for framework in ["CSRD", "TCFD"]:
        assert framework in analysis_data["framework_coverage"]
        coverage = analysis_data["framework_coverage"][framework]
        assert coverage["coverage_percentage"] > 20  # Should find some requirements

    # 3. Verify metrics were extracted
    assert len(analysis_data["extracted_metrics"]) > 0

    # Check for specific metrics
    metrics_found = {m["metric_name"] for m in analysis_data["extracted_metrics"]}
    assert any("CO2" in m or "emission" in m.lower() for m in metrics_found)

    # 4. Verify gap analysis
    assert len(analysis_data["gap_analysis"]) > 0

    # Check severity distribution
    severities = [gap["severity"] for gap in analysis_data["gap_analysis"]]
    assert any(s in ["critical", "high"] for s in severities)

    # 5. Verify recommendations
    assert len(analysis_data["recommendations"]) > 0
    assert any("CSRD" in r for r in analysis_data["recommendations"])


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
