#!/usr/bin/env python3
"""
License Audit Script for Unknown Licenses
Identifies and reports license information for packages with unknown licenses
"""

import subprocess
import json
import sys

# Packages reported as having unknown licenses
UNKNOWN_LICENSE_PACKAGES = [
    "opentelemetry-api",
    "opentelemetry-sdk", 
    "opentelemetry-instrumentation",
    "opentelemetry-exporter-otlp-proto-grpc",
    "opentelemetry-proto",
    "opentelemetry-semantic-conventions",
    "opentelemetry-instrumentation-dbapi",
    "opentelemetry-instrumentation-fastapi",
    "opentelemetry-instrumentation-psycopg2",
    "opentelemetry-instrumentation-requests",
    "opentelemetry-instrumentation-sqlalchemy",
    "opentelemetry-instrumentation-asgi",
    "opentelemetry-util-http",
    "opentelemetry-exporter-otlp-proto-common",
    "pillow",
    "urllib3",
    "scikit-learn",
    "anyio",
    "click",
    "joblib",
    "threadpoolctl",
    "pytest-asyncio",
    "pytest-xdist",
    "pytest-mock",
    "execnet",
    "mypy-extensions",
    "wcwidth",
]

def check_package_license(package_name):
    """Check license for a specific package using pip show."""
    try:
        result = subprocess.run(
            f"pip show {package_name}",
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            for line in lines:
                if line.startswith('License:'):
                    return line.split(':', 1)[1].strip()
        return "NOT_FOUND"
    except Exception as e:
        return f"ERROR: {e}"

def analyze_licenses():
    """Analyze all unknown license packages."""
    print("=" * 70)
    print("LICENSE AUDIT REPORT - Unknown License Analysis")
    print("=" * 70)
    print()
    
    results = {
        "safe": [],
        "needs_review": [],
        "problematic": [],
        "not_found": []
    }
    
    for package in sorted(UNKNOWN_LICENSE_PACKAGES):
        license_info = check_package_license(package)
        
        # Categorize based on license
        if license_info == "NOT_FOUND":
            results["not_found"].append(package)
        elif any(lic in license_info.upper() for lic in ["MIT", "BSD", "APACHE"]):
            results["safe"].append(f"{package}: {license_info}")
        elif any(lic in license_info.upper() for lic in ["GPL", "AGPL", "COPYLEFT"]):
            results["problematic"].append(f"{package}: {license_info}")
        else:
            results["needs_review"].append(f"{package}: {license_info}")
    
    # Print results
    print("✅ SAFE LICENSES (MIT/BSD/Apache - OK for commercial use):")
    for item in results["safe"]:
        print(f"  • {item}")
    print()
    
    print("⚠️ NEEDS REVIEW:")
    for item in results["needs_review"]:
        print(f"  • {item}")
    print()
    
    print("🔴 PROBLEMATIC LICENSES (GPL/AGPL - Legal review required):")
    for item in results["problematic"]:
        print(f"  • {item}")
    print()
    
    print("❓ NOT FOUND (Package not installed):")
    for item in results["not_found"]:
        print(f"  • {item}")
    print()
    
    # Summary
    total = len(UNKNOWN_LICENSE_PACKAGES)
    safe_count = len(results["safe"])
    problematic_count = len(results["problematic"])
    
    print("=" * 70)
    print(f"SUMMARY: {safe_count}/{total} safe, {problematic_count}/{total} problematic")
    
    if problematic_count > 0:
        print("⚠️ ACTION REQUIRED: Review GPL/AGPL packages with legal team")
        return 1
    else:
        print("✅ No GPL/AGPL licenses found - OK for commercial use")
        return 0

if __name__ == "__main__":
    sys.exit(analyze_licenses())