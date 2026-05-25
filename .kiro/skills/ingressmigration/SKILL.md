---
name: EKS Ingress Migration
description: "Assess EKS Ingress architecture - give an AWS account ID, discover all clusters across regions, evaluate migration options, rate each area GREEN/AMBER/RED, and generate per-cluster assessment reports. Use when: ingress migration, ALB ingress, nginx ingress, Gateway API, load balancer controller, ingress modernization, ingress audit."
---

# EKS Ingress Migration Skill

## Overview

This skill assesses your live EKS cluster's current Ingress architecture and evaluates migration options. It discovers what ingress controllers are running, maps the routing topology, identifies risks, and presents the findings so your team can decide the best migration path.

**This is an assessment tool, not a decision-maker.** The skill presents findings and options — the migration strategy and readiness decision belongs to the user's DevOps team.

**Migration options assessed:**

| Option | Status | Notes |
|--------|--------|-------|
| Gateway API (HTTPRoute + Gateway) | ✅ Assessed | Official Kubernetes successor to Ingress. AWS LB Controller v2.7+ supports it. |
| AWS Load Balancer Controller (ALB Ingress) | ✅ Assessed | Stay on Ingress API but swap NGINX→ALB. Gets WAF, Cognito, Shield. |
| AWS Transform (ATX) — Automated | ✅ Included | TD included. For customers with ATX access — fully automated manifest rewriting. |

## Workflow

```
Pre-flight → Assess (7 sections) → Current Architecture Topology → Dual Report (md + html) → Export Manifests
```

1. **Pre-flight** — Discover cluster, validate permissions
2. **Assessment** — Run 7 sections, collect findings and topology data
3. **Current Architecture** — Compile topology data into JSON for the HTML report's interactive 3D view (nodes, controllers, ingresses, services)
4. **Dual Report** — Automatically generate both:
   - **Markdown** (detailed) — full findings, ratings, options, CLI commands
   - **HTML** (visual summary) — interactive dashboard with 3D current architecture view, collapsible sections
5. **Export Manifests** — Generate ready-to-apply YAML files:
   - `current/` — existing Ingress resources (clean, no status fields)
   - `target/gateway-api/` — Gateway API resources (GatewayClass, Gateway, HTTPRoute) in apply order
   - `target/alb/` — ALB Controller Ingress resources (converted annotations)

**Important:** After assessment completes, proceed directly to report generation and manifest export. Do NOT pause to ask the user — generate all outputs automatically.

## What Gets Assessed

| Area | Key Checks |
|------|------------|
| Ingress Discovery | Controllers, versions, IngressClass, Ingress resource inventory |
| Ingress Resource Analysis | Annotations, path rules, TLS, backends — conversion complexity |
| DNS & Certificates | external-dns, cert-manager, ACM — Gateway API source support |
| Traffic & Routing | Routing patterns, advanced features, mapping to HTTPRoute |
| Migration Risk | Downtime risk, feature gaps, rollback plan |
| Migration Planning | Scope, conversion complexity, timeline estimate |

## Report Structure (5 Navigation Pages)

| Nav Page | Contains |
|----------|----------|
| Overview | Cluster info table, Executive Summary (bullet points), 3D Current Architecture |
| Assessment Summary | Assessment Summary table, Current Configuration, Ingress Discovery |
| Routing Topology | Routing table (per-route line items), Traffic & Routing |
| Migration Approach | Migration Options — Gateway API phases, ALB Controller path, ATX automated path, Export Manifests button |
| Appendix | Blockers, Recommendations, Investigate Manually, Ingress Resource Analysis, DNS & Certificates, Migration Risk, Migration Planning, AWS Reference Links |

## Steering Files

Before executing checks for any section, read the corresponding steering file from `steering/` directory.

