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

Save to `~/ingress_migration/<cluster>-topology.json`. Include nodes (EC2 instances).

## Step 4: Write Markdown Report

**Filename:** `~/ingress_migration/EKS-Ingress-Migration-<cluster>-<YYYY-MM-DD>-<HHMM>.md`

### Content Rules (MANDATORY)

1. **Use tables for all structured data.** Never write lists of facts as prose.
2. **No ID column in any table.** Remove all "ID" columns — they add no value for the reader.
3. **No raw YAML/config in findings.** YAML belongs only in Migration Approach.
4. **Every finding cell: max 2 sentences.**
5. **No filler text.** Go straight to content.
6. **No readiness score.** This is an assessment, not a scorecard.
7. **No ASCII art diagrams.** The HTML has the 3D topology.
8. **Multi-value cells:** when a cell has multiple items (e.g., namespaces, controllers), put each on its own line using `<br>` — not comma-separated.
9. **Executive Summary must be bullet points** — precise and comprehensive, not paragraphs.

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

- [Key finding 1 — what ingress controllers exist, how many Ingress resources]
- [Key finding 2 — current architecture state]
- [Key finding 3 — top blockers or issues found]
- [Key finding 4 — Gateway API readiness status]
- [Additional bullet points as needed — keep each precise and informative]

---

## Assessment Summary

| Category | Rating | Key Finding |
|----------|--------|-------------|
| Ingress Discovery | 🟢 GREEN | [one-line summary] |
| Gateway API Readiness | 🔴 RED | [one-line summary] |
| Ingress Resources | 🟡 AMBER | [one-line summary] |
| DNS & Certificates | 🟢 GREEN | [one-line summary] |
| Traffic & Routing | 🟢 GREEN | [one-line summary] |
| Migration Risk | 🟡 AMBER | [one-line summary] |
| Migration Plan | 🟢 GREEN | [one-line summary] |

---

## Current Configuration

| Property | Value |
|----------|-------|
| Ingress Controller(s) | [name v1.2.3<br>name2 v4.5.6] |
| Controller Namespace(s) | [ns1<br>ns2] |
| Total Ingress Resources | [count] |
| Namespaces with Ingress | [ns1<br>ns2<br>ns3] |
| Routing Pattern | [host-based / path-based / both] |
| TLS Enabled | [yes/no/partial — X of Y] |
| Load Balancer Type | [ALB / NLB / nginx / etc.] |
| Node Count | [count] |
| Instance Types | [m5.xlarge<br>m5.2xlarge] |

---

## Ingress Discovery

| Item | Rating | Current State | Recommendation | Reference |
|------|--------|---------------|----------------|-----------|
| Ingress Controllers Installed | [rating] | [summary] | [action or "None required"] | [link] |
| IngressClass Resources | [rating] | [summary] | [action or "None required"] | [link] |
| Ingress Resource Inventory | [rating] | [summary] | [action or "None required"] | [link] |

---

## Routing Topology

| Ingress Name | Namespace | Controller | Host | Path | Backend Service | Port | TLS |
|-------------|-----------|------------|------|------|-----------------|------|-----|
| [name] | [ns] | [controller] | [host] | [path] | [svc] | [port] | [yes/no] |

---

## Traffic & Routing

| Item | Rating | Current Config | Recommendation | Reference |
|------|--------|----------------|----------------|-----------|
| Routing Pattern Mapping | [rating] | `Ingress/<name>: <host><path> → <backend>:<port> (<pathType>, TLS:<yes/no>)` | [action] | [link] |
| Advanced Traffic Features | [rating] | `annotations: <key>=<value>` (one per line, actual values) | [action] | [link] |
| Cross-Namespace Routing | [rating] | `<ns>/<ingress> → <target-ns>/<svc>` or "All same-namespace" | [action] | [link] |

> **Current Config column:** Show actual config in compact 1-liner format so the DevOps team knows exactly what exists and where. Use backtick code formatting. Multiple routes = one per line with `<br>`.

