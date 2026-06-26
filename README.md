# EKS Ingress Migration Assessment Skill

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-green.svg)](https://www.python.org/)
[![Claude Code](https://img.shields.io/badge/Claude_Code-skill-orange.svg)](https://docs.anthropic.com/en/docs/claude-code)
[![Kiro CLI](https://img.shields.io/badge/Kiro_CLI-skill-purple.svg)](https://kiro.dev)

> ⚠️ **Important:** This is sample code for demonstration and educational purposes only. It is not intended for production use without additional security testing and review. Use at your own risk.

A [Claude Code](https://docs.anthropic.com/en/docs/claude-code) / [Kiro CLI](https://kiro.dev) skill that performs automated EKS Ingress migration assessments. It connects to live EKS clusters, discovers all Ingress resources, scores migration **impact (1–5)** across all assessment areas, and generates an interactive HTML report with 3D routing diagram visualization and ready-to-apply manifests.

**Three migration paths supported:**
- **Gateway API** (HTTPRoute + Gateway) — the Kubernetes-native successor to Ingress
- **AWS Load Balancer Controller** (ALB Ingress) — stay on Ingress API, swap NGINX→ALB
- **AWS Transform (ATX)** — fully automated manifest rewriting using the included Transform Definition

Checks are informed by the [EKS Best Practices Guide](https://docs.aws.amazon.com/eks/latest/best-practices/), [Gateway API specification](https://gateway-api.sigs.k8s.io/), and [AWS Load Balancer Controller docs](https://kubernetes-sigs.github.io/aws-load-balancer-controller/). All operations are **read-only** — the skill does not modify your cluster.

## Table of Contents

- [Getting Started](#getting-started)
- [What Gets Assessed](#what-gets-assessed)
- [Output](#output)
- [MCP Server Setup](#mcp-server-setup)
- [Required Permissions](#required-permissions)
- [Limitations](#limitations)
- [Troubleshooting](#troubleshooting)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [Security](#security)
- [License](#license)

## Getting Started

### Prerequisites

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) or [Kiro CLI](https://kiro.dev) installed
- [Python 3.10+](https://www.python.org/) (report tool uses only stdlib — no pip packages needed)
- AWS credentials configured — `aws sts get-caller-identity` should succeed

### Quick Start

```bash
git clone https://github.com/kritktongrakroj/eks-ingress-assessment-skill.git
cd eks-ingress-assessment-skill
```

**With Claude Code:**
```bash
claude
```

**With Kiro CLI:**
```bash
kiro
```

On first launch, the tool will prompt you to enable two MCP servers from `.mcp.json`. **Enable both** — they are required for the skill to work:

- `awslabs.eks-mcp-server` — connects to your EKS cluster's Kubernetes API
- `awslabs.aws-documentation-mcp-server` — looks up AWS documentation during assessment

Then ask:

> Run an ingress migration assessment for account 123456789012

The skill discovers all EKS clusters across every enabled region in the account, shows a discovery table, and walks you through the full assessment.

## What Gets Assessed

| # | Area | What It Checks |
|---|------|----------------|
| 1 | **Ingress Discovery** | Installed controllers, IngressClass resources, Ingress inventory |
| 2 | **Ingress Resource Analysis** | Annotation→HTTPRoute mapping, TLS config, backend compatibility |
| 3 | **DNS & Certificates** | external-dns Gateway API source, cert-manager integration, ACM |
| 4 | **Traffic & Routing** | Routing patterns mapped to HTTPRoute, advanced features, cross-namespace |
| 5 | **Migration Risk** | Downtime risk, feature gap analysis, rollback readiness |
| 6 | **Migration Planning** | Scope, conversion complexity per route, timeline estimate |
| 7 | **Migration Options** | Gateway API phased plan (Foundation → Convert → Cutover → Cleanup) |

### Impact Indicator (rating model)

Findings are scored by **Impact 1–5** — weighing security/reputation, business/revenue, and the nature & effort to remediate (not by how small the YAML edit is):

| Impact | Band | Meaning |
|--------|------|---------|
| 🟡 1–2 | Low | Hardening gap / best practice; no revenue or downtime impact; hours–1 day, single-scope. |
| 🟠 3–4 | Medium | Limited-reputation breach or short-downtime revenue loss; tech debt that's hard to reverse; area/single-cluster scope. |
| 🔴 5 | High | Major/reputational breach or prolonged downtime; needs re-design/re-architecture (may need approval). |
| ⬜ Unknown | — | Cannot determine — investigate manually. |

> Migration-execution risk counts: a one-line class switch that provisions a new ALB + needs DNS cutover, or a feature with no faithful equivalent (CORS, rate-limit, auth), is **not** automatically Low.

## Output

The skill generates multiple output formats per cluster:

| Format | Description |
|--------|-------------|
| **HTML Report** | Interactive dashboard with 3D routing diagram, cluster dropdown, dark/light theme |
| **Markdown Report** | Detailed findings, ratings, recommendations, CLI commands |
| **Topology JSON** | Cluster architecture data (nodes, controllers, ingresses, services) |
| **Current Manifests** | Existing Ingress resources as clean YAML (backup) |
| **Target Manifests** | Gateway API resources + ALB Ingress resources in apply order |

### Report Features

- **3D Routing Diagram** — Three.js visualization with orbit/zoom/click (nodes, controllers, ingresses, services as distinct 3D shapes)
- **Multi-cluster support** — Single HTML with cluster dropdown selector
- **Export Manifests** — Download button for ready-to-apply Gateway API YAML
- **Dark/Light theme** — Toggle with system preference detection

### Output Location

All files are written to `~/ingress_migration/`:

```
~/ingress_migration/
├── EKS-Ingress-Migration-<cluster>-<date>.md       # Per-cluster markdown
├── EKS-Ingress-Migration-<date>.html               # Combined HTML (all clusters)
├── <cluster>-topology.json                          # Topology data
└── <cluster>-manifests/
    ├── current/                                     # Existing Ingress YAML
    │   └── <namespace>-<ingress-name>.yaml
    └── target/
        ├── gateway-api/                             # Gateway API YAML
        │   ├── 00-gateway-api-crds.yaml
        │   ├── 01-gatewayclass.yaml
        │   ├── 02-gateway.yaml
        │   └── 03-httproute-<name>.yaml
        └── alb/                                     # ALB Controller YAML
            └── <namespace>-<ingress-name>.yaml
```

## MCP Server Setup

This skill uses two MCP servers, both pre-configured in `.mcp.json`. No setup is needed for the default configuration — just clone and run.

**Using a specific AWS profile or region**

Update the `env` block for the EKS MCP server in `.mcp.json`:

```json
"env": {
  "AWS_PROFILE": "your-profile",
  "AWS_REGION": "ap-southeast-1",
  "FASTMCP_LOG_LEVEL": "ERROR"
}
```

**Switching to the AWS-Managed EKS MCP Server**

The default uses the [open-source EKS MCP server](https://github.com/awslabs/mcp). If your team needs CloudTrail audit logging or automatic updates, you can switch to the [AWS-managed EKS MCP server](https://docs.aws.amazon.com/eks/latest/userguide/eks-mcp-introduction.html) instead.

1. Attach the `AmazonEKSMCPReadOnlyAccess` managed policy to your IAM user/role.
2. Replace the `awslabs.eks-mcp-server` block in `.mcp.json`:

```json
"awslabs.eks-mcp-server": {
  "command": "uvx",
  "args": [
    "mcp-proxy-for-aws@latest",
    "https://eks-mcp.{region}.api.aws/mcp",
    "--service", "eks-mcp",
    "--profile", "default",
    "--region", "{region}",
    "--read-only"
  ]
}
```

> **Important:** The server name (`"awslabs.eks-mcp-server"`) must stay exactly as shown — the skill routes tool calls by this name.

## Required Permissions

### AWS IAM

Minimum IAM permissions:

```
eks:ListClusters, eks:DescribeCluster, eks:ListAddons, eks:DescribeAddon
elasticloadbalancing:DescribeLoadBalancers, elasticloadbalancing:DescribeTargetGroups
iam:GetRole, iam:ListAttachedRolePolicies
acm:ListCertificates
route53:ListHostedZones
```

### Kubernetes RBAC

Your IAM identity needs read access to Kubernetes resources via an [EKS access entry](https://docs.aws.amazon.com/eks/latest/userguide/access-entries.html):

- `get`/`list` on: Nodes, Deployments, DaemonSets, Services, Ingresses, IngressClasses
- `get`/`list` on: GatewayClasses, Gateways, HTTPRoutes (if Gateway API CRDs installed)

## Limitations

- **Point-in-time snapshot** — reflects cluster state at the time of the run; does not monitor ongoing changes.
- **Assessment only** — the skill presents findings and options. The migration strategy decision belongs to your DevOps team.
- **Three migration paths** — Gateway API, ALB Controller, and ATX automated. The skill assesses all three and recommends based on findings.
- **No cluster modifications** — all operations are read-only. Generated manifests must be reviewed and applied manually.
- **Scaled-down clusters** — clusters with 0 nodes can still be assessed for Ingress resources (the API server is always available), but workload health cannot be verified.

## Troubleshooting

**MCP server not responding**

1. Check Python is installed: `python3 --version`
2. Check AWS credentials: `aws sts get-caller-identity`
3. Test the MCP server directly: `uvx awslabs.eks-mcp-server@latest`
4. Verify `AWS_PROFILE` and `AWS_REGION` in `.mcp.json` match your environment

**No clusters found**

The skill enumerates all enabled regions in the account (via `aws ec2 describe-regions`) and scans each for clusters — no region list is hardcoded. If none are found, confirm clusters actually exist in the account and that your credentials are allowed to list them.

**Permission denied errors**

Ensure your IAM identity has the permissions listed in [Required Permissions](#required-permissions) and has a Kubernetes RBAC binding via [EKS access entry](https://docs.aws.amazon.com/eks/latest/userguide/access-entries.html).

**HTML report not generating**

The `report_to_html.py` tool uses only Python stdlib — no pip packages needed. Verify:
```bash
python3 tools/report_to_html.py --help
```

## Project Structure

```
eks-ingress-assessment-skill/
├── README.md                              # This file
├── LICENSE                                # MIT license
├── SECURITY.md                            # Security policy
├── .mcp.json                              # MCP server configuration
├── CLAUDE.md                              # Claude Code project instructions
├── .gitignore                             # Excludes reports/, __pycache__/
├── .claude/
│   └── skills/
│       └── ingressmigration/
│           └── SKILL.md                   # Skill definition (Claude Code)
├── .kiro/
│   └── skills/
│       └── ingressmigration/
│           └── SKILL.md                   # Skill definition (Kiro CLI)
├── steering/                              # Assessment logic (agent instructions)
│   ├── ingress-discovery.md               #   Controllers, IngressClass, inventory
│   ├── ingress-resources.md               #   Annotations, TLS, backends
│   ├── dns-certificates.md                #   external-dns, cert-manager, ACM
│   ├── traffic-routing.md                 #   Routing patterns → HTTPRoute
│   ├── migration-risk.md                  #   Downtime, feature gaps, rollback
│   ├── migration-plan.md                  #   Phased plan with YAML examples
│   ├── gateway-api.md                     #   Gateway API CRDs & controller support
│   ├── alb-migration.md                   #   NGINX→ALB annotation mapping & phases
│   ├── atx-guide.md                       #   AWS Transform automated migration guide
│   └── report-generation.md               #   Report template & generation rules
├── samples/                               # Before/after manifest examples
│   ├── nginx/                             #   8 sample NGINX Ingress manifests
│   └── alb/                               #   8 ATX-migrated ALB equivalents
├── atx/                                   # AWS Transform (ATX) package
│   └── td_ingress-nginx-lbc/              #   Transform Definition for automated migration
│       ├── transformation_definition.md   #     TD instruction set
│       ├── summaries.md                   #     Document summaries
│       └── document_references/           #     Source reference material
├── tools/
│   └── report_to_html.py                  # MD → HTML with Three.js 3D routing diagram
└── reports/                               # Generated reports (gitignored)
    └── .gitkeep
```

## Contributing

Contributions are welcome! Please [open an issue](https://github.com/kritktongrakroj/eks-ingress-assessment-skill/issues) first to discuss what you'd like to change.

## Security

This skill is **read-only** and does not create, modify, or delete any AWS or Kubernetes resources. All operations are describe, list, and get calls.

Generated manifests in `target/` directories are proposals — they must be reviewed by your team before applying.

If you discover a security vulnerability, please see [SECURITY.md](SECURITY.md) for responsible disclosure instructions.

## License

This project is licensed under the [MIT License](LICENSE).
