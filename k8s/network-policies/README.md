# Network Policies Documentation

This directory contains Kubernetes NetworkPolicy manifests implementing a comprehensive zero-trust network security model for the Business Intelligence platform.

## Architecture Overview

The network security model implements:
- **Default Deny-All**: All traffic is blocked by default
- **Explicit Allow**: Only specifically permitted traffic is allowed
- **Microsegmentation**: Application tiers are properly isolated
- **Zero Trust**: No implicit trust relationships exist
- **Namespace Isolation**: Cross-namespace communication is controlled

## Security Policies

### 1. Default Deny (`default-deny.yaml`)
- Blocks all ingress and egress traffic by default
- Applies to all pods in the namespace
- Foundation for zero-trust networking

### 2. Application Tier Policies (`app-tier-policies.yaml`)
- **BI Platform**: Can connect to PostgreSQL, receive connections from web tier
- **Web Frontend**: Can connect to BI app, accepts public traffic
- Implements proper tier separation

### 3. Data Tier Isolation (`data-tier-isolation.yaml`)
- **PostgreSQL**: Only accepts connections from BI app
- **Redis**: Restricted cache access
- No external internet access for data services

### 4. Ingress/Egress Controls (`ingress-egress-controls.yaml`)
- Public services have IP-based ingress restrictions
- Data services have limited egress to essential services only
- External API access is explicitly controlled

### 5. Namespace Isolation (`namespace-isolation.yaml`)
- Prevents cross-namespace communication
- Allows essential system access (DNS, Kubernetes API)
- Enforces tenant isolation

### 6. Microsegmentation (`microsegmentation.yaml`)
- Web tier → App tier communication only
- App tier → Data tier communication only
- Blocks direct web tier → data tier communication

### 7. Zero Trust (`zero-trust.yaml`)
- DNS access for all pods
- Monitoring integration
- Controlled external API access

## Network Architecture

```
Internet/Load Balancer
         ↓
    Web Tier (port 80/443)
         ↓ (port 8501)
    App Tier (BI Platform)
         ↓ (port 5432/6379)
    Data Tier (PostgreSQL/Redis)
         ↓ (port 53)
    DNS Services
```

## Security Features

### Traffic Control
- **Ingress**: Controlled by source IP/namespace
- **Egress**: Limited to necessary destinations only
- **DNS**: Allowed for all pods to kube-system
- **External APIs**: Whitelisted endpoints only

### Isolation Levels
1. **Pod-level**: Individual pod network policies
2. **Tier-level**: Web/App/Data tier separation
3. **Namespace-level**: Tenant isolation
4. **Cluster-level**: External access control

### Monitoring & Compliance
- All traffic is logged and monitored
- Policy violations are tracked
- Zero-trust compliance is validated
- Network connectivity is continuously tested

## Deployment Order

1. Deploy `default-deny.yaml` first
2. Deploy tier-specific policies
3. Deploy namespace isolation
4. Verify connectivity works as expected

## Testing

Network policies are validated through comprehensive TDD tests:

```bash
# Run network policy tests
make test-infrastructure

# Run specific network tests
pytest tests/infrastructure/test_network_policies_tdd.py -v
```

## Security Best Practices

### Principle of Least Privilege
- Each policy grants minimal necessary access
- No broad "allow all" rules
- Regular policy review and tightening

### Defense in Depth
- Multiple layers of network controls
- Application and network-level security
- Monitoring and alerting integration

### Zero Trust Implementation
- Default deny-all baseline
- Explicit allow rules only
- No implicit trust relationships
- Continuous verification

## Common Patterns

### Allow Internal Service Communication
```yaml
egress:
- to:
  - podSelector:
      matchLabels:
        app: target-service
  ports:
  - protocol: TCP
    port: 8080
```

### Allow DNS Resolution
```yaml
egress:
- to:
  - namespaceSelector:
      matchLabels:
        name: kube-system
  ports:
  - protocol: UDP
    port: 53
```

### Restrict External Access
```yaml
egress:
- to:
  - namespaceSelector: {}
    podSelector:
      matchLabels:
        external-api: "allowed"
  ports:
  - protocol: TCP
    port: 443
```

## Troubleshooting

### Common Issues
1. **Connection Timeouts**: Check if explicit allow rule exists
2. **DNS Resolution Fails**: Ensure DNS policy allows kube-system access  
3. **External API Calls Fail**: Verify external-api label on target pods
4. **Cross-Namespace Blocked**: Check namespace isolation policies

### Debug Commands
```bash
# Test connectivity between pods
kubectl exec -it source-pod -- nc -zv target-pod 8080

# Check network policy status
kubectl get networkpolicies -n business-intelligence

# View policy details
kubectl describe networkpolicy default-deny -n business-intelligence

# Monitor policy violations
kubectl logs -l app=network-policy-monitor -n monitoring
```

## Maintenance

### Regular Tasks
- Review and update IP allowlists
- Audit policy effectiveness
- Test disaster recovery scenarios
- Update documentation

### Policy Updates
1. Test changes in staging environment
2. Apply policies in order of restrictiveness
3. Monitor for broken connections
4. Rollback if issues occur

## Compliance

This network security implementation meets requirements for:
- **SOC 2 Type II**: Network segmentation controls
- **ISO 27001**: Access control and network security
- **PCI DSS**: Network isolation for sensitive data
- **GDPR**: Data protection through network controls
