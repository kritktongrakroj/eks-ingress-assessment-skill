# DNS & Certificate Management

## Purpose
Assess DNS automation and TLS certificate management for Gateway API migration.

## Checks to Execute

### 4.1 — external-dns Gateway API Support

**What to check:**
- external-dns Deployment installed
- Source configuration — **must include `gateway-httproute`** for Gateway API migration
- IRSA/Pod Identity for Route 53 access

**How to check:**
1. List Deployments → filter for `external-dns`
2. Check container args for `--source=` values
3. Check ServiceAccount for IRSA annotation

**Critical:** external-dns must be configured with `--source=gateway-httproute` (and optionally `--source=gateway-grpcroute`) to auto-manage DNS for Gateway API resources. If only `--source=ingress` is set, DNS won't work after migration.

**Rating:**
- 🟢 GREEN: external-dns installed with `gateway-httproute` source, IRSA configured
- 🟡 AMBER: external-dns installed but only `ingress` source — needs config update
- 🔴 RED: No external-dns — DNS records managed manually
- ⬜ UNKNOWN: Cannot determine DNS management

### 4.2 — cert-manager Gateway API Integration

**What to check:**
- cert-manager installed and healthy
- Gateway API integration enabled (cert-manager v1.15+ has native Gateway API support)
- ClusterIssuer/Issuer configured

**How to check:**
1. List Deployments → filter for `cert-manager`
2. Check cert-manager version (v1.15+ for Gateway API)
3. Check for `--feature-gates=ExperimentalGatewayAPISupport=true` in controller args (pre-v1.15)
4. List ClusterIssuers → check solver type

**Rating:**
- 🟢 GREEN: cert-manager v1.15+ with Gateway API support, ClusterIssuer ready
- 🟡 AMBER: cert-manager installed but Gateway API feature gate not enabled, or older version
- 🔴 RED: No cert-manager and TLS certs are static K8s Secrets
- ⬜ UNKNOWN: Cannot determine cert management

### 4.3 — ACM Integration

**What to check:**
- Current Ingress resources using ACM certificate ARNs
- ACM certificates available in the account/region
- Gateway API ACM model: certificates referenced on Gateway listener via annotation

**How to check:**
1. Scan Ingress annotations for `alb.ingress.kubernetes.io/certificate-arn`
2. Extract unique ACM ARNs
3. Verify certificates exist and are valid

**Rating:**
- 🟢 GREEN: Using ACM certificates — maps directly to Gateway listener annotations
- 🟡 AMBER: Mix of ACM and K8s Secret certificates
- 🔴 RED: No ACM — all self-managed Secrets
- ⬜ UNKNOWN: Cannot verify ACM certificate status
