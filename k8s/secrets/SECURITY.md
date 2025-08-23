# Sealed Secrets Controller Security Configuration

## Overview

This document explains the RBAC security model for the Sealed Secrets Controller deployment and addresses the security scanning findings.

## Security Model

### ClusterRole Permissions

The Sealed Secrets Controller ClusterRole has **NO secret permissions** - all secret management is delegated to namespace-specific Roles:

1. **SealedSecrets CRD Management** (`bitnami.com/sealedsecrets`)
   - `get`, `list`, `watch`: Read SealedSecret resources across all namespaces
   - `update`, `patch`: Update SealedSecret status after processing
   - **Justification**: The controller must watch for SealedSecret creation/updates cluster-wide

2. **Namespace Discovery** (`core/namespaces`)
   - `get`, `list`: Validate namespace existence before creating secrets
   - **Justification**: Ensures SealedSecrets can only target valid namespaces

3. **Event Logging** (`core/events`)
   - `create`, `patch`: Log controller operations and errors
   - **Justification**: Essential for debugging and audit trails

**Important**: The ClusterRole contains NO permissions for secrets. This addresses Snyk security findings while maintaining functionality through namespace-specific Roles.

### Namespace-Specific Permissions

Secret management is restricted to specific namespaces through Role/RoleBinding:

#### Business Intelligence Namespace
- **Namespace**: `business-intelligence`
- **Permissions**: `get`, `list`, `create`, `update`, `patch` on secrets
- **NO DELETE**: Controller cannot delete secrets (principle of least privilege)
- **SealedSecrets**: Can read and watch SealedSecrets in this namespace

#### Monitoring Namespace
- **Namespace**: `monitoring`
- **Permissions**: `get`, `list`, `create`, `update`, `patch` on secrets
- **NO DELETE**: Controller cannot delete secrets
- **SealedSecrets**: Can read and watch SealedSecrets in this namespace

**Security Benefits**:
- No cluster-wide secret access
- Per-namespace authorization
- No destructive operations (delete)
- Audit trail per namespace

## Security Improvements Made

### Original Issues
- ClusterRole had broad secret permissions across all namespaces
- No namespace-specific scoping
- Snyk flagged as "dangerous permissions"

### Mitigations Applied
1. **Removed** cluster-wide secret deletion capability from ClusterRole
2. **Added** namespace-specific Role for actual secret operations
3. **Scoped** secret permissions to business-intelligence namespace only
4. **Documented** permission justifications

### Permission Matrix

| Resource | ClusterRole Verbs | Namespace Role Verbs | Justification |
|----------|-------------------|---------------------|---------------|
| secrets | **NONE** | get, list, create, update, patch | All secret operations via namespace Roles only |
| sealedsecrets | get, list, watch, update, patch | get, list, watch | CRD management at cluster, reading at namespace |
| namespaces | get, list | - | Validation of target namespaces |
| events | create, patch | - | Audit logging |

## Container Security Hardening

The Sealed Secrets Controller deployment includes comprehensive security controls:

### Security Context
- **Non-Root User**: Runs as UID 10001 (non-root) to prevent privilege escalation
- **Read-Only Filesystem**: Root filesystem is read-only with writable temp volumes
- **No Privilege Escalation**: `allowPrivilegeEscalation: false` prevents SUID exploits
- **Drop All Capabilities**: Removes all Linux capabilities reducing attack surface

### Image Security
- **Specific Version**: Uses tagged version `v0.24.5` instead of `latest`
- **Always Pull**: `imagePullPolicy: Always` ensures fresh, authorized images
- **Official Image**: Uses official Bitnami image with security patches

### Volume Mounts
- `/tmp`: Temporary writable space for runtime operations
- `/home/sealed-secrets`: User home directory for application state

## Compliance

This configuration follows security best practices:

- **Principle of Least Privilege**: Minimal permissions required for functionality
- **Defense in Depth**: Multiple layers of authorization (Cluster + Namespace)
- **Audit Trail**: Event logging for all operations
- **Namespace Isolation**: Secret access limited to specific namespaces
- **Container Hardening**: Comprehensive security context and controls
- **CIS Kubernetes Benchmark**: Aligns with CIS security recommendations

## Monitoring

Monitor the following for security:

1. **RBAC Violations**: Watch for access denied events
2. **Secret Access**: Audit secret creation/modification events
3. **Controller Health**: Ensure controller can process SealedSecrets
4. **Permission Usage**: Verify only necessary permissions are used

## Testing

The security configuration is validated by:

- Infrastructure TDD tests verify controller functionality
- RBAC policies tested against actual SealedSecret processing
- Negative tests confirm unauthorized access is blocked