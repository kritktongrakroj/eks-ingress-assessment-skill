# Migration Risk Assessment

## Purpose
Evaluate risk of migrating from Ingress to Gateway API.

## Checks to Execute

### 6.1 — Downtime Risk

**What to check:**
- Can Ingress and Gateway API coexist during migration? (yes — different resource types)
- DNS cutover strategy (weighted DNS, blue-green, or instant switch)
- DNS TTL values

**How to check:**
1. Confirm Ingress resources and HTTPRoute resources can coexist (they can — different API groups)
2. Check external-dns configuration for TTL
3. Count active Ingress resources (migration scope)

**Key insight:** Ingress and Gateway API resources are completely independent. You can run both simultaneously — the old Ingress keeps working while you create HTTPRoute equivalents and test them. Cutover is a DNS switch.

**Rating:**
- 🟢 GREEN: Low Ingress count, DNS automation in place, coexistence confirmed
- 🟡 AMBER: High Ingress count makes phased migration complex but still zero-downtime
- 🔴 RED: No DNS automation — manual DNS changes during cutover risk downtime
- ⬜ UNKNOWN: Cannot assess traffic patterns

### 6.2 — Feature Gap Analysis

**What to check:**
- Features used in current Ingress that have no Gateway API equivalent
- Workarounds available via AWS services

**How to check:**
1. Compile annotation inventory from Section 3
2. Map each to Gateway API equivalent or workaround:
   - nginx rate limiting → AWS WAF rate-based rules
   - nginx basic auth → ALB + Cognito/OIDC (Gateway annotation)
   - nginx custom error pages → CloudFront custom error responses
   - nginx modsecurity → AWS WAF managed rules
   - nginx configuration-snippet → ❌ No equivalent (redesign)
   - nginx server-snippet → ❌ No equivalent (redesign)

**Rating:**
- 🟢 GREEN: All features have Gateway API or AWS service equivalents
- 🟡 AMBER: Some features need AWS service substitution
- 🔴 RED: Critical dependency on features with no equivalent — architecture redesign needed
- ⬜ UNKNOWN: Cannot determine feature gap

### 6.3 — Rollback Readiness

**What to check:**
- Old Ingress resources preserved during migration (don't delete until validated)
- Ingress resources version-controlled (Git)
- GitOps rollback available (ArgoCD/Flux)

**How to check:**
1. Confirm old Ingress resources will be kept (not deleted)
2. Check workspace for IaC files managing Ingress resources
3. Check for ArgoCD/Flux managing Ingress resources

**Rating:**
- 🟢 GREEN: Ingress resources in Git, GitOps managed, rollback = revert HTTPRoute + keep Ingress
- 🟡 AMBER: Ingress resources in Git but no GitOps
- 🔴 RED: Ingress resources not in version control
- ⬜ UNKNOWN: Cannot determine rollback readiness
