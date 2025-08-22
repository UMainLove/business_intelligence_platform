# 🚀 Business Intelligence Platform - Deployment Guide

This comprehensive guide covers all deployment options for the Business Intelligence Platform, from local development to production Kubernetes clusters.

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Production Configuration](#production-configuration)
- [Monitoring & Observability](#monitoring--observability)
- [Security Configuration](#security-configuration)
- [Troubleshooting](#troubleshooting)

## 🎯 Quick Start

### Prerequisites

```bash
# Required tools
- Python 3.10+ 
- Docker & Docker Compose
- kubectl (for Kubernetes)
- git

# Optional tools for development
- make
- Node.js 16+ (for some development tools)
```

### 1-Minute Setup

```bash
# Clone and setup
git clone <repository-url>
cd business_intelligence_platform

# Setup environment
cp .env.example .env
# Edit .env with your API keys

# Start with Docker Compose (recommended)
docker-compose up -d

# Access the application
open http://localhost:8501
```

## 🏠 Local Development

### Python Virtual Environment

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup development tools
make install-dev

# Run the application
streamlit run app_bi.py
```

### Database Setup

**PostgreSQL (Production-like):**
```bash
# Start PostgreSQL with Docker
docker run -d \
  --name bi-postgres \
  -e POSTGRES_DB=business_intelligence \
  -e POSTGRES_USER=bi_user \
  -e POSTGRES_PASSWORD=your_password \
  -p 5432:5432 \
  postgres:16-alpine

# Initialize database
make db-init
```

**SQLite (Development):**
```bash
# Uses local SQLite file (automatic)
# Location: data/business_intelligence.db
```

### Redis Cache

```bash
# Start Redis with Docker
docker run -d \
  --name bi-redis \
  -p 6379:6379 \
  redis:7-alpine

# Test connection
redis-cli ping
```

## 🐳 Docker Deployment

### Docker Compose (Recommended)

**Production-ready stack:**
```yaml
# docker-compose.yml
version: '3.8'
services:
  bi-app:
    build: .
    ports:
      - "8501:8501"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - DATABASE_URL=postgresql://bi_user:password@postgres:5432/business_intelligence
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: business_intelligence
      POSTGRES_USER: bi_user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init_db.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

**Commands:**
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f bi-app

# Scale the application
docker-compose up -d --scale bi-app=3

# Stop all services
docker-compose down

# Clean restart
docker-compose down -v && docker-compose up -d
```

### Single Container

```bash
# Build image
docker build -t business-intelligence:latest .

# Run with environment variables
docker run -d \
  --name bi-app \
  -p 8501:8501 \
  -e ANTHROPIC_API_KEY=your_key \
  -e DATABASE_URL=sqlite:///data/bi.db \
  -v $(pwd)/data:/app/data \
  business-intelligence:latest
```

## ☸️ Kubernetes Deployment

### Prerequisites

```bash
# Install required tools
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl && sudo mv kubectl /usr/local/bin/

# Install kustomize
curl -s "https://raw.githubusercontent.com/kubernetes-sigs/kustomize/master/hack/install_kustomize.sh" | bash
sudo mv kustomize /usr/local/bin/
```

### Environment Configuration

The platform supports three environments with Kustomize overlays:

**Development Environment:**
```bash
# Deploy to development
make k8s-deploy-dev

# Or manually
kubectl apply -k k8s/monitoring/overlays/dev
```

**Staging Environment:**
```bash
# Deploy to staging
make k8s-deploy-staging

# Or manually
kubectl apply -k k8s/monitoring/overlays/staging
```

**Production Environment:**
```bash
# Deploy to production
make k8s-deploy-prod

# Or manually
kubectl apply -k k8s/monitoring/overlays/production
```

### Manual Kubernetes Deployment

**1. Create Namespace:**
```bash
kubectl create namespace business-intelligence
kubectl label namespace business-intelligence monitoring=enabled
```

**2. Deploy Base Manifests:**
```bash
# Apply all base manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
```

**3. Deploy Monitoring Stack:**
```bash
# Deploy monitoring components
kubectl apply -k k8s/monitoring/base/
```

**4. Verify Deployment:**
```bash
# Check pod status
kubectl get pods -n business-intelligence

# Check services
kubectl get svc -n business-intelligence

# Check HPA status
kubectl get hpa -n business-intelligence

# View logs
kubectl logs -l app=business-intelligence -n business-intelligence
```

### Auto-scaling Configuration

The platform includes Horizontal Pod Autoscaler (HPA) for automatic scaling:

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: business-intelligence-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: business-intelligence
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## 🏭 Production Configuration

### Environment Variables

**Core Configuration:**
```bash
# API Keys
ANTHROPIC_API_KEY=your_anthropic_api_key

# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname
REDIS_URL=redis://host:6379/0

# Application
ENVIRONMENT=production
LOG_LEVEL=info
DEBUG_MODE=false

# Performance
MAX_WORKERS=4
CACHE_TTL=3600
REQUEST_TIMEOUT=30

# Security
SECRET_KEY=your_secret_key
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CORS_ORIGINS=https://yourdomain.com
```

**Monitoring Configuration:**
```bash
# Prometheus
PROMETHEUS_ENDPOINT=http://prometheus:9090
METRICS_RETENTION_DAYS=30

# Grafana
GRAFANA_ENDPOINT=http://grafana:3000
GRAFANA_USER=admin
GRAFANA_PASSWORD=secure_password

# AlertManager
ALERTMANAGER_ENDPOINT=http://alertmanager:9093
ALERT_THROTTLE_MINUTES=15
```

### Resource Requirements

**Minimum Requirements:**
```yaml
resources:
  requests:
    cpu: 100m
    memory: 256Mi
  limits:
    cpu: 500m
    memory: 512Mi
```

**Production Requirements:**
```yaml
resources:
  requests:
    cpu: 200m
    memory: 512Mi
  limits:
    cpu: 1000m
    memory: 1Gi
```

**High-Load Requirements:**
```yaml
resources:
  requests:
    cpu: 500m
    memory: 1Gi
  limits:
    cpu: 2000m
    memory: 2Gi
```

### Database Configuration

**PostgreSQL Production Setup:**
```sql
-- Create optimized database
CREATE DATABASE business_intelligence
  WITH ENCODING 'UTF8'
       LC_COLLATE='en_US.UTF-8'
       LC_CTYPE='en_US.UTF-8'
       TEMPLATE=template0;

-- Create user with limited privileges
CREATE USER bi_user WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE business_intelligence TO bi_user;
GRANT USAGE ON SCHEMA public TO bi_user;
GRANT CREATE ON SCHEMA public TO bi_user;

-- Performance tuning
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
```

## 📊 Monitoring & Observability

### Prometheus Configuration

The platform includes comprehensive monitoring with Prometheus:

**Metrics Collected:**
- Application performance metrics
- Business intelligence query metrics
- Database connection pool metrics
- Redis cache hit/miss ratios
- Custom business KPIs

**Access Prometheus:**
```bash
# Port-forward to access locally
kubectl port-forward svc/prometheus 9090:9090 -n monitoring

# Open in browser
open http://localhost:9090
```

### Grafana Dashboards

**Pre-configured Dashboards:**
- BI Platform Overview
- Application Performance
- Database Metrics
- Cache Performance
- Business KPIs

**Access Grafana:**
```bash
# Port-forward to access locally
kubectl port-forward svc/grafana 3000:3000 -n monitoring

# Open in browser (admin/admin123)
open http://localhost:3000
```

### AlertManager

**Configured Alerts:**
- High error rate (>5% for 5 minutes)
- High response time (>2s for 5 minutes)
- Database connection failures
- Memory usage >90%
- Disk space <10%

**Access AlertManager:**
```bash
# Port-forward to access locally
kubectl port-forward svc/alertmanager 9093:9093 -n monitoring

# Open in browser
open http://localhost:9093
```

### Health Checks

**Application Health Endpoints:**
```bash
# Basic health check
curl http://localhost:8501/health

# Detailed health check
curl http://localhost:8501/health/detailed

# Readiness probe
curl http://localhost:8501/ready

# Liveness probe
curl http://localhost:8501/alive
```

**Kubernetes Health Checks:**
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8501
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /ready
    port: 8501
  initialDelaySeconds: 5
  periodSeconds: 5
```

## 🔒 Security Configuration

### Secrets Management

**Kubernetes Secrets:**
```bash
# Create secrets manually
kubectl create secret generic bi-secrets \
  --from-literal=anthropic-api-key=your_key \
  --from-literal=database-password=your_password \
  -n business-intelligence

# Or use sealed secrets (recommended)
echo -n 'your_secret' | kubectl create secret generic bi-secrets \
  --dry-run=client --from-file=key=/dev/stdin -o yaml | \
  kubeseal -o yaml > sealed-secret.yaml
```

**Environment-specific Secrets:**
```bash
# Development
kubectl apply -f k8s/secrets/dev-secrets.yaml

# Staging  
kubectl apply -f k8s/secrets/staging-secrets.yaml

# Production
kubectl apply -f k8s/secrets/prod-secrets.yaml
```

### Network Policies

**Zero Trust Network Configuration:**
```yaml
# Example: Allow only necessary traffic
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: bi-app-network-policy
spec:
  podSelector:
    matchLabels:
      app: business-intelligence
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8501
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - protocol: TCP
      port: 53
    - protocol: UDP
      port: 53
```

### RBAC Configuration

**Service Account and Permissions:**
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: business-intelligence-sa
  namespace: business-intelligence
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: business-intelligence
  name: bi-app-role
rules:
- apiGroups: [""]
  resources: ["configmaps", "secrets"]
  verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: bi-app-rolebinding
  namespace: business-intelligence
subjects:
- kind: ServiceAccount
  name: business-intelligence-sa
  namespace: business-intelligence
roleRef:
  kind: Role
  name: bi-app-role
  apiGroup: rbac.authorization.k8s.io
```

## 🔧 Troubleshooting

### Common Issues

**1. Application Won't Start**
```bash
# Check logs
kubectl logs -l app=business-intelligence -n business-intelligence

# Common issues:
# - Missing API keys in secrets
# - Database connection failures
# - Insufficient resources
```

**2. Database Connection Issues**
```bash
# Test database connectivity
kubectl exec -it deployment/business-intelligence -n business-intelligence -- \
  python -c "
from src.database_config import db_config
print('Testing database connection...')
try:
    conn = db_config.get_connection()
    print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
"
```

**3. Redis Connection Issues**
```bash
# Test Redis connectivity
kubectl exec -it deployment/redis -n business-intelligence -- redis-cli ping

# Check Redis logs
kubectl logs deployment/redis -n business-intelligence
```

**4. HPA Not Scaling**
```bash
# Check HPA status
kubectl describe hpa business-intelligence-hpa -n business-intelligence

# Check metrics server
kubectl top pods -n business-intelligence

# Ensure metrics server is running
kubectl get pods -n kube-system | grep metrics-server
```

**5. Monitoring Stack Issues**
```bash
# Check monitoring stack health
make monitoring-check

# Check individual components
kubectl get pods -n monitoring
kubectl logs -l app=prometheus -n monitoring
kubectl logs -l app=grafana -n monitoring
kubectl logs -l app=alertmanager -n monitoring
```

### Performance Tuning

**Application Performance:**
```bash
# Increase worker processes
export MAX_WORKERS=8

# Optimize cache settings  
export CACHE_TTL=7200
export REDIS_MAX_CONNECTIONS=20

# Tune database connections
export DB_POOL_SIZE=20
export DB_MAX_OVERFLOW=30
```

**Kubernetes Resource Tuning:**
```yaml
# For high-load scenarios
resources:
  requests:
    cpu: 1000m
    memory: 2Gi
  limits:
    cpu: 4000m
    memory: 4Gi

# HPA for aggressive scaling
spec:
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        averageUtilization: 60
```

### Logs and Debugging

**Application Logs:**
```bash
# Tail application logs
kubectl logs -f deployment/business-intelligence -n business-intelligence

# Get logs from all pods
kubectl logs -l app=business-intelligence -n business-intelligence --tail=100

# Save logs to file
kubectl logs deployment/business-intelligence -n business-intelligence > app.log
```

**System Health Check:**
```bash
# Comprehensive health check
make health-check

# Database health
make db-health

# Cache health  
redis-cli --raw info | grep connected_clients

# Monitoring health
make monitoring-check
```

### Backup and Recovery

**Database Backup:**
```bash
# PostgreSQL backup
kubectl exec deployment/postgres -n business-intelligence -- \
  pg_dump -U bi_user business_intelligence > backup_$(date +%Y%m%d_%H%M%S).sql

# Automated backup script
kubectl create job --from=cronjob/postgres-backup backup-manual -n business-intelligence
```

**Application Data Backup:**
```bash
# Backup persistent volumes
kubectl get pvc -n business-intelligence
# Use your cloud provider's snapshot functionality
```

**Disaster Recovery:**
```bash
# Quick restore procedure
1. Deploy fresh cluster: kubectl apply -k k8s/monitoring/overlays/production
2. Restore database: psql -U bi_user -d business_intelligence < backup.sql  
3. Verify health: make monitoring-check
4. Update DNS: point domain to new cluster
```

## 📞 Support

For deployment issues:

1. **Check logs**: `kubectl logs` and `make health-check`
2. **Review documentation**: This guide and [INFRASTRUCTURE.md](INFRASTRUCTURE.md)
3. **Validate configuration**: `make k8s-validate`
4. **Test components**: `make test-infrastructure`

---

**Next Steps:**
- [Infrastructure Documentation](INFRASTRUCTURE.md)
- [Code Quality Guidelines](CODE_QUALITY.md) 
- [CI/CD Pipeline Documentation](CICD.md)