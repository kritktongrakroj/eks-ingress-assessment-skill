# Report Generation

## Purpose

Generate dual-format assessment report matching the 5-section navigation structure:
**Overview → Assessment Summary → Routing Topology → Migration Approach → Appendix**

This is an **assessment report** — present findings and options, do not prescribe a single migration path.

## Step 1: Build Master Finding List

Compile ALL findings from sections 1–7. Every item must appear. No item may be skipped.

## Step 2: Consistency Checks (MANDATORY)

| Check | Fix |
|-------|-----|
| RED item missing from Blockers table | Add it |
| AMBER item missing from Recommendations table | Add it |
| UNKNOWN item missing from Investigate Manually table | Add it |
| Executive Summary mentions wrong rating | Fix to match master list |
| Prose paragraph that should be a table | Convert to table |
| Raw YAML in findings (not Migration Approach) | Replace with summary |

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
6. **No readiness score.** This is an assessment, not a scorecard.
7. **No ASCII art diagrams.** The HTML has the 3D topology.
8. **Multi-value cells in tables:** put each item on its own line using `<br>` (the renderer turns this into real line breaks). For **Current Configuration**, use nested bullet/sub-bullet lists instead of a table.
9. **Executive Summary = one-shot understanding for a non-technical reader.** Top-level bullet per impact theme, indented sub-bullets for specifics. Bold the key term in each bullet; wrap the most damaging facts in `!! !!` (renders red).
10. **Emphasis syntax (supported by the renderer):** `**bold**` for key terms, `!!red highlight!!` for high-impact / at-risk items, backticks for `versions/code`. Use sparingly — only words that carry the impact.
11. **Lead with impact.** Order Executive Summary bullets and Assessment Summary rows from highest impact to lowest.
12. **Download buttons (renderer tokens):** drop `[[DL:gateway-api]]`, `[[DL:alb]]`, `[[DL:atx]]`, or `[[DL:current]]` anywhere in the markdown — the renderer replaces each with a one-click download button for that option's combined routing config (built from the exported manifests). Prefer a download button over printing long target/current config text.
13. **In-page anchor links:** write `[blocker](#blockers)` to link to a section — the renderer auto-scopes the anchor to the cluster (e.g. `#c0-blockers`). Use this wherever the text says "see Blockers".
14. **Impact meters everywhere:** Ingress Discovery and Traffic & Routing also use the **Impact 1–5** scale (🟡1-2 / 🟠3-4 / 🔴5), not GREEN/AMBER/RED.

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

#### Phase 1 — Foundation
| Step | Action |
|------|--------|
| 1 | Install Gateway API CRDs |
| 2 | Verify/upgrade AWS LB Controller (v2.7+) |
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
| 1 | Install AWS LB Controller v2.7+ | `kubectl get deploy -n kube-system aws-load-balancer-controller` |
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

| Finding | Action Required | Effort |
|---------|----------------|--------|
| [finding name — rating] | [specific action] | [hours/days] |

> If no RED items exist, write: "No blockers identified."

---

## Recommendations

| Finding | Action | Priority | Effort |
|---------|--------|----------|--------|
| [finding name — rating] | [specific action] | [High/Medium/Low] | [hours/days] |

---

## Investigate Manually

| Item | Question to Answer |
|------|--------------------|
| [item name] | [what to check and why] |

> If no UNKNOWN items exist, write: "All items were assessed successfully."

---

## Ingress Resource Analysis

| Item | Rating | Current State | Recommendation | Reference |
|------|--------|---------------|----------------|-----------|
| Annotation Inventory & Mapping | [rating] | [summary] | [action] | [link] |
| TLS Configuration | [rating] | [summary] | [action] | [link] |
| Backend Service Compatibility | [rating] | [summary] | [action] | [link] |

---

## DNS & Certificates

| Item | Rating | Current State | Recommendation | Reference |
|------|--------|---------------|----------------|-----------|
| external-dns Gateway API Support | [rating] | [summary] | [action] | [link] |
| cert-manager Gateway Integration | [rating] | [summary] | [action] | [link] |
| ACM Integration | [rating] | [summary] | [action] | [link] |

---

## Migration Risk

| Item | Rating | Current State | Recommendation | Reference |
|------|--------|---------------|----------------|-----------|
| Downtime Risk | [rating] | [summary] | [action] | [link] |
| Feature Gap Analysis | [rating] | [summary] | [action] | [link] |
| Rollback Readiness | [rating] | [summary] | [action] | [link] |

---

## Migration Planning

| Item | Rating | Current State | Recommendation | Reference |
|------|--------|---------------|----------------|-----------|
| Migration Scope | [rating] | [summary] | [action] | [link] |
| Conversion Complexity per Route | [rating] | [summary] | [action] | [link] |
| Timeline Estimate | [rating] | [summary] | [action] | [link] |

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
- **Overview:** Information table, Executive Summary, 3D Architecture
- **Assessment Summary:** Assessment Summary table, Current Configuration, Ingress Discovery
- **Routing Topology:** Routing Topology table, Traffic & Routing
- **Migration Approach:** Migration Options (Option 1: Gateway API phases, Option 2: ALB Controller with annotation table, Option 3: ATX automated), Export Manifests (download button)
- **Appendix:** Blockers, Recommendations, Investigate Manually, Ingress Resource Analysis, DNS & Certificates, Migration Risk, Migration Planning, AWS Reference Links

Note: Gateway API Readiness is intentionally excluded as a standalone section — it biases toward a single migration path. Gateway API details are covered in the Migration Options section.

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

## Step 6: Export Manifests

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
6. Inform the user: "Manifests exported to `~/ingress_migration/<cluster>/manifests/` — review and apply with `kubectl apply -f target/gateway-api/` or `kubectl apply -f target/alb/`"

**Pass manifests directory to HTML report tool** via `--manifests` flag so the HTML can offer a download button.
