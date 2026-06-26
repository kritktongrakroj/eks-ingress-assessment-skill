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

**Key insight (and its limits):** Ingress and the new Gateway/ALB resources can *exist* side by side in the cluster — but **coexistence in the cluster ≠ safe gradual traffic shift.** NGINX usually sits behind a Classic/Network Load Balancer (L4); the target is a **new L7 ALB with a different DNS name**. You can only do weighted/gradual DNS shifting if the fronting DNS/LB architecture supports it. If it doesn't, the cutover is effectively **all-or-nothing**, or relies on **very low DNS TTLs** with real risk of **stale-DNS traffic hanging** on the old endpoint. Do **not** rate downtime Low merely because the two resource types can coexist.

**Also check:** does a weighted/blue-green path actually exist (Route 53 weighted records / a shared front door), and what are the current DNS TTLs? If neither, flag the cutover as higher risk.

**Impact (per Impact Indicator):**
- 🟡 1–2 (Low): A real gradual-shift path exists (e.g. Route 53 weighted records or shared front door) **and** DNS automation/low TTL is in place.
- 🟠 3–4 (Medium): Cross-architecture cutover (NGINX/L4 → new L7 ALB) with no proven weighted-shift path — plan a tight, low-TTL cutover window; partial-outage risk.
- 🔴 5 (High): All-or-nothing cutover, no DNS automation, high TTLs, or business-critical hosts — manual DNS changes risk real downtime.
- ⬜ Unknown: Cannot assess DNS/front-door architecture.

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
- **Session affinity / stateful routing** — any Ingress using `nginx.ingress.kubernetes.io/affinity: cookie` (sticky sessions) or otherwise relying on connection/session state.

**How to check:**
1. Confirm old Ingress resources will be kept (not deleted)
2. Check workspace for IaC files managing Ingress resources
3. Check for ArgoCD/Flux managing Ingress resources
4. Scan for `affinity: cookie` / `session-cookie-*` annotations (e.g. `legacy-mirror-sticky`).

> **Sticky sessions break the rollback story.** GitOps revert is not a clean rollback for **stateful/sticky** ingresses: NGINX affinity cookies do not carry to an ALB (ALB uses its own `AWSALB`/`AWSALBCORS` cookie), so switching NGINX↔ALB — including a **rollback** — **drops every in-flight logged-in session**, a direct business impact. The architect must **externalize session state (e.g. Redis/central session store) before** the Ingress migration so traffic can move either direction without dropping users. Flag any sticky-session Ingress as a rollback-readiness risk and require a session-handling plan; rate it Medium+ accordingly.

**Impact (per Impact Indicator):**
- 🟡 1–2 (Low): Ingress resources in Git, GitOps managed, rollback = revert HTTPRoute + keep Ingress
- 🟠 3–4 (Medium): Ingress resources in Git but no GitOps
- 🔴 5 (High): Ingress resources not in version control
- ⬜ Unknown: Cannot determine rollback readiness

### 6.4 — ALB Ingress → Gateway API Translation Blockers

> **Scope:** applies only when routes already use the AWS LB Controller (ALB) Ingress **and** the chosen target is Gateway API (the `lbc-migrate` automated path in `steering/gateway-api.md`). Skip for NGINX-only estates — those are covered by 6.2. All checks are **read-only** (inspect annotations / TG ownership; never modify).

**What to check:**
- **WAF Classic** annotations (`alb.ingress.kubernetes.io/waf-acl-id`, `web-acl-id`) — **not supported** by the Gateway translation; must move to WAFv2 first.
- **`frontend-nlb-*`** annotations — **not supported**; no Gateway equivalent.
- **External Target Group** references in `alb.ingress.kubernetes.io/actions.*` — a TG can be owned by only one ALB; the new Gateway ALB cannot attach a TG still owned by the Ingress ALB.
- **`group.order` / cross-namespace IngressGroup** — rule priority and count differ on the Gateway side; cross-namespace groups require `lbc-migrate --all-namespaces` or the output is incomplete.

**How to check:**
1. Inventory in-use `alb.ingress.kubernetes.io/*` annotations from Section 3.
2. Flag any `waf-acl-id` / `web-acl-id` / `frontend-nlb-*` against the LBC annotation-support list.
3. For `actions.*`, identify whether the referenced TG is an external (pre-existing) TG owned by the current Ingress ALB.
4. Note any IngressGroup spanning multiple namespaces.

**Impact (per Impact Indicator):**
- 🟡 1–2 (Low): No WAF Classic / `frontend-nlb-*` / external-TG / cross-namespace group in use — translation is clean.
- 🟠 3–4 (Medium): WAF Classic or cross-namespace IngressGroup present — resolvable but needs a pre-step (WAFv2 move, namespace-scoped run).
- 🔴 5 (High): External-TG ownership conflict on a live route — needs an ownership/cutover plan before any apply.
- ⬜ Unknown: Cannot inspect annotations / TG ownership.
