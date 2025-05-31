"""
API Versioning for ESG Platform
================================

Implements API versioning with:
- URL path versioning (/v1/, /v2/)
- Header-based versioning
- Backward compatibility
- Deprecation warnings
"""

from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Callable
from datetime import datetime
from functools import wraps

# Version configuration
API_VERSIONS = {
    "v1": {
        "status": "stable",
        "released": "2024-01-01",
        "deprecated": None,
        "sunset": None,
    },
    "v2": {
        "status": "beta",
        "released": "2024-06-01",
        "deprecated": None,
        "sunset": None,
    },
}

DEFAULT_VERSION = "v1"
SUNSET_WARNING_DAYS = 90


class APIVersion:
    """API Version handler"""

    def __init__(self, version: str):
        self.version = version
        self.info = API_VERSIONS.get(version, {})

    @property
    def is_deprecated(self) -> bool:
        return self.info.get("deprecated") is not None

    @property
    def is_sunset(self) -> bool:
        sunset = self.info.get("sunset")
        if sunset:
            return datetime.now() > datetime.fromisoformat(sunset)
        return False

    @property
    def days_until_sunset(self) -> Optional[int]:
        sunset = self.info.get("sunset")
        if sunset:
            delta = datetime.fromisoformat(sunset) - datetime.now()
            return delta.days
        return None


def version_router(app: FastAPI) -> Dict[str, FastAPI]:
    """Create versioned routers"""
    routers = {}

    for version in API_VERSIONS:
        versioned_app = FastAPI(
            title=f"ESG Intelligence API {version.upper()}",
            version=version,
            docs_url=f"/{version}/docs",
            redoc_url=f"/{version}/redoc",
            openapi_url=f"/{version}/openapi.json",
        )
        routers[version] = versioned_app

    return routers


class VersionMiddleware:
    """Middleware to handle API versioning"""

    def __init__(self, app: FastAPI, routers: Dict[str, FastAPI]):
        self.app = app
        self.routers = routers

    async def __call__(self, request: Request, call_next):
        # Extract version from path
        path_parts = request.url.path.strip("/").split("/")

        if path_parts and path_parts[0] in API_VERSIONS:
            version = path_parts[0]
            api_version = APIVersion(version)

            # Check if version is sunset
            if api_version.is_sunset:
                return JSONResponse(
                    status_code=410,
                    content={
                        "error": "API version sunset",
                        "message": f"Version {version} is no longer available",
                        "current_version": DEFAULT_VERSION,
                    },
                )

            # Add deprecation headers if needed
            response = await call_next(request)

            if api_version.is_deprecated:
                response.headers["Sunset"] = api_version.info["sunset"]
                response.headers["Deprecation"] = "true"
                response.headers["Link"] = (
                    f'</{DEFAULT_VERSION}/>; rel="successor-version"'
                )

                if (
                    api_version.days_until_sunset
                    and api_version.days_until_sunset <= SUNSET_WARNING_DAYS
                ):
                    response.headers["Warning"] = (
                        f'299 - "This API version will sunset in {api_version.days_until_sunset} days"'
                    )

            response.headers["API-Version"] = version
            return response

        # Default to latest stable version
        response = await call_next(request)
        response.headers["API-Version"] = DEFAULT_VERSION
        return response


def versioned_endpoint(versions: Dict[str, Callable]):
    """Decorator for version-specific endpoint implementations"""

    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Get version from request
            version = request.path_params.get("version", DEFAULT_VERSION)

            # Get version-specific implementation
            implementation = versions.get(version, versions.get(DEFAULT_VERSION))

            if not implementation:
                raise HTTPException(
                    status_code=400,
                    detail=f"Endpoint not available in version {version}",
                )

            return await implementation(*args, **kwargs)

        return wrapper

    return decorator


