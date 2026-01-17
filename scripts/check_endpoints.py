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
"""

import sys
import time
from dataclasses import dataclass
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


@dataclass
class Endpoint:
    """Represents an API endpoint."""

    name: str
    url: str
    method: str = "GET"
    description: str = ""
    used_in_code: bool = True
    test_params: Optional[dict] = None


@dataclass
class EndpointResult:
    """Result of testing an endpoint."""

    endpoint: Endpoint
    status: EndpointStatus
    status_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None


# Define all endpoints used by the SG Diagram Downloader
ENDPOINTS_IN_CODE = [
    Endpoint(
        name="SG Base URL",
        url="http://csg.drdlr.gov.za/",
        description="Main Surveyor General website base URL",
        used_in_code=True,
    ),
    Endpoint(
        name="SG List Documents",
        url="http://csg.drdlr.gov.za/esio/listdocument.jsp",
        description="Lists available SG diagram documents for a parcel",
        used_in_code=True,
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
    ),
    Endpoint(
        name="SG ESIO Base",
        url="http://csg.drdlr.gov.za/esio/",
        description="ESIO service base path",
        used_in_code=True,
    ),
    Endpoint(
        name="Alternative IP (Commented)",
        url="http://196.25.56.232/",
        description="Alternative base URL (commented out in code)",
        used_in_code=False,
    ),
]

# Known/documented endpoints that might exist but aren't used
KNOWN_UNUSED_ENDPOINTS = [
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


def check_all_endpoints(verbose: bool = True) -> dict:
    """Check all endpoints and return categorized results.

    Args:
        verbose: If True, print progress to stdout.

    Returns:
        Dictionary with categorized results.
    """
    results = {
        "used_and_available": [],
        "used_but_unavailable": [],
        "unused_but_available": [],
        "unused_and_unavailable": [],
        "all_results": [],
    }

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
        results["all_results"].append(result)

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
            results["used_and_available"].append(result)
        elif is_used and not is_available:
            results["used_but_unavailable"].append(result)
        elif not is_used and is_available:
            results["unused_but_available"].append(result)
        else:
            results["unused_and_unavailable"].append(result)

    return results


def print_summary(results: dict) -> None:
    """Print a summary of the endpoint check results."""
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()

    # Used and available (good)
    print("USED AND AVAILABLE (Working correctly):")
    print("-" * 40)
    if results["used_and_available"]:
        for r in results["used_and_available"]:
            print(f"  [OK] {r.endpoint.name}")
            print(f"       {r.endpoint.url}")
    else:
        print("  (none)")
    print()

    # Used but unavailable (critical issue!)
    print("USED BUT UNAVAILABLE (BROKEN - needs attention!):")
    print("-" * 40)
    if results["used_but_unavailable"]:
        for r in results["used_but_unavailable"]:
            print(f"  [BROKEN] {r.endpoint.name}")
            print(f"           {r.endpoint.url}")
            if r.error_message:
                print(f"           Error: {r.error_message}")
    else:
        print("  (none - all used endpoints are working)")
    print()

    # Unused but available (potential alternatives)
    print("UNUSED BUT AVAILABLE (Potential alternatives):")
    print("-" * 40)
    if results["unused_but_available"]:
        for r in results["unused_but_available"]:
            print(f"  [AVAILABLE] {r.endpoint.name}")
            print(f"              {r.endpoint.url}")
    else:
        print("  (none)")
    print()

    # Unused and unavailable
    print("UNUSED AND UNAVAILABLE:")
    print("-" * 40)
    if results["unused_and_unavailable"]:
        for r in results["unused_and_unavailable"]:
            print(f"  [N/A] {r.endpoint.name}")
            print(f"        {r.endpoint.url}")
    else:
        print("  (none)")
    print()

    # Overall status
    print("=" * 70)
    total = len(results["all_results"])
    available = len(results["used_and_available"]) + len(results["unused_but_available"])
    broken = len(results["used_but_unavailable"])

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


def main():
    """Main entry point."""
    print()
    results = check_all_endpoints(verbose=True)
    print_summary(results)

    # Return exit code based on results
    if results["used_but_unavailable"]:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
