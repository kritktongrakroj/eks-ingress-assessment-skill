# Gateway API Readiness

> **Rating model:** Express every finding as **Impact 1–5** using the *Impact Indicator* rubric (security/reputation · business/revenue · nature & effort to remediate). Band mapping is a starting point — GREEN→🟡 1–2, AMBER→🟠 3–4, RED→🔴 5 — but the Impact Indicator criteria set the final score (e.g. an easy-to-deploy prerequisite stays 🟡 low even if it blocks a path). All checks are **read-only** (`kubectl get/describe`, `aws … describe/list`).


## Purpose
Gather the **Gateway API prerequisites** for **Migration Options → Option 1 (Gateway API)**. This is **not a standalone rated section** in the report — `report-generation.md` folds these findings into Option 1 (CRDs, controller version, GatewayClass). Treat "not yet installed" prerequisites as **🟡 Low impact** (easy to deploy), per the Impact Indicator — never as a blocker on their own.

## Context
Gateway API is the official successor to Ingress in Kubernetes. The Ingress resource will not receive new features and is on a deprecation path. AWS Load Balancer Controller supports Gateway API natively — **L4 (TCP/UDP/TLSRoute) ≥ v2.13.3, L7 (HTTPRoute/GRPCRoute) ≥ v2.14** (GA from the 2026 release line) — via the `gateway.k8s.aws/alb` controller name. The LBC targets Gateway API CRDs **v1.3.0**. On **EKS Auto Mode**, Gateway API/load balancing is provided through the `eks.amazonaws.com` API group (built-in) rather than a self-managed LBC.

## Caveats & Risks (MUST surface in Migration Options → Option 1)

Even when the LBC version is sufficient, do **not** present Gateway API as a frictionless drop-in:
- **L7 feature parity is still maturing.** ALB Gateway API (HTTPRoute/GRPCRoute) reached support only in v2.14 and GA in the 2026 line; some **TLS handling and routing-filter** behaviours are not yet at parity with the mature Ingress API. Recommend verifying the specific filters/TLS options each route needs against the installed LBC version **before** committing to a cutover.
- **EKS Auto Mode load-balancer ownership conflict.** If the cluster runs **both** Auto Mode's built-in controller (`eks.amazonaws.com`) **and** a self-managed AWS LB Controller (`gateway.k8s.aws/alb` / `ingress.k8s.aws/alb`) — as `eks-devops-sin` does — two reconcilers can contend for the **same** Gateway/Ingress. Scope ownership explicitly (distinct `GatewayClass`/`IngressClass` per controller) so they don't fight over a load balancer. Flag this whenever both are present.
- **Gateway topology / blast radius.** Do **not** recommend collapsing all teams onto one shared Gateway to "save cost." A single Gateway concentrates blast radius — one team's broken `HTTPRoute` or overload degrades everyone. Recommend **per-security-boundary Gateways** (e.g. a `public-gateway` for general web, a separate `private-gateway` for `team-payments`), accepting extra cost for isolation.

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

**Impact (per Impact Indicator):**
- 🟡 1–2 (Low): Core CRDs (GatewayClass, Gateway, HTTPRoute, ReferenceGrant) installed at v1
- 🟠 3–4 (Medium): CRDs installed but at beta versions, or missing ReferenceGrant
- 🔴 5 (High): No Gateway API CRDs installed
- ⬜ Unknown: Cannot list CRDs

**If RED — provide install command:**
```bash
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.3.0/standard-install.yaml
```

### 2.2 — AWS Load Balancer Controller (Gateway API Support)

**What to check:**
- AWS LB Controller installed (required as the Gateway API implementation on EKS)
- Version **≥ v2.14** for L7 (HTTPRoute/GRPCRoute), **≥ v2.13.3** for L4 (TCP/UDP/TLSRoute)
- IAM configuration (IRSA or Pod Identity)
- Pod health and replica count

**How to check:**
1. Describe Deployment `aws-load-balancer-controller` in kube-system
2. Check image tag — must be **≥ v2.14** (L7) or **≥ v2.13.3** (L4) for Gateway API
3. Check ServiceAccount for IRSA annotation or Pod Identity
4. List EKS add-ons → check for `aws-load-balancer-controller`

**Impact (per Impact Indicator):**
- 🟡 1–2 (Low): v2.14+ installed, healthy, 2+ replicas, IRSA/Pod Identity configured
- 🟠 3–4 (Medium): Installed but < v2.14 (Ingress works; L7 Gateway API needs upgrade)
- 🔴 5 (High): Not installed, or pods unhealthy
- ⬜ Unknown: Cannot determine version

**Critical:** AWS LB Controller **< v2.13 does NOT support Gateway API**, and **L7 (HTTPRoute) requires ≥ v2.14**. On **EKS Auto Mode**, the built-in controller provides Gateway API via the `eks.amazonaws.com` API group instead — no self-managed LBC install needed.

### 2.3 — GatewayClass Configuration

**What to check:**
- GatewayClass resources defined
- Controller name: `gateway.k8s.aws/alb` (AWS LB Controller)
- GatewayClass accepted status
- Whether a default GatewayClass exists

**How to check:**
1. List GatewayClass resources (gateway.networking.k8s.io/v1)
2. Check `spec.controllerName` — must be `gateway.k8s.aws/alb` for AWS
3. Check status conditions for `Accepted: True`

**Impact (per Impact Indicator):**
- 🟡 1–2 (Low): GatewayClass defined with AWS controller, status Accepted
- 🟠 3–4 (Medium): GatewayClass defined but not yet Accepted, or using third-party controller
- 🔴 5 (High): No GatewayClass defined
- ⬜ Unknown: Cannot determine controller support

### 2.4 — Gateway API Adoption Status

**What to check:**
- Whether any Gateway API resources already exist (Gateway, HTTPRoute, GRPCRoute)
- If migration has already started (partial adoption)

**Purpose:** Understand the starting point — is this a greenfield Gateway API setup or a partial migration?

**How to check:**
1. List Gateway resources across all namespaces
2. List HTTPRoute resources across all namespaces
3. List GRPCRoute resources across all namespaces

**Impact (per Impact Indicator):**
- 🟡 1–2 (Low): Gateway API already in use — migration partially done
- 🟡 1–2 (Low): CRDs installed but no resources yet — ready to start
- 🟡 1–2 (Low): No CRDs installed — easy-to-deploy prerequisite (install CRDs + GatewayClass); a planning item, not a blocker
- ⬜ Unknown: Cannot list Gateway API resources

**Note:** Foundation setup (CRDs, GatewayClass) is an easy, low-impact prerequisite per the Impact Indicator — surface it as an Option 1 Phase-1 step, not a high-impact finding.
