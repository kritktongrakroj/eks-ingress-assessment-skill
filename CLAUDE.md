# EKS Ingress Migration Skill

This is a Claude Code / Kiro skill that assesses EKS Ingress architecture and evaluates migration options.

## How It Works

- Two MCP servers in `.mcp.json`: `awslabs.eks-mcp-server` + `awslabs.aws-documentation-mcp-server`
- Steering files in `steering/` guide per-section checks — read them before running each section
- `tools/report_to_html.py` converts markdown report to HTML with 3D Routing Diagram topology
- Reports output to `~/ingress_migration/`

## Workflow

1. **Pre-flight** — Discover cluster, validate permissions
2. **Assessment (Steps 1-7)** — Load steering files, execute checks, score Impact 1–5 (per the Impact Indicator), collect topology data (including EC2 nodes)
3. **Current Architecture** — Compile topology JSON, then immediately proceed to report generation
4. **Dual Report** — Automatically generate both markdown (detailed) and HTML (visual with 3D routing diagram) — do NOT pause to ask the user

## Critical Rules

- Load the steering file BEFORE executing checks
- Only rate based on what was actually observed — never assume
- If a check fails, mark UNKNOWN
- Every RED finding must have a specific recommendation
- Collect topology data during assessment including node (EC2 instance) information
- **Always generate both md and html reports**
- This is an **assessment tool** — present findings and options, do not prescribe a single migration path
- Gateway API is the primary quick-win option, but other paths may be added
- **Do NOT include a readiness score** — the migration decision belongs to the user's team
- Use tables for all structured data — no prose lists of facts
