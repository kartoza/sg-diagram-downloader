#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utility to check the status of all API/web service endpoints used by the
SG Diagram Downloader plugin.

This script:
1. Identifies all endpoints used by the downloader
2. Tests each endpoint for availability
3. Reports which endpoints are working, broken, or unused

Usage:
    python scripts/check_endpoints.py

    # Or as a module:
    from scripts.check_endpoints import get_endpoint_mapping
    mapping = get_endpoint_mapping()
"""

import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import httpx


class EndpointStatus(Enum):
    """Status of an endpoint."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    TIMEOUT = "timeout"
    ERROR = "error"
    UNKNOWN = "unknown"


class EndpointCategory(Enum):
    """Category for endpoint mapping."""

    USED_AND_AVAILABLE = "used_and_available"
    USED_BUT_UNAVAILABLE = "used_but_unavailable"
    NOT_USED_BUT_AVAILABLE = "not_used_but_available"
    NOT_USED_AND_UNAVAILABLE = "not_used_and_unavailable"


@dataclass
class Endpoint:
    """Represents an API endpoint."""

    name: str
    url: str
    method: str = "GET"
    description: str = ""
    used_in_code: bool = True
    source_file: str = ""
    source_line: Optional[int] = None
    test_params: Optional[dict] = None


@dataclass
class EndpointResult:
    """Result of testing an endpoint."""

    endpoint: Endpoint
    status: EndpointStatus
    category: Optional[EndpointCategory] = None
    status_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None


