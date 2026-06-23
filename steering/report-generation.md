# Report Generation

## Purpose

Generate dual-format assessment report matching the 5-section navigation structure:
**Overview → Assessment Summary → Routing Topology → Migration Approach → Analysis**

This is an **assessment report** — present findings and options, do not prescribe a single migration path.

## Step 1: Build Master Finding List & Calculate the Migration Difficulty Score

### 1.1 — Build the Master Finding List

Compile ALL findings from sections 1–7. Every item must appear. No item may be skipped. Each finding already carries an **Impact 1–5** (per the Impact Indicator rubric). This list is the single source of truth for the score — every point deducted MUST trace back to exactly one row here.

### 1.2 — What the score means

The **Migration Difficulty Score** is a **0–100** number where **high = easy/low-risk to migrate off NGINX** and **low = hard / high business impact**. It is a *deduction model*: start at 100, subtract points for each rated finding, then apply a hard-blocker override. It does NOT pick a migration path — it tells the reader how much effort and risk leaving NGINX entails.

### 1.3 — Map each finding to a scoring category

Every finding belongs to exactly one category. Categories are weighted by a **max deduction cap** — the cap is how much that dimension can drag down "ease of migration".

| Category | Max deduction | Findings that feed it (source sections) |
|----------|--------------|-----------------------------------------|
| Feature-Gap (untranslatable annotations) | 30 | Annotations with no faithful ALB/Gateway-API equivalent — CORS, rate-limit, `auth-url`/`auth-snippet`, `configuration-snippet`/`server-snippet`/Lua, ModSecurity, regex rewrite with capture groups (Ingress Resource Analysis, Traffic & Routing, Blockers) |
| Routing Complexity | 20 | Regex paths, `rewrite-target`, canary/traffic-split, header/method routing, mirroring, cross-namespace fan-out (Traffic & Routing, Routing Topology) |
| TLS & Certificates | 15 | cert-manager→ACM move, SNI, mTLS client-cert, TLS passthrough (DNS & Certificates Analysis) |
| DNS Cutover & Blast Radius | 15 | New ALB endpoint + DNS repoint, external-dns Gateway-API source maturity, hostname/TTL stability (DNS & Certificates Analysis, Migration Risk) |
| Downtime / Rollback Readiness | 10 | New-LB provisioning, long-lived/stateful connections, presence of a weighted/blue-green rollback path (Migration Risk) |
| Controller Health & EOL/CVE | 10 | NGINX version EOL, active CVE exposure, controller pod health (Ingress Discovery) |
| Scale / Volume | 10 | Count of Ingress resources, namespaces, owning teams = raw effort (Ingress Discovery, Routing Topology) |
| Backend Compatibility | 5 | Exotic backends, `ExternalName`, service-type edge cases (Ingress Resource Analysis) |

Caps deliberately sum to 115 (over-provisioned) so a genuinely messy cluster floors toward 0.

### 1.4 — Scoring algorithm (deterministic — follow EXACTLY)

```
# Per-finding base points by Impact (reuse the rating you already assigned)
def base_points(impact):
    return {5: 10, 4: 6, 3: 4, 2: 2, 1: 1}[impact]   # Unknown (⬜) = 0 pts, but list it

score = 100
for each category:
    cat_deduction = 0
    for each finding in this category:
        cat_deduction += base_points(finding.impact)
    cat_deduction = min(cat_deduction, category_cap)   # apply the per-category cap
    score -= cat_deduction
score = max(0, score)

# --- Hard-Blocker Override (apply AFTER arithmetic) ---
# Any blocker => migration needs re-architecture / approval => cap at 59 (VERY HARD).
# A hard blocker is ALWAYS an Impact-5 finding, but not every Impact-5 is a hard blocker.
has_hard_blocker = False
if any production route uses an NGINX feature with NO ALB/Gateway-API equivalent
   AND no documented workaround (Lua/snippet/mirror/regex-capture-rewrite):  has_hard_blocker = True
if TLS passthrough OR mTLS client-cert termination is required
   AND the target path cannot honor it without redesign:                     has_hard_blocker = True
if cross-namespace / shared-LB routing cannot be expressed without ownership
   changes (Gateway API ReferenceGrant gap) for a production route:          has_hard_blocker = True
if a revenue-critical hostname cutover has no rollback path
   (single hostname, no weighted / blue-green option):                       has_hard_blocker = True
if the controller is EOL with an active exploitable CVE
   AND no maintenance window is available:                                   has_hard_blocker = True
if EKS Auto Mode managed load-balancing AND a self-managed AWS LB Controller
   both run and race for ownership (must be reconciled first):               has_hard_blocker = True

if has_hard_blocker:
    score = min(score, 59)
```

