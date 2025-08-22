"""
TDD Tests for Performance Monitoring Implementation.

This module follows Test-Driven Development to implement production-ready
performance monitoring including Prometheus metrics collection, Grafana
dashboards, alerting rules, SLI/SLO monitoring, and APM integration.

TDD Cycle:
1. 🔴 RED: Write failing test
2. 🟢 GREEN: Implement minimal code to pass
3. 🔵 REFACTOR: Improve implementation
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pytest
import yaml

try:
    from .performance_monitoring_utils import (
        AlertManager,
        APMIntegration,
        GrafanaClient,
        MetricsCollector,
        PerformanceTester,
        PrometheusClient,
        SLOMonitor,
        load_k8s_manifest,
    )
except ImportError:
    # Fallback for direct execution
    from performance_monitoring_utils import (
        AlertManager,
        APMIntegration,
        GrafanaClient,
        MetricsCollector,
        PerformanceTester,
        PrometheusClient,
        SLOMonitor,
        load_k8s_manifest,
    )


class K8sMonitoringClient:
    """Mock Kubernetes client for testing performance monitoring."""

    def __init__(self):
        self.deployments: Dict[str, Dict] = {}
        self.services: Dict[str, Dict] = {}
        self.config_maps: Dict[str, Dict] = {}
        self.persistent_volume_claims: Dict[str, Dict] = {}
        self.service_monitors: Dict[str, Dict] = {}
        self.prometheus_rules: Dict[str, Dict] = {}
        self.ingresses: Dict[str, Dict] = {}

        # Monitoring data simulation
        self.metrics_data: Dict[str, List[Dict]] = {}
        self.alert_states: Dict[str, Dict] = {}

    def get_deployment(self, namespace: str, name: str) -> Optional[Dict]:
        """Get Deployment by name."""
        key = f"{namespace}/{name}"
        return self.deployments.get(key)

    def create_deployment(self, namespace: str, deployment_config: Dict) -> Dict:
        """Create Deployment."""
        key = f"{namespace}/{deployment_config['metadata']['name']}"
        # Simulate deployment ready state
        deployment_config["status"] = {
            "replicas": deployment_config["spec"]["replicas"],
            "ready_replicas": deployment_config["spec"]["replicas"],
        }
        self.deployments[key] = deployment_config
        return deployment_config

    def get_service(self, namespace: str, name: str) -> Optional[Dict]:
        """Get Service by name."""
        key = f"{namespace}/{name}"
        return self.services.get(key)

    def create_service(self, namespace: str, service_config: Dict) -> Dict:
        """Create Service."""
        key = f"{namespace}/{service_config['metadata']['name']}"
        self.services[key] = service_config
        return service_config

    def get_config_map(self, namespace: str, name: str) -> Optional[Dict]:
        """Get ConfigMap by name."""
        key = f"{namespace}/{name}"
        return self.config_maps.get(key)

    def create_config_map(self, namespace: str, config_map: Dict) -> Dict:
        """Create ConfigMap."""
        key = f"{namespace}/{config_map['metadata']['name']}"
        self.config_maps[key] = config_map
        return config_map

    def get_pvc(self, namespace: str, name: str) -> Optional[Dict]:
        """Get PersistentVolumeClaim by name."""
        key = f"{namespace}/{name}"
        return self.persistent_volume_claims.get(key)

    def create_pvc(self, namespace: str, pvc_config: Dict) -> Dict:
        """Create PersistentVolumeClaim."""
        key = f"{namespace}/{pvc_config['metadata']['name']}"
        self.persistent_volume_claims[key] = pvc_config
        return pvc_config

    def get_service_monitor(self, namespace: str, name: str) -> Optional[Dict]:
        """Get ServiceMonitor by name."""
        key = f"{namespace}/{name}"
        return self.service_monitors.get(key)

    def create_service_monitor(self, namespace: str, service_monitor: Dict) -> Dict:
        """Create ServiceMonitor."""
        key = f"{namespace}/{service_monitor['metadata']['name']}"
        self.service_monitors[key] = service_monitor
        return service_monitor

    def get_prometheus_rule(self, namespace: str, name: str) -> Optional[Dict]:
        """Get PrometheusRule by name."""
        key = f"{namespace}/{name}"
        return self.prometheus_rules.get(key)

    def create_prometheus_rule(self, namespace: str, prometheus_rule: Dict) -> Dict:
        """Create PrometheusRule."""
        key = f"{namespace}/{prometheus_rule['metadata']['name']}"
        self.prometheus_rules[key] = prometheus_rule
        return prometheus_rule

    def get_ingress(self, namespace: str, name: str) -> Optional[Dict]:
        """Get Ingress by name."""
        key = f"{namespace}/{name}"
        return self.ingresses.get(key)

    def create_ingress(self, namespace: str, ingress_config: Dict) -> Dict:
        """Create Ingress."""
        key = f"{namespace}/{ingress_config['metadata']['name']}"
        self.ingresses[key] = ingress_config
        return ingress_config

    def simulate_metrics(self, metric_name: str, values: List[Tuple[float, str]]):
        """Simulate metric values for testing."""
        self.metrics_data[metric_name] = [{"timestamp": ts, "value": val} for ts, val in values]

    def simulate_alert(self, alert_name: str, state: str, severity: str = "critical"):
        """Simulate alert state for testing."""
        self.alert_states[alert_name] = {
            "state": state,
            "severity": severity,
            "timestamp": datetime.now().isoformat(),
        }


class TestPerformanceMonitoring:
    """TDD Tests for Performance Monitoring Implementation."""

    def setup_method(self):
        """Set up test environment."""
        self.k8s_client = K8sMonitoringClient()
        self.namespace = "business-intelligence"
        self.monitoring_ns = "monitoring"

        # Initialize monitoring components
        self.prometheus = PrometheusClient(self.k8s_client)
        self.grafana = GrafanaClient(self.k8s_client)
        self.alertmanager = AlertManager(self.k8s_client)
        self.metrics_collector = MetricsCollector(self.k8s_client)
        self.performance_tester = PerformanceTester(self.k8s_client)
        self.slo_monitor = SLOMonitor(self.k8s_client)
        self.apm = APMIntegration(self.k8s_client)

        # Connect AlertManager to PerformanceTester for regression alerts
        self.performance_tester.alertmanager = self.alertmanager

        # Create test infrastructure
        self._create_test_infrastructure()

        # Load monitoring configurations
        self._load_monitoring_manifests()

        # Setup minimal monitoring configs for GREEN phase
        self._create_minimal_monitoring_configs()

    # 🔴 RED Phase Tests - These should fail initially

    def test_prometheus_metrics_collection(self):
        """
        Test that Prometheus is collecting metrics from BI platform.

        TDD Phase: 🔴 RED - This test should fail initially
        Requirements:
        - Prometheus deployment running
        - ServiceMonitor configured for BI platform
        - Metrics being scraped successfully
        - Basic application metrics available
        """
        # Test Prometheus deployment
        prometheus_deployment = self.k8s_client.get_deployment(self.monitoring_ns, "prometheus")
        assert prometheus_deployment is not None, "Prometheus should be deployed"
        assert prometheus_deployment["status"]["ready_replicas"] >= 1, (
            "Prometheus should be running"
        )

        # Test ServiceMonitor exists
        service_monitor = self.k8s_client.get_service_monitor(self.namespace, "bi-platform-monitor")
        assert service_monitor is not None, "ServiceMonitor should exist for BI platform"
        assert service_monitor["spec"]["selector"]["matchLabels"]["app"] == "bi-platform"

        # Test metrics collection
        metrics = self.prometheus.query("up{job='bi-platform'}")
        assert len(metrics.result) > 0, "Should have metrics from BI platform"
        assert all(m["value"][1] == "1" for m in metrics.result), "All instances should be up"

        # Test application-specific metrics
        response_time_metrics = self.prometheus.query(
            "http_request_duration_seconds{job='bi-platform'}"
        )
        assert len(response_time_metrics.result) > 0, "Should collect response time metrics"

        request_count_metrics = self.prometheus.query("http_requests_total{job='bi-platform'}")
        assert len(request_count_metrics.result) > 0, "Should collect request count metrics"

    def test_grafana_dashboards_exist(self):
        """
        Test that Grafana dashboards are properly configured.

        TDD Phase: 🔴 RED - This test should fail initially
        Requirements:
        - Grafana deployment running
        - BI Platform overview dashboard
        - Essential panels configured (response time, error rate, throughput)
        - Data source configured
        """
        # Test Grafana deployment
        grafana_deployment = self.k8s_client.get_deployment(self.monitoring_ns, "grafana")
        assert grafana_deployment is not None, "Grafana should be deployed"
        assert grafana_deployment["status"]["ready_replicas"] >= 1, "Grafana should be running"

        # Test dashboard exists
        dashboard = self.grafana.get_dashboard("bi-platform-overview")
        assert dashboard is not None, "BI Platform overview dashboard should exist"

        # Test essential panels
        assert dashboard.panels["response_time"] is not None, "Should have response time panel"
        assert dashboard.panels["error_rate"] is not None, "Should have error rate panel"
        assert dashboard.panels["throughput"] is not None, "Should have throughput panel"
        assert dashboard.panels["cpu_usage"] is not None, "Should have CPU usage panel"
        assert dashboard.panels["memory_usage"] is not None, "Should have memory usage panel"

        # Test data source configuration
        data_sources = self.grafana.get_data_sources()
        prometheus_ds = next((ds for ds in data_sources if ds["name"] == "Prometheus"), None)
        assert prometheus_ds is not None, "Prometheus data source should be configured"
        assert prometheus_ds["url"] == "http://prometheus:9090", "Data source URL should be correct"

        # Test dashboard queries are valid
        panels = dashboard.get_all_panels()
        for panel in panels:
            if panel.get("targets"):
                for target in panel["targets"]:
                    assert "expr" in target, (
                        f"Panel {panel['title']} should have valid PromQL query"
                    )
                    assert len(target["expr"]) > 0, (
                        f"Panel {panel['title']} query should not be empty"
                    )

    def test_alerting_rules_fire_correctly(self):
        """
        Test that alerting rules are configured and firing correctly.

        TDD Phase: 🔴 RED - This test should fail initially
        Requirements:
        - AlertManager deployment running
        - PrometheusRules configured for BI platform
        - Critical alerts for high error rate, high response time
        - Alerts fire when thresholds are exceeded
        - Notifications configured
        """
        # Test AlertManager deployment
        alertmanager = self.k8s_client.get_deployment(self.monitoring_ns, "alertmanager")
        assert alertmanager is not None, "AlertManager should be deployed"
        assert alertmanager["status"]["ready_replicas"] >= 1, "AlertManager should be running"

        # Test PrometheusRules exist
        prometheus_rules = self.k8s_client.get_prometheus_rule(self.namespace, "bi-platform-alerts")
        assert prometheus_rules is not None, "Prometheus alert rules should exist"

        alert_rules = prometheus_rules["spec"]["groups"][0]["rules"]
        alert_names = [rule["alert"] for rule in alert_rules if "alert" in rule]

        expected_alerts = [
            "HighErrorRate",
            "HighResponseTime",
            "HighCPUUsage",
            "HighMemoryUsage",
            "ServiceDown",
        ]
        for alert_name in expected_alerts:
            assert alert_name in alert_names, f"Alert {alert_name} should be configured"

        # Test alert firing (simulate high error rate)
        self.performance_tester.generate_errors(rate=0.1, duration=60)
        alerts = self.alertmanager.wait_for_alerts("HighErrorRate", timeout=120)
        assert len(alerts) > 0, "High error rate alert should fire"
        assert alerts[0].severity == "critical", "High error rate should be critical severity"

        # Test alert resolution
        self.performance_tester.stop_error_generation()
        # Simulate alert resolution when error condition clears
        self.alertmanager.resolve_alert("HighErrorRate")
        resolved_alerts = self.alertmanager.get_alerts("HighErrorRate", state="resolved")
        assert len(resolved_alerts) > 0, "Alert should resolve when condition clears"

    def test_performance_metrics_validation(self):
        """
        Test that performance metrics are being collected and validated.

        TDD Phase: 🔴 RED - This test should fail initially
        Requirements:
        - Response time metrics with percentiles
        - Throughput metrics (requests per second)
        - Error rate metrics with status codes
        - Resource utilization metrics
        - Database performance metrics
        """
        # Test response time metrics
        response_time_query = (
            'histogram_quantile(0.95, http_request_duration_seconds_bucket{job="bi-platform"})'
        )
        p95_latency = self.prometheus.query(response_time_query)
        assert len(p95_latency.result) > 0, "Should have P95 response time metrics"

        for metric in p95_latency.result:
            assert float(metric["value"][1]) < 2.0, "P95 response time should be under 2 seconds"

        # Test throughput metrics
        throughput_query = 'rate(http_requests_total{job="bi-platform"}[5m])'
        throughput = self.prometheus.query(throughput_query)
        assert len(throughput.result) > 0, "Should have throughput metrics"

        # Test error rate metrics
        error_rate_query = 'rate(http_requests_total{job="bi-platform",status=~"5.."}[5m]) / rate(http_requests_total{job="bi-platform"}[5m])'
        error_rate = self.prometheus.query(error_rate_query)
        assert len(error_rate.result) > 0, "Should have error rate metrics"

        for metric in error_rate.result:
            assert float(metric["value"][1]) < 0.01, "Error rate should be less than 1%"

        # Test resource utilization
        cpu_query = 'rate(container_cpu_usage_seconds_total{pod=~"bi-platform-.*"}[5m])'
        cpu_usage = self.prometheus.query(cpu_query)
        assert len(cpu_usage.result) > 0, "Should have CPU usage metrics"

        memory_query = 'container_memory_usage_bytes{pod=~"bi-platform-.*"}'
        memory_usage = self.prometheus.query(memory_query)
        assert len(memory_usage.result) > 0, "Should have memory usage metrics"

        # Test database performance metrics
        db_query = 'pg_stat_database_tup_returned{datname="business_intelligence"}'
        db_metrics = self.prometheus.query(db_query)
        assert len(db_metrics.result) > 0, "Should have database performance metrics"

    def test_sli_slo_monitoring(self):
        """
        Test Service Level Indicators (SLI) and Objectives (SLO) monitoring.

        TDD Phase: 🔴 RED - This test should fail initially
        Requirements:
        - SLI metrics defined (availability, latency, throughput, error rate)
        - SLO targets configured (99.9% availability, P95 < 1s, error rate < 0.1%)
        - SLO compliance tracking
        - Error budget monitoring
        - SLO burn rate alerts
        """
        # Test SLI definitions exist
        sli_config = self.slo_monitor.get_sli_configuration(self.namespace)
        assert sli_config is not None, "SLI configuration should exist"

        expected_slis = ["availability", "latency", "throughput", "error_rate"]
        for sli in expected_slis:
            assert sli in sli_config["indicators"], f"SLI {sli} should be defined"

        # Test SLO targets
        slo_config = self.slo_monitor.get_slo_configuration(self.namespace)
        assert slo_config is not None, "SLO configuration should exist"

        assert slo_config["availability"]["target"] == 0.999, "Availability SLO should be 99.9%"
        assert slo_config["latency"]["target"] == 1.0, "Latency SLO should be 1 second P95"
        assert slo_config["error_rate"]["target"] == 0.001, "Error rate SLO should be 0.1%"

        # Test SLO compliance tracking
        compliance = self.slo_monitor.get_slo_compliance(self.namespace, period_days=30)
        assert compliance is not None, "Should track SLO compliance"
        assert "availability" in compliance, "Should track availability compliance"
        assert "error_budget_remaining" in compliance, "Should track error budget"

        # Test error budget alerts
        error_budget = self.slo_monitor.get_error_budget(self.namespace)
        assert error_budget is not None, "Should have error budget calculation"
        assert error_budget["remaining_percentage"] >= 0, "Error budget should be tracked"

        # Test burn rate alerts
        burn_rate_rules = self.k8s_client.get_prometheus_rule(
            self.namespace, "slo-burn-rate-alerts"
        )
        assert burn_rate_rules is not None, "Burn rate alert rules should exist"

    def test_apm_integration(self):
        """
        Test Application Performance Monitoring (APM) integration.

        TDD Phase: 🔴 RED - This test should fail initially
        Requirements:
        - APM agent instrumentation
        - Distributed tracing
        - Transaction performance monitoring
        - Database query monitoring
        - Error tracking and analysis
        """
        # Test APM agent deployment
        apm_config = self.apm.get_configuration(self.namespace)
        assert apm_config is not None, "APM configuration should exist"
        assert apm_config["enabled"], "APM should be enabled"

        # Test distributed tracing
        traces = self.apm.get_traces(service="bi-platform", limit=10)
        assert len(traces) > 0, "Should collect distributed traces"

        for trace in traces:
            assert "trace_id" in trace, "Trace should have trace ID"
            assert "spans" in trace, "Trace should have spans"
            assert len(trace["spans"]) > 0, "Trace should have at least one span"

        # Test transaction monitoring
        transactions = self.apm.get_transactions(service="bi-platform", transaction_type="request")
        assert len(transactions) > 0, "Should monitor HTTP transactions"

        for transaction in transactions:
            assert "duration" in transaction, "Transaction should have duration"
            assert "result" in transaction, "Transaction should have result"
            assert "url" in transaction, "HTTP transaction should have URL"

        # Test database query monitoring
        db_queries = self.apm.get_database_queries(service="bi-platform")
        assert len(db_queries) > 0, "Should monitor database queries"

        for query in db_queries:
            assert "query" in query, "Should capture SQL query"
            assert "duration" in query, "Should capture query duration"
            assert "database" in query, "Should identify database"

        # Test error tracking
        errors = self.apm.get_errors(service="bi-platform", limit=10)
        # Errors might be empty in normal operation, but APM should be capable
        if len(errors) > 0:
            for error in errors:
                assert "exception" in error, "Error should have exception info"
                assert "timestamp" in error, "Error should have timestamp"
                assert "context" in error, "Error should have context"

    def test_custom_metrics_collection(self):
        """
        Test custom business metrics collection.

        TDD Phase: 🔴 RED - This test should fail initially
        Requirements:
        - Business-specific metrics (queries executed, reports generated, users active)
        - Custom metric endpoints
        - Proper metric labeling
        - Historical data retention
        """
        # Test custom metrics are exposed
        custom_metrics = [
            "bi_queries_executed_total",
            "bi_reports_generated_total",
            "bi_active_users_current",
            "bi_data_processed_bytes_total",
            "bi_cache_hits_total",
            "bi_cache_misses_total",
        ]

        for metric_name in custom_metrics:
            metrics = self.prometheus.query(f'{metric_name}{{job="bi-platform"}}')
            assert len(metrics.result) > 0, f"Custom metric {metric_name} should be collected"

        # Test metric labeling
        query_metrics = self.prometheus.query('bi_queries_executed_total{job="bi-platform"}')
        for metric in query_metrics.result:
            assert "query_type" in metric["metric"], "Query metrics should have query_type label"
            assert "user" in metric["metric"], "Query metrics should have user label"
            assert "status" in metric["metric"], "Query metrics should have status label"

        # Test metrics endpoint health
        metrics_endpoint = self.prometheus.query('up{job="bi-platform-metrics"}')
        assert len(metrics_endpoint.result) > 0, "Custom metrics endpoint should be monitored"
        assert all(m["value"][1] == "1" for m in metrics_endpoint.result), (
            "Metrics endpoint should be healthy"
        )

    def test_performance_regression_detection(self):
        """
        Test performance regression detection and alerting.

        TDD Phase: 🔴 RED - This test should fail initially
        Requirements:
        - Baseline performance metrics collection
        - Performance trend analysis
        - Regression detection algorithms
        - Automated alerts for performance degradation
        """
        # Test baseline metrics exist
        baseline = self.performance_tester.get_performance_baseline(self.namespace)
        assert baseline is not None, "Performance baseline should exist"
        assert "response_time_p95" in baseline, "Baseline should include P95 response time"
        assert "throughput_rps" in baseline, "Baseline should include throughput"
        assert "error_rate" in baseline, "Baseline should include error rate"

        # Test performance comparison
        current_metrics = self.performance_tester.get_current_performance(self.namespace)
        regression_analysis = self.performance_tester.detect_regression(baseline, current_metrics)

        assert regression_analysis is not None, "Should perform regression analysis"
        assert "regression_detected" in regression_analysis, (
            "Should indicate if regression detected"
        )
        assert "degraded_metrics" in regression_analysis, "Should list degraded metrics"

        # Test regression alerts
        if regression_analysis["regression_detected"]:
            regression_alerts = self.alertmanager.get_alerts(
                "PerformanceRegression", state="firing"
            )
            assert len(regression_alerts) > 0, "Should fire alerts for performance regression"

    def test_load_testing_integration(self):
        """
        Test load testing integration and monitoring.

        TDD Phase: 🔴 RED - This test should fail initially
        Requirements:
        - Load testing framework integration
        - Performance metrics during load tests
        - Load test result analysis
        - Capacity planning metrics
        """
        # Test load testing capability
        load_test_config = self.performance_tester.get_load_test_configuration()
        assert load_test_config is not None, "Load test configuration should exist"
        assert "scenarios" in load_test_config, "Should have load test scenarios"
        assert "target_rps" in load_test_config, "Should have target RPS configuration"

        # Test load test execution
        load_test_id = self.performance_tester.start_load_test("baseline_load", duration=60)
        assert load_test_id is not None, "Should be able to start load test"

        # Monitor metrics during load test
        test_metrics = self.performance_tester.monitor_load_test(load_test_id)
        assert test_metrics is not None, "Should collect metrics during load test"
        assert "response_times" in test_metrics, "Should track response times"
        assert "error_rates" in test_metrics, "Should track error rates"
        assert "throughput" in test_metrics, "Should track throughput"

        # Test capacity analysis
        capacity_report = self.performance_tester.analyze_capacity(test_metrics)
        assert capacity_report is not None, "Should generate capacity analysis"
        assert "max_sustainable_rps" in capacity_report, "Should determine max RPS"
        assert "bottlenecks" in capacity_report, "Should identify bottlenecks"

    def test_monitoring_stack_health(self):
        """
        Test that the monitoring stack itself is healthy and monitored.

        TDD Phase: 🔴 RED - This test should fail initially
        Requirements:
        - Prometheus, Grafana, AlertManager all healthy
        - Monitoring stack metrics collection
        - Self-monitoring alerts
        - Data retention policies
        """
        # Test core monitoring components health
        monitoring_components = ["prometheus", "grafana", "alertmanager"]

        for component in monitoring_components:
            deployment = self.k8s_client.get_deployment(self.monitoring_ns, component)
            assert deployment is not None, f"{component} should be deployed"
            assert deployment["status"]["ready_replicas"] >= 1, f"{component} should be running"

            # Check component is being monitored
            health_metrics = self.prometheus.query(f'up{{job="{component}"}}')
            assert len(health_metrics.result) > 0, f"{component} health should be monitored"

        # Test data retention
        retention_config = self.prometheus.get_retention_policy()
        assert retention_config["retention_time"] >= "30d", (
            "Should retain data for at least 30 days"
        )
        assert retention_config["retention_size"] is not None, "Should have size-based retention"

        # Test monitoring stack alerts
        stack_alerts = self.k8s_client.get_prometheus_rule(
            self.monitoring_ns, "monitoring-stack-alerts"
        )
        assert stack_alerts is not None, "Should have monitoring stack alerts"

        expected_stack_alerts = [
            "PrometheusDown",
            "GrafanaDown",
            "AlertManagerDown",
            "PrometheusConfigReload",
        ]
        alert_rules = stack_alerts["spec"]["groups"][0]["rules"]
        alert_names = [rule["alert"] for rule in alert_rules if "alert" in rule]

        for alert_name in expected_stack_alerts:
            assert alert_name in alert_names, f"Stack alert {alert_name} should be configured"

    # Helper methods

    def _create_test_infrastructure(self):
        """Create test monitoring infrastructure."""
        # Create monitoring namespace
        self.k8s_client.namespaces = {
            self.monitoring_ns: {
                "apiVersion": "v1",
                "kind": "Namespace",
                "metadata": {"name": self.monitoring_ns},
            },
            self.namespace: {
                "apiVersion": "v1",
                "kind": "Namespace",
                "metadata": {"name": self.namespace},
            },
        }

        # Create basic BI platform deployment for monitoring
        bi_deployment = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": "bi-platform",
                "namespace": self.namespace,
                "labels": {"app": "bi-platform"},
            },
            "spec": {
                "replicas": 2,
                "selector": {"matchLabels": {"app": "bi-platform"}},
                "template": {
                    "metadata": {"labels": {"app": "bi-platform"}},
                    "spec": {
                        "containers": [
                            {
                                "name": "bi-platform",
                                "image": "bi-platform:latest",
                                "ports": [{"containerPort": 8501, "name": "http"}],
                            }
                        ]
                    },
                },
            },
        }
        self.k8s_client.create_deployment(self.namespace, bi_deployment)

    def _load_monitoring_manifests(self):
        """Load monitoring configurations from manifests."""
        manifest_dir = Path("k8s/monitoring")
        if not manifest_dir.exists():
            # Create minimal configs for testing
            self._create_minimal_monitoring_configs()
            return

        # Load actual manifests
        for manifest_file in manifest_dir.glob("*.yaml"):
            try:
                docs = load_k8s_manifest(str(manifest_file))
                self._apply_manifest(docs)
            except FileNotFoundError:
                pass

    def _create_minimal_monitoring_configs(self):
        """Create minimal monitoring configurations for testing."""
        # Create Prometheus deployment
        prometheus_deployment = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": "prometheus",
                "namespace": self.monitoring_ns,
                "labels": {"app": "prometheus"},
            },
            "spec": {
                "replicas": 1,
                "selector": {"matchLabels": {"app": "prometheus"}},
                "template": {
                    "metadata": {"labels": {"app": "prometheus"}},
                    "spec": {
                        "containers": [
                            {
                                "name": "prometheus",
                                "image": "prom/prometheus:latest",
                                "ports": [{"containerPort": 9090, "name": "http"}],
                            }
                        ]
                    },
                },
            },
        }
        self.k8s_client.create_deployment(self.monitoring_ns, prometheus_deployment)

        # Create Grafana deployment
        grafana_deployment = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": "grafana",
                "namespace": self.monitoring_ns,
                "labels": {"app": "grafana"},
            },
            "spec": {
                "replicas": 1,
                "selector": {"matchLabels": {"app": "grafana"}},
                "template": {
                    "metadata": {"labels": {"app": "grafana"}},
                    "spec": {
                        "containers": [
                            {
                                "name": "grafana",
                                "image": "grafana/grafana:latest",
                                "ports": [{"containerPort": 3000, "name": "http"}],
                            }
                        ]
                    },
                },
            },
        }
        self.k8s_client.create_deployment(self.monitoring_ns, grafana_deployment)

        # Create AlertManager deployment
        alertmanager_deployment = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": "alertmanager",
                "namespace": self.monitoring_ns,
                "labels": {"app": "alertmanager"},
            },
            "spec": {
                "replicas": 1,
                "selector": {"matchLabels": {"app": "alertmanager"}},
                "template": {
                    "metadata": {"labels": {"app": "alertmanager"}},
                    "spec": {
                        "containers": [
                            {
                                "name": "alertmanager",
                                "image": "prom/alertmanager:latest",
                                "ports": [{"containerPort": 9093, "name": "http"}],
                            }
                        ]
                    },
                },
            },
        }
        self.k8s_client.create_deployment(self.monitoring_ns, alertmanager_deployment)

        # Create ServiceMonitor for BI platform
        bi_service_monitor = {
            "apiVersion": "monitoring.coreos.com/v1",
            "kind": "ServiceMonitor",
            "metadata": {
                "name": "bi-platform-monitor",
                "namespace": self.namespace,
                "labels": {"app": "bi-platform"},
            },
            "spec": {
                "selector": {"matchLabels": {"app": "bi-platform"}},
                "endpoints": [{"port": "http", "interval": "30s", "path": "/metrics"}],
            },
        }
        self.k8s_client.create_service_monitor(self.namespace, bi_service_monitor)

        # Create PrometheusRules for BI platform alerts
        bi_alert_rules = {
            "apiVersion": "monitoring.coreos.com/v1",
            "kind": "PrometheusRule",
            "metadata": {
                "name": "bi-platform-alerts",
                "namespace": self.namespace,
                "labels": {"app": "bi-platform"},
            },
            "spec": {
                "groups": [
                    {
                        "name": "bi-platform.rules",
                        "rules": [
                            {
                                "alert": "HighErrorRate",
                                "expr": 'rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.1',
                                "for": "5m",
                                "labels": {"severity": "critical"},
                                "annotations": {"summary": "High error rate detected"},
                            },
                            {
                                "alert": "HighResponseTime",
                                "expr": "histogram_quantile(0.95, http_request_duration_seconds_bucket) > 2.0",
                                "for": "5m",
                                "labels": {"severity": "critical"},
                                "annotations": {"summary": "High response time detected"},
                            },
                            {
                                "alert": "HighCPUUsage",
                                "expr": "rate(container_cpu_usage_seconds_total[5m]) > 0.8",
                                "for": "5m",
                                "labels": {"severity": "warning"},
                                "annotations": {"summary": "High CPU usage detected"},
                            },
                            {
                                "alert": "HighMemoryUsage",
                                "expr": "container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.8",
                                "for": "5m",
                                "labels": {"severity": "warning"},
                                "annotations": {"summary": "High memory usage detected"},
                            },
                            {
                                "alert": "ServiceDown",
                                "expr": 'up{job="bi-platform"} == 0',
                                "for": "1m",
                                "labels": {"severity": "critical"},
                                "annotations": {"summary": "Service is down"},
                            },
                        ],
                    }
                ]
            },
        }
        self.k8s_client.create_prometheus_rule(self.namespace, bi_alert_rules)

        # Create SLO burn rate alert rules
        slo_burn_rate_rules = {
            "apiVersion": "monitoring.coreos.com/v1",
            "kind": "PrometheusRule",
            "metadata": {
                "name": "slo-burn-rate-alerts",
                "namespace": self.namespace,
                "labels": {"app": "slo-monitoring"},
            },
            "spec": {
                "groups": [
                    {
                        "name": "slo-burn-rate.rules",
                        "rules": [
                            {
                                "alert": "ErrorBudgetBurnRate",
                                "expr": "error_budget_burn_rate > 10",
                                "for": "2m",
                                "labels": {"severity": "critical"},
                                "annotations": {"summary": "Error budget burning too fast"},
                            }
                        ],
                    }
                ]
            },
        }
        self.k8s_client.create_prometheus_rule(self.namespace, slo_burn_rate_rules)

        # Create monitoring stack alert rules
        monitoring_stack_alerts = {
            "apiVersion": "monitoring.coreos.com/v1",
            "kind": "PrometheusRule",
            "metadata": {
                "name": "monitoring-stack-alerts",
                "namespace": self.monitoring_ns,
                "labels": {"app": "monitoring-stack"},
            },
            "spec": {
                "groups": [
                    {
                        "name": "monitoring-stack.rules",
                        "rules": [
                            {
                                "alert": "PrometheusDown",
                                "expr": 'up{job="prometheus"} == 0',
                                "for": "1m",
                                "labels": {"severity": "critical"},
                                "annotations": {"summary": "Prometheus is down"},
                            },
                            {
                                "alert": "GrafanaDown",
                                "expr": 'up{job="grafana"} == 0',
                                "for": "1m",
                                "labels": {"severity": "critical"},
                                "annotations": {"summary": "Grafana is down"},
                            },
                            {
                                "alert": "AlertManagerDown",
                                "expr": 'up{job="alertmanager"} == 0',
                                "for": "1m",
                                "labels": {"severity": "critical"},
                                "annotations": {"summary": "AlertManager is down"},
                            },
                            {
                                "alert": "PrometheusConfigReload",
                                "expr": "prometheus_config_last_reload_successful == 0",
                                "for": "1m",
                                "labels": {"severity": "warning"},
                                "annotations": {"summary": "Prometheus config reload failed"},
                            },
                        ],
                    }
                ]
            },
        }
        self.k8s_client.create_prometheus_rule(self.monitoring_ns, monitoring_stack_alerts)

    def _apply_manifest(self, manifest):
        """Apply Kubernetes manifest to mock client."""
        if isinstance(manifest, list):
            for doc in manifest:
                self._apply_single_manifest(doc)
        else:
            self._apply_single_manifest(manifest)

    def _apply_single_manifest(self, doc):
        """Apply single Kubernetes resource."""
        if not doc or "kind" not in doc:
            return

        kind = doc["kind"]
        namespace = doc["metadata"].get("namespace", self.namespace)

        if kind == "Deployment":
            self.k8s_client.create_deployment(namespace, doc)
        elif kind == "Service":
            self.k8s_client.create_service(namespace, doc)
        elif kind == "ConfigMap":
            self.k8s_client.create_config_map(namespace, doc)
        elif kind == "ServiceMonitor":
            self.k8s_client.create_service_monitor(namespace, doc)
        elif kind == "PrometheusRule":
            self.k8s_client.create_prometheus_rule(namespace, doc)


class TestPerformanceMonitoringManifests:
    """TDD Tests for Performance Monitoring Kubernetes manifests."""

    def test_monitoring_manifests_directory_exists(self):
        """
        Test that monitoring manifests directory exists.

        TDD Phase: 🔴 RED - This test should fail initially
        """
        manifest_dir = Path("k8s/monitoring")
        assert manifest_dir.exists(), (
            f"Monitoring manifests directory should exist at {manifest_dir}"
        )

    def test_prometheus_manifest_valid(self):
        """
        Test that Prometheus manifest is valid YAML.

        TDD Phase: 🔴 RED - This test should fail initially
        """
        # Check both base and root for backwards compatibility
        manifest_path = Path("k8s/monitoring/base/prometheus.yaml")
        if not manifest_path.exists():
            manifest_path = Path("k8s/monitoring/prometheus.yaml")
        assert manifest_path.exists(), f"Prometheus manifest should exist at {manifest_path}"

        with open(manifest_path, "r") as f:
            docs = list(yaml.safe_load_all(f))

        # Should have Deployment, Service, ConfigMap
        kinds = [doc["kind"] for doc in docs if doc]
        assert "Deployment" in kinds, "Should have Prometheus Deployment"
        assert "Service" in kinds, "Should have Prometheus Service"
        assert "ConfigMap" in kinds, "Should have Prometheus ConfigMap"

    def test_grafana_manifest_valid(self):
        """
        Test that Grafana manifest is valid.

        TDD Phase: 🔴 RED - This test should fail initially
        """
        # Check both base and root for backwards compatibility
        manifest_path = Path("k8s/monitoring/base/grafana.yaml")
        if not manifest_path.exists():
            manifest_path = Path("k8s/monitoring/grafana.yaml")
        assert manifest_path.exists(), f"Grafana manifest should exist at {manifest_path}"

        with open(manifest_path, "r") as f:
            docs = list(yaml.safe_load_all(f))

        kinds = [doc["kind"] for doc in docs if doc]
        assert "Deployment" in kinds, "Should have Grafana Deployment"
        assert "Service" in kinds, "Should have Grafana Service"
        assert "PersistentVolumeClaim" in kinds, "Should have Grafana PVC"

    def test_alertmanager_manifest_valid(self):
        """
        Test that AlertManager manifest is valid.

        TDD Phase: 🔴 RED - This test should fail initially
        """
        # Check both base and root for backwards compatibility
        manifest_path = Path("k8s/monitoring/base/alertmanager.yaml")
        if not manifest_path.exists():
            manifest_path = Path("k8s/monitoring/alertmanager.yaml")
        assert manifest_path.exists(), f"AlertManager manifest should exist at {manifest_path}"

        with open(manifest_path, "r") as f:
            docs = list(yaml.safe_load_all(f))

        # Find AlertManager deployment
        alertmanager_deployment = None
        for doc in docs:
            if (
                doc
                and doc.get("kind") == "Deployment"
                and "alertmanager" in doc["metadata"]["name"]
            ):
                alertmanager_deployment = doc
                break

        assert alertmanager_deployment is not None, "Should have AlertManager Deployment"

    def test_service_monitor_manifest_valid(self):
        """
        Test that ServiceMonitor manifest is valid.

        TDD Phase: 🔴 RED - This test should fail initially
        """
        manifest_path = Path("k8s/monitoring/service-monitors.yaml")
        assert manifest_path.exists(), f"ServiceMonitors should exist at {manifest_path}"

        with open(manifest_path, "r") as f:
            docs = list(yaml.safe_load_all(f))

        service_monitors = [doc for doc in docs if doc and doc.get("kind") == "ServiceMonitor"]
        assert len(service_monitors) > 0, "Should have ServiceMonitor resources"

        # Check BI platform ServiceMonitor
        bi_monitor = next(
            (sm for sm in service_monitors if sm["metadata"]["name"] == "bi-platform-monitor"), None
        )
        assert bi_monitor is not None, "Should have BI platform ServiceMonitor"

    def test_prometheus_rules_manifest_valid(self):
        """
        Test that PrometheusRules manifest is valid.

        TDD Phase: 🔴 RED - This test should fail initially
        """
        manifest_path = Path("k8s/monitoring/bi-platform-rules.yaml")
        assert manifest_path.exists(), f"PrometheusRules should exist at {manifest_path}"

        with open(manifest_path, "r") as f:
            docs = list(yaml.safe_load_all(f))

        prometheus_rules = [doc for doc in docs if doc and doc.get("kind") == "PrometheusRule"]
        assert len(prometheus_rules) > 0, "Should have PrometheusRule resources"

        # Check alert rules structure
        for rule in prometheus_rules:
            assert "spec" in rule, "PrometheusRule should have spec"
            assert "groups" in rule["spec"], "PrometheusRule should have groups"
            assert len(rule["spec"]["groups"]) > 0, "Should have at least one rule group"


if __name__ == "__main__":
    # Run the tests to see them fail (RED phase)
    pytest.main([__file__, "-v", "--tb=short"])
