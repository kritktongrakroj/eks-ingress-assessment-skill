# Skill eval harness

Self-test that protects the skill's **accuracy** and guards against **context skew** —
i.e. unintentional edits that silently make the assessment wrong, drop a safety rule, or
break the report renderer.

## Run

```bash
python3 tests/run_evals.py
```

Exit code `0` = all checks pass; `1` = at least one regression (details printed). No third-party
dependencies — Python stdlib only. Runs automatically on every push / PR via
`.github/workflows/eval.yml`.

## What it checks (130+ assertions, 3 groups)

**A. Invariants** — factual + structural correctness must not regress:
- No `GREEN/AMBER/RED` rating tokens (the skill uses **Impact 1–5** / Impact Indicator).
- Correct AWS facts: GatewayClass `gateway.k8s.aws/alb`; LBC Gateway API **≥ v2.14 (L7) / ≥ v2.13.3 (L4)**; Gateway API CRDs **v1.3.0**; no false "v2.7+ supports Gateway API" claim.
- EKS Auto Mode awareness (`eks.amazonaws.com/alb`) and controller EOL/CVE check (CVE-2023-5044) present.
- Structure: References group + Export Materials present; no Migration Planning / Investigate Manually sections; `.kiro` and `.claude` SKILL.md identical.

**B. Accuracy guards** — the hard-won practitioner/architect lessons must stay taught
(Basic-Auth→OIDC is a behavior change; CORS/rate-limit are High; class switch provisions a new
ALB + needs DNS cutover; internal-scheme subnet check; end-to-end TLS; coexist ≠ safe shift;
sticky-session rollback; path-matching semantics + shadow/replay; snippet blind spot;
snippet-incomplete manifest gate; controller-ownership pre-apply gate; blast-radius Gateways;
timeline scales to redesign blockers).

**C. Renderer** — `report_to_html.py` builds a report from `tests/eval_data/` and the output is
asserted: bold/red emphasis, nested bullets (incl. in-cell), `<br>` renders (not escaped),
orange Impact badges, no leftover `[[DL:]]` tokens, download buttons, the sci-fi 3D scene
(bloom + entity-iconic builders), References/Export Materials, cluster-scoped anchors, and
valid inline JS (via `node --check` when Node is available).

## Before you edit the skill

Run the harness before committing steering/tool changes. If it fails, you've changed a fact,
dropped a safety rule, or broken the renderer — fix it or update the harness deliberately.