### 1.5 — Score interpretation

| Score | Label | Meaning |
|-------|-------|---------|
| 90–100 | **TRIVIAL** | Mechanical — ALB Controller / ATX auto-converts; hours |
| 80–89 | **EASY** | Minor manual tweaks |
| 70–79 | **MODERATE** | Several features need manual mapping; plan it |
| 60–69 | **HARD** | Significant feature gaps or risky cutover |
| 0–59 | **VERY HARD / RE-ARCHITECT** | Blocker(s) — needs redesign or approval |

### 1.6 — Build the Score Breakdown table (MANDATORY)

Before writing the headline number, produce this table so the math is auditable. Sum `base_points` per category, apply the cap, and the row order is highest-deduction first. The **Total** row must equal `100 − score` (pre-override). If a hard blocker fired, add a final line stating the override.

```
| Category | Findings | Raw pts | Capped | Cap |
|----------|----------|---------|--------|-----|
| Feature-Gap | snippet on /checkout (5), CORS on api (4) | 16 | 16 | 30 |
| Routing Complexity | rewrite-target ×3 (3) | 4 | 4 | 20 |
| ... | ... | ... | ... | ... |
| **Total deductions** | | | **-XX** | |
```

Then: `Score = 100 − (total capped deductions) = XX`. If `has_hard_blocker`, append: `Hard blocker (<which>) → score capped at 59 (VERY HARD / RE-ARCHITECT).`

### 1.7 — Worked example

Findings: `configuration-snippet` Lua on the checkout route (Impact 5, Feature-Gap, no equivalent → also a hard blocker), `rewrite-target` regex on 3 routes (Impact 3, Routing), cert-manager→ACM move (Impact 3, TLS), 40 ingresses across 6 teams (Impact 4, Scale), NGINX 1.9.x EOL no active CVE (Impact 3, Controller).

```
Feature-Gap:  10  (cap 30)
Routing:       4  (cap 20)
TLS:           4  (cap 15)
Scale:         6  (cap 10)
Controller:    4  (cap 10)
Σ = 28  →  score = 100 − 28 = 72  (MODERATE)

Hard blocker: checkout uses a Lua snippet with no equivalent and no workaround → TRUE
score = min(72, 59) = 59  →  VERY HARD / RE-ARCHITECT
```

The Lua block alone makes this a re-architecture job even though the arithmetic said "moderate" — that is the entire purpose of the override.

## Step 2: Consistency Checks (MANDATORY)

| Check | Fix |
|-------|-----|
| High-impact (5) item missing from Blockers table | Add it |
| Medium-impact item missing from Recommendations table | Add it |
| Executive Summary mentions wrong rating | Fix to match master list |
| Prose paragraph that should be a table | Convert to table |
| Raw YAML in findings (not Migration Approach) | Replace with summary |
| Score Breakdown total ≠ (100 − score) | Recompute — the table is the source of truth |
| Hard blocker present but score > 59 | Apply the override — cap at 59 |
| Headline `[[SCORE:nn:LABEL]]` band ≠ the 1.5 table | Fix the label to match the number |

## Step 3: Write Topology JSON

Save to `~/ingress_migration/<cluster>/topology.json`. Include nodes (EC2 instances).

## Step 4: Write Markdown Report

**Filename:** `~/ingress_migration/<cluster>/report.md`

### Content Rules (MANDATORY)