| User Request | Steering File |
|---|---|
| Full migration assessment | ALL files in order (skip gateway-api.md, alb-migration.md, atx-guide.md) |
| What ingress controllers do I have? | `steering/ingress-discovery.md` |
| Analyze my Ingress resources | `steering/ingress-resources.md` |
| DNS / certs / TLS | `steering/dns-certificates.md` |
| Routing complexity | `steering/traffic-routing.md` |
| Migration risks | `steering/migration-risk.md` |
| Migration plan | `steering/migration-plan.md` |
| Generate report | `steering/report-generation.md` |
| ALB Controller migration path | `steering/alb-migration.md` |
| AWS Transform (ATX) automated path | `steering/atx-guide.md` |

## Tool Usage Rules

1. **Do NOT call any tools when this skill is first activated.** Wait for the user to ask.
2. **Do NOT hardcode or guess cluster names.** Always discover by listing first.
3. **Do NOT retry a failed MCP tool call more than once.**
4. **Always load the relevant steering file before executing checks.**
5. **Only rate based on what was actually observed — never assume.**
6. If a check fails or returns no data, mark UNKNOWN.
7. Every RED finding must have a specific, actionable recommendation.
8. **Collect topology data during assessment** — every Ingress host, path, backend, controller, namespace, and the nodes (EC2 instances). This feeds the 3D Current Architecture view.
9. **Do NOT paste raw YAML/config in findings.** Summarize what was found.
10. **Use tables for all structured data.** No prose lists of facts.
11. **No filler text.** Go straight to content.
12. **Every finding cell: max 2 sentences.**
13. **No ASCII art diagrams.** The HTML has the 3D topology.
14. **No ID column in tables.** Remove all "ID" columns.
15. **Multi-value cells:** use `<br>` for line breaks, not commas.
16. **Executive Summary must be bullet points** — precise and comprehensive.

## Skill Home Directory

