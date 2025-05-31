import database_schema
from esg_frameworks import ESGFrameworkManager, Framework, DisclosureRequirement
import os
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse, Response
import uvicorn
from pydantic import BaseModel, HttpUrl, EmailStr
from typing import Dict, List, Optional, Any
import hashlib
import json
from datetime import datetime, timedelta
import jwt
import redis
import httpx
from bs4 import BeautifulSoup
import yake
from transformers import pipeline
import sqlite3
import stripe
import numpy as np
from urllib.parse import urlparse
from collections import defaultdict
import time
import logging
import sys
from pydantic import validator
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi.middleware.cors import CORSMiddleware

# Optional import for trafilatura
try:
    import trafilatura

    TRAFILATURA_AVAILABLE = True
except ImportError:
    TRAFILATURA_AVAILABLE = False
    trafilatura = None

# Load environment variables from .env file
from dotenv import load_dotenv

load_dotenv()

# Import ESG framework modules

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("esg_platform.log"),
    ],
)
logger = logging.getLogger(__name__)

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
STRIPE_KEY = os.getenv("STRIPE_SECRET_KEY")
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    logger.error("JWT_SECRET environment variable is not set!")
    raise ValueError("JWT_SECRET must be set in environment variables")

FREE_TIER_CREDITS = int(os.getenv("FREE_TIER_CREDITS", "100"))
DATABASE_PATH = os.getenv("DATABASE_PATH", "esg_data.db")

# Initialize services
app = FastAPI(title="ESG Intelligence API", version="1.0.0")
security = HTTPBearer()
redis_client = redis.from_url(REDIS_URL, decode_responses=True)
stripe.api_key = STRIPE_KEY

# Load ML model once
sentiment_analyzer = pipeline(
    "sentiment-analysis", model="ProsusAI/finbert", device=-1
)  # CPU for cost efficiency

# --- METRICS ---
# Prometheus metrics
request_count = Counter(
    "esg_api_requests_total", "Total API requests", ["method", "endpoint", "status"]
)
request_duration = Histogram(
    "esg_api_request_duration_seconds", "Request duration", ["method", "endpoint"]
)
active_users = Gauge("esg_active_users", "Number of active users")
scraping_errors = Counter("esg_scraping_errors_total", "Total scraping errors")
analysis_scores = Histogram("esg_analysis_scores", "ESG analysis scores", ["category"])


# --- MODELS ---
class AnalyzeRequest(BaseModel):
    url: Optional[HttpUrl] = None
    text: Optional[str] = None
    company_name: Optional[str] = None
    quick_mode: bool = True  # Faster, cheaper analysis
    frameworks: List[str] = ["CSRD", "GRI", "SASB", "TCFD"]  # Which frameworks to check
    industry_sector: Optional[str] = None
    reporting_period: Optional[str] = None
    extract_metrics: bool = True

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com/sustainability-report",
                "company_name": "Example Corp",
                "quick_mode": False,
                "frameworks": ["CSRD", "TCFD"],
                "industry_sector": "Technology",
                "reporting_period": "2023",
            }
        }

    @validator("text")
    def validate_text_length(cls, v):
        if v and len(v) > 100000:  # 100k char limit
            raise ValueError("Text content too long (max 100k characters)")
        return v

    @validator("url", "text")
    def validate_input_provided(cls, v, values):
        if not v and not values.get("text") and not values.get("url"):
            raise ValueError("Either URL or text must be provided")
        return v

    @validator("frameworks")
    def validate_frameworks(cls, v):
        valid_frameworks = ["CSRD", "GRI", "SASB", "TCFD"]
        for framework in v:
            if framework not in valid_frameworks:
                raise ValueError(
                    f'Invalid framework: {framework}. Must be one of: {", ".join(valid_frameworks)}'
                )
        return v


class SubscriptionTier(BaseModel):
    tier: str  # free, starter, growth, enterprise
    credits: int
    price: float

    @validator("tier")
    def validate_tier(cls, v):
        valid_tiers = ["free", "starter", "growth", "enterprise"]
        if v not in valid_tiers:
            raise ValueError(f'Invalid tier. Must be one of: {", ".join(valid_tiers)}')
        return v


class UserRegistration(BaseModel):
    email: EmailStr

    class Config:
        json_schema_extra = {"example": {"email": "user@example.com"}}


class SubscriptionRequest(BaseModel):
    tier: str
    payment_method: str

    @validator("tier")
    def validate_tier(cls, v):
        valid_tiers = ["starter", "growth", "enterprise"]
        if v not in valid_tiers:
            raise ValueError(f'Invalid tier. Must be one of: {", ".join(valid_tiers)}')
        return v


class CompareRequest(BaseModel):
    companies: List[str]

    @validator("companies")
    def validate_companies(cls, v):
        if not v:
            raise ValueError("At least one company must be provided")
        if len(v) > 5:
            raise ValueError("Maximum 5 companies can be compared at once")
        return v


class ExportRequest(BaseModel):
    format: str = "json"

    @validator("format")
    def validate_format(cls, v):
        valid_formats = ["json", "csv"]
        if v not in valid_formats:
            raise ValueError(
                f'Invalid format. Must be one of: {", ".join(valid_formats)}'
            )
        return v


class ESGScoreResponse(BaseModel):
    environmental: float
    social: float
    governance: float
    overall: float

    class Config:
        json_schema_extra = {
            "example": {
                "environmental": 75.5,
                "social": 82.3,
                "governance": 79.1,
                "overall": 78.9,
            }
        }


# Enhanced response models for framework compliance
class FrameworkCoverage(BaseModel):
    framework: str
    coverage_percentage: float
    requirements_found: int
    requirements_total: int
    mandatory_met: int
    mandatory_total: int


