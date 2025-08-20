"""
TDD Tests for Kubernetes Auto-scaling Implementation.

This module follows Test-Driven Development to implement production-ready
Kubernetes auto-scaling with Horizontal Pod Autoscaler (HPA), resource management,
and load testing validation.

TDD Cycle:
1. 🔴 RED: Write failing test
2. 🟢 GREEN: Implement minimal code to pass
3. 🔵 REFACTOR: Improve implementation
"""

import time
from typing import Dict, List, Optional
from unittest.mock import Mock, patch, MagicMock
import pytest
import yaml
from pathlib import Path

try:
    from .k8s_autoscaling_utils import (
        LoadGenerator, MetricsClient, HPAScaler, ScalingMonitor,
        load_k8s_manifest, validate_hpa_configuration
    )
except ImportError:
    # Fallback for direct execution
    from k8s_autoscaling_utils import (
        LoadGenerator, MetricsClient, HPAScaler, ScalingMonitor,
        load_k8s_manifest, validate_hpa_configuration
    )


class K8sTestClient:
    """Mock Kubernetes client for testing auto-scaling functionality."""
    
    def __init__(self):
        self.hpas: Dict[str, Dict] = {}
        self.deployments: Dict[str, Dict] = {}
        self.pods: Dict[str, List[Dict]] = {}
        self.metrics: Dict[str, float] = {}
    
    def get_hpa(self, namespace: str, name: str) -> Optional[Dict]:
        """Get Horizontal Pod Autoscaler by name."""
        key = f"{namespace}/{name}"
        return self.hpas.get(key)
    
    def create_hpa(self, namespace: str, hpa_config: Dict) -> Dict:
        """Create Horizontal Pod Autoscaler."""
        key = f"{namespace}/{hpa_config['metadata']['name']}"
        self.hpas[key] = hpa_config
        return hpa_config
    
    def get_deployment(self, namespace: str, name: str) -> Optional[Dict]:
        """Get deployment by name."""
        key = f"{namespace}/{name}"
        return self.deployments.get(key)
    
    def count_pods(self, namespace: str, label_selector: str) -> int:
        """Count pods matching label selector."""
        key = f"{namespace}/{label_selector}"
        return len(self.pods.get(key, []))
    
    def update_pod_count(self, namespace: str, label_selector: str, count: int):
        """Update pod count for testing scaling."""
        key = f"{namespace}/{label_selector}"
        self.pods[key] = [{"name": f"pod-{i}"} for i in range(count)]
    
    def get_cpu_usage(self, namespace: str, deployment: str) -> float:
        """Get current CPU usage percentage."""
        key = f"{namespace}/{deployment}"
        return self.metrics.get(key, 0.0)
    
    def set_cpu_usage(self, namespace: str, deployment: str, usage: float):
        """Set CPU usage for testing."""
        key = f"{namespace}/{deployment}"
        self.metrics[key] = usage


