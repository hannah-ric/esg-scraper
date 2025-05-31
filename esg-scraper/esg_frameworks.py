"""
ESG Framework Analysis Module
============================

This module provides comprehensive ESG framework analysis capabilities including:
- CSRD (Corporate Sustainability Reporting Directive)
- GRI (Global Reporting Initiative)
- SASB (Sustainability Accounting Standards Board)
- TCFD (Task Force on Climate-related Financial Disclosures)

Each framework includes specific requirements, keywords, and metrics extraction patterns.
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple
import re
from collections import defaultdict


class Framework(Enum):
    """ESG Framework enumeration"""

    CSRD = "CSRD"
    GRI = "GRI"
    SASB = "SASB"
    TCFD = "TCFD"


@dataclass
class DisclosureRequirement:
    """Individual disclosure requirement within a framework"""

    requirement_id: str
    framework: Framework
    category: str
    subcategory: str
    description: str
    keywords: List[str]
    mandatory: bool
    metrics_patterns: List[str] = None

    def __post_init__(self):
        if self.metrics_patterns is None:
            self.metrics_patterns = []


class ESGFrameworkManager:
    """Manager for ESG framework analysis and compliance checking"""

    def __init__(self):
        self.requirements = self._initialize_requirements()
        self.keyword_index = self._build_keyword_index()
        self.metrics_extractors = self._build_metrics_extractors()

    def _initialize_requirements(self) -> Dict[Framework, List[DisclosureRequirement]]:
        """Initialize all framework requirements"""
        requirements = {}

        # CSRD Requirements
        requirements[Framework.CSRD] = self._get_csrd_requirements()

        # GRI Requirements
        requirements[Framework.GRI] = self._get_gri_requirements()

        # SASB Requirements
        requirements[Framework.SASB] = self._get_sasb_requirements()

        # TCFD Requirements
        requirements[Framework.TCFD] = self._get_tcfd_requirements()

        return requirements

    def _get_csrd_requirements(self) -> List[DisclosureRequirement]:
        """Corporate Sustainability Reporting Directive requirements"""
        return [
            # Environmental - Climate Change
            DisclosureRequirement(
                requirement_id="CSRD-E1-1",
                framework=Framework.CSRD,
                category="Environmental",
                subcategory="Climate Change",
                description="Transition plan for climate change mitigation",
                keywords=[
                    "transition plan",
                    "climate mitigation",
                    "net zero",
                    "carbon neutral",
                    "decarbonization",
                ],
                mandatory=True,
                metrics_patterns=[
                    r"(\d+\.?\d*)\s*%.*emission.*reduction",
                    r"net zero.*(\d{4})",
                ],
            ),
            DisclosureRequirement(
                requirement_id="CSRD-E1-2",
                framework=Framework.CSRD,
                category="Environmental",
                subcategory="Climate Change",
                description="Physical and transition risks from climate change",
                keywords=[
                    "physical risk",
                    "transition risk",
                    "climate risk",
                    "scenario analysis",
                ],
                mandatory=True,
                metrics_patterns=[r"(\d+\.?\d*)\s*(billion|million).*risk exposure"],
            ),
            DisclosureRequirement(
                requirement_id="CSRD-E1-3",
                framework=Framework.CSRD,
                category="Environmental",
                subcategory="Climate Change",
                description="GHG emissions and energy consumption",
                keywords=[
                    "scope 1",
                    "scope 2",
                    "scope 3",
                    "ghg emissions",
                    "greenhouse gas",
                    "energy consumption",
                ],
                mandatory=True,
                metrics_patterns=[
                    r"(\d+\.?\d*)\s*t.*co2",
                    r"(\d+\.?\d*)\s*tonnes.*carbon",
                    r"(\d+\.?\d*)\s*(kwh|mwh|gwh)",
                ],
            ),
            # Environmental - Pollution
            DisclosureRequirement(
                requirement_id="CSRD-E2-1",
                framework=Framework.CSRD,
                category="Environmental",
                subcategory="Pollution",
                description="Air, water and soil pollution",
                keywords=[
                    "air pollution",
                    "water pollution",
                    "soil pollution",
                    "emissions to air",
                    "emissions to water",
                ],
                mandatory=True,
                metrics_patterns=[r"(\d+\.?\d*)\s*(mg|g|kg|tonnes).*pollutant"],
            ),
            # Environmental - Water and Marine Resources
            DisclosureRequirement(
                requirement_id="CSRD-E3-1",
                framework=Framework.CSRD,
                category="Environmental",
                subcategory="Water and Marine Resources",
                description="Water consumption and marine resources impact",
                keywords=[
                    "water consumption",
                    "water withdrawal",
                    "water discharge",
                    "marine resources",
                    "water stress",
                ],
                mandatory=True,
                metrics_patterns=[
                    r"(\d+\.?\d*)\s*(m3|liters|litres).*water",
                    r"(\d+\.?\d*)\s*megalit",
                ],
            ),
            # Environmental - Biodiversity and Ecosystems
            DisclosureRequirement(
                requirement_id="CSRD-E4-1",
                framework=Framework.CSRD,
                category="Environmental",
                subcategory="Biodiversity and Ecosystems",
                description="Biodiversity and ecosystems impact",
                keywords=[
                    "biodiversity",
                    "ecosystem",
                    "habitat",
                    "species",
                    "deforestation",
                    "nature",
                ],
                mandatory=True,
                metrics_patterns=[
                    r"(\d+\.?\d*)\s*(hectares|ha).*land",
                    r"(\d+\.?\d*)\s*species.*protected",
                ],
            ),
            # Environmental - Circular Economy
            DisclosureRequirement(
                requirement_id="CSRD-E5-1",
                framework=Framework.CSRD,
                category="Environmental",
                subcategory="Circular Economy",
                description="Resource use, circular economy, and waste",
                keywords=[
                    "circular economy",
                    "waste",
                    "recycling",
                    "material flow",
                    "resource efficiency",
                ],
                mandatory=True,
                metrics_patterns=[
                    r"(\d+\.?\d*)\s*(tonnes|kg).*waste",
                    r"(\d+\.?\d*)\s*%.*recycl",
                ],
            ),
            # Social - Own Workforce
            DisclosureRequirement(
                requirement_id="CSRD-S1-1",
                framework=Framework.CSRD,
                category="Social",
                subcategory="Own Workforce",
                description="Working conditions and equal treatment",
                keywords=[
                    "working conditions",
                    "equal treatment",
                    "non-discrimination",
                    "diversity",
                    "inclusion",
                ],
                mandatory=True,
                metrics_patterns=[
                    r"(\d+\.?\d*)\s*%.*women.*management",
                    r"(\d+\.?\d*)\s*%.*diversity",
                ],
            ),
            DisclosureRequirement(
                requirement_id="CSRD-S1-2",
                framework=Framework.CSRD,
                category="Social",
                subcategory="Own Workforce",
                description="Social dialogue and collective bargaining",
                keywords=[
                    "collective bargaining",
                    "trade union",
                    "works council",
                    "social dialogue",
                ],
                mandatory=True,
                metrics_patterns=[r"(\d+\.?\d*)\s*%.*covered.*collective"],
            ),
            # Social - Workers in Value Chain
            DisclosureRequirement(
                requirement_id="CSRD-S2-1",
                framework=Framework.CSRD,
                category="Social",
                subcategory="Workers in Value Chain",
                description="Due diligence on working conditions in value chain",
                keywords=[
                    "value chain",
                    "supply chain",
                    "due diligence",
                    "working conditions",
                    "supplier assessment",
                ],
                mandatory=True,
                metrics_patterns=[
                    r"(\d+\.?\d*)\s*%.*suppliers.*assessed",
                    r"(\d+)\s*suppliers.*audited",
                ],
            ),
            # Social - Affected Communities
            DisclosureRequirement(
                requirement_id="CSRD-S3-1",
                framework=Framework.CSRD,
                category="Social",
                subcategory="Affected Communities",
                description="Human rights and community impact",
                keywords=[
                    "human rights",
                    "community",
                    "indigenous rights",
                    "land rights",
                    "displacement",
                ],
                mandatory=True,
                metrics_patterns=[
                    r"(\d+)\s*communities.*engaged",
                    r"(\d+\.?\d*)\s*(million|billion).*community.*investment",
                ],
            ),
            # Social - Consumers and End-users
            DisclosureRequirement(
                requirement_id="CSRD-S4-1",
                framework=Framework.CSRD,
                category="Social",
                subcategory="Consumers and End-users",
                description="Consumer and end-user safety and satisfaction",
                keywords=[
                    "consumer safety",
                    "product safety",
                    "data protection",
                    "privacy",
                    "customer satisfaction",
                ],
                mandatory=True,
                metrics_patterns=[
                    r"(\d+)\s*safety.*incidents",
                    r"(\d+\.?\d*)\s*%.*customer.*satisfaction",
                ],
            ),
            # Governance - Business Conduct
            DisclosureRequirement(
                requirement_id="CSRD-G1-1",
                framework=Framework.CSRD,
                category="Governance",
                subcategory="Business Conduct",
                description="Anti-corruption and anti-bribery policies",
                keywords=[
                    "anti-corruption",
                    "anti-bribery",
                    "business ethics",
                    "code of conduct",
                    "whistleblowing",
                ],
                mandatory=True,
                metrics_patterns=[
                    r"(\d+)\s*corruption.*cases",
                    r"(\d+\.?\d*)\s*%.*training.*ethics",
                ],
            ),
            DisclosureRequirement(
                requirement_id="CSRD-G1-2",
                framework=Framework.CSRD,
                category="Governance",
                subcategory="Business Conduct",
                description="Management of relationships with suppliers",
                keywords=[
                    "supplier relationship",
                    "procurement",
                    "vendor management",
                    "supplier code",
                ],
                mandatory=True,
                metrics_patterns=[
                    r"(\d+)\s*suppliers.*total",
                    r"(\d+\.?\d*)\s*%.*suppliers.*compliant",
                ],
            ),
        ]

    def _get_gri_requirements(self) -> List[DisclosureRequirement]:
        """Global Reporting Initiative requirements"""
        return [
            # GRI Universal Standards
            DisclosureRequirement(
                requirement_id="GRI-2-1",
                framework=Framework.GRI,
                category="Governance",
                subcategory="Organizational Details",
                description="Organizational details and reporting boundary",
                keywords=[
                    "organizational structure",
                    "reporting boundary",
                    "subsidiaries",
                    "joint ventures",
                ],
                mandatory=True,
                metrics_patterns=[
                    r"(\d+)\s*countries.*operations",
                    r"(\d+)\s*employees.*total",
                ],
            ),
            DisclosureRequirement(
                requirement_id="GRI-2-6",
                framework=Framework.GRI,
                category="Governance",
                subcategory="Strategy and Analysis",
                description="Statement from senior decision-maker",
                keywords=[
                    "ceo statement",
                    "leadership message",
                    "senior management",
                    "strategy statement",
                ],
                mandatory=True,
            ),
            # GRI Topic-Specific Standards - Environmental
            DisclosureRequirement(
                requirement_id="GRI-305-1",
                framework=Framework.GRI,
                category="Environmental",
                subcategory="Emissions",
                description="Direct (Scope 1) GHG emissions",
                keywords=[
                    "scope 1",
                    "direct emissions",
                    "ghg emissions",
                    "co2 emissions",
                ],
                mandatory=False,
                metrics_patterns=[
                    r"(\d+\.?\d*)\s*t.*co2.*scope.*1",
                    r"(\d+\.?\d*)\s*tonnes.*direct.*emissions",
                ],
            ),
            DisclosureRequirement(
                requirement_id="GRI-305-2",
                framework=Framework.GRI,
                category="Environmental",
                subcategory="Emissions",
                description="Energy indirect (Scope 2) GHG emissions",
                keywords=[
                    "scope 2",
                    "indirect emissions",
                    "energy emissions",
                    "electricity emissions",
                ],
                mandatory=False,
                metrics_patterns=[
                    r"(\d+\.?\d*)\s*t.*co2.*scope.*2",
                    r"(\d+\.?\d*)\s*tonnes.*indirect.*emissions",
                ],
            ),
            DisclosureRequirement(
                requirement_id="GRI-305-3",
                framework=Framework.GRI,
                category="Environmental",
                subcategory="Emissions",
                description="Other indirect (Scope 3) GHG emissions",
                keywords=[
                    "scope 3",
                    "value chain emissions",
                    "supply chain emissions",
                    "other indirect",
                ],
                mandatory=False,
                metrics_patterns=[
                    r"(\d+\.?\d*)\s*t.*co2.*scope.*3",
                    r"(\d+\.?\d*)\s*tonnes.*value.*chain",
                ],
            ),
            DisclosureRequirement(
                requirement_id="GRI-303-3",
                framework=Framework.GRI,
                category="Environmental",
                subcategory="Water and Effluents",
                description="Water withdrawal",
                keywords=[
                    "water withdrawal",
                    "water consumption",
                    "water sources",
                    "freshwater",
                ],
                mandatory=False,
                metrics_patterns=[
                    r"(\d+\.?\d*)\s*(m3|megalit).*water.*withdrawal",
                    r"(\d+\.?\d*)\s*liters.*water",
                ],
            ),
            # GRI Topic-Specific Standards - Social
            DisclosureRequirement(
                requirement_id="GRI-401-1",
                framework=Framework.GRI,
                category="Social",
                subcategory="Employment",
                description="New employee hires and employee turnover",
                keywords=[
                    "employee turnover",
                    "new hires",
                    "attrition",
                    "retention",
                    "workforce changes",
                ],
                mandatory=False,
                metrics_patterns=[
                    r"(\d+\.?\d*)\s*%.*turnover",
                    r"(\d+)\s*new.*hires",
                    r"(\d+\.?\d*)\s*%.*retention",
                ],
            ),
            DisclosureRequirement(
                requirement_id="GRI-405-1",
                framework=Framework.GRI,
                category="Social",
                subcategory="Diversity and Equal Opportunity",
                description="Diversity of governance bodies and employees",
                keywords=[
                    "diversity",
                    "gender diversity",
                    "age diversity",
                    "ethnic diversity",
                    "board composition",
                ],
                mandatory=False,
                metrics_patterns=[
                    r"(\d+\.?\d*)\s*%.*women.*board",
                    r"(\d+\.?\d*)\s*%.*women.*management",
                ],
            ),
            DisclosureRequirement(
                requirement_id="GRI-403-9",
                framework=Framework.GRI,
                category="Social",
                subcategory="Occupational Health and Safety",
                description="Work-related injuries",
                keywords=[
                    "work injuries",
                    "accident rate",
                    "safety incidents",
                    "occupational health",
                ],
                mandatory=False,
                metrics_patterns=[
                    r"(\d+\.?\d*)\s*.*injury.*rate",
                    r"(\d+)\s*safety.*incidents",
                ],
            ),
            # GRI Topic-Specific Standards - Governance
            DisclosureRequirement(
                requirement_id="GRI-205-3",
                framework=Framework.GRI,
                category="Governance",
                subcategory="Anti-corruption",
                description="Confirmed incidents of corruption and actions taken",
                keywords=[
                    "corruption incidents",
                    "anti-corruption",
                    "bribery",
                    "fraud",
                    "ethics violations",
                ],
                mandatory=False,
                metrics_patterns=[
                    r"(\d+)\s*corruption.*incidents",
                    r"(\d+)\s*ethics.*violations",
                ],
            ),
        ]

    def _get_sasb_requirements(self) -> List[DisclosureRequirement]:
        """Sustainability Accounting Standards Board requirements"""
        return [
            # Technology & Communications Sector
            DisclosureRequirement(
                requirement_id="SASB-TC-220a.1",
                framework=Framework.SASB,
                category="Social",
                subcategory="Data Privacy",
                description="Description of policies and practices relating to behavioral advertising",
                keywords=[
                    "behavioral advertising",
                    "data privacy",
                    "user tracking",
                    "advertising policies",
                ],
                mandatory=False,
                metrics_patterns=[
                    r"(\d+)\s*privacy.*complaints",
                    r"(\d+\.?\d*)\s*(million|billion).*users.*affected",
                ],
            ),
            DisclosureRequirement(
                requirement_id="SASB-TC-220a.2",
                framework=Framework.SASB,
                category="Social",
                subcategory="Data Privacy",
                description="Number of users whose information is used for secondary purposes",
                keywords=[
                    "secondary use",
                    "data sharing",
                    "user data",
                    "information use",
                ],
                mandatory=False,
                metrics_patterns=[
                    r"(\d+\.?\d*)\s*(million|billion).*users.*secondary",
                    r"(\d+\.?\d*)\s*%.*data.*shared",
                ],
            ),
            # Energy Sector
            DisclosureRequirement(
                requirement_id="SASB-EM-EP-110a.1",
                framework=Framework.SASB,
                category="Environmental",
                subcategory="Air Quality",
                description="Air emissions of criteria pollutants",
                keywords=[
                    "air emissions",
                    "nox",
                    "sox",
                    "particulate matter",
                    "criteria pollutants",
                ],
                mandatory=False,
                metrics_patterns=[
                    r"(\d+\.?\d*)\s*tonnes.*nox",
                    r"(\d+\.?\d*)\s*tonnes.*sox",
                ],
            ),
            # Financial Services
            DisclosureRequirement(
                requirement_id="SASB-FN-CB-410a.1",
                framework=Framework.SASB,
                category="Social",
                subcategory="Financial Inclusion",
                description="Number and amount of loans outstanding to underbanked populations",
                keywords=[
                    "financial inclusion",
                    "underbanked",
                    "microfinance",
                    "community lending",
                ],
                mandatory=False,
                metrics_patterns=[
                    r"(\d+\.?\d*)\s*(million|billion).*loans.*underbanked",
                    r"(\d+)\s*loans.*community",
                ],
            ),
            # Healthcare
            DisclosureRequirement(
                requirement_id="SASB-HC-BP-240a.1",
                framework=Framework.SASB,
                category="Social",
                subcategory="Product Safety",
                description="List of products listed in the FDA's MedWatch Safety Alerts",
                keywords=[
                    "product safety",
                    "fda alerts",
                    "medical device safety",
                    "drug safety",
                ],
                mandatory=False,
                metrics_patterns=[
                    r"(\d+)\s*safety.*alerts",
                    r"(\d+)\s*product.*recalls",
                ],
            ),
            # General SASB Requirements
            DisclosureRequirement(
                requirement_id="SASB-GEN-000.A",
                framework=Framework.SASB,
                category="Governance",
                subcategory="Business Model",
                description="Description of the nature of business operations",
                keywords=[
                    "business model",
                    "operations description",
                    "industry description",
                    "value creation",
                ],
                mandatory=True,
            ),
            DisclosureRequirement(
                requirement_id="SASB-GEN-000.B",
                framework=Framework.SASB,
                category="Governance",
                subcategory="Business Environment",
                description="Description of how the organization identifies, assesses, and manages "
                "sustainability risks",
                keywords=[
                    "sustainability risk",
                    "risk management",
                    "materiality assessment",
                    "risk governance",
                ],
                mandatory=True,
                metrics_patterns=[
                    r"(\d+)\s*material.*topics",
                    r"(\d+)\s*risks.*identified",
                ],
            ),
        ]

    def _get_tcfd_requirements(self) -> List[DisclosureRequirement]:
        """Task Force on Climate-related Financial Disclosures requirements"""
        return [
            # Governance
            DisclosureRequirement(
                requirement_id="TCFD-GOV-A",
                framework=Framework.TCFD,
                category="Governance",
                subcategory="Board Oversight",
                description="Board's oversight of climate-related risks and opportunities",
                keywords=[
                    "board oversight",
                    "climate governance",
                    "board responsibility",
                    "climate committee",
                ],
                mandatory=True,
                metrics_patterns=[
                    r"(\d+)\s*board.*meetings.*climate",
                    r"(\d+)\s*directors.*climate.*experience",
                ],
            ),
            DisclosureRequirement(
                requirement_id="TCFD-GOV-B",
                framework=Framework.TCFD,
                category="Governance",
                subcategory="Management Role",
                description="Management's role in assessing and managing climate-related risks",
                keywords=[
                    "management role",
                    "climate management",
                    "executive responsibility",
                    "climate officer",
                ],
                mandatory=True,
            ),
            # Strategy
            DisclosureRequirement(
                requirement_id="TCFD-STR-A",
                framework=Framework.TCFD,
                category="Environmental",
                subcategory="Climate Risks and Opportunities",
                description="Climate-related risks and opportunities identified over short, medium, and long term",
                keywords=[
                    "climate risks",
                    "climate opportunities",
                    "physical risk",
                    "transition risk",
                    "time horizons",
                ],
                mandatory=True,
                metrics_patterns=[
                    r"(\d+)\s*climate.*risks",
                    r"(\d+)\s*climate.*opportunities",
                ],
            ),
            DisclosureRequirement(
                requirement_id="TCFD-STR-B",
                framework=Framework.TCFD,
                category="Environmental",
                subcategory="Business Impact",
                description="Impact of climate-related risks and opportunities on business, "
                "strategy, and financial planning",
                keywords=[
                    "business impact",
                    "strategic impact",
                    "financial impact",
                    "climate strategy",
                ],
                mandatory=True,
                metrics_patterns=[
                    r"(\d+\.?\d*)\s*(million|billion).*climate.*impact",
                    r"(\d+\.?\d*)\s*%.*revenue.*climate",
                ],
            ),
            DisclosureRequirement(
                requirement_id="TCFD-STR-C",
                framework=Framework.TCFD,
                category="Environmental",
                subcategory="Climate Scenarios",
                description="Resilience of strategy under different climate-related scenarios",
                keywords=[
                    "scenario analysis",
                    "climate scenarios",
                    "stress testing",
                    "resilience",
                    "2 degree",
                    "1.5 degree",
                ],
                mandatory=True,
                metrics_patterns=[
                    r"(\d+\.?\d*)\s*degree.*scenario",
                    r"(\d+)\s*scenarios.*analyzed",
                ],
            ),
            # Risk Management
            DisclosureRequirement(
                requirement_id="TCFD-RM-A",
                framework=Framework.TCFD,
                category="Governance",
                subcategory="Risk Identification",
                description="Processes for identifying and assessing climate-related risks",
                keywords=[
                    "risk identification",
                    "risk assessment",
                    "climate risk process",
                    "risk methodology",
                ],
                mandatory=True,
            ),
            DisclosureRequirement(
                requirement_id="TCFD-RM-B",
                framework=Framework.TCFD,
                category="Governance",
                subcategory="Risk Management",
                description="Processes for managing climate-related risks",
                keywords=[
                    "risk management",
                    "risk mitigation",
                    "climate risk controls",
                    "risk monitoring",
                ],
                mandatory=True,
            ),
            DisclosureRequirement(
                requirement_id="TCFD-RM-C",
                framework=Framework.TCFD,
                category="Governance",
                subcategory="Risk Integration",
                description="Integration of climate-related risks into overall risk management",
                keywords=[
                    "risk integration",
                    "enterprise risk",
                    "integrated risk",
                    "overall risk management",
                ],
                mandatory=True,
            ),
            # Metrics and Targets
            DisclosureRequirement(
                requirement_id="TCFD-MT-A",
                framework=Framework.TCFD,
                category="Environmental",
                subcategory="Climate Metrics",
                description="Metrics used to assess climate-related risks and opportunities",
                keywords=[
                    "climate metrics",
                    "risk metrics",
                    "opportunity metrics",
                    "performance indicators",
                ],
                mandatory=True,
                metrics_patterns=[
                    r"(\d+)\s*climate.*metrics",
                    r"(\d+\.?\d*)\s*(million|billion).*carbon.*value",
                ],
            ),
            DisclosureRequirement(
                requirement_id="TCFD-MT-B",
                framework=Framework.TCFD,
                category="Environmental",
                subcategory="GHG Emissions",
                description="Scope 1, 2, and if appropriate, Scope 3 GHG emissions and related risks",
                keywords=[
                    "scope 1",
                    "scope 2",
                    "scope 3",
                    "ghg emissions",
                    "carbon footprint",
                    "emissions data",
                ],
                mandatory=True,
                metrics_patterns=[
                    r"(\d+\.?\d*)\s*t.*co2.*scope",
                    r"(\d+\.?\d*)\s*tonnes.*emissions",
                ],
            ),
            DisclosureRequirement(
                requirement_id="TCFD-MT-C",
                framework=Framework.TCFD,
                category="Environmental",
                subcategory="Climate Targets",
                description="Targets used to manage climate-related risks and opportunities",
                keywords=[
                    "climate targets",
                    "emission targets",
                    "net zero",
                    "carbon neutral",
                    "reduction targets",
                ],
                mandatory=True,
                metrics_patterns=[
                    r"(\d+\.?\d*)\s*%.*reduction.*target",
                    r"net zero.*(\d{4})",
                    r"carbon neutral.*(\d{4})",
                ],
            ),
        ]

    def _build_keyword_index(
        self,
    ) -> Dict[str, List[Tuple[Framework, DisclosureRequirement]]]:
        """Build keyword index for fast requirement lookup"""
        index = defaultdict(list)

        for framework, requirements in self.requirements.items():
            for req in requirements:
                for keyword in req.keywords:
                    index[keyword.lower()].append((framework, req))

        return dict(index)

    def _build_metrics_extractors(self) -> Dict[str, re.Pattern]:
        """Build regex patterns for metrics extraction"""
        extractors = {
            "percentage": re.compile(r"(\d+\.?\d*)\s*%", re.IGNORECASE),
            "emissions": re.compile(r"(\d+\.?\d*)\s*(t|tonnes|tons).*co2", re.IGNORECASE),
            "energy": re.compile(r"(\d+\.?\d*)\s*(kwh|mwh|gwh|tj|pj)", re.IGNORECASE),
            "water": re.compile(r"(\d+\.?\d*)\s*(m3|liters|litres|megalit)", re.IGNORECASE),
            "waste": re.compile(r"(\d+\.?\d*)\s*(kg|tonnes|tons).*waste", re.IGNORECASE),
            "currency": re.compile(
                r"(\d+\.?\d*)\s*(million|billion|trillion).*(\$|USD|EUR|GBP)",
                re.IGNORECASE,
            ),
            "employees": re.compile(r"(\d+\.?\d*)\s*(employees|workers|staff|people)", re.IGNORECASE),
        }

        return extractors

    def find_relevant_requirements(self, content: str) -> Dict[Framework, List[DisclosureRequirement]]:
        """Find requirements that match content based on keywords"""
        content_lower = content.lower()
        relevant_reqs = defaultdict(list)

        # Track which requirements we've already added per framework
        added_reqs = defaultdict(set)

        # Search for keyword matches
        for keyword, framework_reqs in self.keyword_index.items():
            if keyword in content_lower:
                for framework, req in framework_reqs:
                    if req.requirement_id not in added_reqs[framework]:
                        relevant_reqs[framework].append(req)
                        added_reqs[framework].add(req.requirement_id)

        return dict(relevant_reqs)

    def extract_metrics(
        self, content: str, requirements: List[DisclosureRequirement] = None
    ) -> Dict[str, Dict[str, List[str]]]:
        """Extract numerical metrics from content"""
        metrics = defaultdict(lambda: defaultdict(list))

        # Extract using general patterns
        for metric_type, pattern in self.metrics_extractors.items():
            matches = pattern.findall(content)
            for match in matches:
                if isinstance(match, tuple):
                    value = match[0]
                    unit = match[1] if len(match) > 1 else ""
                else:
                    value = match
                    unit = metric_type

                metrics["general"][metric_type].append(f"{value} {unit}".strip())

        # Extract using requirement-specific patterns
        if requirements:
            for req in requirements:
                if req.metrics_patterns:
                    for pattern_str in req.metrics_patterns:
                        try:
                            pattern = re.compile(pattern_str, re.IGNORECASE)
                            matches = pattern.findall(content)
                            for match in matches:
                                if isinstance(match, tuple):
                                    value = match[0]
                                    unit = match[1] if len(match) > 1 else ""
                                else:
                                    value = match
                                    unit = ""

                                metrics[req.requirement_id][req.category].append(f"{value} {unit}".strip())
                        except re.error:
                            continue  # Skip invalid regex patterns

        return dict(metrics)

    def generate_gap_analysis(
        self, found_requirements: Dict[Framework, List[DisclosureRequirement]]
    ) -> Dict[Framework, List[DisclosureRequirement]]:
        """Generate gap analysis showing missing requirements"""
        gaps = {}

        for framework in Framework:
            all_reqs = self.requirements[framework]
            found_reqs = found_requirements.get(framework, [])
            found_ids = {req.requirement_id for req in found_reqs}

            missing_reqs = [req for req in all_reqs if req.requirement_id not in found_ids]
            gaps[framework] = missing_reqs

        return gaps

    def calculate_coverage_score(
        self, found_requirements: Dict[Framework, List[DisclosureRequirement]]
    ) -> Dict[Framework, float]:
        """Calculate coverage percentage for each framework"""
        coverage = {}

        for framework in Framework:
            total_reqs = len(self.requirements[framework])
            found_reqs = len(found_requirements.get(framework, []))

            coverage[framework] = (found_reqs / total_reqs * 100) if total_reqs > 0 else 0

        return coverage

    def get_framework_summary(self) -> Dict[str, Any]:
        """Get summary statistics for all frameworks"""
        summary = {}

        for framework in Framework:
            reqs = self.requirements[framework]
            categories = set(req.category for req in reqs)
            mandatory_count = len([req for req in reqs if req.mandatory])

            summary[framework.value] = {
                "total_requirements": len(reqs),
                "mandatory_requirements": mandatory_count,
                "optional_requirements": len(reqs) - mandatory_count,
                "categories": list(categories),
                "category_count": len(categories),
            }

        return summary


# Convenience functions for easy import
def get_framework_manager() -> ESGFrameworkManager:
    """Get initialized framework manager"""
    return ESGFrameworkManager()


def analyze_text_against_frameworks(content: str, frameworks: List[str] = None) -> Dict[str, Any]:
    """Quick analysis of text content against specified frameworks"""
    manager = ESGFrameworkManager()

    if frameworks:
        framework_enums = [Framework[name] for name in frameworks if name in Framework.__members__]
    else:
        framework_enums = list(Framework)

    # Find relevant requirements
    found_requirements = manager.find_relevant_requirements(content)

    # Filter by requested frameworks
    filtered_requirements = {
        framework: reqs for framework, reqs in found_requirements.items() if framework in framework_enums
    }

    # Calculate coverage
    coverage = manager.calculate_coverage_score(filtered_requirements)

    # Generate gaps
    gaps = manager.generate_gap_analysis(filtered_requirements)

    # Extract metrics
    all_found_reqs = []
    for reqs in filtered_requirements.values():
        all_found_reqs.extend(reqs)

    metrics = manager.extract_metrics(content, all_found_reqs)

    return {
        "requirements_found": filtered_requirements,
        "coverage_scores": coverage,
        "gap_analysis": gaps,
        "extracted_metrics": metrics,
        "framework_summary": manager.get_framework_summary(),
    }


if __name__ == "__main__":
    # Example usage
    manager = ESGFrameworkManager()

    sample_text = """
    Our company has committed to achieving net zero emissions by 2030. We have implemented
    a comprehensive transition plan that includes reducing scope 1 and scope 2 emissions by
    50% over the next 5 years. Our board has established a climate committee with oversight
    responsibilities for climate-related risks and opportunities.

    We have conducted scenario analysis including 1.5 degree and 2 degree warming scenarios
    to assess the resilience of our business strategy. Physical risks include increased
    flooding and extreme weather events that could impact our operations.

    Our workforce diversity initiatives have resulted in 40% women in senior management
    positions. We provide extensive training on anti-corruption policies and have had
    zero confirmed incidents of corruption this year.
    """

    result = analyze_text_against_frameworks(sample_text, ["TCFD", "CSRD"])

    print("Framework Analysis Results:")
    print("=" * 50)

    for framework, coverage in result["coverage_scores"].items():
        print(f"\n{framework.value} Coverage: {coverage:.1f}%")

        found_count = len(result["requirements_found"].get(framework, []))
        gap_count = len(result["gap_analysis"].get(framework, []))
        print(f"Requirements Found: {found_count}")
        print(f"Requirements Missing: {gap_count}")

    print(f"\nMetrics Extracted: {len(result['extracted_metrics'])} categories")