class ExtractedMetric(BaseModel):
    metric_name: str
    metric_value: str
    metric_unit: str
    confidence: float
    requirement_id: Optional[str] = None
    framework: Optional[str] = None


class GapAnalysisItem(BaseModel):
    framework: str
    requirement_id: str
    category: str
    description: str
    severity: str


class RequirementFinding(BaseModel):
    requirement_id: str
    framework: str
    category: str
    subcategory: str
    description: str
    found: bool
    confidence: float
    keywords_matched: List[str]


class AnalysisResponse(BaseModel):
    scores: ESGScoreResponse
    keywords: List[str]
    insights: Optional[List[str]] = []
    sentiment: Optional[Dict[str, Any]] = None
    analysis_type: str
    confidence: float
    timestamp: str
    source: str
    credits_used: int
    credits_remaining: int
    company: Optional[str] = None
    peers: Optional[Dict[str, Any]] = None


class EnhancedAnalysisResponse(AnalysisResponse):
    """Enhanced response with framework compliance data"""

    framework_coverage: Optional[Dict[str, FrameworkCoverage]] = None
    extracted_metrics: Optional[List[ExtractedMetric]] = None
    gap_analysis: Optional[List[GapAnalysisItem]] = None
    recommendations: Optional[List[str]] = None
    requirement_findings: Optional[List[RequirementFinding]] = None


