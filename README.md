# EKS Ingress → Gateway API Migration Skill

An AI-powered skill for [Claude Code](https://docs.anthropic.com/en/docs/build-with-claude/claude-code) and [Kiro CLI](https://kiro.dev) that assesses your Amazon EKS cluster's readiness to migrate from legacy Ingress resources to **Kubernetes Gateway API**.

## Why Gateway API?

The Kubernetes project has signaled that the Ingress resource will not receive new features and is on a deprecation path. Gateway API is the official successor — migrating to ALB Ingress now only to migrate again later is wasted effort. This skill focuses exclusively on the Gateway API path.

## How It Works

The skill connects to your live EKS cluster via [MCP servers](https://modelcontextprotocol.io/), runs automated checks across **7 assessment areas**, rates each item 🟢 GREEN / 🟡 AMBER / 🔴 RED / ⬜ UNKNOWN, and generates a migration readiness report with a phased plan.

### Workflow

```
Pre-flight → Assess (7 sections) → 3D Topology Visualization → Dual Report (md + html) → Export Manifests
```

### Assessment Areas

| # | Area | What It Checks |
|---|------|----------------|
| 1 | **Ingress Discovery** | Installed controllers, IngressClass, Ingress inventory |
| 2 | **Gateway API Readiness** | CRDs, GatewayClass, AWS LB Controller Gateway support, existing resources |
| 3 | **Ingress Resource Analysis** | Annotation→HTTPRoute mapping, TLS, backend compatibility |
| 4 | **DNS & Certificates** | external-dns Gateway API source, cert-manager Gateway integration, ACM |
| 5 | **Traffic & Routing** | Routing patterns mapped to HTTPRoute, advanced features, cross-namespace |
| 6 | **Migration Risk** | Downtime risk, feature gaps, rollback readiness |
| 7 | **Migration Plan** | Scope, conversion complexity, phased timeline with YAML examples |

### Output

- **3D routing topology** (Three.js) — interactive visualization of controllers → ingresses → services
- **Detailed Markdown report** — full findings, CLI commands, YAML examples
- **Visual HTML report** — dashboard with 3D topology, collapsible sections, dark/light theme
- **Export Manifests** — ready-to-apply YAML files (`current/` backup + `target/` Gateway API resources)
- **Blocker list** — RED items that must be fixed before migration

## Quick Start

1. Open this project in Claude Code or Kiro
2. Enable the MCP servers when prompted
3. Ask: *"Run an ingress migration assessment"*

The skill will discover your clusters, ask which one to assess, then run the full assessment.

## Project Structure

```
ingressmigration/
├── .kiro/skills/ingressmigration/
│   └── SKILL.md                  # Skill definition — entry point
├── steering/                     # Per-section assessment guides
│   ├── ingress-discovery.md      #   Step 1: Controller & IngressClass discovery
│   ├── gateway-api.md            #   Step 2: Gateway API CRDs, GatewayClass, controller
│   ├── ingress-resources.md      #   Step 3: Annotation→HTTPRoute mapping, TLS, backends
│   ├── dns-certificates.md       #   Step 4: DNS & cert Gateway API support
│   ├── traffic-routing.md        #   Step 5: Routing patterns → HTTPRoute mapping
│   ├── migration-risk.md         #   Step 6: Risk, feature gaps, rollback
│   ├── migration-plan.md         #   Step 7: Phased plan with YAML examples
│   └── report-generation.md      #   Step 8-9: Dual report generation
├── tools/
│   └── report_to_html.py        # MD → HTML with Three.js 3D topology
├── reports/                      # Generated reports land here
├── .mcp.json                     # MCP server configuration
├── CLAUDE.md                     # Claude Code project instructions
└── .gitignore
```

## Prerequisites

- **AWS credentials** configured with EKS read access (`aws sts get-caller-identity` should work)
- **Python 3.10+** and **[uv](https://docs.astral.sh/uv/)** installed
- **Claude Code** or **Kiro CLI**

## Inspired By

This skill follows the patterns established by:

- [eks-operation-review-skill](https://github.com/kahhaw9368/eks-operation-review-skill) — Operational excellence assessment
- [eks-upgrade-skill](https://github.com/kahhaw9368/eks-upgrade-skill) — Upgrade readiness assessment
- [sample-apex-skills](https://github.com/aws-samples/sample-apex-skills) — EKS recon, best practices, and more

## Status

🚧 **Work in progress** — The skill structure and steering files are in place. We'll deep-dive into each assessment step to refine the checks, add edge cases, and validate against real clusters.

## Changelog

| Date | Update |
|------|--------|
| 2026-04-29 | Initial skill creation — SKILL.md, 8 steering files, report_to_html.py, .mcp.json |
| 2026-04-29 | Attached skill to Kiro CLI global config via symlink (`~/.kiro/skills/ingressmigration`) |
| 2026-04-29 | Added changelog to README for tracking updates |
| 2026-04-29 | Added permission validation step (Action 3) to pre-flight — checks required + optional IAM/K8s RBAC permissions, shows exact missing permission and fix, degrades gracefully for optional ones |
| 2026-04-29 | Rebuilt `report_to_html.py` — dashboard-style HTML with sidebar nav, animated SVG score ring, collapsible sections, color-coded rating badges, dark/light theme, responsive + print-friendly |
| 2026-04-29 | **Major update:** Refocused migration target to **Gateway API only** (Ingress is on deprecation path). Removed ALB-as-target references. |
| 2026-04-29 | New workflow: assess → 3D topology visualization → user review → dual report. Agent must show interactive topology before generating report. |
| 2026-04-29 | Rebuilt `report_to_html.py` with **Three.js 3D routing topology** — controllers (orange), ingresses (blue), services (green), gateway resources (purple) as 3D spheres with orbit/zoom/click. Loaded via `--topology` flag. |
| 2026-04-29 | Rewrote all steering files for Gateway API target: `gateway-api.md` (CRDs + AWS LB Controller Gateway support + GatewayClass), `ingress-resources.md` (annotation→HTTPRoute mapping table), `dns-certificates.md` (Gateway API source checks), `traffic-routing.md` (patterns→HTTPRoute), `migration-risk.md` (Gateway-focused). |
| 2026-04-29 | New `steering/migration-plan.md` — phased plan (Foundation → Convert & Test → Cutover → Cleanup) with Gateway/HTTPRoute YAML examples. |
| 2026-04-29 | Removed `steering/aws-lb-controller.md` — content merged into `gateway-api.md` section 2.2. |
| 2026-04-29 | Dual output: markdown (detailed findings + CLI commands) + HTML (visual dashboard with 3D topology + score ring). Both always generated. |
| 2026-04-29 | HTML fix: stripped `**` markers from all text, auto-expanding table columns (`table-layout:auto`, `white-space:nowrap` on first col), skip YAML/code blocks and ASCII art in HTML output |
| 2026-04-29 | Gateway API Readiness section reframed as readiness assessment ("what needs to be set up") not inventory of existing resources |
| 2026-04-29 | Traffic section renamed to "Traffic & Routing" (removed "Complexity"). Architecture section = prose in md, 3D topology in HTML (no ASCII art). |
| 2026-04-29 | Added content rules: findings must be summary explanations not raw config pastes. YAML examples only in Migration Plan section. |
| 2026-04-29 | Renamed skill from `ingressmigration` to **EKS Ingress Migration**. Added Skill Home Directory section with absolute paths — skill is fully self-contained, no dependency on other skills. |
| 2026-04-29 | Removed `uv` prerequisite — `report_to_html.py` uses only Python stdlib. Clarified MCP/AWS tool prerequisites. |
| 2026-04-29 | Removed "User Review" pause step — assessment now auto-proceeds to report generation without stopping to ask. |
| 2026-04-29 | Rewrote `report-generation.md` — strict table-driven template, no filler text, max 2 sentences per finding cell, deterministic scoring formula, mandatory consistency validation pass, all structured data in tables (cluster info, architecture, routing topology, migration phases, blockers, recommendations). |
| 2026-04-29 | **Major reframe:** Skill is now an assessment tool, not a migration recommender. Gateway API is Option 1 quick-win, not the only path. Removed readiness score — decision belongs to user's DevOps team. |
| 2026-04-29 | Report output path changed to `~/ingress_migration/` (fixed location, not project-relative). |
| 2026-04-29 | Rebuilt `report_to_html.py` — removed sidebar nav, removed score ring/donut, removed logo. Clean single-column layout with light/dark theme. |
| 2026-04-29 | 3D topology renamed to **Current Architecture**. Added 5 distinct shapes: box=Node(EC2), sphere=Controller, octahedron=Ingress, cone=Service, dodecahedron=Gateway. Added EC2 instance node layer showing instanceId/instanceType/zone. |
| 2026-04-29 | Report template rewritten: Assessment Summary table replaces score table, Migration Plan renamed to Migration Options, added Investigate Manually section for UNKNOWN items. |
| 2026-04-29 | HTML design upgraded to match sample-apex-skills style: Poppins + Lora fonts, warm earthy palette (#faf9f5 bg, #141413 headers, #d97757 accent), uppercase section headers, clean card layout. |
| 2026-04-29 | Added dark/light theme toggle button in banner. Remembers preference via localStorage, defaults to system preference. Report renamed to **Ingress Assessment & Migration**. |
| 2026-04-29 | **Report restructured into 5 navigation sections:** Overview (3D + info + exec summary as bullets), Assessment Summary (summary table + current config + Section 01), Routing Topology (route table + Section 05), Migration Approach (Gateway API steps only, no code), Appendix (blockers, recommendations, remaining sections, reference links). |
| 2026-04-29 | Removed Section 02 (Gateway API Readiness) from assessment — biases toward single migration path. Removed ID column from all tables. Multi-value cells use `<br>` line breaks instead of commas. |
| 2026-04-29 | 3D topology connection lines upgraded from `LineBasicMaterial` to `CylinderGeometry` pipes — much bolder and easier to see. Left nav with scroll-based active highlighting. |
| 2026-04-29 | **Multi-cluster support:** User provides AWS Account ID as input. Skill discovers all EKS clusters across regions (ap-southeast-1, ap-southeast-7, us-east-1), shows discovery table, assesses each selected cluster, generates separate report per cluster. |
| 2026-04-29 | **Single HTML with cluster dropdown:** Multiple cluster reports combine into one HTML file. Left nav has a cluster selector dropdown — switching clusters swaps all content and 3D topology. CLI accepts multiple report + topology files. |
| 2026-04-29 | **Removed section numbers from report.** Sections renamed to descriptive names: Ingress Discovery, Traffic & Routing, Ingress Resource Analysis, DNS & Certificates, Migration Risk, Migration Planning. Each section lives on its own nav page — numbers no longer make sense. |
| 2026-04-29 | HTML fixes: (1) Cluster dropdown restyled — dark bg, white text, accent border on focus, custom arrow icon. (2) Dropdown shows cluster name only (stripped date/time), prefers topology JSON `cluster` field. (3) Nav links now use JS `scrollIntoView` with auto-open of collapsed `<details>` sections. |
| 2026-05-06 | **Traffic & Routing** — "Current State" column replaced with "Current Config" showing actual config in compact 1-liner format (e.g., `Ingress/shopping-app: /* → frontend:80 (Prefix, TLS:no)`). DevOps teams see exact config at a glance. |
| 2026-05-06 | **Migration Options Convert & Test** — "Conversion Notes" column replaced with "Target Config" showing actual HTTPRoute config in compact 1-liner (e.g., `HTTPRoute/shopping-app-route: parentRef=main-gateway, path=/* → frontend:80`). Teams can test faster. |
| 2026-05-06 | **Export Manifests** — New Step 10 in workflow. Generates `<cluster>-manifests/current/` (existing Ingress as clean YAML) and `<cluster>-manifests/target/` (Gateway API resources in numbered apply order). |
| 2026-05-06 | `report_to_html.py` — Added `--manifests` flag. HTML report now includes "Export Manifests" section under Migration Approach with per-file download links and a "Download All Target Manifests" button (base64-embedded, no server needed). |

## License

MIT