1. **Use tables for all structured data.** Never write lists of facts as prose.
2. **No ID column in any table.** Remove all "ID" columns — they add no value for the reader.
3. **No raw YAML/config in findings.** YAML belongs only in Migration Approach.
4. **Every finding cell: max 2 sentences.**
5. **No filler text.** Go straight to content.
6. **One Migration Difficulty Score (0–100), derived only from the rated findings.** It is a deterministic roll-up of the per-finding Impact ratings (see Step 1), shown once on the Overview page — not a separate prescriptive verdict. The migration-path decision still belongs to the team. Do NOT invent ad-hoc per-section sub-scores.
7. **No ASCII art diagrams.** The HTML has the 3D routing diagram.
8. **Multi-value cells in tables:** put each item on its own line using `<br>` (the renderer turns this into real line breaks). For **Current Configuration**, use nested bullet/sub-bullet lists instead of a table.
9. **Executive Summary = one-shot understanding for a non-technical reader.** Top-level bullet per impact theme, indented sub-bullets for specifics. Bold the key term in each bullet; wrap the most damaging facts in `!! !!` (renders red).
10. **Emphasis syntax (supported by the renderer):** `**bold**` for key terms, `!!red highlight!!` for high-impact / at-risk items, backticks for `versions/code`. Use sparingly — only words that carry the impact.
11. **Lead with impact.** Order Executive Summary bullets and Assessment Summary rows from highest impact to lowest.
12. **Download buttons (renderer tokens):** drop `[[DL:gateway-api]]`, `[[DL:alb]]`, `[[DL:atx]]`, or `[[DL:current]]` anywhere in the markdown — the renderer replaces each with a one-click download button for that option's combined routing config (built from the exported manifests). Prefer a download button over printing long target/current config text.
13. **In-page anchor links:** write `[blocker](#blockers)` to link to a section — the renderer auto-scopes the anchor to the cluster (e.g. `#c0-blockers`). Use this wherever the text says "see Blockers".
14. **Impact everywhere, by the rubric:** Assessment Summary, Ingress Discovery, Routing Topology, Traffic & Routing, Blockers, Recommendations, Ingress Resource Analysis, DNS & Certificates Analysis, Migration Risk all use the **Impact 1–5** scale (🟡1-2 / 🟠3-4 / 🔴5) — never GREEN/AMBER/RED. Every score MUST be justified against the **Impact Indicator** rubric (security/reputation · business/revenue · nature & effort), not ad-hoc judgement. Note: easy-to-deploy prerequisites (e.g. installing CRDs) are LOW even if they block a path.

### Report Template (follow EXACTLY)

