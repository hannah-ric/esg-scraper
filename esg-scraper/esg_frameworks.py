"""
ESG Reporting Frameworks Alignment Module
Implements CSRD, GRI, SASB, and TCFD requirements
"""

from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Framework(Enum):
    """ESG Reporting Frameworks"""
    CSRD = "CSRD"  # Corporate Sustainability Reporting Directive
    GRI = "GRI"    # Global Reporting Initiative
    SASB = "SASB"  # Sustainability Accounting Standards Board
    TCFD = "TCFD"  # Task Force on Climate-related Financial Disclosures

@dataclass
class DisclosureRequirement:
    """Represents a specific disclosure requirement"""
    framework: Framework
    category: str
    subcategory: str
    requirement_id: str
    description: str
    keywords: List[str]
    metrics: List[str] = field(default_factory=list)
    mandatory: bool = True
    
    def __hash__(self):
        return hash(self.requirement_id)
    
    def __eq__(self, other):
        if isinstance(other, DisclosureRequirement):
            return self.requirement_id == other.requirement_id
        return False

class ESGFrameworkManager:
    """Manages ESG framework requirements and mappings"""
    
    def __init__(self):
        self.requirements = self._load_requirements()
        self.keyword_map = self._build_keyword_map()
        
    def _load_requirements(self) -> Dict[Framework, List[DisclosureRequirement]]:
        """Load all framework requirements"""
        return {
            Framework.CSRD: self._load_csrd_requirements(),
            Framework.GRI: self._load_gri_requirements(),
            Framework.SASB: self._load_sasb_requirements(),
            Framework.TCFD: self._load_tcfd_requirements()
        }
    
    def _load_csrd_requirements(self) -> List[DisclosureRequirement]:
        """CSRD (EU Corporate Sustainability Reporting Directive) requirements"""
        return [
            # Environmental
            DisclosureRequirement(
                framework=Framework.CSRD,
                category="Environmental",
                subcategory="Climate Change",
                requirement_id="CSRD-E1-1",
                description="GHG emissions (Scope 1, 2, 3)",
                keywords=["scope 1", "scope 2", "scope 3", "ghg emissions", "greenhouse gas", "carbon footprint"],
                metrics=["tCO2e", "metric tons CO2", "carbon emissions"],
                mandatory=True
            ),
            DisclosureRequirement(
                framework=Framework.CSRD,
                category="Environmental",
                subcategory="Climate Change",
                requirement_id="CSRD-E1-2",
                description="Climate transition plan",
                keywords=["transition plan", "net zero", "carbon neutral", "climate strategy", "decarbonization"],
                metrics=["target year", "reduction percentage"],
                mandatory=True
            ),
            DisclosureRequirement(
                framework=Framework.CSRD,
                category="Environmental",
                subcategory="Pollution",
                requirement_id="CSRD-E2-1",
                description="Pollution of air, water, and soil",
                keywords=["air pollution", "water pollution", "soil contamination", "emissions", "discharge"],
                metrics=["kg", "tons", "ppm", "mg/L"],
                mandatory=True
            ),
            DisclosureRequirement(
                framework=Framework.CSRD,
                category="Environmental",
                subcategory="Water Resources",
                requirement_id="CSRD-E3-1",
                description="Water consumption and withdrawal",
                keywords=["water consumption", "water withdrawal", "water usage", "water stress"],
                metrics=["cubic meters", "liters", "gallons"],
                mandatory=True
            ),
            DisclosureRequirement(
                framework=Framework.CSRD,
                category="Environmental",
                subcategory="Biodiversity",
                requirement_id="CSRD-E4-1",
                description="Impact on biodiversity and ecosystems",
                keywords=["biodiversity", "ecosystem", "habitat", "species", "deforestation", "land use"],
                metrics=["hectares", "species affected", "protected areas"],
                mandatory=True
            ),
            DisclosureRequirement(
                framework=Framework.CSRD,
                category="Environmental",
                subcategory="Circular Economy",
                requirement_id="CSRD-E5-1",
                description="Resource use and circular economy",
                keywords=["circular economy", "recycling", "waste", "reuse", "resource efficiency"],
                metrics=["recycling rate %", "tons waste", "material efficiency"],
                mandatory=True
            ),
            
            # Social
            DisclosureRequirement(
                framework=Framework.CSRD,
                category="Social",
                subcategory="Workforce",
                requirement_id="CSRD-S1-1",
                description="Working conditions and equal treatment",
                keywords=["working conditions", "equal treatment", "fair wages", "work-life balance"],
                metrics=["employee satisfaction %", "turnover rate", "wage gap"],
                mandatory=True
            ),
            DisclosureRequirement(
                framework=Framework.CSRD,
                category="Social",
                subcategory="Workforce",
                requirement_id="CSRD-S1-2",
                description="Health and safety",
                keywords=["health and safety", "workplace safety", "injury rate", "occupational health"],
                metrics=["LTIFR", "injury rate", "safety incidents"],
                mandatory=True
            ),
            DisclosureRequirement(
                framework=Framework.CSRD,
                category="Social",
                subcategory="Value Chain",
                requirement_id="CSRD-S2-1",
                description="Workers in the value chain",
                keywords=["supply chain workers", "supplier standards", "labor practices", "child labor"],
                metrics=["supplier audits", "compliance rate %"],
                mandatory=True
            ),
            DisclosureRequirement(
                framework=Framework.CSRD,
                category="Social",
                subcategory="Communities",
                requirement_id="CSRD-S3-1",
                description="Affected communities",
                keywords=["local communities", "community impact", "indigenous rights", "land rights"],
                metrics=["community investments", "grievances", "consultations"],
                mandatory=True
            ),
            DisclosureRequirement(
                framework=Framework.CSRD,
                category="Social",
                subcategory="Consumers",
                requirement_id="CSRD-S4-1",
                description="Consumer and end-user impacts",
                keywords=["consumer safety", "product safety", "data privacy", "customer satisfaction"],
                metrics=["safety incidents", "recalls", "satisfaction score"],
                mandatory=True
            ),
            
            # Governance
            DisclosureRequirement(
                framework=Framework.CSRD,
                category="Governance",
                subcategory="Business Conduct",
                requirement_id="CSRD-G1-1",
                description="Business conduct and corporate culture",
                keywords=["business ethics", "code of conduct", "anti-corruption", "whistleblower"],
                metrics=["ethics violations", "training hours", "whistleblower reports"],
                mandatory=True
            ),
        ]
    
    def _load_gri_requirements(self) -> List[DisclosureRequirement]:
        """GRI (Global Reporting Initiative) Standards requirements"""
        return [
            # GRI Universal Standards
            DisclosureRequirement(
                framework=Framework.GRI,
                category="Universal",
                subcategory="Foundation",
                requirement_id="GRI-2-1",
                description="Organizational details",
                keywords=["organization details", "company structure", "operations", "headquarters"],
                metrics=["employees", "operations", "countries"],
                mandatory=True
            ),
            DisclosureRequirement(
                framework=Framework.GRI,
                category="Universal",
                subcategory="Strategy",
                requirement_id="GRI-2-22",
                description="Statement on sustainable development strategy",
                keywords=["sustainability strategy", "sustainable development", "strategic priorities"],
                mandatory=True
            ),
            
            # GRI Topic Standards - Environmental
            DisclosureRequirement(
                framework=Framework.GRI,
                category="Environmental",
                subcategory="Materials",
                requirement_id="GRI-301-1",
                description="Materials used by weight or volume",
                keywords=["materials used", "raw materials", "material consumption"],
                metrics=["tons", "kg", "volume"],
                mandatory=False
            ),
            DisclosureRequirement(
                framework=Framework.GRI,
                category="Environmental",
                subcategory="Energy",
                requirement_id="GRI-302-1",
                description="Energy consumption within the organization",
                keywords=["energy consumption", "electricity", "fuel consumption", "renewable energy"],
                metrics=["GJ", "MWh", "kWh"],
                mandatory=False
            ),
            DisclosureRequirement(
                framework=Framework.GRI,
                category="Environmental",
                subcategory="Water",
                requirement_id="GRI-303-3",
                description="Water withdrawal",
                keywords=["water withdrawal", "water sources", "groundwater", "surface water"],
                metrics=["megaliters", "cubic meters"],
                mandatory=False
            ),
            DisclosureRequirement(
                framework=Framework.GRI,
                category="Environmental",
                subcategory="Emissions",
                requirement_id="GRI-305-1",
                description="Direct (Scope 1) GHG emissions",
                keywords=["scope 1 emissions", "direct emissions", "ghg emissions"],
                metrics=["tCO2e", "metric tons CO2"],
                mandatory=False
            ),
            DisclosureRequirement(
                framework=Framework.GRI,
                category="Environmental",
                subcategory="Emissions",
                requirement_id="GRI-305-2",
                description="Energy indirect (Scope 2) GHG emissions",
                keywords=["scope 2 emissions", "indirect emissions", "purchased electricity"],
                metrics=["tCO2e", "metric tons CO2"],
                mandatory=False
            ),
            DisclosureRequirement(
                framework=Framework.GRI,
                category="Environmental",
                subcategory="Emissions",
                requirement_id="GRI-305-3",
                description="Other indirect (Scope 3) GHG emissions",
                keywords=["scope 3 emissions", "value chain emissions", "supply chain emissions"],
                metrics=["tCO2e", "metric tons CO2"],
                mandatory=False
            ),
            
            # GRI Topic Standards - Social
            DisclosureRequirement(
                framework=Framework.GRI,
                category="Social",
                subcategory="Employment",
                requirement_id="GRI-401-1",
                description="New employee hires and employee turnover",
                keywords=["new hires", "employee turnover", "attrition rate", "retention"],
                metrics=["number", "rate %"],
                mandatory=False
            ),
            DisclosureRequirement(
                framework=Framework.GRI,
                category="Social",
                subcategory="Health & Safety",
                requirement_id="GRI-403-9",
                description="Work-related injuries",
                keywords=["work injuries", "accident rate", "ltifr", "safety incidents"],
                metrics=["number", "rate", "hours"],
                mandatory=False
            ),
            DisclosureRequirement(
                framework=Framework.GRI,
                category="Social",
                subcategory="Training",
                requirement_id="GRI-404-1",
                description="Average hours of training per year per employee",
                keywords=["training hours", "employee development", "skills training"],
                metrics=["hours", "hours per employee"],
                mandatory=False
            ),
            DisclosureRequirement(
                framework=Framework.GRI,
                category="Social",
                subcategory="Diversity",
                requirement_id="GRI-405-1",
                description="Diversity of governance bodies and employees",
                keywords=["diversity", "gender diversity", "age diversity", "minority representation"],
                metrics=["percentage", "ratio"],
                mandatory=False
            ),
        ]
    
    def _load_sasb_requirements(self) -> List[DisclosureRequirement]:
        """SASB (Sustainability Accounting Standards Board) requirements"""
        # Note: SASB is industry-specific. This is a general subset.
        return [
            # Environment
            DisclosureRequirement(
                framework=Framework.SASB,
                category="Environment",
                subcategory="GHG Emissions",
                requirement_id="SASB-EM-1",
                description="Gross global Scope 1 emissions",
                keywords=["scope 1", "direct emissions", "ghg emissions", "carbon emissions"],
                metrics=["metric tons CO2e"],
                mandatory=False
            ),
            DisclosureRequirement(
                framework=Framework.SASB,
                category="Environment",
                subcategory="Energy Management",
                requirement_id="SASB-EM-2",
                description="Total energy consumed",
                keywords=["energy consumption", "total energy", "energy use"],
                metrics=["gigajoules", "GJ", "MWh"],
                mandatory=False
            ),
            DisclosureRequirement(
                framework=Framework.SASB,
                category="Environment",
                subcategory="Water Management",
                requirement_id="SASB-EM-3",
                description="Total water withdrawn",
                keywords=["water withdrawal", "water consumption", "freshwater"],
                metrics=["thousand cubic meters"],
                mandatory=False
            ),
            
            # Social Capital
            DisclosureRequirement(
                framework=Framework.SASB,
                category="Social Capital",
                subcategory="Data Security",
                requirement_id="SASB-SC-1",
                description="Data breaches and customer privacy",
                keywords=["data breach", "data security", "privacy", "cybersecurity"],
                metrics=["number of breaches", "records affected"],
                mandatory=False
            ),
            DisclosureRequirement(
                framework=Framework.SASB,
                category="Social Capital",
                subcategory="Product Safety",
                requirement_id="SASB-SC-2",
                description="Product safety and quality",
                keywords=["product safety", "recalls", "quality issues", "safety incidents"],
                metrics=["number of recalls", "units affected"],
                mandatory=False
            ),
            
            # Human Capital
            DisclosureRequirement(
                framework=Framework.SASB,
                category="Human Capital",
                subcategory="Employee Health & Safety",
                requirement_id="SASB-HC-1",
                description="Total recordable incident rate (TRIR)",
                keywords=["trir", "incident rate", "safety performance", "workplace injuries"],
                metrics=["rate", "incidents per 200,000 hours"],
                mandatory=False
            ),
            DisclosureRequirement(
                framework=Framework.SASB,
                category="Human Capital",
                subcategory="Employee Engagement",
                requirement_id="SASB-HC-2",
                description="Employee engagement and diversity",
                keywords=["employee engagement", "diversity metrics", "inclusion"],
                metrics=["percentage", "engagement score"],
                mandatory=False
            ),
            
            # Business Model & Innovation
            DisclosureRequirement(
                framework=Framework.SASB,
                category="Business Model",
                subcategory="Product Lifecycle",
                requirement_id="SASB-BM-1",
                description="Product lifecycle management",
                keywords=["lifecycle", "end-of-life", "product stewardship", "circular design"],
                metrics=["percentage recyclable", "take-back rate"],
                mandatory=False
            ),
            
            # Leadership & Governance
            DisclosureRequirement(
                framework=Framework.SASB,
                category="Governance",
                subcategory="Business Ethics",
                requirement_id="SASB-LG-1",
                description="Business ethics and competitive behavior",
                keywords=["business ethics", "anti-corruption", "competitive behavior", "compliance"],
                metrics=["fines", "legal proceedings"],
                mandatory=False
            ),
        ]
    
    def _load_tcfd_requirements(self) -> List[DisclosureRequirement]:
        """TCFD (Task Force on Climate-related Financial Disclosures) requirements"""
        return [
            # Governance
            DisclosureRequirement(
                framework=Framework.TCFD,
                category="Governance",
                subcategory="Board Oversight",
                requirement_id="TCFD-GOV-1",
                description="Board oversight of climate-related risks and opportunities",
                keywords=["board oversight", "climate governance", "board climate", "climate committee"],
                mandatory=True
            ),
            DisclosureRequirement(
                framework=Framework.TCFD,
                category="Governance",
                subcategory="Management Role",
                requirement_id="TCFD-GOV-2",
                description="Management's role in assessing climate-related risks",
                keywords=["management role", "climate risk management", "executive responsibility"],
                mandatory=True
            ),
            
            # Strategy
            DisclosureRequirement(
                framework=Framework.TCFD,
                category="Strategy",
                subcategory="Climate Risks",
                requirement_id="TCFD-STR-1",
                description="Climate-related risks and opportunities identified",
                keywords=["climate risks", "physical risks", "transition risks", "climate opportunities"],
                mandatory=True
            ),
            DisclosureRequirement(
                framework=Framework.TCFD,
                category="Strategy",
                subcategory="Business Impact",
                requirement_id="TCFD-STR-2",
                description="Impact on business, strategy, and financial planning",
                keywords=["business impact", "financial impact", "climate strategy", "strategic planning"],
                mandatory=True
            ),
            DisclosureRequirement(
                framework=Framework.TCFD,
                category="Strategy",
                subcategory="Scenario Analysis",
                requirement_id="TCFD-STR-3",
                description="Climate scenario analysis",
                keywords=["scenario analysis", "2°c scenario", "1.5°c scenario", "climate scenarios"],
                mandatory=True
            ),
            
            # Risk Management
            DisclosureRequirement(
                framework=Framework.TCFD,
                category="Risk Management",
                subcategory="Risk Identification",
                requirement_id="TCFD-RM-1",
                description="Processes for identifying climate-related risks",
                keywords=["risk identification", "risk assessment", "climate risk process"],
                mandatory=True
            ),
            DisclosureRequirement(
                framework=Framework.TCFD,
                category="Risk Management",
                subcategory="Risk Management",
                requirement_id="TCFD-RM-2",
                description="Processes for managing climate-related risks",
                keywords=["risk management", "risk mitigation", "climate risk management"],
                mandatory=True
            ),
            DisclosureRequirement(
                framework=Framework.TCFD,
                category="Risk Management",
                subcategory="Integration",
                requirement_id="TCFD-RM-3",
                description="Integration into overall risk management",
                keywords=["risk integration", "enterprise risk", "integrated risk management"],
                mandatory=True
            ),
            
            # Metrics and Targets
            DisclosureRequirement(
                framework=Framework.TCFD,
                category="Metrics & Targets",
                subcategory="Climate Metrics",
                requirement_id="TCFD-MT-1",
                description="Metrics used to assess climate risks and opportunities",
                keywords=["climate metrics", "kpis", "performance indicators", "climate indicators"],
                mandatory=True
            ),
            DisclosureRequirement(
                framework=Framework.TCFD,
                category="Metrics & Targets",
                subcategory="GHG Emissions",
                requirement_id="TCFD-MT-2",
                description="Scope 1, 2, and 3 GHG emissions",
                keywords=["scope 1", "scope 2", "scope 3", "ghg emissions", "carbon footprint"],
                metrics=["tCO2e", "metric tons CO2"],
                mandatory=True
            ),
            DisclosureRequirement(
                framework=Framework.TCFD,
                category="Metrics & Targets",
                subcategory="Climate Targets",
                requirement_id="TCFD-MT-3",
                description="Targets for managing climate risks and opportunities",
                keywords=["climate targets", "emission targets", "net zero target", "carbon neutral"],
                metrics=["reduction %", "target year"],
                mandatory=True
            ),
        ]
    
    def _build_keyword_map(self) -> Dict[str, List[DisclosureRequirement]]:
        """Build a reverse mapping from keywords to requirements"""
        keyword_map = {}
        for framework_reqs in self.requirements.values():
            for req in framework_reqs:
                for keyword in req.keywords:
                    keyword_lower = keyword.lower()
                    if keyword_lower not in keyword_map:
                        keyword_map[keyword_lower] = []
                    keyword_map[keyword_lower].append(req)
        return keyword_map
    
    def find_relevant_requirements(self, text: str) -> Dict[Framework, List[DisclosureRequirement]]:
        """Find which disclosure requirements are relevant to the given text"""
        text_lower = text.lower()
        found_requirements = {framework: set() for framework in Framework}
        
        # Search for keywords
        for keyword, requirements in self.keyword_map.items():
            if keyword in text_lower:
                for req in requirements:
                    found_requirements[req.framework].add(req)
        
        # Convert sets to lists
        return {
            framework: list(reqs) 
            for framework, reqs in found_requirements.items() 
            if reqs
        }
    
    def extract_metrics(self, text: str, requirements: List[DisclosureRequirement]) -> Dict[str, Any]:
        """Extract quantitative metrics from text based on requirements"""
        metrics = {}
        
        # Common metric patterns
        patterns = {
            "tCO2e": r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:t|metric tons?|tonnes?)\s*CO2e?',
            "percentage": r'(\d+(?:\.\d+)?)\s*%',
            "currency": r'(?:\$|€|£)\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:million|billion|M|B)?',
            "count": r'(\d+(?:,\d{3})*)\s*(?:employees?|workers?|people|incidents?|breaches?)',
            "energy": r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:GJ|MWh|kWh|gigajoules?|megawatt)',
            "water": r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:cubic meters?|m³|liters?|gallons?)',
            "area": r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:hectares?|ha|acres?|km²|square)',
        }
        
        for req in requirements:
            req_metrics = {}
            
            # Search for metrics mentioned in the requirement
            for metric_unit in req.metrics:
                for pattern_name, pattern in patterns.items():
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    if matches and metric_unit.lower() in text.lower():
                        req_metrics[metric_unit] = matches
            
            if req_metrics:
                metrics[req.requirement_id] = req_metrics
        
        return metrics
    
    def calculate_framework_coverage(self, found_requirements: Dict[Framework, List[DisclosureRequirement]]) -> Dict[Framework, float]:
        """Calculate percentage coverage for each framework"""
        coverage = {}
        
        for framework in Framework:
            total_requirements = len([r for r in self.requirements[framework] if r.mandatory])
            found_mandatory = len([r for r in found_requirements.get(framework, []) if r.mandatory])
            
            if total_requirements > 0:
                coverage[framework] = (found_mandatory / total_requirements) * 100
            else:
                coverage[framework] = 0.0
        
        return coverage
    
    def generate_gap_analysis(self, found_requirements: Dict[Framework, List[DisclosureRequirement]]) -> Dict[Framework, List[DisclosureRequirement]]:
        """Identify missing mandatory requirements for each framework"""
        gaps = {}
        
        for framework in Framework:
            found_ids = {req.requirement_id for req in found_requirements.get(framework, [])}
            missing = [
                req for req in self.requirements[framework]
                if req.mandatory and req.requirement_id not in found_ids
            ]
            if missing:
                gaps[framework] = missing
        
        return gaps 