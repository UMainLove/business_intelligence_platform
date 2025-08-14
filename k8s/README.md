# Business Intelligence Platform - Kubernetes Deployment

This directory contains Kubernetes manifests for deploying the Business Intelligence Platform in a production environment.

## Quick Start

1. **Create Namespace and Secrets**

```bash
kubectl apply -f namespace.yaml
kubectl apply -f secrets.yaml
```

### Deploy Database Services**

```bash
kubectl apply -f postgres.yaml
kubectl apply -f redis.yaml
```

1. **Deploy Application**

```bash
kubectl apply -f deployment.yaml
kubectl apply -f rbac.yaml
kubectl apply -f hpa.yaml
```

### Setup Ingress (Optional)

```bash
kubectl apply -f ingress.yaml
```

1. **Deploy Monitoring (Optional)**

```bash
kubectl apply -f monitoring.yaml
```

## Files Overview

- **namespace.yaml**: Creates the `business-intelligence` namespace
- **secrets.yaml**: Contains secrets and configuration maps
- **postgres.yaml**: PostgreSQL database deployment with persistent storage
- **redis.yaml**: Redis cache deployment with persistent storage
- **deployment.yaml**: Main BI application deployment with 2 replicas
- **ingress.yaml**: Ingress configuration for external access
- **hpa.yaml**: Horizontal Pod Autoscaler for automatic scaling
- **monitoring.yaml**: Prometheus and Grafana monitoring stack
- **rbac.yaml**: Role-Based Access Control and Network Policies

## Prerequisites

- Kubernetes cluster (v1.20+)
- kubectl configured
- NGINX Ingress Controller (for ingress)
- cert-manager (for TLS certificates)
- Metrics server (for HPA)

## Configuration

### Secrets

Before deployment, update the base64-encoded secrets in `secrets.yaml`:

- `anthropic-api-key`: Your Anthropic API key
- `postgres-password`: Database password
- `redis-password`: Redis password
- `grafana-password`: Grafana admin password

### Domain Configuration

Update `ingress.yaml` to use your actual domain:

```yaml
- host: bi.yourdomain.com  # Replace with your domain
```

## Scaling

The platform automatically scales between 2-10 replicas based on:

- CPU utilization > 70%
- Memory utilization > 80%

Manual scaling:

```bash
kubectl scale deployment bi-app --replicas=5 -n business-intelligence
```

## Monitoring

Access monitoring dashboards:

- Grafana: `http://bi.yourdomain.com/grafana` (admin/password from secrets)
- Prometheus: `http://bi.yourdomain.com/prometheus`

## Storage

Persistent volumes are used for:

- PostgreSQL data (10Gi)
- Redis data (1Gi)
- Application data (5Gi)
- Application logs (2Gi)
- Prometheus metrics (5Gi)
- Grafana dashboards (2Gi)

## Security Features

- Non-root containers
- Read-only root filesystems
- Network policies restricting traffic
- RBAC with minimal permissions
- TLS encryption via cert-manager
- Secret management via Kubernetes secrets

## Troubleshooting

Check pod status:

```bash
kubectl get pods -n business-intelligence
```

View logs:

```bash
kubectl logs -f deployment/bi-app -n business-intelligence
```

Check resources:

```bash
kubectl top pods -n business-intelligence
```

Access shell:

```bash
kubectl exec -it deployment/bi-app -n business-intelligence -- /bin/bash
```

## Health Checks

All services include:

- Liveness probes (restart unhealthy containers)
- Readiness probes (remove from load balancing when not ready)
- Health check endpoints

## Backup Strategy

Recommended backup approach:

1. **Database**: Use pg_dump for PostgreSQL backups
2. **Redis**: Use BGSAVE for Redis snapshots
3. **Application Data**: Regular PVC snapshots
4. **Configuration**: Keep manifests in version control

## Updates

Rolling updates are performed automatically:

```bash
kubectl set image deployment/bi-app bi-app=business-intelligence:v2.0 -n business-intelligence
```

Monitor rollout:

```bash
kubectl rollout status deployment/bi-app -n business-intelligence
```

## Resource Requirements

Minimum cluster requirements:

- 4 vCPUs
- 8GB RAM
- 50GB storage
- 3 worker nodes (recommended)
