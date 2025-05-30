"""
Advanced ESG Metrics Extraction System
Extracts, standardizes, and maps quantitative metrics to ESG frameworks
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime
import spacy
from pint import UnitRegistry

logger = logging.getLogger(__name__)

# Initialize unit registry for conversions
ureg = UnitRegistry()

class MetricCategory(Enum):
    """ESG metric categories aligned with major frameworks"""
    # Environmental
    GHG_EMISSIONS = "ghg_emissions"
    ENERGY = "energy"
    WATER = "water"
    WASTE = "waste"
    BIODIVERSITY = "biodiversity"
    
    # Social
    EMPLOYMENT = "employment"
    DIVERSITY = "diversity"
    HEALTH_SAFETY = "health_safety"
    TRAINING = "training"
    COMMUNITY = "community"
    
    # Governance
    BOARD_COMPOSITION = "board_composition"
    ETHICS = "ethics"
    RISK_MANAGEMENT = "risk_management"
    COMPENSATION = "compensation"
    COMPLIANCE = "compliance"

@dataclass
class ExtractedMetric:
    """Represents an extracted ESG metric"""
    metric_name: str
    value: float
    unit: str
    category: MetricCategory
    context: str  # Surrounding text for context
    confidence: float
    year: Optional[int] = None
    scope: Optional[str] = None  # e.g., Scope 1, 2, 3 for emissions
    normalized_value: Optional[float] = None
    normalized_unit: Optional[str] = None
    framework_mappings: Dict[str, List[str]] = None  # Framework -> requirement IDs

class MetricsExtractor:
    """Advanced metrics extraction with NLP and pattern matching"""
    
    def __init__(self):
        # Load spaCy model for NER
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except:
            logger.warning("spaCy model not found. Install with: python -m spacy download en_core_web_sm")
            self.nlp = None
        
        # Define metric patterns
        self.metric_patterns = self._build_metric_patterns()
        
        # Define unit mappings
        self.unit_mappings = self._build_unit_mappings()
        
        # Framework requirement mappings
        self.framework_mappings = self._build_framework_mappings()
    
    def _build_metric_patterns(self) -> Dict[MetricCategory, List[Dict[str, Any]]]:
        """Build regex patterns for different metric types"""
        
        patterns = {
            MetricCategory.GHG_EMISSIONS: [
                {
                    'pattern': r'(?:scope\s*[123]?\s*)?(?:ghg|greenhouse\s*gas|carbon|co2e?)\s*emissions?\s*[:=]?\s*([\d,]+\.?\d*)\s*(mt|metric\s*ton|tco2e?|tonnes?\s*co2e?|kg\s*co2e?)',
                    'value_group': 1,
                    'unit_group': 2,
                    'scope_pattern': r'scope\s*([123])'
                },
                {
                    'pattern': r'([\d,]+\.?\d*)\s*(mt|metric\s*ton|tco2e?|tonnes?\s*co2e?)\s*(?:of\s*)?(?:scope\s*[123]?\s*)?(?:emissions?|ghg|greenhouse\s*gas)',
                    'value_group': 1,
                    'unit_group': 2
                },
                {
                    'pattern': r'reduced\s*(?:carbon|co2|ghg)\s*emissions?\s*by\s*([\d,]+\.?\d*)\s*(%|percent|tonnes?|mt)',
                    'value_group': 1,
                    'unit_group': 2,
                    'is_reduction': True
                }
            ],
            
            MetricCategory.ENERGY: [
                {
                    'pattern': r'(?:total\s*)?energy\s*(?:consumption|usage|use)\s*[:=]?\s*([\d,]+\.?\d*)\s*(mwh|gwh|kwh|tj|gj|mj)',
                    'value_group': 1,
                    'unit_group': 2
                },
                {
                    'pattern': r'([\d,]+\.?\d*)\s*(%|percent)\s*(?:of\s*)?(?:energy\s*)?(?:from\s*)?renewable\s*(?:energy\s*)?(?:sources?)?',
                    'value_group': 1,
                    'unit_group': 2,
                    'metric_subtype': 'renewable_percentage'
                },
                {
                    'pattern': r'renewable\s*energy\s*[:=]?\s*([\d,]+\.?\d*)\s*(mwh|gwh|kwh|%|percent)',
                    'value_group': 1,
                    'unit_group': 2
                }
            ],
            
            MetricCategory.WATER: [
                {
                    'pattern': r'water\s*(?:consumption|usage|withdrawal|use)\s*[:=]?\s*([\d,]+\.?\d*)\s*(m3|cubic\s*meters?|ml|million\s*liters?|gallons?|megalitres?)',
                    'value_group': 1,
                    'unit_group': 2
                },
                {
                    'pattern': r'([\d,]+\.?\d*)\s*(m3|cubic\s*meters?|ml|million\s*liters?)\s*(?:of\s*)?water',
                    'value_group': 1,
                    'unit_group': 2
                }
            ],
            
            MetricCategory.WASTE: [
                {
                    'pattern': r'(?:total\s*)?waste\s*(?:generated|produced)\s*[:=]?\s*([\d,]+\.?\d*)\s*(tonnes?|tons?|kg|mt)',
                    'value_group': 1,
                    'unit_group': 2
                },
                {
                    'pattern': r'([\d,]+\.?\d*)\s*(%|percent)\s*(?:of\s*)?waste\s*(?:diverted|recycled|recovered)',
                    'value_group': 1,
                    'unit_group': 2,
                    'metric_subtype': 'recycling_rate'
                }
            ],
            
            MetricCategory.DIVERSITY: [
                {
                    'pattern': r'([\d,]+\.?\d*)\s*(%|percent)\s*(?:of\s*)?(?:female|women)\s*(?:representation|employees?|workforce|directors?|board\s*members?)',
                    'value_group': 1,
                    'unit_group': 2,
                    'metric_subtype': 'gender_diversity'
                },
                {
                    'pattern': r'(?:female|women)\s*(?:representation|employees?|workforce)\s*[:=]?\s*([\d,]+\.?\d*)\s*(%|percent)',
                    'value_group': 1,
                    'unit_group': 2,
                    'metric_subtype': 'gender_diversity'
                }
            ],
            
            MetricCategory.HEALTH_SAFETY: [
                {
                    'pattern': r'(?:trir|total\s*recordable\s*incident\s*rate)\s*[:=]?\s*([\d,]+\.?\d*)',
                    'value_group': 1,
                    'unit_group': None,
                    'default_unit': 'rate',
                    'metric_subtype': 'trir'
                },
                {
                    'pattern': r'(?:ltifr|lost\s*time\s*injury\s*frequency\s*rate)\s*[:=]?\s*([\d,]+\.?\d*)',
                    'value_group': 1,
                    'unit_group': None,
                    'default_unit': 'rate',
                    'metric_subtype': 'ltifr'
                },
                {
                    'pattern': r'([\d,]+)\s*(?:workplace\s*)?(?:fatalities|deaths)',
                    'value_group': 1,
                    'unit_group': None,
                    'default_unit': 'count',
                    'metric_subtype': 'fatalities'
                }
            ],
            
            MetricCategory.TRAINING: [
                {
                    'pattern': r'([\d,]+\.?\d*)\s*(?:average\s*)?hours?\s*(?:of\s*)?training\s*(?:per\s*)?(?:employee|person)',
                    'value_group': 1,
                    'unit_group': None,
                    'default_unit': 'hours/employee'
                },
                {
                    'pattern': r'training\s*hours?\s*[:=]?\s*([\d,]+\.?\d*)\s*(?:hours?)?',
                    'value_group': 1,
                    'unit_group': None,
                    'default_unit': 'hours'
                }
            ]
        }
        
        return patterns
    
    def _build_unit_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Build unit standardization mappings"""
        
        return {
            # Emissions units
            'tco2': {'standard': 'tCO2e', 'category': 'emissions'},
            'tco2e': {'standard': 'tCO2e', 'category': 'emissions'},
            'tonnes co2': {'standard': 'tCO2e', 'category': 'emissions'},
            'tonnes co2e': {'standard': 'tCO2e', 'category': 'emissions'},
            'mt': {'standard': 'tCO2e', 'category': 'emissions', 'multiplier': 1000000},
            'metric ton': {'standard': 'tCO2e', 'category': 'emissions'},
            'kg co2': {'standard': 'tCO2e', 'category': 'emissions', 'multiplier': 0.001},
            'kg co2e': {'standard': 'tCO2e', 'category': 'emissions', 'multiplier': 0.001},
            
            # Energy units
            'mwh': {'standard': 'MWh', 'category': 'energy'},
            'gwh': {'standard': 'MWh', 'category': 'energy', 'multiplier': 1000},
            'kwh': {'standard': 'MWh', 'category': 'energy', 'multiplier': 0.001},
            'tj': {'standard': 'MWh', 'category': 'energy', 'multiplier': 277.778},
            'gj': {'standard': 'MWh', 'category': 'energy', 'multiplier': 0.277778},
            
            # Water units
            'm3': {'standard': 'm³', 'category': 'water'},
            'cubic meters': {'standard': 'm³', 'category': 'water'},
            'ml': {'standard': 'm³', 'category': 'water', 'multiplier': 1000000},
            'million liters': {'standard': 'm³', 'category': 'water', 'multiplier': 1000},
            'megalitres': {'standard': 'm³', 'category': 'water', 'multiplier': 1000},
            
            # Waste units
            'tonnes': {'standard': 'tonnes', 'category': 'waste'},
            'tons': {'standard': 'tonnes', 'category': 'waste', 'multiplier': 0.907185},
            'kg': {'standard': 'tonnes', 'category': 'waste', 'multiplier': 0.001},
            
            # Percentage
            '%': {'standard': '%', 'category': 'percentage'},
            'percent': {'standard': '%', 'category': 'percentage'}
        }
    
    def _build_framework_mappings(self) -> Dict[str, Dict[MetricCategory, List[str]]]:
        """Map metric categories to framework requirements"""
        
        return {
            'CSRD': {
                MetricCategory.GHG_EMISSIONS: ['E1-1', 'E1-2', 'E1-3', 'E1-4', 'E1-5'],
                MetricCategory.ENERGY: ['E1-5', 'E1-6'],
                MetricCategory.WATER: ['E3-1', 'E3-2', 'E3-3'],
                MetricCategory.WASTE: ['E5-1', 'E5-2', 'E5-3'],
                MetricCategory.DIVERSITY: ['S1-6', 'S1-7', 'S1-8'],
                MetricCategory.HEALTH_SAFETY: ['S1-4', 'S1-5'],
                MetricCategory.TRAINING: ['S1-10', 'S1-11']
            },
            'GRI': {
                MetricCategory.GHG_EMISSIONS: ['305-1', '305-2', '305-3', '305-4', '305-5'],
                MetricCategory.ENERGY: ['302-1', '302-2', '302-3', '302-4'],
                MetricCategory.WATER: ['303-3', '303-4', '303-5'],
                MetricCategory.WASTE: ['306-3', '306-4', '306-5'],
                MetricCategory.DIVERSITY: ['405-1', '405-2'],
                MetricCategory.HEALTH_SAFETY: ['403-9', '403-10'],
                MetricCategory.TRAINING: ['404-1', '404-2']
            },
            'SASB': {
                MetricCategory.GHG_EMISSIONS: ['EM-1', 'EM-2'],
                MetricCategory.ENERGY: ['EN-1', 'EN-2'],
                MetricCategory.WATER: ['WA-1', 'WA-2'],
                MetricCategory.WASTE: ['WS-1', 'WS-2'],
                MetricCategory.DIVERSITY: ['HC-1', 'HC-2'],
                MetricCategory.HEALTH_SAFETY: ['HS-1', 'HS-2']
            },
            'TCFD': {
                MetricCategory.GHG_EMISSIONS: ['MT-1', 'MT-2', 'MT-3'],
                MetricCategory.ENERGY: ['MT-4', 'MT-5']
            }
        }
    
    def extract_metrics(self, text: str, year: Optional[int] = None) -> List[ExtractedMetric]:
        """Extract all ESG metrics from text"""
        
        extracted_metrics = []
        
        # Extract year if not provided
        if not year:
            year = self._extract_year(text)
        
        # Process each metric category
        for category, patterns in self.metric_patterns.items():
            for pattern_info in patterns:
                matches = re.finditer(
                    pattern_info['pattern'], 
                    text, 
                    re.IGNORECASE | re.MULTILINE
                )
                
                for match in matches:
                    metric = self._process_match(
                        match, pattern_info, category, text, year
                    )
                    if metric:
                        extracted_metrics.append(metric)
        
        # Deduplicate and rank by confidence
        extracted_metrics = self._deduplicate_metrics(extracted_metrics)
        
        return extracted_metrics
    
    def _process_match(self, match: re.Match, pattern_info: Dict[str, Any], 
                      category: MetricCategory, full_text: str, 
                      year: Optional[int]) -> Optional[ExtractedMetric]:
        """Process a regex match into an ExtractedMetric"""
        
        try:
            # Extract value
            value_str = match.group(pattern_info['value_group'])
            value = float(value_str.replace(',', ''))
            
            # Extract unit
            if pattern_info.get('unit_group'):
                unit = match.group(pattern_info['unit_group']).lower()
            else:
                unit = pattern_info.get('default_unit', '')
            
            # Extract context (surrounding text)
            start = max(0, match.start() - 100)
            end = min(len(full_text), match.end() + 100)
            context = full_text[start:end].strip()
            
            # Extract scope for emissions
            scope = None
            if category == MetricCategory.GHG_EMISSIONS and 'scope_pattern' in pattern_info:
                scope_match = re.search(pattern_info['scope_pattern'], context, re.IGNORECASE)
                if scope_match:
                    scope = f"Scope {scope_match.group(1)}"
            
            # Normalize value and unit
            normalized_value, normalized_unit = self._normalize_metric(value, unit)
            
            # Determine metric name
            metric_name = self._generate_metric_name(category, pattern_info, context)
            
            # Calculate confidence
            confidence = self._calculate_confidence(match, context, pattern_info)
            
            # Map to frameworks
            framework_mappings = {}
            for framework, mappings in self.framework_mappings.items():
                if category in mappings:
                    framework_mappings[framework] = mappings[category]
            
            return ExtractedMetric(
                metric_name=metric_name,
                value=value,
                unit=unit,
                category=category,
                context=context,
                confidence=confidence,
                year=year,
                scope=scope,
                normalized_value=normalized_value,
                normalized_unit=normalized_unit,
                framework_mappings=framework_mappings
            )
            
        except Exception as e:
            logger.error(f"Error processing match: {e}")
            return None
    
    def _normalize_metric(self, value: float, unit: str) -> Tuple[float, str]:
        """Normalize metric value and unit"""
        
        unit_lower = unit.lower().strip()
        
        if unit_lower in self.unit_mappings:
            mapping = self.unit_mappings[unit_lower]
            normalized_unit = mapping['standard']
            
            # Apply multiplier if exists
            if 'multiplier' in mapping:
                normalized_value = value * mapping['multiplier']
            else:
                normalized_value = value
                
            return normalized_value, normalized_unit
        
        return value, unit
    
    def _generate_metric_name(self, category: MetricCategory, 
                            pattern_info: Dict[str, Any], context: str) -> str:
        """Generate descriptive metric name"""
        
        base_name = category.value.replace('_', ' ').title()
        
        # Add subtype if available
        if 'metric_subtype' in pattern_info:
            subtype = pattern_info['metric_subtype'].replace('_', ' ').title()
            return f"{base_name} - {subtype}"
        
        # Add scope for emissions
        if category == MetricCategory.GHG_EMISSIONS:
            if 'scope 1' in context.lower():
                return f"{base_name} - Scope 1"
            elif 'scope 2' in context.lower():
                return f"{base_name} - Scope 2"
            elif 'scope 3' in context.lower():
                return f"{base_name} - Scope 3"
        
        # Add reduction/increase context
        if 'is_reduction' in pattern_info:
            return f"{base_name} - Reduction"
        
        return base_name
    
    def _calculate_confidence(self, match: re.Match, context: str, 
                            pattern_info: Dict[str, Any]) -> float:
        """Calculate confidence score for extracted metric"""
        
        confidence = 0.7  # Base confidence
        
        # Boost for exact pattern matches
        if match.group(0).count(' ') < 5:  # Compact match
            confidence += 0.1
        
        # Boost for year proximity
        year_pattern = r'\b(20\d{2})\b'
        year_matches = re.findall(year_pattern, context)
        if year_matches:
            confidence += 0.1
        
        # Boost for framework mentions
        framework_keywords = ['gri', 'sasb', 'tcfd', 'csrd', 'reported', 'disclosed']
        if any(keyword in context.lower() for keyword in framework_keywords):
            confidence += 0.05
        
        # Penalty for conditional language
        conditional_words = ['target', 'goal', 'aim', 'plan', 'expect', 'forecast']
        if any(word in context.lower() for word in conditional_words):
            confidence -= 0.2
        
        return min(max(confidence, 0.1), 0.95)
    
    def _extract_year(self, text: str) -> Optional[int]:
        """Extract reporting year from text"""
        
        # Look for common year patterns
        patterns = [
            r'(?:fiscal|fy|year|reporting\s*period)\s*(\d{4})',
            r'(?:as\s*of|ended)\s*(?:december|dec)?\s*\d{1,2},?\s*(\d{4})',
            r'(\d{4})\s*(?:annual|sustainability|esg)\s*report',
            r'(?:in|for|during)\s*(\d{4})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                year = int(match.group(1))
                if 2000 <= year <= datetime.now().year + 1:
                    return year
        
        return None
    
    def _deduplicate_metrics(self, metrics: List[ExtractedMetric]) -> List[ExtractedMetric]:
        """Remove duplicate metrics, keeping highest confidence"""
        
        unique_metrics = {}
        
        for metric in metrics:
            # Create key for deduplication
            key = (
                metric.metric_name,
                metric.normalized_value,
                metric.normalized_unit,
                metric.year,
                metric.scope
            )
            
            if key not in unique_metrics or metric.confidence > unique_metrics[key].confidence:
                unique_metrics[key] = metric
        
        return list(unique_metrics.values())
    
    def map_to_frameworks(self, metrics: List[ExtractedMetric], 
                         frameworks: List[str]) -> Dict[str, Dict[str, List[ExtractedMetric]]]:
        """Map extracted metrics to specific framework requirements"""
        
        framework_metrics = {fw: {} for fw in frameworks}
        
        for metric in metrics:
            for framework in frameworks:
                if framework in metric.framework_mappings:
                    for requirement_id in metric.framework_mappings[framework]:
                        if requirement_id not in framework_metrics[framework]:
                            framework_metrics[framework][requirement_id] = []
                        framework_metrics[framework][requirement_id].append(metric)
        
        return framework_metrics
    
    def identify_gaps(self, extracted_metrics: List[ExtractedMetric], 
                     frameworks: List[str]) -> Dict[str, List[str]]:
        """Identify missing metrics for each framework"""
        
        gaps = {fw: [] for fw in frameworks}
        
        # Get all requirements for each framework
        for framework in frameworks:
            if framework in self.framework_mappings:
                all_requirements = set()
                for category_requirements in self.framework_mappings[framework].values():
                    all_requirements.update(category_requirements)
                
                # Check which requirements have metrics
                covered_requirements = set()
                for metric in extracted_metrics:
                    if framework in metric.framework_mappings:
                        covered_requirements.update(metric.framework_mappings[framework])
                
                # Identify gaps
                gaps[framework] = list(all_requirements - covered_requirements)
        
        return gaps
    
    def generate_metrics_report(self, metrics: List[ExtractedMetric]) -> Dict[str, Any]:
        """Generate comprehensive metrics report"""
        
        report = {
            'total_metrics': len(metrics),
            'metrics_by_category': {},
            'metrics_by_year': {},
            'normalized_metrics': [],
            'high_confidence_metrics': [],
            'coverage_summary': {}
        }
        
        # Group by category
        for metric in metrics:
            category = metric.category.value
            if category not in report['metrics_by_category']:
                report['metrics_by_category'][category] = []
            report['metrics_by_category'][category].append({
                'name': metric.metric_name,
                'value': metric.value,
                'unit': metric.unit,
                'normalized_value': metric.normalized_value,
                'normalized_unit': metric.normalized_unit,
                'confidence': metric.confidence,
                'year': metric.year
            })
        
        # Group by year
        for metric in metrics:
            if metric.year:
                year = str(metric.year)
                if year not in report['metrics_by_year']:
                    report['metrics_by_year'][year] = []
                report['metrics_by_year'][year].append(metric.metric_name)
        
        # High confidence metrics
        report['high_confidence_metrics'] = [
            {
                'name': m.metric_name,
                'value': f"{m.normalized_value} {m.normalized_unit}",
                'confidence': m.confidence
            }
            for m in metrics if m.confidence >= 0.8
        ]
        
        # Coverage summary
        for framework, mapping in self.framework_mappings.items():
            total_requirements = sum(len(reqs) for reqs in mapping.values())
            covered = sum(
                1 for m in metrics 
                if framework in m.framework_mappings 
                and m.framework_mappings[framework]
            )
            report['coverage_summary'][framework] = {
                'total_requirements': total_requirements,
                'covered': covered,
                'percentage': round((covered / total_requirements * 100) if total_requirements > 0 else 0, 1)
            }
        
        return report


# Example usage
if __name__ == "__main__":
    # Test the extractor
    extractor = MetricsExtractor()
    
    sample_text = """
    In 2023, our company achieved significant environmental milestones:
    - Total Scope 1 emissions: 45,000 tCO2e
    - Scope 2 emissions reduced to 23,500 metric tons CO2
    - Scope 3 emissions: 120,000 tonnes CO2e
    - Energy consumption: 450 GWh (35% from renewable sources)
    - Water usage: 2.5 million cubic meters
    - Waste generated: 12,000 tonnes (78% diverted from landfill)
    - Female representation: 42% of total workforce
    - Board diversity: 38% women directors
    - TRIR: 0.45
    - Average training hours per employee: 32 hours
    """
    
    metrics = extractor.extract_metrics(sample_text)
    
    print(f"Extracted {len(metrics)} metrics:")
    for metric in metrics:
        print(f"- {metric.metric_name}: {metric.normalized_value} {metric.normalized_unit} (confidence: {metric.confidence:.2f})")
    
    # Generate report
    report = extractor.generate_metrics_report(metrics)
    print(f"\nCoverage Summary:")
    for framework, coverage in report['coverage_summary'].items():
        print(f"- {framework}: {coverage['percentage']}% coverage") 