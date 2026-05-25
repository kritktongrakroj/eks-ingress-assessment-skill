# Traffic & Routing Complexity

## Purpose
Assess routing complexity and map current patterns to Gateway API HTTPRoute equivalents.

## Checks to Execute

### 5.1 — Routing Pattern Mapping

**What to check:**
- Host-based routing → HTTPRoute `hostnames` field
- Path-based routing → HTTPRoute `matches[].path`
- Default backend → HTTPRoute with no matches (catch-all)
- Complexity per Ingress resource

**How to check:**
1. For each Ingress, count `spec.rules` entries
2. Count unique hosts across all Ingress resources
3. Check path types (Prefix, Exact, ImplementationSpecific)
4. Flag ImplementationSpecific — Gateway API only supports Exact and PathPrefix

**Gateway API mapping:**
- Ingress `spec.rules[].host` → HTTPRoute `spec.hostnames[]`
- Ingress `spec.rules[].http.paths[]` → HTTPRoute `spec.rules[].matches[].path`
- Ingress `Prefix` → HTTPRoute `PathPrefix`
- Ingress `Exact` → HTTPRoute `Exact`
- Ingress `ImplementationSpecific` → ❌ Must be converted to Exact or PathPrefix

**Rating:**
- 🟢 GREEN: Simple host+path routing, all Prefix/Exact — direct HTTPRoute mapping
- 🟡 AMBER: Some ImplementationSpecific paths or regex patterns needing conversion
- 🔴 RED: Heavy regex routing, >20 rules per Ingress, complex rewrite chains
- ⬜ UNKNOWN: Cannot parse routing rules

**Report output format:** In the report's "Current Config" column, show actual config as compact 1-liner:
`Ingress/<name>: <host><path> → <backend>:<port> (<pathType>, TLS:<yes/no>)`
Example: `Ingress/shopping-app: /*→frontend:80 (Prefix, TLS:no)`
Example: `Ingress/nginx-alb: app.example.com/* → nginx-service:80 (Prefix, TLS:ACM)`

### 5.2 — Advanced Traffic Features

**What to check:**
- Canary/weighted routing → HTTPRoute `backendRefs[].weight`
- Header-based routing → HTTPRoute `matches[].headers`
- URL rewriting → HTTPRoute `filters[].urlRewrite`
- Request redirect → HTTPRoute `filters[].requestRedirect`
- Request/response header modification → HTTPRoute `filters[].requestHeaderModifier`
- Authentication → No native Gateway API equivalent (use ALB Cognito/OIDC annotation)
- Rate limiting → No native equivalent (use AWS WAF)
- CORS → No native equivalent (use application-level or WAF)

**How to check:**
1. Scan annotations for advanced features
2. Map each to Gateway API equivalent or workaround
3. Flag features with no equivalent

**Rating:**
- 🟢 GREEN: Features used have direct HTTPRoute equivalents (weighted routing, header matching, rewrites)
- 🟡 AMBER: Some features need AWS service substitution (WAF for rate limiting, Cognito for auth)
- 🔴 RED: Critical dependency on nginx lua/snippets with no Gateway API path
- ⬜ UNKNOWN: Cannot determine feature usage

### 5.3 — Cross-Namespace Routing

**What to check:**
- Ingress resources referencing services in other namespaces
- Gateway API model: cross-namespace routing requires explicit ReferenceGrant
- Service mesh integration (Istio, Linkerd)

**How to check:**
1. Check Ingress backends for cross-namespace references
2. List Services of type ExternalName
3. Check for Istio VirtualService / Linkerd ServiceProfile CRDs

**Rating:**
- 🟢 GREEN: All routing within same namespace — straightforward HTTPRoute conversion
- 🟡 AMBER: Some cross-namespace routing — need to create ReferenceGrant resources
- 🔴 RED: Heavy service mesh integration — Gateway API migration must coordinate with mesh
- ⬜ UNKNOWN: Cannot determine cross-namespace routing

**Topology data to collect:** Record all routing patterns, hosts, paths, and features for the 3D visualization.
