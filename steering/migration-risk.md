# Migration Risk Assessment

> **Rating model:** Express every finding as **Impact 1–5** using the *Impact Indicator* rubric (security/reputation · business/revenue · nature & effort to remediate). Band mapping is a starting point — GREEN→🟡 1–2, AMBER→🟠 3–4, RED→🔴 5 — but the Impact Indicator criteria set the final score (e.g. an easy-to-deploy prerequisite stays 🟡 low even if it blocks a path). All checks are **read-only** (`kubectl get/describe`, `aws … describe/list`).


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

**Impact (per Impact Indicator):**
- 🟡 1–2 (Low): Low Ingress count, DNS automation in place, coexistence confirmed
- 🟠 3–4 (Medium): High Ingress count makes phased migration complex but still zero-downtime
- 🔴 5 (High): No DNS automation — manual DNS changes during cutover risk downtime
- ⬜ Unknown: Cannot assess traffic patterns

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

**Impact (per Impact Indicator):**
- 🟡 1–2 (Low): All features have Gateway API or AWS service equivalents
- 🟠 3–4 (Medium): Some features need AWS service substitution
- 🔴 5 (High): Critical dependency on features with no equivalent — architecture redesign needed
- ⬜ Unknown: Cannot determine feature gap

### 6.3 — Rollback Readiness

**What to check:**
- Old Ingress resources preserved during migration (don't delete until validated)
- Ingress resources version-controlled (Git)
- GitOps rollback available (ArgoCD/Flux)

**How to check:**
1. Confirm old Ingress resources will be kept (not deleted)
2. Check workspace for IaC files managing Ingress resources
3. Check for ArgoCD/Flux managing Ingress resources

**Impact (per Impact Indicator):**
- 🟡 1–2 (Low): Ingress resources in Git, GitOps managed, rollback = revert HTTPRoute + keep Ingress
- 🟠 3–4 (Medium): Ingress resources in Git but no GitOps
- 🔴 5 (High): Ingress resources not in version control
- ⬜ Unknown: Cannot determine rollback readiness
