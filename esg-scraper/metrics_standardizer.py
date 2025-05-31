"""
Metrics Standardization Module
=============================

Standardizes extracted ESG metrics for consistent database storage and analysis.
Handles unit conversion, normalization, and validation.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class MetricCategory(Enum):
    """Standard metric categories"""

    EMISSIONS = "emissions"
    ENERGY = "energy"
    WATER = "water"
    WASTE = "waste"
    SOCIAL = "social"
    GOVERNANCE = "governance"
    FINANCIAL = "financial"


class MetricUnit(Enum):
    """Standard units for metrics"""

    # Emissions
    TCO2E = "tCO2e"  # Metric tons CO2 equivalent
    KTCO2E = "ktCO2e"  # Kilotons CO2 equivalent
    MTCO2E = "MtCO2e"  # Megatons CO2 equivalent

    # Energy
    KWH = "kWh"  # Kilowatt hours
    MWH = "MWh"  # Megawatt hours
    GWH = "GWh"  # Gigawatt hours
    TJ = "TJ"  # Terajoules

    # Water
    M3 = "m3"  # Cubic meters
    LITERS = "liters"
    MEGALITERS = "ML"  # Megaliters

    # Waste
    KG = "kg"  # Kilograms
    TONS = "tons"  # Metric tons

    # Social
    COUNT = "count"  # People, incidents, etc.
    PERCENTAGE = "%"  # Percentages
    HOURS = "hours"  # Training hours, etc.

    # Financial
    USD = "USD"  # US Dollars
    EUR = "EUR"  # Euros
    GBP = "GBP"  # British Pounds


class MetricStandardizer:
    """Standardizes and normalizes ESG metrics"""

    def __init__(self):
        self.unit_conversions = self._build_unit_conversions()
        self.metric_patterns = self._build_metric_patterns()
        self.validation_rules = self._build_validation_rules()

    def standardize_metrics(
        self, metrics: List[Dict[str, Any]], company_context: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Standardize a list of extracted metrics

        Args:
            metrics: List of raw extracted metrics
            company_context: Optional context (industry, size, etc.)

        Returns:
            List of standardized metrics
        """
        standardized = []

        for metric in metrics:
            try:
                std_metric = self._standardize_single_metric(metric, company_context)
                if std_metric and self._validate_metric(std_metric):
                    standardized.append(std_metric)
            except Exception as e:
                logger.warning(f"Failed to standardize metric: {metric}, error: {e}")
                continue

        return standardized

    def _standardize_single_metric(
        self, metric: Dict[str, Any], context: Dict[str, Any] = None
    ) -> Optional[Dict[str, Any]]:
        """Standardize a single metric"""

        # Extract components
        name = metric.get("metric_name", "").lower()
        value = metric.get("metric_value", "")
        unit = metric.get("metric_unit", "")

        # Categorize metric
        category = self._categorize_metric(name, unit)

        # Parse and normalize value
        normalized_value, confidence = self._normalize_value(value)
        if normalized_value is None:
            return None

        # Standardize unit
        std_unit = self._standardize_unit(unit, category)

        # Convert to base unit
        base_value = self._convert_to_base_unit(normalized_value, unit, std_unit)

        # Build standardized metric
        standardized = {
            "metric_name": self._standardize_name(name),
            "metric_value": base_value,
            "metric_unit": std_unit,
            "metric_category": category.value,
            "original_value": metric.get("metric_value"),
            "original_unit": metric.get("metric_unit"),
            "confidence": min(metric.get("confidence", 0.5) * confidence, 1.0),
            "framework": metric.get("framework"),
            "requirement_id": metric.get("requirement_id"),
            "reporting_period": self._extract_period(metric, context),
            "scope": self._extract_scope(name),
            "is_target": self._is_target_metric(name),
            "standardized_at": datetime.utcnow().isoformat(),
        }

        # Add context if available
        if context:
            standardized["company_size"] = context.get("size")
            standardized["industry_sector"] = context.get("industry")

        return standardized

    def _categorize_metric(self, name: str, unit: str) -> MetricCategory:
        """Categorize metric based on name and unit"""
        name_lower = name.lower()
        unit_lower = unit.lower()

        # Emissions
        if any(term in name_lower for term in ["emission", "co2", "ghg", "carbon"]):
            return MetricCategory.EMISSIONS

        # Energy
        if any(
            term in name_lower for term in ["energy", "electricity", "power"]
        ) or any(term in unit_lower for term in ["kwh", "mwh", "gwh", "joule"]):
            return MetricCategory.ENERGY

        # Water
        if any(term in name_lower for term in ["water", "consumption"]) and any(
            term in unit_lower for term in ["liter", "litre", "m3", "cubic"]
        ):
            return MetricCategory.WATER

        # Waste
        if any(term in name_lower for term in ["waste", "recycl", "disposal"]):
            return MetricCategory.WASTE

        # Social
        if any(
            term in name_lower
            for term in [
                "employee",
                "worker",
                "diversity",
                "training",
                "safety",
                "incident",
            ]
        ):
            return MetricCategory.SOCIAL

        # Governance
        if any(
            term in name_lower
            for term in ["board", "governance", "ethics", "compliance", "audit"]
        ):
            return MetricCategory.GOVERNANCE

        # Financial
        if any(term in unit_lower for term in ["usd", "eur", "gbp", "$", "€", "£"]):
            return MetricCategory.FINANCIAL

        # Default to emissions if unclear
        return MetricCategory.EMISSIONS

    def _normalize_value(self, value: str) -> Tuple[Optional[float], float]:
        """
        Normalize value string to float
        Returns (normalized_value, confidence)
        """
        if not value:
            return None, 0.0

        # Remove commas and spaces
        cleaned = str(value).replace(",", "").replace(" ", "")

        # Handle ranges (e.g., "100-150")
        if "-" in cleaned and not cleaned.startswith("-"):
            parts = cleaned.split("-")
            try:
                # Take average of range
                avg = (float(parts[0]) + float(parts[1])) / 2
                return avg, 0.8  # Lower confidence for ranges
            except:
                pass

        # Handle approximate values (e.g., "~100", "approximately 100")
        if cleaned.startswith("~") or "approx" in str(value).lower():
            cleaned = cleaned.replace("~", "")
            try:
                return float(cleaned), 0.9  # Slightly lower confidence
            except:
                pass

        # Standard conversion
        try:
            return float(cleaned), 1.0
        except:
            # Try extracting first number
            numbers = re.findall(r"-?\d+\.?\d*", cleaned)
            if numbers:
                return float(numbers[0]), 0.7  # Lower confidence

        return None, 0.0

    def _standardize_unit(self, unit: str, category: MetricCategory) -> str:
        """Standardize unit based on category"""
        unit_lower = unit.lower().strip()

        # Map common variations to standard units
        unit_mappings = {
            # Emissions
            "tco2e": MetricUnit.TCO2E.value,
            "tons co2": MetricUnit.TCO2E.value,
            "tonnes co2": MetricUnit.TCO2E.value,
            "metric tons co2": MetricUnit.TCO2E.value,
            "ktco2e": MetricUnit.KTCO2E.value,
            "mtco2e": MetricUnit.MTCO2E.value,
            # Energy
            "kwh": MetricUnit.KWH.value,
            "mwh": MetricUnit.MWH.value,
            "gwh": MetricUnit.GWH.value,
            "terajoules": MetricUnit.TJ.value,
            "tj": MetricUnit.TJ.value,
            # Water
            "m3": MetricUnit.M3.value,
            "cubic meters": MetricUnit.M3.value,
            "liters": MetricUnit.LITERS.value,
            "litres": MetricUnit.LITERS.value,
            "megaliters": MetricUnit.MEGALITERS.value,
            "ml": MetricUnit.MEGALITERS.value,
            # Waste
            "kg": MetricUnit.KG.value,
            "tons": MetricUnit.TONS.value,
            "tonnes": MetricUnit.TONS.value,
            "metric tons": MetricUnit.TONS.value,
            # Percentage
            "%": MetricUnit.PERCENTAGE.value,
            "percent": MetricUnit.PERCENTAGE.value,
            "percentage": MetricUnit.PERCENTAGE.value,
        }

        # Check mappings
        for key, value in unit_mappings.items():
            if key in unit_lower:
                return value

        # Category-based defaults
        category_defaults = {
            MetricCategory.EMISSIONS: MetricUnit.TCO2E.value,
            MetricCategory.ENERGY: MetricUnit.MWH.value,
            MetricCategory.WATER: MetricUnit.M3.value,
            MetricCategory.WASTE: MetricUnit.TONS.value,
            MetricCategory.SOCIAL: MetricUnit.COUNT.value,
            MetricCategory.GOVERNANCE: MetricUnit.PERCENTAGE.value,
            MetricCategory.FINANCIAL: MetricUnit.USD.value,
        }

        return category_defaults.get(category, unit)

    def _convert_to_base_unit(
        self, value: float, from_unit: str, to_unit: str
    ) -> float:
        """Convert value to base unit"""

        # Define conversion factors to base units
        conversions = {
            # Emissions to tCO2e
            ("ktco2e", "tCO2e"): 1000,
            ("mtco2e", "tCO2e"): 1000000,
            # Energy to MWh
            ("kwh", "MWh"): 0.001,
            ("gwh", "MWh"): 1000,
            ("tj", "MWh"): 277.778,  # 1 TJ = 277.778 MWh
            # Water to m3
            ("liters", "m3"): 0.001,
            ("megaliters", "m3"): 1000,
            ("ml", "m3"): 1000,
            # Waste to tons
            ("kg", "tons"): 0.001,
        }

        # Normalize unit names
        from_normalized = from_unit.lower().replace(" ", "")
        to_normalized = to_unit

        # Look for conversion
        key = (from_normalized, to_normalized)
        if key in conversions:
            return value * conversions[key]

        # Inverse conversion
        inverse_key = (to_normalized, from_normalized)
        if inverse_key in conversions:
            return value / conversions[inverse_key]

        # No conversion needed
        return value

    def _standardize_name(self, name: str) -> str:
        """Standardize metric name"""
        # Common name standardizations
        name_mappings = {
            "scope 1 emissions": "Scope 1 GHG Emissions",
            "scope 2 emissions": "Scope 2 GHG Emissions",
            "scope 3 emissions": "Scope 3 GHG Emissions",
            "energy consumption": "Total Energy Consumption",
            "renewable energy": "Renewable Energy Consumption",
            "water consumption": "Total Water Consumption",
            "waste generated": "Total Waste Generated",
            "recycling rate": "Waste Recycling Rate",
            "employee turnover": "Employee Turnover Rate",
            "gender diversity": "Gender Diversity Ratio",
            "board diversity": "Board Diversity Ratio",
        }

        name_lower = name.lower().strip()

        # Check mappings
        for key, value in name_mappings.items():
            if key in name_lower:
                return value

        # Title case if no mapping found
        return name.title()

    def _extract_period(
        self, metric: Dict[str, Any], context: Dict[str, Any] = None
    ) -> str:
        """Extract reporting period"""
        # Check metric for year
        value_str = str(metric.get("metric_value", ""))
        year_match = re.search(r"20\d{2}", value_str)
        if year_match:
            return year_match.group()

        # Check context
        if context and context.get("reporting_period"):
            return context["reporting_period"]

        # Default to current year
        return str(datetime.now().year)

    def _extract_scope(self, name: str) -> Optional[str]:
        """Extract scope from metric name"""
        name_lower = name.lower()

        if "scope 1" in name_lower:
            return "1"
        elif "scope 2" in name_lower:
            return "2"
        elif "scope 3" in name_lower:
            return "3"

        return None

    def _is_target_metric(self, name: str) -> bool:
        """Determine if metric is a target/goal"""
        target_keywords = [
            "target",
            "goal",
            "commitment",
            "by 2030",
            "by 2040",
            "by 2050",
            "will",
            "plan to",
            "aim to",
        ]
        name_lower = name.lower()
        return any(keyword in name_lower for keyword in target_keywords)

    def _validate_metric(self, metric: Dict[str, Any]) -> bool:
        """Validate standardized metric"""
        # Required fields
        required = ["metric_name", "metric_value", "metric_unit", "metric_category"]
        if not all(field in metric for field in required):
            return False

        # Value validation
        value = metric["metric_value"]
        if not isinstance(value, (int, float)) or value < 0:
            return False

        # Category validation
        if metric["metric_category"] not in [c.value for c in MetricCategory]:
            return False

        # Percentage validation
        if metric["metric_unit"] == "%" and value > 100:
            return False

        return True

    def _build_unit_conversions(self) -> Dict[Tuple[str, str], float]:
        """Build comprehensive unit conversion table"""
        return {
            # Emissions
            ("kg co2", "tCO2e"): 0.001,
            ("lb co2", "tCO2e"): 0.000453592,
            # Energy
            ("btu", "MWh"): 0.00000029307,
            ("gj", "MWh"): 0.277778,
            # Add more conversions as needed
        }

    def _build_metric_patterns(self) -> Dict[str, re.Pattern]:
        """Build regex patterns for metric extraction"""
        return {
            "emissions_reduction": re.compile(
                r"reduced?.*emissions?.*by\s+(\d+\.?\d*)\s*(%|percent)", re.IGNORECASE
            ),
            "renewable_energy": re.compile(
                r"(\d+\.?\d*)\s*(%|percent).*renewable\s+energy", re.IGNORECASE
            ),
            # Add more patterns
        }

    def _build_validation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Build validation rules for different metric types"""
        return {
            "emissions": {
                "min": 0,
                "max": 1000000000,  # 1 billion tCO2e (reasonable upper limit)
                "units": [MetricUnit.TCO2E, MetricUnit.KTCO2E, MetricUnit.MTCO2E],
            },
            "percentage": {"min": 0, "max": 100, "units": [MetricUnit.PERCENTAGE]},
            # Add more rules
        }

    def aggregate_metrics(
        self, metrics: List[Dict[str, Any]], aggregation_type: str = "sum"
    ) -> Dict[str, Any]:
        """
        Aggregate metrics by category and type

        Args:
            metrics: List of standardized metrics
            aggregation_type: "sum", "average", "latest"
        """
        from collections import defaultdict

        aggregated = defaultdict(lambda: defaultdict(list))

        for metric in metrics:
            category = metric["metric_category"]
            name = metric["metric_name"]
            value = metric["metric_value"]

            aggregated[category][name].append(
                {
                    "value": value,
                    "unit": metric["metric_unit"],
                    "period": metric.get("reporting_period"),
                    "confidence": metric.get("confidence", 1.0),
                }
            )

        # Perform aggregation
        result = {}
        for category, metrics_dict in aggregated.items():
            result[category] = {}
            for name, values in metrics_dict.items():
                if aggregation_type == "sum":
                    total = sum(v["value"] for v in values)
                    result[category][name] = {
                        "value": total,
                        "unit": values[0]["unit"],
                        "count": len(values),
                    }
                elif aggregation_type == "average":
                    avg = sum(v["value"] for v in values) / len(values)
                    result[category][name] = {
                        "value": avg,
                        "unit": values[0]["unit"],
                        "count": len(values),
                    }
                elif aggregation_type == "latest":
                    # Sort by period and take latest
                    sorted_values = sorted(
                        values, key=lambda x: x.get("period", ""), reverse=True
                    )
                    result[category][name] = {
                        "value": sorted_values[0]["value"],
                        "unit": sorted_values[0]["unit"],
                        "period": sorted_values[0].get("period"),
                    }

        return result
