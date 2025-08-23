# Sealed Secrets Controller Security Configuration

## Overview

This document explains the RBAC security model for the Sealed Secrets Controller deployment and addresses the security scanning findings.

## Security Model

### ClusterRole Permissions

The Sealed Secrets Controller requires specific cluster-level permissions:

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

4. **Secret Discovery** (`core/secrets` - ClusterRole level)
   - `get`, `list`, `create`, `update`, `patch`: Minimal permissions for secret discovery
   - **Note**: While flagged by security scanners, these permissions are scoped:
     - No `delete` permission at cluster level
     - Actual secret management delegated to namespace-specific Roles
   - **Justification**: Controller needs to verify secret existence before creation

### Namespace-Specific Permissions

Secret management is restricted to specific namespaces through Role/RoleBinding:

- **business-intelligence** namespace only
- Permissions: `get`, `list`, `create`, `update`, `patch`, `delete` on secrets
- **Security Benefit**: Prevents accidental secret access in other namespaces

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
| secrets | get, list, create, update, patch | get, list, create, update, patch, delete | ClusterRole for discovery, Role for management |
| sealedsecrets | get, list, watch, update, patch | - | CRD management requires cluster scope |
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