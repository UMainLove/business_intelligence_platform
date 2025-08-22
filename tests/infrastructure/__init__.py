"""
Infrastructure TDD Test Suite

This package contains Test-Driven Development (TDD) implementations for production-ready
infrastructure components including:

- Kubernetes Auto-scaling (HPA, resource management)
- Production Infrastructure (PVCs, service mesh, backup/recovery, HA)
- Secrets Management (sealed secrets, rotation, vault integration, RBAC)
- Network Policies (microsegmentation, zero-trust, isolation)

Each module follows the RED-GREEN-REFACTOR TDD cycle:
1. 🔴 RED: Write failing tests that specify requirements
2. 🟢 GREEN: Implement minimal code to make tests pass
3. 🔵 REFACTOR: Improve implementation while keeping tests green

Test Statistics:
- Kubernetes Auto-scaling: 9 tests
- Production Infrastructure: 13 tests
- Secrets Management: 14 tests
- Network Policies: 14 tests
- Total: 50 comprehensive infrastructure tests

Usage:
    # Run all infrastructure tests
    pytest tests/infrastructure/ -v

    # Run specific test module
    pytest tests/infrastructure/test_network_policies_tdd.py -v

    # Run with coverage
    pytest tests/infrastructure/ --cov=tests/infrastructure --cov-report=html
"""

__version__ = "1.0.0"
__author__ = "Business Intelligence Platform Team"

# Test module information
TEST_MODULES = {
    "k8s_autoscaling": {
        "file": "test_k8s_autoscaling_tdd.py",
        "tests": 9,
        "coverage": "Kubernetes HPA, resource limits, scaling behavior",
        "manifests": "k8s/autoscaling/",
    },
    "production_infrastructure": {
        "file": "test_production_infrastructure_tdd.py",
        "tests": 13,
        "coverage": "PVCs, service mesh, backup/recovery, HA, monitoring",
        "manifests": "k8s/production/",
    },
    "secrets_management": {
        "file": "test_secrets_management_tdd.py",
        "tests": 14,
        "coverage": "Sealed secrets, rotation, vault, encryption, RBAC",
        "manifests": "k8s/secrets/",
    },
    "network_policies": {
        "file": "test_network_policies_tdd.py",
        "tests": 14,
        "coverage": "Zero-trust networking, microsegmentation, isolation",
        "manifests": "k8s/network-policies/",
    },
}

TOTAL_TESTS = sum(module["tests"] for module in TEST_MODULES.values())


def get_test_summary():
    """Get summary of infrastructure test modules."""
    return {"total_tests": TOTAL_TESTS, "modules": TEST_MODULES, "version": __version__}