# --- CORE ENGINE ---
class LeanESGEngine:
    """Ultra-efficient ESG analysis engine"""

    def __init__(self):
        self.keyword_scorer = KeywordScorer()
        self.cache_ttl = 86400  # 24 hours

    async def analyze(
        self, content: str, company_name: str = None, quick_mode: bool = True
    ) -> Dict[str, Any]:
        """Fast ESG analysis with caching"""

        # Check cache first
        cache_key = f"esg:{hashlib.md5(content.encode()).hexdigest()}"
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)

        # Quick analysis (low cost)
        if quick_mode:
            result = self._quick_analysis(content)
        else:
            # Full analysis (higher cost, better accuracy)
            result = await self._full_analysis(content)

        # Add company context if provided
        if company_name:
            result["company"] = company_name
            result["peers"] = await self._get_peer_comparison(
                company_name, result["scores"]
            )

        # Cache result
        redis_client.setex(cache_key, self.cache_ttl, json.dumps(result))

        return result

    def _quick_analysis(self, content: str) -> Dict[str, Any]:
        """Fast keyword-based analysis"""
        # Simple keyword scoring
        scores = self.keyword_scorer.score(content)

        # Extract key insights
        kw_extractor = yake.KeywordExtractor(lan="en", n=2, top=10)
        keywords = [kw[0] for kw in kw_extractor.extract_keywords(content)]

        return {
            "scores": scores,
            "keywords": keywords,
            "analysis_type": "quick",
            "confidence": 0.7,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def _full_analysis(self, content: str) -> Dict[str, Any]:
        """Comprehensive ML-based analysis"""
        # Sentiment analysis
        sentiments = sentiment_analyzer(content[:512])  # Limit for performance

        # Advanced scoring
        scores = self.keyword_scorer.advanced_score(content, sentiments)

        # Extract insights
        insights = self._extract_insights(content, scores)

        return {
            "scores": scores,
            "insights": insights,
            "sentiment": sentiments[0] if sentiments else None,
            "analysis_type": "full",
            "confidence": 0.85,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def _get_peer_comparison(self, company: str, scores: Dict) -> Dict:
        """Simple peer comparison"""
        # In production, query from database
        # For now, return mock comparison
        industry_avg = {"environmental": 65, "social": 70, "governance": 72}

        return {
            "industry_average": industry_avg,
            "relative_performance": {
                k: "above" if scores.get(k, 0) > v else "below"
                for k, v in industry_avg.items()
            },
        }

    def _extract_insights(self, content: str, scores: Dict) -> List[str]:
        """Extract actionable insights"""
        insights = []

        # Score-based insights
        for category, score in scores.items():
            if score < 50:
                insights.append(f"Improve {category} disclosure and performance")
            elif score > 80:
                insights.append(f"Strong {category} performance detected")

        # Content-based insights
        if "net zero" in content.lower():
            insights.append("Net-zero commitment identified")
        if "diversity" in content.lower() and "target" in content.lower():
            insights.append("Diversity targets mentioned")

        return insights[:5]  # Limit insights


class KeywordScorer:
    """Efficient keyword-based ESG scoring"""

    def __init__(self):
        self.keywords = {
            "environmental": {
                "high_weight": [
                    "carbon neutral",
                    "net zero",
                    "renewable energy",
                    "science-based targets",
                ],
                "medium_weight": [
                    "emissions",
                    "climate",
                    "sustainability",
                    "recycling",
                ],
                "low_weight": ["environment", "green", "eco", "conservation"],
            },
            "social": {
                "high_weight": [
                    "human rights",
                    "diversity equity inclusion",
                    "employee wellbeing",
                ],
                "medium_weight": ["diversity", "safety", "community", "training"],
                "low_weight": ["social", "employee", "workplace", "engagement"],
            },
            "governance": {
                "high_weight": [
                    "board independence",
                    "executive compensation",
                    "audit committee",
                ],
                "medium_weight": ["governance", "ethics", "compliance", "transparency"],
                "low_weight": ["board", "management", "oversight", "control"],
            },
        }

    def score(self, content: str) -> Dict[str, float]:
        """Calculate ESG scores based on keywords"""
        content_lower = content.lower()
        scores = {}

        for category, keyword_groups in self.keywords.items():
            score = 0
            max_score = 0

            # High weight keywords (3 points each)
            for keyword in keyword_groups["high_weight"]:
                if keyword in content_lower:
                    score += 3
                max_score += 3

            # Medium weight keywords (2 points each)
            for keyword in keyword_groups["medium_weight"]:
                if keyword in content_lower:
                    score += 2
                max_score += 2

            # Low weight keywords (1 point each)
            for keyword in keyword_groups["low_weight"]:
                if keyword in content_lower:
                    score += 1
                max_score += 1

            # Normalize to 0-100
            scores[category] = min(
                100, (score / max_score * 100) if max_score > 0 else 0
            )

        # Overall score
        scores["overall"] = np.mean(list(scores.values()))

        return {k: round(v, 1) for k, v in scores.items()}

    def advanced_score(self, content: str, sentiment: Dict) -> Dict[str, float]:
        """Enhanced scoring with sentiment adjustment"""
        base_scores = self.score(content)

        # Adjust based on sentiment
        if sentiment and sentiment.get("label") == "POSITIVE":
            multiplier = 1.1
        elif sentiment and sentiment.get("label") == "NEGATIVE":
            multiplier = 0.9
        else:
            multiplier = 1.0

        return {k: round(v * multiplier, 1) for k, v in base_scores.items()}


# Enhanced ESG Engine with framework compliance
class EnhancedESGEngine(LeanESGEngine):
    """Enhanced ESG analysis engine with framework compliance"""

    def __init__(self):
        super().__init__()
        self.framework_manager = ESGFrameworkManager()
        self.enhanced_keyword_scorer = EnhancedKeywordScorer()

    async def analyze(
        self,
        content: str,
        company_name: str = None,
        quick_mode: bool = True,
        frameworks: List[str] = None,
        industry_sector: str = None,
        extract_metrics: bool = True,
    ) -> Dict[str, Any]:
        """Enhanced analysis with framework compliance checking"""

        # Get base analysis
        base_result = await super().analyze(content, company_name, quick_mode)

        if not quick_mode and frameworks:
            # Perform framework analysis
            framework_results = self._analyze_frameworks(content, frameworks)

            # Extract metrics if requested
            metrics = []
            if extract_metrics:
                metrics = self._extract_all_metrics(
                    content, framework_results["requirements"]
                )

            # Calculate coverage
            coverage = self._calculate_coverage(framework_results)

            # Generate gap analysis
            gaps = self._generate_gaps(framework_results, industry_sector)

            # Generate recommendations
            recommendations = self._generate_recommendations(gaps, coverage)

            # Get requirement findings
            requirement_findings = self._get_requirement_findings(
                framework_results, content
            )

            # Enhance base result
            base_result.update(
                {
                    "framework_coverage": coverage,
                    "extracted_metrics": metrics,
                    "gap_analysis": gaps,
                    "recommendations": recommendations,
                    "requirement_findings": requirement_findings,
                }
            )

        return base_result

    def _analyze_frameworks(
        self, content: str, framework_names: List[str]
    ) -> Dict[str, Any]:
        """Analyze content against specified frameworks"""
        frameworks = [
            Framework[name] for name in framework_names if name in Framework.__members__
        ]

        # Find relevant requirements
        found_requirements = self.framework_manager.find_relevant_requirements(content)

        # Filter by requested frameworks
        filtered_requirements = {
            framework: reqs
            for framework, reqs in found_requirements.items()
            if framework in frameworks
        }

        return {
            "requirements": filtered_requirements,
            "all_requirements": {
                framework: self.framework_manager.requirements[framework]
                for framework in frameworks
            },
        }

    def _extract_all_metrics(
        self, content: str, requirements: Dict[Framework, List[DisclosureRequirement]]
    ) -> List[Dict[str, Any]]:
        """Extract all metrics from content"""
        all_metrics = []

        for framework, reqs in requirements.items():
            metrics = self.framework_manager.extract_metrics(content, reqs)

            for req_id, req_metrics in metrics.items():
                for metric_unit, values in req_metrics.items():
                    for value in values:
                        all_metrics.append(
                            {
                                "metric_name": metric_unit,
                                "metric_value": value,
                                "metric_unit": metric_unit,
                                "confidence": 0.8,  # Would use ML model for real confidence
                                "requirement_id": req_id,
                                "framework": framework.value,
                            }
                        )

        return all_metrics

    def _calculate_coverage(
        self, framework_results: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """Calculate coverage for each framework"""
        coverage = {}

        for framework in framework_results["all_requirements"].keys():
            total_reqs = len(framework_results["all_requirements"][framework])
            found_reqs = len(framework_results["requirements"].get(framework, []))

            mandatory_total = len(
                [
                    r
                    for r in framework_results["all_requirements"][framework]
                    if r.mandatory
                ]
            )
            mandatory_found = len(
                [
                    r
                    for r in framework_results["requirements"].get(framework, [])
                    if r.mandatory
                ]
            )

            coverage[framework.value] = {
                "framework": framework.value,
                "coverage_percentage": (
                    (found_reqs / total_reqs * 100) if total_reqs > 0 else 0
                ),
                "requirements_found": found_reqs,
                "requirements_total": total_reqs,
                "mandatory_met": mandatory_found,
                "mandatory_total": mandatory_total,
            }

        return coverage

    def _generate_gaps(
        self, framework_results: Dict[str, Any], industry_sector: str = None
    ) -> List[Dict[str, Any]]:
        """Generate gap analysis"""
        gaps = []

        gap_analysis = self.framework_manager.generate_gap_analysis(
            framework_results["requirements"]
        )

        for framework, missing_reqs in gap_analysis.items():
            for req in missing_reqs:
                # Determine severity based on framework and industry
                severity = self._determine_severity(req, framework, industry_sector)

                gaps.append(
                    {
                        "framework": framework.value,
                        "requirement_id": req.requirement_id,
                        "category": req.category,
                        "description": req.description,
                        "severity": severity,
                    }
                )

        return gaps

    def _determine_severity(
        self,
        requirement: DisclosureRequirement,
        framework: Framework,
        industry: str = None,
    ) -> str:
        """Determine severity of missing requirement"""
        # CSRD is mandatory in EU
        if framework == Framework.CSRD and requirement.mandatory:
            return "critical"

        # Industry-specific logic
        if industry:
            industry_lower = industry.lower()
            if (
                industry_lower in ["energy", "utilities", "oil & gas"]
                and "emission" in requirement.description.lower()
            ):
                return "critical"
            elif (
                industry_lower in ["technology", "finance"]
                and "data" in requirement.description.lower()
            ):
                return "high"
            elif (
                industry_lower in ["manufacturing", "automotive"]
                and "supply chain" in requirement.description.lower()
            ):
                return "high"

        # Default based on mandatory status
        return "high" if requirement.mandatory else "medium"

    def _generate_recommendations(
        self, gaps: List[Dict[str, Any]], coverage: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        # Framework-specific recommendations
        for framework_name, cov in coverage.items():
            if cov["coverage_percentage"] < 50:
                recommendations.append(
                    f"Improve {framework_name} disclosure: Currently at {cov['coverage_percentage']:.1f}% coverage. "
                    f"Focus on {cov['mandatory_total'] - cov['mandatory_met']} missing mandatory requirements."
                )

        # Category-specific recommendations
        critical_gaps = [g for g in gaps if g["severity"] == "critical"]
        if critical_gaps:
            categories = set(g["category"] for g in critical_gaps)
            for category in categories:
                recommendations.append(
                    f"Critical gap in {category}: Immediate action required to meet regulatory requirements."
                )

        # High severity gaps
        high_gaps = [g for g in gaps if g["severity"] == "high"]
        if high_gaps:
            categories = set(g["category"] for g in high_gaps[:3])  # Top 3 categories
            recommendations.append(
                f"Priority areas for improvement: {', '.join(categories)}"
            )

        # Positive recommendations
        for framework_name, cov in coverage.items():
            if cov["coverage_percentage"] > 80:
                recommendations.append(
                    f"Strong {framework_name} compliance ({cov['coverage_percentage']:.1f}%). "
                    f"Consider pursuing certification or external verification."
                )

        return recommendations[:10]  # Limit recommendations

    def _get_requirement_findings(
        self, framework_results: Dict[str, Any], content: str
    ) -> List[Dict[str, Any]]:
        """Get detailed findings for each requirement"""
        findings = []
        content_lower = content.lower()

        for framework, requirements in framework_results["requirements"].items():
            for req in requirements:
                # Find which keywords were matched
                matched_keywords = [
                    kw for kw in req.keywords if kw.lower() in content_lower
                ]

                findings.append(
                    {
                        "requirement_id": req.requirement_id,
                        "framework": framework.value,
                        "category": req.category,
                        "subcategory": req.subcategory,
                        "description": req.description,
                        "found": True,
                        "confidence": min(
                            0.9, 0.3 + (0.1 * len(matched_keywords))
                        ),  # Simple confidence calculation
                        "keywords_matched": matched_keywords,
                    }
                )

        return findings


# Enhanced Keyword Scorer with framework alignment
class EnhancedKeywordScorer(KeywordScorer):
    """Enhanced keyword scorer aligned with ESG frameworks"""

    def __init__(self):
        super().__init__()
        # Enhance keywords based on frameworks
        self.keywords["environmental"].update(
            {
                "csrd_aligned": [
                    "double materiality",
                    "transition plan",
                    "climate scenario",
                    "taxonomy alignment",
                    "dnsh",
                    "do no significant harm",
                ],
                "tcfd_aligned": [
                    "physical risk",
                    "transition risk",
                    "climate opportunity",
                    "scenario analysis",
                    "2 degree scenario",
                    "1.5 degree",
                ],
                "gri_aligned": [
                    "material topics",
                    "stakeholder impact",
                    "environmental management",
                ],
                "sasb_aligned": [
                    "financially material",
                    "industry-specific",
                    "operational efficiency",
                ],
            }
        )

        self.keywords["social"].update(
            {
                "csrd_aligned": [
                    "due diligence",
                    "value chain workers",
                    "affected communities",
                    "consumer safety",
                    "data protection",
                    "gdpr",
                ],
                "gri_aligned": [
                    "stakeholder engagement",
                    "material topics",
                    "human rights assessment",
                    "collective bargaining",
                    "local communities",
                ],
                "sasb_aligned": ["human capital", "social capital", "customer welfare"],
            }
        )

        self.keywords["governance"].update(
            {
                "csrd_aligned": [
                    "sustainability governance",
                    "remuneration policy",
                    "business conduct",
                    "whistleblower protection",
                    "anti-corruption",
                ],
                "sasb_aligned": [
                    "systemic risk",
                    "competitive behavior",
                    "regulatory capture",
                    "political influence",
                    "lobbying",
                ],
                "tcfd_aligned": [
                    "climate governance",
                    "board oversight",
                    "risk committee",
                ],
            }
        )


# --- WEB SCRAPER ---
class LeanScraper:
    """Minimal, efficient web scraper with fallback options"""

    def __init__(self):
        # Check if trafilatura is available
        try:
            import trafilatura

            self.has_trafilatura = True
            self.trafilatura = trafilatura
        except ImportError:
            self.has_trafilatura = False
            logger.warning("Trafilatura not available, using fallback scraper")

    def _is_safe_url(self, url: str) -> bool:
        """Validate URL for safety to prevent SSRF attacks"""
        try:
            parsed = urlparse(url)

            # Check scheme
            if parsed.scheme not in ["http", "https"]:
                return False

            # Block internal hostnames
            blocked_hosts = [
                "localhost",
                "127.0.0.1",
                "0.0.0.0",
                "169.254.169.254",
                "metadata.google.internal",
            ]
            if parsed.hostname and parsed.hostname.lower() in blocked_hosts:
                return False

            # Block private IP ranges
            import socket
            import ipaddress

            try:
                ip = socket.gethostbyname(parsed.hostname)
                ip_obj = ipaddress.ip_address(ip)
                if ip_obj.is_private or ip_obj.is_reserved or ip_obj.is_loopback:
                    return False
            except Exception:
                pass

            return True
        except Exception:
            return False

    def _fallback_scrape(self, html_content: str) -> str:
        """Fallback scraping using BeautifulSoup only"""
        try:
            soup = BeautifulSoup(html_content, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            # Try to find main content areas first
            main_content = (
                soup.find("main")
                or soup.find("article")
                or soup.find("div", {"class": ["content", "main", "article"]})
            )

            if main_content:
                text = main_content.get_text(separator=" ", strip=True)
            else:
                text = soup.get_text(separator=" ", strip=True)

            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = " ".join(chunk for chunk in chunks if chunk)

            return text

        except Exception as e:
            logger.error(f"Fallback scraping failed: {e}")
            return html_content  # Return raw HTML as last resort

    async def scrape(self, url: str) -> str:
        """Scrape and extract main content with fallback options"""
        # Validate URL first
        if not self._is_safe_url(url):
            raise ValueError("Invalid or unsafe URL")

        async with httpx.AsyncClient(timeout=10) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                html_content = response.text

                # Try trafilatura first if available
                if self.has_trafilatura:
                    try:
                        content = self.trafilatura.extract(html_content)
                        if (
                            content and len(content.strip()) > 100
                        ):  # Ensure we got meaningful content
                            return content[:50000]  # Limit content size
                        else:
                            logger.warning(
                                "Trafilatura extracted insufficient content, using fallback"
                            )
                    except Exception as e:
                        logger.warning(
                            f"Trafilatura extraction failed: {e}, using fallback"
                        )

                # Fallback to BeautifulSoup
                content = self._fallback_scrape(html_content)
                return content[:50000]  # Limit content size

            except httpx.HTTPError as e:
                logger.error(f"HTTP error while scraping {url}: {e}")
                raise ValueError(f"Failed to fetch URL: {e}")
            except Exception as e:
                logger.error(f"Unexpected error while scraping {url}: {e}")
                raise ValueError(f"Scraping failed: {e}")


# --- USAGE TRACKING ---
class UsageTracker:
    """Track API usage for billing"""

    def __init__(self):
        self.costs = {"analyze_quick": 1, "analyze_full": 5, "scrape": 2, "export": 10}

    async def track_usage(self, user_id: str, operation: str, count: int = 1):
        """Track usage and check limits"""
        key = f"usage:{user_id}:{datetime.utcnow().strftime('%Y-%m')}"

        # Get current usage
        current = int(redis_client.get(key) or 0)

        # Check limit
        user_limit = await self.get_user_limit(user_id)
        cost = self.costs.get(operation, 1) * count

        if current + cost > user_limit:
            raise HTTPException(status_code=429, detail="Usage limit exceeded")

        # Track usage
        redis_client.incrby(key, cost)
        redis_client.expire(key, 86400 * 31)  # 31 days

        return current + cost

    async def get_user_limit(self, user_id: str) -> int:
        """Get user's credit limit based on subscription"""
        sub_key = f"subscription:{user_id}"
        subscription = redis_client.hgetall(sub_key)

        if not subscription:
            return FREE_TIER_CREDITS

        tier_limits = {
            "free": 100,
            "starter": 1000,
            "growth": 5000,
            "enterprise": 50000,
        }

        return tier_limits.get(subscription.get("tier", "free"), FREE_TIER_CREDITS)


# --- AUTH ---
def create_token(user_id: str) -> str:
    """Create JWT token"""
    payload = {"user_id": user_id, "exp": datetime.utcnow() + timedelta(days=30)}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        return payload["user_id"]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


# --- API ENDPOINTS ---
engine = EnhancedESGEngine()  # Use enhanced engine
scraper = LeanScraper()
usage_tracker = UsageTracker()


@app.post("/auth/register")
async def register(registration: UserRegistration):
    """Register new user with free tier"""
    user_id = hashlib.md5(registration.email.encode()).hexdigest()

    # Check if exists
    if redis_client.exists(f"user:{user_id}"):
        raise HTTPException(status_code=400, detail="User already exists")

    # Create user
    redis_client.hset(
        f"user:{user_id}",
        mapping={
            "email": registration.email,
            "created": datetime.utcnow().isoformat(),
            "tier": "free",
        },
    )

    # Set subscription
    redis_client.hset(
        f"subscription:{user_id}",
        mapping={"tier": "free", "credits": FREE_TIER_CREDITS},
    )

    token = create_token(user_id)

    return {"token": token, "tier": "free", "credits": FREE_TIER_CREDITS}


@app.post("/analyze", response_model=EnhancedAnalysisResponse)
async def analyze_endpoint(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(verify_token),
):
    """Enhanced analysis endpoint with framework compliance"""
    # Check rate limit
    await check_rate_limit(user_id, "analyze")

    # Track usage
    operation = "analyze_quick" if request.quick_mode else "analyze_full"
    usage = await usage_tracker.track_usage(user_id, operation)

    # Get content
    if request.url:
        content = await scraper.scrape(str(request.url))
        source = str(request.url)
    elif request.text:
        content = request.text
        source = "direct_text"
    else:
        raise HTTPException(status_code=400, detail="Provide URL or text")

    # Enhanced analysis with frameworks
    result = await engine.analyze(
        content,
        request.company_name,
        request.quick_mode,
        request.frameworks,
        request.industry_sector,
        request.extract_metrics,
    )

    # Add metadata
    result["source"] = source
    result["credits_used"] = usage_tracker.costs[operation]
    result["credits_remaining"] = await usage_tracker.get_user_limit(user_id) - usage

    # Save to enhanced database
    await db_manager.save_analysis(
        user_id, source, result, request.industry_sector, request.reporting_period
    )

    # Log for analytics (async)
    background_tasks.add_task(
        log_analytics, user_id, operation, result["scores"]["overall"]
    )

    # Update metrics
    analysis_scores.labels(category="environmental").observe(
        result["scores"]["environmental"]
    )
    analysis_scores.labels(category="social").observe(result["scores"]["social"])
    analysis_scores.labels(category="governance").observe(
        result["scores"]["governance"]
    )

    return result


@app.post("/compare")
async def compare_companies(
    request: CompareRequest, user_id: str = Depends(verify_token)
):
    """Compare multiple companies"""
    # Track usage
    await usage_tracker.track_usage(user_id, "analyze_quick", len(request.companies))

    results = {}
    for company in request.companies:
        # Check cache
        cache_key = f"company:{company.strip().lower()}"
        cached = redis_client.get(cache_key)

        if cached:
            results[company] = json.loads(cached)
        else:
            # Mock data for demo - in production, pull from database
            results[company] = {
                "scores": {
                    "environmental": np.random.randint(40, 90),
                    "social": np.random.randint(40, 90),
                    "governance": np.random.randint(40, 90),
                    "overall": np.random.randint(40, 90),
                },
                "trend": np.random.choice(["improving", "stable", "declining"]),
            }

            # Cache for 1 hour
            redis_client.setex(cache_key, 3600, json.dumps(results[company]))

    return {
        "companies": results,
        "benchmark": {"environmental": 65, "social": 70, "governance": 72},
    }


@app.post("/export")
async def export_data(request: ExportRequest, user_id: str = Depends(verify_token)):
    """Export analysis data"""
    # Track usage
    await usage_tracker.track_usage(user_id, "export")

    # Get user's recent analyses
    analyses = await db_manager.get_user_analyses(user_id)

    if request.format == "json":
        return {"data": analyses}
    elif request.format == "csv":
        # Convert to CSV
        import io
        import csv

        output = io.StringIO()
        if analyses:
            fieldnames = analyses[0].keys()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(analyses)

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=esg_data.csv"},
        )


@app.get("/usage")
async def get_usage(user_id: str = Depends(verify_token)):
    """Get usage statistics"""
    key = f"usage:{user_id}:{datetime.utcnow().strftime('%Y-%m')}"
    current_usage = int(redis_client.get(key) or 0)
    limit = await usage_tracker.get_user_limit(user_id)

    return {
        "current_usage": current_usage,
        "limit": limit,
        "percentage": round((current_usage / limit * 100), 1) if limit > 0 else 0,
        "reset_date": (datetime.utcnow().replace(day=1) + timedelta(days=31)).strftime(
            "%Y-%m-%d"
        ),
    }


@app.post("/subscribe")
async def subscribe(request: SubscriptionRequest, user_id: str = Depends(verify_token)):
    """Subscribe to paid tier"""
    tiers = {
        "starter": {"price": 49, "credits": 1000},
        "growth": {"price": 199, "credits": 5000},
        "enterprise": {"price": 999, "credits": 50000},
    }

    tier_info = tiers[request.tier]

    # Process payment (Stripe)
    try:
        # Create Stripe subscription
        customer = stripe.Customer.create(
            email=redis_client.hget(f"user:{user_id}", "email"),
            payment_method=request.payment_method,
            invoice_settings={"default_payment_method": request.payment_method},
        )

        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{"price": f"price_{request.tier}"}],  # Stripe price IDs
            expand=["latest_invoice.payment_intent"],
        )

        # Update user subscription
        redis_client.hset(
            f"subscription:{user_id}",
            mapping={
                "tier": request.tier,
                "credits": tier_info["credits"],
                "stripe_customer_id": customer.id,
                "stripe_subscription_id": subscription.id,
                "updated": datetime.utcnow().isoformat(),
            },
        )

        return {"success": True, "tier": request.tier, "credits": tier_info["credits"]}

    except Exception as e:
        logger.error(f"Subscription error for user {user_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
    }


# New framework-specific endpoints
@app.get("/frameworks")
async def get_frameworks():
    """Get available ESG frameworks and their requirements"""
    framework_info = {}
    manager = ESGFrameworkManager()

    for framework in Framework:
        requirements = manager.requirements[framework]
        framework_info[framework.value] = {
            "name": framework.value,
            "total_requirements": len(requirements),
            "mandatory_requirements": len([r for r in requirements if r.mandatory]),
            "categories": list(set(r.category for r in requirements)),
        }

    return {"frameworks": framework_info}


@app.get("/company/{company_name}/history")
async def get_company_esg_history(
    company_name: str, days: int = 90, user_id: str = Depends(verify_token)
):
    """Get historical ESG scores and framework compliance for a company"""
    history = await db_manager.get_company_history(company_name, days)

    if not history:
        raise HTTPException(
            status_code=404, detail="No historical data found for this company"
        )

    # Process framework coverage from JSON
    for record in history:
        if record.get("framework_coverage"):
            record["framework_coverage"] = json.loads(record["framework_coverage"])

    return {
        "company": company_name,
        "period_days": days,
        "history": history,
        "trend": _calculate_trend(history),
    }


@app.get("/analysis/{analysis_id}/gaps")
async def get_analysis_gaps(analysis_id: int, user_id: str = Depends(verify_token)):
    """Get detailed gap analysis for a specific analysis"""
    gaps = await db_manager.get_framework_gaps(analysis_id)

    if not gaps:
        raise HTTPException(
            status_code=404, detail="No gap analysis found for this analysis"
        )

    # Group by framework and severity
    grouped_gaps = {}
    for gap in gaps:
        framework = gap["framework"]
        if framework not in grouped_gaps:
            grouped_gaps[framework] = {
                "critical": [],
                "high": [],
                "medium": [],
                "low": [],
            }
        grouped_gaps[framework][gap["severity"]].append(gap)

    return {
        "analysis_id": analysis_id,
        "total_gaps": len(gaps),
        "gaps_by_framework": grouped_gaps,
        "critical_count": len([g for g in gaps if g["severity"] == "critical"]),
        "high_count": len([g for g in gaps if g["severity"] == "high"]),
    }


@app.post("/benchmark")
async def benchmark_companies(
    companies: List[str],
    frameworks: List[str] = ["CSRD", "TCFD"],
    user_id: str = Depends(verify_token),
):
    """Benchmark multiple companies against ESG frameworks"""
    if len(companies) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 companies allowed")

    # Track usage
    await usage_tracker.track_usage(user_id, "analyze_quick", len(companies))

    results = {}
    for company in companies:
        # Get latest analysis for each company
        # In production, this would query the database
        # For now, return mock data
        results[company] = {
            "scores": {
                "environmental": np.random.randint(40, 90),
                "social": np.random.randint(40, 90),
                "governance": np.random.randint(40, 90),
                "overall": np.random.randint(40, 90),
            },
            "framework_compliance": {
                framework: {
                    "coverage": np.random.randint(30, 95),
                    "mandatory_met": np.random.randint(5, 15),
                }
                for framework in frameworks
            },
        }

    # Calculate averages
    avg_scores = {
        "environmental": np.mean(
            [r["scores"]["environmental"] for r in results.values()]
        ),
        "social": np.mean([r["scores"]["social"] for r in results.values()]),
        "governance": np.mean([r["scores"]["governance"] for r in results.values()]),
        "overall": np.mean([r["scores"]["overall"] for r in results.values()]),
    }

    return {
        "companies": results,
        "average_scores": avg_scores,
        "best_performer": max(results.items(), key=lambda x: x[1]["scores"]["overall"])[
            0
        ],
        "frameworks_analyzed": frameworks,
    }


def _calculate_trend(history: List[Dict]) -> Dict[str, str]:
    """Calculate trend from historical data"""
    if len(history) < 2:
        return {"overall": "insufficient_data"}

    # Sort by date
    sorted_history = sorted(history, key=lambda x: x["analysis_date"])

    trends = {}
    for score_type in ["environmental", "social", "governance", "overall"]:
        recent = sorted_history[-1][f"{score_type}_score"]
        previous = sorted_history[-2][f"{score_type}_score"]

        if recent > previous + 2:
            trends[score_type] = "improving"
        elif recent < previous - 2:
            trends[score_type] = "declining"
        else:
            trends[score_type] = "stable"

    return trends


# --- ANALYTICS ---
async def log_analytics(user_id: str, operation: str, score: float):
    """Log usage analytics"""
    # Simple analytics - in production, use proper analytics service
    key = f"analytics:{datetime.utcnow().strftime('%Y-%m-%d')}"
    redis_client.hincrby(key, operation, 1)
    redis_client.expire(key, 86400 * 90)  # 90 days


# --- RATE LIMITING ---
class RateLimiter:
    """Simple in-memory rate limiter"""

    def __init__(self):
        self.requests = defaultdict(list)

    def is_allowed(self, key: str, max_requests: int = 10, window: int = 60) -> bool:
        """Check if request is allowed within rate limit"""
        now = time.time()
        # Clean old requests
        self.requests[key] = [t for t in self.requests[key] if now - t < window]

        if len(self.requests[key]) >= max_requests:
            return False

        self.requests[key].append(now)
        return True


rate_limiter = RateLimiter()


async def check_rate_limit(user_id: str, operation: str = "default"):
    """Check rate limit for user"""
    key = f"{user_id}:{operation}"
    if not rate_limiter.is_allowed(key):
        raise HTTPException(
            status_code=429, detail="Rate limit exceeded. Please try again later."
        )


# --- DATABASE ---
class DatabaseManager:
    """Base SQLite database manager"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or DATABASE_PATH
        self.init_db()

    def init_db(self):
        """Initialize basic database tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON analyses(user_id)")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_company_name ON analyses(company_name)"
            )


class EnhancedDatabaseManager(DatabaseManager):
    """Enhanced SQLite database manager with framework compliance support"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or DATABASE_PATH
        self.init_db()

    def init_db(self):
        """Initialize enhanced database tables"""
        with sqlite3.connect(self.db_path) as conn:
            # Execute the enhanced schema
            conn.executescript(database_schema.ENHANCED_SCHEMA)

    async def save_analysis(
        self,
        user_id: str,
        source: str,
        result: Dict[str, Any],
        industry_sector: str = None,
        reporting_period: str = None,
    ):
        """Save enhanced analysis result to database"""
        with sqlite3.connect(self.db_path) as conn:
            # Save main analysis
            cursor = conn.execute(
                """
                INSERT INTO analyses (
                    user_id, source_url, company_name,
                    environmental_score, social_score, governance_score, overall_score,
                    keywords, insights, analysis_type,
                    industry_sector, reporting_period
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    user_id,
                    source,
                    result.get("company"),
                    result["scores"].get("environmental", 0),
                    result["scores"].get("social", 0),
                    result["scores"].get("governance", 0),
                    result["scores"].get("overall", 0),
                    json.dumps(result.get("keywords", [])),
                    json.dumps(result.get("insights", [])),
                    result.get("analysis_type", "unknown"),
                    industry_sector,
                    reporting_period,
                ),
            )

            analysis_id = cursor.lastrowid

            # Save framework compliance data
            if result.get("framework_coverage"):
                for framework_name, coverage in result["framework_coverage"].items():
                    conn.execute(
                        """
                        INSERT INTO framework_compliance (
                            analysis_id, framework, coverage_percentage,
                            requirements_found, requirements_total,
                            mandatory_met, mandatory_total
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            analysis_id,
                            framework_name,
                            coverage["coverage_percentage"],
                            coverage["requirements_found"],
                            coverage["requirements_total"],
                            coverage["mandatory_met"],
                            coverage["mandatory_total"],
                        ),
                    )

            # Save requirement findings
            if result.get("requirement_findings"):
                for finding in result["requirement_findings"]:
                    conn.execute(
                        """
                        INSERT INTO requirement_findings (
                            analysis_id, framework, requirement_id,
                            category, subcategory, description,
                            found, confidence_score, extracted_text
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            analysis_id,
                            finding["framework"],
                            finding["requirement_id"],
                            finding["category"],
                            finding["subcategory"],
                            finding["description"],
                            finding["found"],
                            finding["confidence"],
                            json.dumps(finding.get("keywords_matched", [])),
                        ),
                    )

            # Save extracted metrics
            if result.get("extracted_metrics"):
                for metric in result["extracted_metrics"]:
                    conn.execute(
                        """
                        INSERT INTO extracted_metrics (
                            analysis_id, requirement_id, metric_name,
                            metric_value, metric_unit, confidence_score
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                        (
                            analysis_id,
                            metric.get("requirement_id"),
                            metric["metric_name"],
                            metric["metric_value"],
                            metric["metric_unit"],
                            metric["confidence"],
                        ),
                    )

            # Save gap analysis
            if result.get("gap_analysis"):
                for gap in result["gap_analysis"]:
                    conn.execute(
                        """
                        INSERT INTO gap_analysis (
                            analysis_id, framework, requirement_id,
                            category, description, severity,
                            recommendation
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            analysis_id,
                            gap["framework"],
                            gap["requirement_id"],
                            gap["category"],
                            gap["description"],
                            gap["severity"],
                            gap.get("recommendation", ""),
                        ),
                    )

            # Update company profile if provided
            if result.get("company") and industry_sector:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO company_profiles (
                        company_name, industry_sector
                    ) VALUES (?, ?)
                """,
                    (result["company"], industry_sector),
                )

            # Save historical score
            if result.get("company"):
                conn.execute(
                    """
                    INSERT INTO historical_scores (
                        company_name, analysis_date,
                        environmental_score, social_score,
                        governance_score, overall_score,
                        framework_coverage
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        result["company"],
                        datetime.utcnow().date(),
                        result["scores"].get("environmental", 0),
                        result["scores"].get("social", 0),
                        result["scores"].get("governance", 0),
                        result["scores"].get("overall", 0),
                        json.dumps(result.get("framework_coverage", {})),
                    ),
                )

    async def get_user_analyses(self, user_id: str, limit: int = 10):
        """Get recent analyses with framework data for a user"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT a.*,
                       GROUP_CONCAT(DISTINCT fc.framework || ':' || fc.coverage_percentage) as framework_scores
                FROM analyses a
                LEFT JOIN framework_compliance fc ON a.id = fc.analysis_id
                WHERE a.user_id = ?
                GROUP BY a.id
                ORDER BY a.created_at DESC
                LIMIT ?
            """,
                (user_id, limit),
            )

            return [dict(row) for row in cursor.fetchall()]

    async def get_company_history(self, company_name: str, days: int = 90):
        """Get historical ESG scores for a company"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT * FROM historical_scores
                WHERE company_name = ?
                AND analysis_date >= date('now', '-' || ? || ' days')
                ORDER BY analysis_date DESC
            """,
                (company_name, days),
            )

            return [dict(row) for row in cursor.fetchall()]

    async def get_framework_gaps(self, analysis_id: int):
        """Get gap analysis for a specific analysis"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT * FROM gap_analysis
                WHERE analysis_id = ?
                ORDER BY severity DESC, framework
            """,
                (analysis_id,),
            )

            return [dict(row) for row in cursor.fetchall()]


# Initialize enhanced database
db_manager = EnhancedDatabaseManager()


# --- MIDDLEWARE ---
@app.middleware("http")
async def add_metrics(request, call_next):
    """Add Prometheus metrics to all requests"""
    start_time = time.time()

    # Process request
    response = await call_next(request)

    # Record metrics
    duration = time.time() - start_time
    request_count.labels(
        method=request.method, endpoint=request.url.path, status=response.status_code
    ).inc()

    request_duration.labels(method=request.method, endpoint=request.url.path).observe(
        duration
    )

    return response


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type="text/plain")


# After app initialization, add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    # Initialize database on startup
    db_manager = EnhancedDatabaseManager()
    db_manager.init_db()

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Run the application
    uvicorn.run(app, host="0.0.0.0", port=8000)