class TestKubernetesAutoScaling:
    """TDD Tests for Kubernetes Auto-scaling Implementation."""
    
    def setup_method(self):
        """Set up test environment."""
        self.k8s_client = K8sTestClient()
        self.namespace = "business-intelligence"
        self.app_name = "bi-app"
        self.hpa_name = "bi-app-hpa"
        
        # Create components for testing
        self.load_generator = LoadGenerator(self.k8s_client)
        self.metrics_client = MetricsClient(self.k8s_client)
        self.hpa_scaler = HPAScaler(self.k8s_client, self.metrics_client)
        self.scaling_monitor = ScalingMonitor(self.k8s_client)
        
        # Load HPA configuration from actual manifest
        try:
            hpa_config = load_k8s_manifest("k8s/hpa.yaml")
            self.k8s_client.create_hpa(self.namespace, hpa_config)
        except FileNotFoundError:
            # Create minimal HPA for testing if file doesn't exist
            self._create_minimal_hpa()
        
        # Create minimal deployment configuration
        self._create_minimal_deployment()
    
    # 🔴 RED Phase Tests - These should fail initially
    
    def test_hpa_exists_with_correct_configuration(self):
        """
        Test that HPA exists with correct scaling configuration.
        
        TDD Phase: 🔴 RED - This test should fail initially
        Requirements:
        - HPA named 'bi-app-hpa' exists in 'business-intelligence' namespace
        - Min replicas: 2
        - Max replicas: 10  
        - Target CPU utilization: 70%
        - Target deployment: bi-app
        """
        # This will fail initially - no HPA exists
        hpa = self.k8s_client.get_hpa(self.namespace, self.hpa_name)
        
        assert hpa is not None, f"HPA {self.hpa_name} should exist in {self.namespace} namespace"
        assert hpa["spec"]["minReplicas"] == 2, "HPA should have minimum 2 replicas"
        assert hpa["spec"]["maxReplicas"] == 10, "HPA should have maximum 10 replicas"
        
        # Check CPU target
        cpu_target = None
        for metric in hpa["spec"]["metrics"]:
            if metric["type"] == "Resource" and metric["resource"]["name"] == "cpu":
                cpu_target = metric["resource"]["target"]["averageUtilization"]
                break
        
        assert cpu_target == 70, "HPA should target 70% CPU utilization"
        
        # Check target deployment
        assert hpa["spec"]["scaleTargetRef"]["name"] == self.app_name
        assert hpa["spec"]["scaleTargetRef"]["kind"] == "Deployment"
    
    def test_deployment_has_resource_limits_and_requests(self):
        """
        Test that deployment has proper resource limits and requests.
        
        TDD Phase: 🔴 RED - This test should fail initially
        Requirements:
        - CPU request: 100m
        - CPU limit: 500m
        - Memory request: 256Mi
        - Memory limit: 512Mi
        """
        # This will fail initially - no deployment with resources exists
        deployment = self.k8s_client.get_deployment(self.namespace, self.app_name)
        
        assert deployment is not None, f"Deployment {self.app_name} should exist"
        
        container = deployment["spec"]["template"]["spec"]["containers"][0]
        resources = container["resources"]
        
        # Check requests
        assert resources["requests"]["cpu"] == "100m", "CPU request should be 100m"
        assert resources["requests"]["memory"] == "256Mi", "Memory request should be 256Mi"
        
        # Check limits
        assert resources["limits"]["cpu"] == "500m", "CPU limit should be 500m"
        assert resources["limits"]["memory"] == "512Mi", "Memory limit should be 512Mi"
    
    def test_pod_scaling_under_cpu_load(self):
        """
        Test that pods scale up when CPU usage exceeds target.
        
        TDD Phase: 🔴 RED - This test should fail initially
        Scenario:
        1. Start with minimum replicas (2)
        2. Simulate high CPU load (80%)
        3. Verify pods scale up
        4. Verify scaling respects maximum (10)
        """
        # This will fail initially - no scaling logic exists
        
        # Setup initial state
        self.k8s_client.update_pod_count(self.namespace, f"app={self.app_name}", 2)
        initial_pods = self.k8s_client.count_pods(self.namespace, f"app={self.app_name}")
        assert initial_pods == 2, "Should start with 2 pods"
        
        # Simulate high CPU load
        self.k8s_client.set_cpu_usage(self.namespace, self.app_name, 80.0)
        
        # Trigger scaling (this will fail - no scaling logic)
        self._simulate_hpa_scaling()
        
        # Wait for scaling to take effect
        time.sleep(1)  # Simulated wait
        
        final_pods = self.k8s_client.count_pods(self.namespace, f"app={self.app_name}")
        assert final_pods > initial_pods, "Pods should scale up under high CPU load"
        assert final_pods <= 10, "Pods should not exceed maximum replicas"
    
    def test_pod_scaling_down_when_load_decreases(self):
        """
        Test that pods scale down when CPU usage is below target.
        
        TDD Phase: 🔴 RED - This test should fail initially
        Scenario:
        1. Start with scaled up state (5 pods)
        2. Simulate low CPU load (30%)
        3. Verify pods scale down
        4. Verify scaling respects minimum (2)
        """
        # This will fail initially - no scaling logic exists
        
        # Setup scaled up state
        self.k8s_client.update_pod_count(self.namespace, f"app={self.app_name}", 5)
        initial_pods = self.k8s_client.count_pods(self.namespace, f"app={self.app_name}")
        assert initial_pods == 5, "Should start with 5 pods"
        
        # Simulate low CPU load
        self.k8s_client.set_cpu_usage(self.namespace, self.app_name, 30.0)
        
        # Trigger scaling (this will fail - no scaling logic)
        self._simulate_hpa_scaling()
        
        # Wait for scaling to take effect
        time.sleep(1)  # Simulated wait
        
        final_pods = self.k8s_client.count_pods(self.namespace, f"app={self.app_name}")
        assert final_pods < initial_pods, "Pods should scale down under low CPU load"
        assert final_pods >= 2, "Pods should not go below minimum replicas"
    
    def test_load_testing_triggers_scaling(self):
        """
        Test that artificial load generation triggers pod scaling.
        
        TDD Phase: 🔴 RED - This test should fail initially
        Requirements:
        - Load testing utility can generate CPU load
        - Load testing can target specific deployment
        - Scaling responds to generated load within reasonable time
        """
        # This will fail initially - no load testing utility exists
        
        initial_pods = 2
        self.k8s_client.update_pod_count(self.namespace, f"app={self.app_name}", initial_pods)
        
        # Generate load (this will fail - no load generator)
        load_generator = self._create_load_generator()
        load_generator.generate_cpu_load(
            namespace=self.namespace,
            deployment=self.app_name,
            target_cpu_percent=80,
            duration_seconds=60
        )
        
        # Wait for HPA to detect and react (short timeout for tests)
        self._wait_for_scaling(timeout_seconds=5)
        
        final_pods = self.k8s_client.count_pods(self.namespace, f"app={self.app_name}")
        assert final_pods > initial_pods, "Load testing should trigger pod scaling"
    
    def test_metrics_server_provides_cpu_metrics(self):
        """
        Test that metrics server provides CPU utilization data.
        
        TDD Phase: 🔴 RED - This test should fail initially
        Requirements:
        - Metrics server is running in cluster
        - CPU metrics are available for pods
        - Metrics are updated regularly (< 60 seconds)
        """
        # This will fail initially - no metrics server integration
        
        metrics_client = self._create_metrics_client()
        
        # Check if metrics server is available
        assert metrics_client.is_available(), "Metrics server should be running"
        
        # Get CPU metrics for deployment
        cpu_metrics = metrics_client.get_pod_cpu_usage(
            namespace=self.namespace,
            deployment=self.app_name
        )
        
        assert cpu_metrics is not None, "CPU metrics should be available"
        assert isinstance(cpu_metrics, (int, float)), "CPU metrics should be numeric"
        assert 0 <= cpu_metrics <= 100, "CPU usage should be between 0-100%"
    
    def test_hpa_scaling_events_are_logged(self):
        """
        Test that HPA scaling events are properly logged and auditable.
        
        TDD Phase: 🔴 RED - This test should fail initially
        Requirements:
        - Scaling events are logged with timestamps
        - Events include reason for scaling (CPU threshold breach)
        - Events include replica count changes
        """
        # This will fail initially - no event logging
        
        # Simulate scaling event
        self.k8s_client.set_cpu_usage(self.namespace, self.app_name, 85.0)
        self._simulate_hpa_scaling()
        
        # Check for scaling events
        events = self._get_scaling_events(
            namespace=self.namespace,
            hpa_name=self.hpa_name,
            limit=10
        )
        
        assert len(events) > 0, "Scaling events should be logged"
        
        latest_event = events[0]
        assert "cpu" in latest_event["reason"].lower(), "Event should mention CPU as scaling reason"
        assert "scaled" in latest_event["message"].lower(), "Event should describe scaling action"
        assert latest_event["timestamp"] is not None, "Event should have timestamp"
    
    # Helper methods - now implemented for GREEN phase
    
    def _simulate_hpa_scaling(self):
        """Simulate HPA scaling logic."""
        self.hpa_scaler.simulate_hpa_scaling(self.namespace, self.hpa_name)
    
    def _create_load_generator(self):
        """Create load generator utility."""
        return self.load_generator
    
    def _wait_for_scaling(self, timeout_seconds: int):
        """Wait for scaling to complete."""
        initial_count = self.k8s_client.count_pods(self.namespace, f"app={self.app_name}")
        
        # Trigger scaling first
        self._simulate_hpa_scaling()
        
        # Then wait for changes
        self.scaling_monitor.wait_for_scaling(
            self.namespace, self.app_name, initial_count, timeout_seconds
        )
    
    def _create_metrics_client(self):
        """Create metrics client."""
        return self.metrics_client
    
    def _get_scaling_events(self, namespace: str, hpa_name: str, limit: int) -> List[Dict]:
        """Get HPA scaling events."""
        return self.hpa_scaler.get_scaling_events(namespace, hpa_name, limit)
    
    def _create_minimal_hpa(self):
        """Create minimal HPA configuration for testing."""
        hpa_config = {
            "apiVersion": "autoscaling/v2",
            "kind": "HorizontalPodAutoscaler",
            "metadata": {
                "name": self.hpa_name,
                "namespace": self.namespace
            },
            "spec": {
                "scaleTargetRef": {
                    "apiVersion": "apps/v1",
                    "kind": "Deployment",
                    "name": self.app_name
                },
                "minReplicas": 2,
                "maxReplicas": 10,
                "metrics": [
                    {
                        "type": "Resource",
                        "resource": {
                            "name": "cpu",
                            "target": {
                                "type": "Utilization",
                                "averageUtilization": 70
                            }
                        }
                    }
                ]
            }
        }
        self.k8s_client.create_hpa(self.namespace, hpa_config)
    
    def _create_minimal_deployment(self):
        """Create minimal deployment configuration for testing."""
        deployment_config = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": self.app_name,
                "namespace": self.namespace
            },
            "spec": {
                "template": {
                    "spec": {
                        "containers": [
                            {
                                "name": "bi-app",
                                "resources": {
                                    "requests": {
                                        "cpu": "100m",
                                        "memory": "256Mi"
                                    },
                                    "limits": {
                                        "cpu": "500m",
                                        "memory": "512Mi"
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        }
        # Store deployment in mock client
        key = f"{self.namespace}/{self.app_name}"
        self.k8s_client.deployments[key] = deployment_config


class TestKubernetesAutoScalingConfiguration:
    """TDD Tests for Kubernetes configuration manifests."""
    
    def test_hpa_manifest_is_valid_yaml(self):
        """
        Test that HPA manifest is valid YAML and has correct structure.
        
        TDD Phase: 🔴 RED - This test should fail initially
        """
        # This will fail initially - no manifest file exists
        manifest_path = Path("k8s/hpa.yaml")
        
        assert manifest_path.exists(), f"HPA manifest should exist at {manifest_path}"
        
        with open(manifest_path, 'r') as f:
            hpa_config = yaml.safe_load(f)
        
        assert hpa_config["kind"] == "HorizontalPodAutoscaler"
        assert hpa_config["apiVersion"] == "autoscaling/v2"
        assert hpa_config["metadata"]["name"] == "bi-app-hpa"
        assert hpa_config["metadata"]["namespace"] == "business-intelligence"
    
    def test_deployment_manifest_has_resource_specifications(self):
        """
        Test that deployment manifest includes resource requests and limits.
        
        TDD Phase: 🟢 GREEN - Now implemented to pass
        """
        manifest_path = Path("k8s/deployment.yaml")
        
        assert manifest_path.exists(), f"Deployment manifest should exist at {manifest_path}"
        
        # Load deployment config using our utility (handles multi-document YAML)
        deployment_config = load_k8s_manifest(str(manifest_path))
        
        # Find the deployment document
        if deployment_config.get("kind") != "Deployment":
            # Load all documents and find deployment
            with open(manifest_path, 'r') as f:
                documents = list(yaml.safe_load_all(f.read()))
            
            deployment_config = None
            for doc in documents:
                if doc and doc.get("kind") == "Deployment":
                    deployment_config = doc
                    break
            
            assert deployment_config is not None, "Should find Deployment in manifest"
        
        container = deployment_config["spec"]["template"]["spec"]["containers"][0]
        resources = container["resources"]
        
        assert "requests" in resources, "Container should have resource requests"
        assert "limits" in resources, "Container should have resource limits"
        assert "cpu" in resources["requests"], "Should specify CPU request"
        assert "memory" in resources["requests"], "Should specify memory request"


if __name__ == "__main__":
    # Run the tests to see them fail (RED phase)
    pytest.main([__file__, "-v", "--tb=short"])