@dataclass
class EndpointMapping:
    """Complete mapping of all endpoints with their status and availability."""

    used_and_available: list[EndpointResult] = field(default_factory=list)
    used_but_unavailable: list[EndpointResult] = field(default_factory=list)
    not_used_but_available: list[EndpointResult] = field(default_factory=list)
    not_used_and_unavailable: list[EndpointResult] = field(default_factory=list)
    all_results: list[EndpointResult] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert mapping to a dictionary for easy serialization."""
        return {
            "used_and_available": [
                {"name": r.endpoint.name, "url": r.endpoint.url, "status_code": r.status_code}
                for r in self.used_and_available
            ],
            "used_but_unavailable": [
                {"name": r.endpoint.name, "url": r.endpoint.url, "error": r.error_message}
                for r in self.used_but_unavailable
            ],
            "not_used_but_available": [
                {"name": r.endpoint.name, "url": r.endpoint.url, "status_code": r.status_code}
                for r in self.not_used_but_available
            ],
            "not_used_and_unavailable": [
                {"name": r.endpoint.name, "url": r.endpoint.url, "error": r.error_message}
                for r in self.not_used_and_unavailable
            ],
            "summary": {
                "total": len(self.all_results),
                "used_and_available": len(self.used_and_available),
                "used_but_unavailable": len(self.used_but_unavailable),
                "not_used_but_available": len(self.not_used_but_available),
                "not_used_and_unavailable": len(self.not_used_and_unavailable),
            },
        }


# Define all endpoints actively used by the SG Diagram Downloader
ENDPOINTS_IN_CODE = [
    Endpoint(
        name="SG Base URL",
        url="http://csg.drdlr.gov.za/",
        description="Main Surveyor General website base URL",
        used_in_code=True,
        source_file="definitions.py",
        source_line=4,
    ),
    Endpoint(
        name="SG List Documents",
        url="http://csg.drdlr.gov.za/esio/listdocument.jsp",
        description="Lists available SG diagram documents for a parcel",
        used_in_code=True,
        source_file="sg_utilities.py",
        source_line=186,
        test_params={
            "regDivision": "C0160000",
            "office": "SGCTN",
            "Noffice": "2",
            "Erf": "00000001",
            "Portion": "00000",
        },
    ),
    Endpoint(
        name="SG View TIFF",
        url="http://csg.drdlr.gov.za/esio/viewTIFF",
        description="Downloads SG diagram TIFF images",
        used_in_code=True,
        source_file="sg_utilities.py",
        source_line=285,
    ),
    Endpoint(
        name="SG ESIO Base",
        url="http://csg.drdlr.gov.za/esio/",
        description="ESIO service base path used to construct download URLs",
        used_in_code=True,
        source_file="sg_utilities.py",
        source_line=285,
    ),
]

# Known/documented endpoints that are NOT actively used in the code
# These include commented-out alternatives and discovered endpoints
KNOWN_UNUSED_ENDPOINTS = [
    Endpoint(
        name="Alternative IP Base",
        url="http://196.25.56.232/",
        description="Alternative base URL (commented out in code)",
        used_in_code=False,
        source_file="definitions.py",
        source_line=5,
    ),
    Endpoint(
        name="Alternative IP ESIO",
        url="http://196.25.56.232/esio/",
        description="Alternative ESIO path via IP",
        used_in_code=False,
    ),
    Endpoint(
        name="Alternative IP List Documents",
        url="http://196.25.56.232/esio/listdocument.jsp",
        description="Alternative list documents via IP",
        used_in_code=False,
    ),
    Endpoint(
        name="ESIO Search Index",
        url="http://csg.drdlr.gov.za/esio/searchindex.htm",
        description="ESIO search interface for diagrams",
        used_in_code=False,
    ),
    Endpoint(
        name="Data Page",
        url="http://csg.drdlr.gov.za/data.htm",
        description="CSG data page",
        used_in_code=False,
    ),
    Endpoint(
        name="Diagram Documentation",
        url="http://csg.drdlr.gov.za/diagram.htm",
        description="Documentation about diagrams",
        used_in_code=False,
    ),
    Endpoint(
        name="Spatial Data",
        url="http://csg.drdlr.gov.za/spatial.htm",
        description="Spatial data information",
        used_in_code=False,
    ),
]


def test_endpoint(endpoint: Endpoint, timeout: float = 10.0) -> EndpointResult:
    """Test if an endpoint is available.

    Args:
        endpoint: The endpoint to test.
        timeout: Request timeout in seconds.

    Returns:
        EndpointResult with the test results.
    """
    url = endpoint.url
    if endpoint.test_params:
        params = "&".join(f"{k}={v}" for k, v in endpoint.test_params.items())
        url = f"{url}?{params}"

    start_time = time.time()

    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            response = client.request(endpoint.method, url)
            elapsed_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                status = EndpointStatus.AVAILABLE
            elif response.status_code >= 400:
                status = EndpointStatus.UNAVAILABLE
            else:
                status = EndpointStatus.UNKNOWN

            return EndpointResult(
                endpoint=endpoint,
                status=status,
                status_code=response.status_code,
                response_time_ms=elapsed_ms,
            )

    except httpx.TimeoutException:
        return EndpointResult(
            endpoint=endpoint,
            status=EndpointStatus.TIMEOUT,
            error_message="Request timed out",
            response_time_ms=(time.time() - start_time) * 1000,
        )
    except httpx.ConnectError as e:
        return EndpointResult(
            endpoint=endpoint,
            status=EndpointStatus.UNAVAILABLE,
            error_message=f"Connection error: {e}",
        )
    except Exception as e:
        return EndpointResult(
            endpoint=endpoint,
            status=EndpointStatus.ERROR,
            error_message=str(e),
        )


def get_all_endpoints() -> list[Endpoint]:
    """Get all known endpoints (used and unused)."""
    return ENDPOINTS_IN_CODE + KNOWN_UNUSED_ENDPOINTS


def check_all_endpoints(verbose: bool = True) -> EndpointMapping:
    """Check all endpoints and return categorized results.

    Args:
        verbose: If True, print progress to stdout.

    Returns:
        EndpointMapping with categorized results.
    """
    mapping = EndpointMapping()
    all_endpoints = get_all_endpoints()

    if verbose:
        print("=" * 70)
        print("SG Diagram Downloader - Endpoint Status Check")
        print("=" * 70)
        print()

    for endpoint in all_endpoints:
        if verbose:
            print(f"Testing: {endpoint.name}...")
            print(f"  URL: {endpoint.url}")

        result = test_endpoint(endpoint)

        if verbose:
            status_icon = {
                EndpointStatus.AVAILABLE: "[OK]",
                EndpointStatus.UNAVAILABLE: "[FAIL]",
                EndpointStatus.TIMEOUT: "[TIMEOUT]",
                EndpointStatus.ERROR: "[ERROR]",
                EndpointStatus.UNKNOWN: "[???]",
            }.get(result.status, "[???]")

            print(f"  Status: {status_icon} {result.status.value}")
            if result.status_code:
                print(f"  HTTP Code: {result.status_code}")
            if result.response_time_ms:
                print(f"  Response Time: {result.response_time_ms:.0f}ms")
            if result.error_message:
                print(f"  Error: {result.error_message}")
            print()

        # Categorize
        is_available = result.status == EndpointStatus.AVAILABLE
        is_used = endpoint.used_in_code

        if is_used and is_available:
            result.category = EndpointCategory.USED_AND_AVAILABLE
            mapping.used_and_available.append(result)
        elif is_used and not is_available:
            result.category = EndpointCategory.USED_BUT_UNAVAILABLE
            mapping.used_but_unavailable.append(result)
        elif not is_used and is_available:
            result.category = EndpointCategory.NOT_USED_BUT_AVAILABLE
            mapping.not_used_but_available.append(result)
        else:
            result.category = EndpointCategory.NOT_USED_AND_UNAVAILABLE
            mapping.not_used_and_unavailable.append(result)

        mapping.all_results.append(result)

    return mapping


def print_summary(mapping: EndpointMapping) -> None:
    """Print a summary of the endpoint check results."""
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()

    # Used and available (good)
    print("USED AND AVAILABLE (Working correctly):")
    print("-" * 40)
    if mapping.used_and_available:
        for r in mapping.used_and_available:
            print(f"  [OK] {r.endpoint.name}")
            print(f"       {r.endpoint.url}")
            if r.endpoint.source_file:
                loc = f"{r.endpoint.source_file}"
                if r.endpoint.source_line:
                    loc += f":{r.endpoint.source_line}"
                print(f"       Source: {loc}")
    else:
        print("  (none)")
    print()

    # Used but unavailable (critical issue!)
    print("USED BUT UNAVAILABLE (BROKEN - needs attention!):")
    print("-" * 40)
    if mapping.used_but_unavailable:
        for r in mapping.used_but_unavailable:
            print(f"  [BROKEN] {r.endpoint.name}")
            print(f"           {r.endpoint.url}")
            if r.endpoint.source_file:
                loc = f"{r.endpoint.source_file}"
                if r.endpoint.source_line:
                    loc += f":{r.endpoint.source_line}"
                print(f"           Source: {loc}")
            if r.error_message:
                print(f"           Error: {r.error_message}")
    else:
        print("  (none - all used endpoints are working)")
    print()

    # Not used but available (potential alternatives)
    print("NOT USED BUT AVAILABLE (Potential alternatives):")
    print("-" * 40)
    if mapping.not_used_but_available:
        for r in mapping.not_used_but_available:
            print(f"  [AVAILABLE] {r.endpoint.name}")
            print(f"              {r.endpoint.url}")
    else:
        print("  (none)")
    print()

    # Not used and unavailable
    print("NOT USED AND UNAVAILABLE:")
    print("-" * 40)
    if mapping.not_used_and_unavailable:
        for r in mapping.not_used_and_unavailable:
            print(f"  [N/A] {r.endpoint.name}")
            print(f"        {r.endpoint.url}")
    else:
        print("  (none)")
    print()

    # Overall status
    print("=" * 70)
    total = len(mapping.all_results)
    available = len(mapping.used_and_available) + len(mapping.not_used_but_available)
    broken = len(mapping.used_but_unavailable)

    print(f"Total endpoints checked: {total}")
    print(f"Available: {available}")
    print(f"Unavailable: {total - available}")
    print()

    if broken > 0:
        print("WARNING: Some endpoints used by the plugin are not available!")
        print("         The plugin may not function correctly.")
    else:
        print("All endpoints used by the plugin are available.")

    print("=" * 70)


def get_endpoint_mapping(verbose: bool = False) -> EndpointMapping:
    """Get a complete mapping of all endpoints with their availability status.

    This is the main utility function for programmatic use.

    Args:
        verbose: If True, print progress to stdout.

    Returns:
        EndpointMapping object containing:
        - used_and_available: Endpoints used in code that are working
        - used_but_unavailable: Endpoints used in code that are broken (critical!)
        - not_used_but_available: Endpoints not used but could be alternatives
        - not_used_and_unavailable: Endpoints that are neither used nor available

    Example:
        >>> from scripts.check_endpoints import get_endpoint_mapping
        >>> mapping = get_endpoint_mapping()
        >>> print(f"Working endpoints: {len(mapping.used_and_available)}")
        >>> print(f"Broken endpoints: {len(mapping.used_but_unavailable)}")
        >>> # Get as dictionary for JSON serialization
        >>> data = mapping.to_dict()
    """
    return check_all_endpoints(verbose=verbose)


def get_used_endpoints() -> list[Endpoint]:
    """Get list of endpoints that are actively used in the codebase."""
    return ENDPOINTS_IN_CODE.copy()


def get_unused_endpoints() -> list[Endpoint]:
    """Get list of known endpoints that are NOT used in the codebase."""
    return KNOWN_UNUSED_ENDPOINTS.copy()


def main():
    """Main entry point."""
    print()
    mapping = check_all_endpoints(verbose=True)
    print_summary(mapping)

    # Return exit code based on results
    if mapping.used_but_unavailable:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