---

## Migration Options

> This section presents available migration paths. The choice depends on your team's requirements, timeline, and risk tolerance.

### Option 1: Gateway API

Gateway API is the official Kubernetes successor to Ingress. AWS LB Controller v2.7+ supports it natively.

#### Phase 1: Foundation

| Step | Action |
|------|--------|
| 1 | Install Gateway API CRDs |
| 2 | Upgrade AWS LB Controller to v2.7+ |
| 3 | Create GatewayClass resource |
| 4 | Create Gateway resource |

#### Phase 2: Convert & Test

| Ingress | Target HTTPRoute | Target Config |
|---------|-----------------|---------------|
| [ingress-name] | [httproute-name] | `HTTPRoute/<name>: parentRef=<gateway>, hostnames=[<host>], path=<path> → <backend>:<port>` |

> **Target Config column:** Show the equivalent Gateway API config in compact 1-liner format. The DevOps team should be able to read this and know exactly what to create. Use backtick code formatting.

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
- **Migration Approach:** Migration Options (Gateway API phases — steps only, no code), Export Manifests (download button)
- **Appendix:** Blockers, Recommendations, Investigate Manually, Ingress Resource Analysis, DNS & Certificates, Migration Risk, Migration Planning, AWS Reference Links

Note: Gateway API Readiness is intentionally excluded as a standalone section — it biases toward a single migration path. Gateway API details are covered in the Migration Options section.

## Step 5: Generate HTML Report

After ALL cluster markdown reports are written, generate a **single combined HTML**:

```bash
# Single cluster
python3 /home/krittong/my-workspace/ingressmigration/tools/report_to_html.py ~/ingress_migration/<report>.md --topology ~/ingress_migration/<cluster>-topology.json

# Multiple clusters — one HTML with cluster dropdown
python3 /home/krittong/my-workspace/ingressmigration/tools/report_to_html.py \
  ~/ingress_migration/report-a.md ~/ingress_migration/report-b.md \
  --topology ~/ingress_migration/topo-a.json ~/ingress_migration/topo-b.json \
  -o ~/ingress_migration/EKS-Ingress-Migration-<YYYY-MM-DD>-<HHMM>.html
```

Do NOT generate HTML manually. Always use the script.

## Step 6: Export Manifests

After generating the HTML report, export manifest files for each cluster:

**Output directory:** `~/ingress_migration/<cluster>-manifests/`

```
<cluster>-manifests/
├── current/          # Existing Ingress resources as clean YAML (no status/managedFields)
│   └── <namespace>-<ingress-name>.yaml
└── target/           # Generated Gateway API resources ready to apply
    ├── 00-gateway-api-crds.yaml      # kubectl apply -f URL (comment only)
    ├── 01-gatewayclass.yaml
    ├── 02-gateway.yaml
    ├── 03-httproute-<name>.yaml      # One per Ingress conversion
    └── 04-referencegrant-<name>.yaml # Only if cross-namespace
```

**Rules:**
1. `current/` — Extract each Ingress resource as YAML. Strip `status`, `managedFields`, `resourceVersion`, `uid`, `creationTimestamp`, `generation`. Keep only `apiVersion`, `kind`, `metadata.name`, `metadata.namespace`, `metadata.annotations`, `metadata.labels`, `spec`.
2. `target/` — Generate Gateway API manifests based on assessment findings. Number-prefix for apply order. Include comments explaining what each resource does.
3. The `00-gateway-api-crds.yaml` file should contain only a comment with the install command — not the actual CRD content.
4. All manifests must be valid YAML that can be applied with `kubectl apply -f`.
5. Inform the user: "Manifests exported to `~/ingress_migration/<cluster>-manifests/` — review and apply with `kubectl apply -f target/`"

**Pass manifests directory to HTML report tool** via `--manifests` flag so the HTML can offer a download button.