```markdown
# EKS Ingress Migration Assessment Report

| Information | Value |
|-------------|-------|
| Cluster | [name] |
| Region | [region] |
| Kubernetes Version | [version] |
| Account ID | [account-id] |
| Assessment Date | [YYYY-MM-DD HH:MM] |

---

## Migration Difficulty Score

> Place this as the first authored section on the Overview page (the renderer injects the 3D Routing Diagram just above it, so the rendered flow is: cluster info → 3D diagram → this score → Executive Summary). The headline is the `[[SCORE:nn:LABEL]]` token — the renderer turns it into a colored gauge (green = easy, red = hard). `nn` is the 0–100 number from Step 1; `LABEL` is the band (TRIVIAL/EASY/MODERATE/HARD/VERY HARD). One sentence states the bottom line, then the Score Breakdown table makes the math auditable.

[[SCORE:72:MODERATE]]

[One sentence: how hard is leaving NGINX for this cluster, and the single biggest driver. If a hard blocker fired, say so here.]

### Score Breakdown

| Category | Findings | Deduction | Cap |
|----------|----------|-----------|-----|
| [highest-deduction category] | [finding (impact), …] | -X pts | [cap] |
| [next] | [...] | -X pts | [cap] |
| **Total deductions** | | **-X pts** | **Score: XX% — [LABEL]** |

> If a hard blocker fired, add a row below the total: `Hard-blocker override | [which blocker] | score capped at 59 | VERY HARD`.

---

## Executive Summary

> Write for a non-technical / low-tech reader — one glance must answer "how risky is this and why." Lead with the biggest impact. **Bold** the key noun in each bullet; wrap the most damaging facts in `!! !!` so they render red. Split any bullet that lists multiple items into indented sub-bullets.

- **Ingress controllers:** [N] in use — !![the single biggest risk, e.g. one is End-of-Life with known CVEs]!!
  - [Controller A] `vX` (modern)
  - [Controller B] `vX` (modern)
  - [Controller C] `vX` !!(EOL / unsupported)!!
- **Biggest migration blocker:** !![the one thing most preventing a clean migration]!! — [one phrase why]
- **Conversion effort:** [N] Ingress resources — [X] convert cleanly, !![Y] need redesign!! ([features with no Gateway API equivalent])
- **Scope:** [namespaces] namespaces, [hosts] hosts, TLS [partial — X of Y]

---

## Impact Indicator

> Place this rubric **before Assessment Summary** (Overview group). EVERY Impact score in the report MUST follow it — do not invent ad-hoc severities. Impact weighs three dimensions: security/reputation, business/revenue, and nature & effort to remediate; score the dominant one. Render as a table, one row per band, each cell a bullet list.
>
> **Execution risk counts — do NOT score by YAML-edit size.** A small manifest change can still be high-impact. Specifically: changing `ingressClassName` to a *different controller* (e.g. nginx→alb) **provisions a brand-new load balancer** and only takes traffic after a **DNS cutover** (it is a parallel-run + cutover, not a no-op edit); moving a feature that has **no faithful equivalent** (CORS, rate-limit, external auth) to WAF/app usually needs **application/code changes**; and any TLS/cert-store change done together with routing changes risks **SSL handshake errors / downtime**. Score these by the operational risk, not the diff size.

| Impact | Meaning |
|--------|---------|
| 🟡 1–2 Low | - **Security:** hardening gap, no business-effective breach (e.g. a secret kept in-cluster, not in a secrets manager)<br>- **Business:** no revenue loss / downtime / lost transactions<br>- **Nature:** optional "should/may-do" best practice (reliability / automation)<br>- **Effort:** hours–1 day, one person, single service or route, no impact to business flows |
| 🟠 3–4 Medium | - **Security:** breach with limited reputation / trust loss (weigh likelihood & history)<br>- **Business:** revenue loss limited to short downtime<br>- **Nature:** tech debt / weak design, hard to reverse, costly to fix later<br>- **Effort:** scoped to part / an area or one cluster — not all flows |
| 🔴 5 High | - **Security:** breach with major loss or reputational damage (weigh likelihood & history)<br>- **Business:** significant revenue loss or prolonged downtime<br>- **Nature & Effort:** needs re-design / re-architecture, maybe business or provider approval. *If large but straightforward to deploy → rate medium-to-low.* |

---

## Assessment Summary

> Rate each theme by **migration Impact 1–5**, highest first. Impact = how hard/risky it is to **transfer or replace that feature** versus the current NGINX/Ingress setup, plus the effort to change.
> Do **NOT** rate trivial "is X installed" prerequisites the customer already knows (e.g. "Gateway API CRDs not installed") — rate the **feature transfer/replacement difficulty** instead.
> Color bands: **1–2 = 🟡 low**, **3–4 = 🟠 medium**, **5 = 🔴 high**.

| Theme | Impact | Why — feature transfer / replacement effort vs. current setup |
|-------|--------|----------------------------------------------------------------|
| [highest-impact theme] | 🔴 5 | [which feature can't transfer cleanly + replacement effort] |
| [next] | 🟠 4 | [...] |
| [next] | 🟠 3 | [...] |
| [next] | 🟡 2 | [...] |
| [lowest] | 🟡 1 | [...] |

> Rows are themes framed as "how hard to replace", e.g.: NGINX snippet/auth/mirror features → no Gateway API equivalent; controller currency (EOL vs modern); TLS/cert model (K8s Secret vs ACM); routing complexity (regex/rewrite); canary/traffic-split portability. Order strictly by Impact descending.

---

## Current Configuration

## Current Configuration

> Goal: convey the environment at a glance. Use a bullet list. For any value with multiple items (controllers, namespaces), use indented **sub-bullets** — never a comma list or a raw `<br>`.

- **Ingress controllers:**
  - [controller-a] `vX` (modern)
  - [controller-b] `vX` (modern)
  - [controller-c] `vX` !!(EOL)!!
- **Controller namespaces:**
  - [ns1]
  - [ns2]
- **Total Ingress resources:** [count]
- **Namespaces with Ingress:**
  - [ns1]
  - [ns2]
- **Routing pattern:** [host-based / path-based / both]
- **TLS enabled:** [partial — X of Y]
- **Load balancer types:** [ALB / NLB / ClusterIP]
- **Nodes:** [count] — [instance types]

---

## Ingress Discovery

| Item | Impact | Current State | Recommendation |
|------|--------|---------------|----------------|
| Ingress Controllers Installed | [🟡1-2 / 🟠3-4 / 🔴5] | [summary] | [action or "None required"] |
| IngressClass Resources | [impact] | [summary] | [action or "None required"] |
| Ingress Resource Inventory | [impact] | [summary] | [action or "None required"] |

---

## Routing Topology

> Keep this table narrow so it fits. Combine host+path into one **Route** column, backend+port into **Backend:Port**, TLS as ✓/—, and add a per-route **Impact** (1–5). Omit a shared host suffix (note it above the table). Use `<br>` for multi-backend cells.

| Ingress | NS | Controller | Route (host · path) | Backend:Port | TLS | Impact |
|---------|----|------------|---------------------|--------------|-----|--------|
| [name] | [ns] | [controller] | [host · path] | [svc:port] | [✓/—] | [impact] |

---

## Traffic & Routing

| Item | Impact | Current Config | Recommendation |
|------|--------|----------------|----------------|
| Routing Pattern Mapping | [impact] | [[DL:current]] | [action] |
| Advanced Traffic Features | [impact] | [[DL:current]] | [action] |
| Cross-Namespace Routing | [impact] | [[DL:current]] | [action] |

> **Current Config column:** use the `[[DL:current]]` download button (the current manifests are already exported) rather than printing long config strings.

---

## Migration Options

> Three migration paths. **Every option uses the same layout** (apply Option 1 as the template):
> 1. an **info panel** (blockquote): `> **What:** … · **Effort:** Low/Medium/High · **Best when:** …` then a second line `> **Routing config:** [[DL:<token>]]`
> 2. aligned **Phase 1 — Foundation / Phase 2 — Convert & Test / Phase 3 — Cutover / Phase 4 — Cleanup**, each a `| Step | Action |` table with numbered steps.
> Do NOT print verbose target config — the `[[DL:*]]` button downloads it. Where a route can't convert, link `(see [blocker](#blockers))`.
> No summary/intro blockquote above the options — send the reader straight into Option 1 so they engage with the steps.

### Option 1: Gateway API

> **What:** Kubernetes-native successor to Ingress (HTTPRoute + Gateway). · **Effort:** Medium · **Best when:** you want the long-term standard.
> **Routing config:** [[DL:gateway-api]]
> **Caveats:** L7 ALB Gateway API support is recent (HTTPRoute ≥ v2.14, GA 2026 line) — verify TLS handling and routing filters per route before cutover. On **EKS Auto Mode** running a self-managed LBC too, scope `GatewayClass`/`IngressClass` per controller to avoid !!load-balancer ownership conflicts!!.

#### Phase 1 — Foundation
| Step | Action |
|------|--------|
| 1 | Install Gateway API CRDs |
| 2 | Verify/upgrade AWS LB Controller (**≥ v2.14** for L7 Gateway API; not needed on Auto Mode) |
| 3 | Create GatewayClass |
| 4 | Create Gateway per listener group |

#### Phase 2 — Convert & Test
| Step | Action |
|------|--------|
| 1 | Generate HTTPRoutes from current Ingress (download config above) |
| 2 | Apply low-risk routes first; validate routing, TLS, health |
| 3 | Routes with no equivalent (snippets/auth/mirror) — redesign (see [blocker](#blockers)) |

#### Phase 3 — Cutover
| Step | Action |
|------|--------|
| 1 | Shift DNS to the Gateway ALB (weighted) |
| 2 | Watch 5xx / latency |
| 3 | Confirm all HTTPRoutes `Accepted=True` |

#### Phase 4 — Cleanup
| Step | Action |
|------|--------|
| 1 | Delete migrated Ingress resources |
| 2 | Remove old controllers |
| 3 | Remove unused IngressClasses |

> Options 2 (ALB) and 3 (ATX) follow the identical panel + Phase 1–4 structure, each with its own `[[DL:alb]]` / `[[DL:atx]]` button. Keep the ALB annotation-conversion table and the ATX "What ATX Converts" table as reference sub-sections under their options.

#### Phase 3: Traffic Cutover

| Step | Action | Validation |
|------|--------|-----------|
| 1 | Update DNS to Gateway LB | [how to verify] |
| 2 | Monitor error rates | [what to watch] |
| 3 | Confirm all routes healthy | [check command] |

#### Phase 4: Cleanup

| Step | Action |
|------|--------|
| 1 | Delete old Ingress resources |
| 2 | Remove old controller |
| 3 | Remove unused IngressClass |

---

### Option 2: AWS Load Balancer Controller (ALB Ingress)

Stay on the Ingress API but swap NGINX annotations for ALB annotations. Gets you WAF, Cognito/OIDC, Shield integration without adopting Gateway API.

**When to choose:** Team not ready for Gateway API, needs ALB features immediately, or has many Ingress resources to convert quickly.

#### Annotation Conversion Summary

| NGINX Annotation | ALB Equivalent |
|-----------------|----------------|
| `ingressClassName: nginx` | `ingressClassName: alb` |
| `nginx...rewrite-target: /$2` | `alb...transforms.<svc>` (url-rewrite JSON) |
| `spec.tls[].secretName` | `alb...certificate-arn` or `certificate-discovery: "true"` |
| `nginx...ssl-redirect: "true"` | `alb...ssl-redirect: "443"` |
| `nginx...proxy-read-timeout` | `alb...target-group-attributes: idle_timeout.timeout_seconds=N` |
| `nginx...auth-url` | `alb...auth-type: oidc` + `auth-idp-oidc` JSON |
| `nginx...enable-cors` | Remove — use AWS WAF or app-level |
| `nginx...whitelist-source-range` | `alb...scheme: internal` + security groups |
| `nginx...proxy-body-size` | Remove — app-level config |

#### Migration Steps

| Step | Action | Validation |
|------|--------|-----------|
| 1 | Install AWS LB Controller **v2.7.2+** (ALB Ingress); not needed on EKS Auto Mode | `kubectl get deploy -n kube-system aws-load-balancer-controller` |
| 2 | Provision ACM certificates | `aws acm list-certificates` — all ISSUED |
| 3 | Convert annotations per mapping above | `kubectl apply --dry-run=client -f <file>` |
| 4 | Deploy migrated Ingress (new ALB created) | `kubectl get ingress -A` shows ALB address |
| 5 | DNS weighted routing: shift traffic CLB→ALB | `dig <host>` resolves to new ALB |
| 6 | Remove NGINX controller + orphaned TLS Secrets | `kubectl delete deploy -n ingress-nginx ingress-nginx-controller` |

#### Per-Ingress Conversion Table

| Ingress | Namespace | Key Changes | Complexity |
|---------|-----------|-------------|-----------|
| [name] | [ns] | [e.g., "rewrite→transforms, TLS→ACM"] | [Low/Medium/High] |

> **Manifests exported to:** `<cluster>-manifests/target/alb/`

---

### Option 3: AWS Transform (ATX) — Automated

For customers with AWS Transform access — fully automated manifest rewriting. ATX reads the included Transform Definition and converts all NGINX Ingress manifests to ALB annotations automatically.

**When to choose:** Many Ingress resources (>10), want consistent automated output, have ATX workspace access.

#### How It Works

| Step | Action | Who |
|------|--------|-----|
| 1 | Upload TD from `atx/td_ingress-nginx-lbc/transformation_definition.md` | You |
| 2 | Point ATX at your Ingress manifest repository | You |
| 3 | ATX scans, converts, validates automatically | ATX |
| 4 | Review diff and merge | You |
| 5 | Deploy + DNS cutover | You |

#### What ATX Converts

| Pattern | Before (NGINX) | After (ALB) |
|---------|----------------|-------------|
| IngressClass | `nginx` | `alb` |
| URI Rewrite | `rewrite-target` + regex | `transforms.<svc>` JSON |
| TLS | K8s Secrets | ACM `certificate-arn` |
| Auth | `auth-url` | `auth-type: oidc` |
| CORS | `enable-cors` | Removed (WAF/app) |
| Internal | `whitelist-source-range` | `scheme: internal` |

#### ATX Validation (Automatic)

- ✅ No `ingressClassName: nginx` remains
- ✅ No `nginx.ingress.kubernetes.io/*` annotations
- ✅ All rewrites use valid `transforms.<svc>` JSON
- ✅ All TLS ingresses have ACM + ssl-redirect + ssl-policy
- ✅ `kubectl apply --dry-run=client` passes

> **TD location:** `atx/td_ingress-nginx-lbc/transformation_definition.md`
> **Contact:** AWS account team for ATX workspace onboarding

---

## Blockers

> Lives under **Migration Approach** (not Analysis). Finding name only — no "— RED" suffix. **Impact 1–5** (🟡1-2 / 🟠3-4 / 🔴5). **Action Required** is a bullet list — use `- item<br>  - sub-item` for sub-bullets. No Effort column (manday effort depends on team experience and can't be fixed reliably).

| Finding | Impact | Action Required |
|---------|--------|-----------------|
| [finding name] | [🔴 5] | - [action]<br>  - [sub-action] |

> If no high-impact items exist, write: "No blockers identified."

---

## Recommendations

> Lives under **Migration Approach**. **Impact 1–5** = how disruptive *implementing* the action is to the running app / production (🟡1-2 / 🟠3-4 / 🔴5). No Effort column.

| Finding | Action | Priority | Impact |
|---------|--------|----------|--------|
| [finding name] | [specific action] | [High/Medium/Low] | [🟡/🟠/🔴 n] |

---

## Ingress Resource Analysis

> **Impact 1–5** = severity *if left as-is* (not migrated). Usually low/medium — the app keeps running on NGINX today (🟡1-2 / 🟠3-4 / 🔴5). **Recommendation** is a bullet list (`- item<br>  - sub-item`). No Reference column.

| Item | Impact | Current State | Recommendation |
|------|--------|---------------|----------------|
| Annotation Inventory & Mapping | [impact] | [summary] | - [action]<br>  - [sub-action] |
| TLS Configuration | [impact] | [summary] | - [action] |
| Backend Service Compatibility | [impact] | [summary] | - [action] |

---

## DNS & Certificates Analysis

> Same approach as Ingress Resource Analysis: **Impact 1–5** if left as-is (usually low — DNS/TLS still serve today), bullet **Recommendation**.

| Item | Impact | Current State | Recommendation |
|------|--------|---------------|----------------|
| external-dns Gateway API Support | [impact] | [summary] | - [action] |
| cert-manager Gateway Integration | [impact] | [summary] | - [action] |
| ACM Integration | [impact] | [summary] | - [action] |

---

## Migration Risk

| Item | Impact | Current State | Recommendation |
|------|--------|---------------|----------------|
| Downtime Risk | [impact] | [summary] | - [action] |
| Feature Gap Analysis | [impact] | [summary] | - [action] |
| Rollback Readiness | [impact] | [summary] | - [action] |

---

## AWS Reference Links

| Topic | URL |
|-------|-----|
| Gateway API on EKS | https://docs.aws.amazon.com/eks/latest/userguide/gateway-api.html |
| AWS Load Balancer Controller | https://kubernetes-sigs.github.io/aws-load-balancer-controller/ |
| Gateway API Specification | https://gateway-api.sigs.k8s.io/ |
| HTTPRoute API Reference | https://gateway-api.sigs.k8s.io/api-types/httproute/ |
| Gateway API Migration Guide | https://gateway-api.sigs.k8s.io/guides/migrating-from-ingress/ |
| external-dns Gateway API | https://kubernetes-sigs.github.io/external-dns/latest/sources/gateway-api/ |
| cert-manager Gateway API | https://cert-manager.io/docs/usage/gateway/ |
| EKS Best Practices | https://docs.aws.amazon.com/eks/latest/best-practices/ |
| EKS User Guide | https://docs.aws.amazon.com/eks/latest/userguide/ |
```

Do NOT fabricate URLs beyond this list.

**Section placement in nav:**
- **Overview:** Information table, **3D Routing Diagram** (injected by the renderer), **Migration Difficulty Score** (headline gauge + Score Breakdown), Executive Summary, Impact Indicator (rubric, just before Assessment Summary)
- **Assessment Summary:** Assessment Summary table, Current Configuration, Ingress Discovery
- **Routing Topology:** Routing Topology table, Traffic & Routing
- **Migration Approach:** Migration Options (Option 1: Gateway API, Option 2: ALB Controller, Option 3: ATX — same panel + Phase 1–4 layout), **Blockers**, **Recommendations**
- **Analysis:** Ingress Resource Analysis, DNS & Certificates Analysis, Migration Risk
- **References:** **Export Materials** (the generated manifests + download buttons, rendered by the tool), then **AWS Reference Links**

Note: There is **no Migration Planning section** (scope/complexity/timeline fold into Migration Options and Blockers) and **no Investigate Manually section**. Blockers/Recommendations live under **Migration Approach**. The former "Appendix" is **Analysis**. **Export Materials** and **AWS Reference Links** live under **References** (Export Materials first). Gateway API Readiness is folded into Migration Options, not a standalone section.

## Step 5: Generate HTML Report

After ALL cluster markdown reports are written, generate a **single combined HTML**:

```bash
# Single cluster
python3 tools/report_to_html.py \
  ~/ingress_migration/<cluster>/report.md \
  --topology ~/ingress_migration/<cluster>/topology.json \
  --manifests ~/ingress_migration/<cluster>/manifests

# Multiple clusters — one HTML with cluster dropdown
python3 tools/report_to_html.py \
  ~/ingress_migration/cluster-a/report.md ~/ingress_migration/cluster-b/report.md \
  --topology ~/ingress_migration/cluster-a/topology.json ~/ingress_migration/cluster-b/topology.json \
  --manifests ~/ingress_migration/cluster-a/manifests ~/ingress_migration/cluster-b/manifests \
  -o ~/ingress_migration/EKS-Ingress-Migration-<YYYY-MM-DD>-<HHMM>.html
```

Do NOT generate HTML manually. Always use the script.

## Step 6: Export Materials

> **Directory contract (required by `report_to_html.py`):** lay manifests out as `current/`, `target/gateway-api/`, and `target/alb/` under the cluster's `manifests/` dir. The renderer recursively loads these subtrees (`rglob`) and powers the `[[DL:current]]` / `[[DL:gateway-api]]` / `[[DL:alb]]` download buttons — a flat `target/*.yaml` layout will not be found.

After generating the HTML report, export manifest files for each cluster:

**Output directory:** `~/ingress_migration/<cluster>/manifests/`

```
~/ingress_migration/
├── <cluster>/
│   ├── report.md                              # Cluster markdown report
│   ├── topology.json                          # Topology data for 3D view
│   └── manifests/
│       ├── current/                           # Existing Ingress resources (clean YAML)
│       │   └── <namespace>-<ingress-name>.yaml
│       └── target/
│           ├── gateway-api/                   # Gateway API resources (apply order)
│           │   ├── 00-gateway-api-crds.yaml
│           │   ├── 01-gatewayclass.yaml
│           │   ├── 02-gateway.yaml
│           │   ├── 03-httproute-<name>.yaml
│           │   └── 04-referencegrant-<name>.yaml  # Only if cross-namespace
│           └── alb/                           # ALB Controller Ingress (converted)
│               └── <namespace>-<ingress-name>.yaml
├── EKS-Ingress-Migration-<YYYY-MM-DD>-<HHMM>.html  # Combined HTML (all clusters)
└── ...
```

**Rules:**
1. `current/` — Extract each Ingress resource as YAML. Strip `status`, `managedFields`, `resourceVersion`, `uid`, `creationTimestamp`, `generation`. Keep only `apiVersion`, `kind`, `metadata.name`, `metadata.namespace`, `metadata.annotations`, `metadata.labels`, `spec`.
2. `target/gateway-api/` — Generate Gateway API manifests based on assessment findings. Number-prefix for apply order. Include comments explaining what each resource does.
3. `target/alb/` — Generate ALB Controller Ingress manifests by applying the annotation mapping from `steering/alb-migration.md`. Each file mirrors the original Ingress but with ALB annotations.
4. The `00-gateway-api-crds.yaml` file should contain only a comment with the install command — not the actual CRD content.
5. All manifests must be valid YAML that can be applied with `kubectl apply -f`.
6. **Snippet / blind-spot safety (CRITICAL):** if any source Ingress uses `configuration-snippet`/`server-snippet`/`modsecurity-snippet` (or §5.5 found snippet-injected routes), the generated target manifests are **incomplete** — they cannot represent snippet-injected `location`s (e.g. `/healthz`, deny `/internal/`). For every such Ingress you MUST:
   - **Not** generate a silently-apply-ready target; instead emit a placeholder containing a prominent header comment `# INCOMPLETE — snippet-injected routes not represented; hand-port before applying` listing the missing paths/behaviours.
   - Replace rule 7's wording for affected files with **"review & hand-port — DO NOT blind-apply"**. Blind-applying would drop health-check paths and access-control denies, breaking probes and exposing internal paths.
7. Inform the user: "Manifests exported to `~/ingress_migration/<cluster>/manifests/`. Files for snippet-free ingresses are apply-ready (`kubectl apply -f …`); files flagged **INCOMPLETE** require manual hand-porting of snippet-injected routes first."
8. **Controller-ownership pre-apply gate (CRITICAL on EKS Auto Mode):** if the cluster runs **both** EKS Auto Mode's built-in load balancing **and** a self-managed AWS LB Controller, the exported manifests MUST carry a blocking warning: *"Do NOT apply until controller ownership is reconciled."* Two reconcilers will **race** for the same AWS resources (port/target-group/IP binding locks, duplicate work, broken networking). The user must first choose **one** owner — either (a) remove the self-managed LBC and use Auto Mode managed load balancing, or (b) disable Auto Mode's load-balancing capability and let the Helm-installed LBC own everything — and scope `IngressClass`/`GatewayClass` accordingly. State this as a prerequisite step, not a footnote.

**Pass manifests directory to HTML report tool** via `--manifests` flag so the HTML can offer a download button.