All relative paths in this skill (steering files, tools) are relative to the **skill project root** (the directory containing this SKILL.md's parent `.kiro/` folder).

When the skill says `steering/ingress-discovery.md`, read `<project-root>/steering/ingress-discovery.md`.
When the skill says `tools/report_to_html.py`, run `<project-root>/tools/report_to_html.py`.

Reports are written to `~/ingress_migration/`.

This skill is **fully self-contained** — it does not depend on any other Kiro skill. All steering files, tools, and templates are inside this project directory.

## Prerequisites

1. **AWS credentials configured** with EKS read access
2. **Python 3.10+** installed (report tool uses only stdlib — no pip packages needed)
3. **EKS MCP server** available (provides `list_k8s_resources`, `manage_k8s_resource` tools)
4. **AWS CLI** or AWS MCP tools available (for `eks`, `acm`, `route53`, `iam`, `elbv2` calls)
5. **Required AWS Permissions:**
   - `eks:DescribeCluster`, `eks:ListClusters`, `eks:ListAddons`, `eks:DescribeAddon`
   - `elasticloadbalancing:DescribeLoadBalancers`, `elasticloadbalancing:DescribeTargetGroups`
   - `iam:GetRole`, `iam:ListAttachedRolePolicies`
   - `acm:ListCertificates`
   - `route53:ListHostedZones`

## Assessment Workflow

### Input

The user provides an **AWS Account ID** (12-digit number). The skill discovers all EKS clusters across regions and assesses each one.

If the user provides a cluster name instead, skip discovery and assess that single cluster.

### Step 0: Pre-flight

**Action 1 — Verify account access**

```
aws sts get-caller-identity --output json
```

Confirm the account ID matches what the user provided.

**Action 2 — Discover all EKS clusters across regions**

Scan these regions for clusters:

| Region | Name |
|--------|------|
| ap-southeast-1 | Singapore |
| ap-southeast-7 | Thailand |
| us-east-1 | N. Virginia |

For each region:
```
aws eks list-clusters --region <region> --output json
```

Compile a discovery table:

| # | Cluster | Region | Version | Status |
|---|---------|--------|---------|--------|
| 1 | cluster-a | ap-southeast-1 | 1.29 | ACTIVE |
| 2 | cluster-b | us-east-1 | 1.28 | ACTIVE |

- If **0 clusters found** → STOP. Tell the user no EKS clusters exist in this account.
- If **1 cluster found** → Confirm and proceed with that cluster.
- If **multiple clusters found** → Show the table. Ask: "Assess all clusters, or select specific ones?"

**Action 3 — For each selected cluster, describe it**

```
aws eks describe-cluster --name <cluster> --region <region> --output json
```

**Action 4 — Validate permissions (per cluster)**

| Check Command | Required IAM Permission |
|---------------|------------------------|
| `aws eks list-addons --cluster-name <cluster> --region <region>` | `eks:ListAddons` |
| `list_k8s_resources(kind="Ingress", api_version="networking.k8s.io/v1")` | K8s RBAC: `get`/`list` on `ingresses` |
| `list_k8s_resources(kind="IngressClass", api_version="networking.k8s.io/v1")` | K8s RBAC: `get`/`list` on `ingressclasses` |
| `list_k8s_resources(kind="Deployment", api_version="apps/v1", namespace="kube-system")` | K8s RBAC: `get`/`list` on `deployments` |

**Optional permissions** (degrades gracefully if missing):

| Check Command | Required Permission | If Missing |
|---------------|---------------------|------------|
| `aws acm list-certificates --region <region>` | `acm:ListCertificates` | Mark 4.3 UNKNOWN |
| `aws route53 list-hosted-zones` | `route53:ListHostedZones` | Mark 4.1 UNKNOWN |
| `aws iam get-role` | `iam:GetRole` | Mark UNKNOWN |

**Action 5 — Verify MCP connectivity**

```
list_k8s_resources(cluster_name="<cluster>", kind="Node", api_version="v1")
```

### Steps 1–7: Run Assessment (per cluster)

For each cluster, run the full assessment:
1. Read each steering file in order
2. Execute the checks
3. Rate each item
4. **Collect topology data** — Ingress resources, controllers, backend services, and Node information (instance IDs, instance types)

### Step 8: Current Architecture Topology (per cluster)

1. Compile topology data collected during Steps 1–7
2. Write JSON: `~/ingress_migration/<cluster>-topology.json`
3. Briefly show topology summary, then proceed to Step 9

**Topology JSON schema:**
```json
{
  "cluster": "name",
  "region": "ap-southeast-1",
  "nodes": [
    { "name": "ip-10-0-1-100.ec2.internal", "instanceId": "i-0abc123def456", "instanceType": "m5.xlarge", "zone": "ap-southeast-1a" }
  ],
  "controllers": [
    { "name": "nginx", "namespace": "ingress-nginx", "version": "1.9.6", "type": "deployment" }
  ],
  "ingresses": [
    {
      "name": "my-app", "namespace": "default", "controller": "nginx",
      "hosts": ["app.example.com"],
      "paths": [{ "path": "/api", "pathType": "Prefix", "backend": "api-svc", "port": 80 }],
      "tls": true, "annotations": {"key": "value"}
    }
  ],
  "services": [
    { "name": "api-svc", "namespace": "default", "type": "ClusterIP", "ports": [80] }
  ],
  "gatewayApi": {
    "crdsInstalled": true,
    "gatewayClasses": [],
    "gateways": [],
    "httpRoutes": []
  }
}
```

### Step 9: Generate Dual Report (per cluster)

Read `steering/report-generation.md` and produce a **markdown report per cluster**:

`~/ingress_migration/EKS-Ingress-Migration-<cluster>-<YYYY-MM-DD>-<HHMM>.md`

After ALL cluster markdown reports are written, generate a **single combined HTML report**:

```bash
python3 tools/report_to_html.py \
  ~/ingress_migration/report-cluster-a.md ~/ingress_migration/report-cluster-b.md \
  --topology ~/ingress_migration/cluster-a-topology.json ~/ingress_migration/cluster-b-topology.json \
  --manifests ~/ingress_migration/cluster-a-manifests ~/ingress_migration/cluster-b-manifests \
  -o ~/ingress_migration/EKS-Ingress-Migration-<YYYY-MM-DD>-<HHMM>.html
```

The HTML report has a **cluster dropdown** in the left nav — selecting a cluster switches all content and the 3D topology.

**Always generate both.** Markdown files are the source of truth; the HTML is for presentation.

### Step 10: Export Manifests (per cluster)

For each cluster that has Ingress resources, generate manifest files:

**Output directory:** `~/ingress_migration/<cluster>-manifests/`

```
<cluster>-manifests/
├── current/
│   └── <namespace>-<ingress-name>.yaml
└── target/
    ├── 00-gateway-api-crds.yaml
    ├── 01-gatewayclass.yaml
    ├── 02-gateway.yaml
    ├── 03-httproute-<name>.yaml
    └── 04-referencegrant-<name>.yaml  (only if needed)
```

**Rules:**
1. `current/` — Each Ingress as clean YAML (strip status, managedFields, resourceVersion, uid, creationTimestamp, generation)
2. `target/gateway-api/` — Generated Gateway API manifests in numbered apply order with comments
3. `target/alb/` — Generated ALB Controller Ingress manifests (annotation-converted)
4. `00-gateway-api-crds.yaml` — Comment-only file with install command
5. All manifests must be valid `kubectl apply -f` ready
6. Skip clusters with 0 Ingress resources (nothing to export)
7. For ALB target, apply annotation mapping from `steering/alb-migration.md`

## Rating Rubric

| Rating | Meaning |
|--------|---------|
| GREEN | No issues found in this area |
| AMBER | Some items need attention |
| RED | Significant issues — must address before migration |
| UNKNOWN | Cannot determine — investigate manually |

## Report Output

All files go to `~/ingress_migration/` organized by cluster:

```
~/ingress_migration/
├── <cluster>/
│   ├── report.md                    # Detailed markdown report
│   ├── topology.json                # Topology data for 3D view
│   └── manifests/
│       ├── current/                 # Existing Ingress YAML (backup)
│       │   └── <ns>-<ingress>.yaml
│       └── target/
│           ├── gateway-api/         # Gateway API resources (apply order)
│           │   ├── 00-gateway-api-crds.yaml
│           │   ├── 01-gatewayclass.yaml
│           │   ├── 02-gateway.yaml
│           │   └── 03-httproute-<name>.yaml
│           └── alb/                 # ALB Controller Ingress (converted)
│               └── <ns>-<ingress>.yaml
└── EKS-Ingress-Migration-<YYYY-MM-DD>-<HHMM>.html  # Combined HTML (all clusters)
```

The single HTML report contains all clusters with a **dropdown selector** in the left nav. Switching clusters swaps the content and 3D topology view. The Migration Approach section includes **Export Manifests** buttons for both Gateway API (orange) and ALB Controller (blue) downloads.

**CLI usage:**
```bash
# Single cluster
python3 tools/report_to_html.py ~/ingress_migration/<cluster>/report.md \
  --topology ~/ingress_migration/<cluster>/topology.json \
  --manifests ~/ingress_migration/<cluster>/manifests/

# Multiple clusters — one HTML with dropdown
python3 tools/report_to_html.py \
  ~/ingress_migration/cluster-a/report.md ~/ingress_migration/cluster-b/report.md \
  --topology ~/ingress_migration/cluster-a/topology.json ~/ingress_migration/cluster-b/topology.json \
  --manifests ~/ingress_migration/cluster-a/manifests ~/ingress_migration/cluster-b/manifests \
  -o ~/ingress_migration/EKS-Ingress-Migration-<YYYY-MM-DD>-<HHMM>.html
```