# Version-specific response transformers
class ResponseTransformer:
    """Transform responses between API versions"""

    @staticmethod
    def v1_to_v2_analysis(v1_response: Dict) -> Dict:
        """Transform v1 analysis response to v2 format"""
        v2_response = v1_response.copy()

        # V2 adds nested score structure
        if "scores" in v2_response:
            v2_response["scoring"] = {
                "methodology": "keyword-based",
                "version": "2.0",
                "scores": v2_response["scores"],
                "confidence_intervals": {
                    "environmental": {"low": 0.9, "high": 1.1},
                    "social": {"low": 0.9, "high": 1.1},
                    "governance": {"low": 0.9, "high": 1.1},
                },
            }
            del v2_response["scores"]

        # V2 adds metadata
        v2_response["_metadata"] = {
            "api_version": "v2",
            "response_time_ms": 0,  # Would be calculated
            "rate_limit_remaining": 100,
        }

        return v2_response

    @staticmethod
    def v2_to_v1_analysis(v2_response: Dict) -> Dict:
        """Transform v2 analysis response to v1 format"""
        v1_response = v2_response.copy()

        # Extract scores from nested structure
        if "scoring" in v1_response:
            v1_response["scores"] = v1_response["scoring"]["scores"]
            del v1_response["scoring"]

        # Remove v2-only fields
        v1_response.pop("_metadata", None)

        return v1_response


# Example versioned endpoint implementations
async def analyze_v1(request_data: Dict) -> Dict:
    """V1 analysis implementation"""
    # Original implementation
    return {
        "scores": {
            "environmental": 75.0,
            "social": 80.0,
            "governance": 85.0,
            "overall": 80.0,
        },
        "keywords": ["sustainability", "carbon neutral"],
        "analysis_type": "quick",
    }


async def analyze_v2(request_data: Dict) -> Dict:
    """V2 analysis implementation with enhanced features"""
    # Enhanced implementation
    result = await analyze_v1(request_data)

    # Transform to v2 format
    return ResponseTransformer.v1_to_v2_analysis(result)


# Version negotiation
def negotiate_version(
    accept_version: Optional[str] = Header(None, alias="Accept-Version"),
    api_version: Optional[str] = Header(None, alias="API-Version"),
) -> str:
    """Negotiate API version from headers"""
    # Priority: Accept-Version > API-Version > Default
    requested_version = accept_version or api_version

    if requested_version:
        # Validate version
        if requested_version not in API_VERSIONS:
            raise HTTPException(
                status_code=400, detail=f"Unsupported API version: {requested_version}"
            )

        # Check if sunset
        version_info = APIVersion(requested_version)
        if version_info.is_sunset:
            raise HTTPException(
                status_code=410,
                detail=f"API version {requested_version} has been sunset",
            )

        return requested_version

    return DEFAULT_VERSION


# Migration utilities
class MigrationGuide:
    """Generate migration guides between versions"""

    @staticmethod
    def generate_v1_to_v2() -> Dict:
        """Generate migration guide from v1 to v2"""
        return {
            "breaking_changes": [
                {
                    "endpoint": "/analyze",
                    "change": "Response structure changed - scores moved to scoring.scores",
                    "migration": "Access scores at response.scoring.scores instead of response.scores",
                }
            ],
            "new_features": [
                {
                    "feature": "Confidence intervals",
                    "description": "Score confidence intervals added to all analyses",
                },
                {
                    "feature": "Response metadata",
                    "description": "API metadata included in all responses",
                },
            ],
            "deprecated_features": [
                {
                    "feature": "Simple score format",
                    "replacement": "Nested scoring structure",
                    "sunset_date": "2025-01-01",
                }
            ],
        }


# Example usage in main app
def setup_versioning(app: FastAPI):
    """Set up API versioning for the main app"""

    # Create versioned routers
    routers = version_router(app)

    # Mount versioned apps
    for version, router in routers.items():
        app.mount(f"/{version}", router)

    # Add version middleware
    app.add_middleware(VersionMiddleware, routers=routers)

    # Add version discovery endpoint
    @app.get("/versions")
    async def get_versions():
        """Get available API versions"""
        return {
            "versions": API_VERSIONS,
            "default": DEFAULT_VERSION,
            "current": DEFAULT_VERSION,
            "supported": [
                v for v, info in API_VERSIONS.items() if not APIVersion(v).is_sunset
            ],
        }

    # Add migration guide endpoint
    @app.get("/migration/{from_version}/{to_version}")
    async def get_migration_guide(from_version: str, to_version: str):
        """Get migration guide between versions"""
        if from_version == "v1" and to_version == "v2":
            return MigrationGuide.generate_v1_to_v2()

        raise HTTPException(
            status_code=404,
            detail=f"No migration guide available from {from_version} to {to_version}",
        )

    return routers
