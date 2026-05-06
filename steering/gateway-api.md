# Gateway API Readiness

## Purpose
Assess readiness for Kubernetes Gateway API — the migration target. Check CRDs, GatewayClass, controller support, and existing Gateway API resources.

## Context
Gateway API is the official successor to Ingress in Kubernetes. The Ingress resource will not receive new features and is on a deprecation path. AWS Load Balancer Controller v2.7+ supports Gateway API natively via `gateway.networking.k8s.aws/alb` controller name.

## Checks to Execute

### 2.1 — Gateway API CRDs

**What to check:**
- Gateway API CRDs installed (GatewayClass, Gateway, HTTPRoute, ReferenceGrant)
- CRD versions (v1 GA, v1beta1, v1alpha2)
- Whether experimental channel CRDs are installed (GRPCRoute, TCPRoute, TLSRoute)

**How to check:**
1. List CRDs → filter for `*.gateway.networking.k8s.io`
2. Check versions on each CRD
3. Look for: `gatewayclasses`, `gateways`, `httproutes`, `referencegrants`, `grpcroutes`, `tcproutes`, `tlsroutes`

**Rating:**
- 🟢 GREEN: Core CRDs (GatewayClass, Gateway, HTTPRoute, ReferenceGrant) installed at v1
- 🟡 AMBER: CRDs installed but at beta versions, or missing ReferenceGrant
- 🔴 RED: No Gateway API CRDs installed
- ⬜ UNKNOWN: Cannot list CRDs

**If RED — provide install command:**
```bash
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.2.1/standard-install.yaml
```

### 2.2 — AWS Load Balancer Controller (Gateway API Support)

**What to check:**
- AWS LB Controller installed (required as the Gateway API implementation on EKS)
- Version v2.7+ (minimum for Gateway API support)
- IAM configuration (IRSA or Pod Identity)
- Pod health and replica count

**How to check:**
1. Describe Deployment `aws-load-balancer-controller` in kube-system
2. Check image tag for version — must be v2.7+ for Gateway API
3. Check ServiceAccount for IRSA annotation or Pod Identity
4. List EKS add-ons → check for `aws-load-balancer-controller`

**Rating:**
- 🟢 GREEN: v2.7+ installed, healthy, 2+ replicas, IRSA/Pod Identity configured
- 🟡 AMBER: Installed but v2.4-v2.6 (supports Ingress but NOT Gateway API — upgrade needed)
- 🔴 RED: Not installed, or v1.x, or pods unhealthy
- ⬜ UNKNOWN: Cannot determine version

**Critical:** AWS LB Controller < v2.7 does NOT support Gateway API. This is a hard blocker.

### 2.3 — GatewayClass Configuration

**What to check:**
- GatewayClass resources defined
- Controller name: `gateway.networking.k8s.aws/alb` (AWS LB Controller)
- GatewayClass accepted status
- Whether a default GatewayClass exists

**How to check:**
1. List GatewayClass resources (gateway.networking.k8s.io/v1)
2. Check `spec.controllerName` — must be `gateway.networking.k8s.aws/alb` for AWS
3. Check status conditions for `Accepted: True`

**Rating:**
- 🟢 GREEN: GatewayClass defined with AWS controller, status Accepted
- 🟡 AMBER: GatewayClass defined but not yet Accepted, or using third-party controller
- 🔴 RED: No GatewayClass defined
- ⬜ UNKNOWN: Cannot determine controller support

### 2.4 — Gateway API Adoption Status

**What to check:**
- Whether any Gateway API resources already exist (Gateway, HTTPRoute, GRPCRoute)
- If migration has already started (partial adoption)

**Purpose:** Understand the starting point — is this a greenfield Gateway API setup or a partial migration?

**How to check:**
1. List Gateway resources across all namespaces
2. List HTTPRoute resources across all namespaces
3. List GRPCRoute resources across all namespaces

**Rating:**
- 🟢 GREEN: Gateway API already in use — migration partially done
- 🟡 AMBER: CRDs installed but no resources yet — ready to start
- 🔴 RED: No CRDs installed — foundation work needed first
- ⬜ UNKNOWN: Cannot list Gateway API resources

**Note:** RED here is expected for most clusters — it simply means the foundation (CRDs, GatewayClass) needs to be set up as part of the migration plan. This is not a blocker, it's a prerequisite to plan for.
