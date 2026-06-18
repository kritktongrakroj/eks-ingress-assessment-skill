#!/usr/bin/env python3
"""
Self-test / eval harness for the EKS Ingress Migration skill.

Guards against unintentional edits that drop accuracy or skew the assessment model.
Zero third-party dependencies (Python stdlib only). Exits non-zero on any failure.

Run:  python3 tests/run_evals.py
CI:   .github/workflows/eval.yml runs this on every push / PR.

Three groups:
  A. INVARIANTS  — factual correctness + rating-model + structure must not regress.
  B. ACCURACY    — key safety guidance must remain present (anti context-skew).
  C. RENDERER    — report_to_html.py must build a report with the expected features.
"""
import os, re, sys, subprocess, tempfile, pathlib

REPO = pathlib.Path(__file__).resolve().parent.parent
FAILS, PASSES = [], 0


def _read(rel):
    p = REPO / rel
    return p.read_text(encoding="utf-8") if p.exists() else ""


def check(name, ok, detail=""):
    global PASSES
    if ok:
        PASSES += 1
    else:
        FAILS.append(f"{name}" + (f" — {detail}" if detail else ""))


def has(rel, needle, ci=False):
    t = _read(rel)
    return (needle.lower() in t.lower()) if ci else (needle in t)


def absent(rel, needle):
    return needle not in _read(rel)


STEERING = [f"steering/{s}.md" for s in (
    "ingress-discovery ingress-resources dns-certificates traffic-routing "
    "migration-risk migration-plan report-generation alb-migration atx-guide gateway-api").split()]
DOCS = STEERING + [".kiro/skills/ingressmigration/SKILL.md",
                   ".claude/skills/ingressmigration/SKILL.md", "CLAUDE.md", "README.md"]


# ---------------------------------------------------------------- A. INVARIANTS
def group_invariants():
    # required files exist
    for f in STEERING + ["tools/report_to_html.py", ".mcp.json",
                         ".kiro/skills/ingressmigration/SKILL.md",
                         ".claude/skills/ingressmigration/SKILL.md"]:
        check(f"exists:{f}", (REPO / f).exists(), "missing")

    # GREEN/AMBER/RED rating tokens must be gone from steering + skill files
    for f in STEERING + [".kiro/skills/ingressmigration/SKILL.md",
                         ".claude/skills/ingressmigration/SKILL.md", "CLAUDE.md"]:
        for tok in ("🟢 GREEN", "🟡 AMBER", "🔴 RED"):
            check(f"no-rating-token:{f}:{tok}", tok not in _read(f),
                  "GREEN/AMBER/RED rating token resurfaced — use Impact 1–5")

    # factual correctness
    for f in DOCS:
        check(f"controllerName:{f}", "gateway.networking.k8s.aws/alb" not in _read(f),
              "wrong GatewayClass controllerName (must be gateway.k8s.aws/alb)")
        check(f"crd-version:{f}", "v1.2.1" not in _read(f),
              "stale Gateway API CRD pin (must be v1.3.0)")
    check("controllerName-correct", has("steering/gateway-api.md", "gateway.k8s.aws/alb"))
    check("lbc-gw-version-l7", has("steering/gateway-api.md", "v2.14"),
          "must state L7 Gateway API needs >= v2.14")
    check("lbc-gw-version-l4", has("steering/gateway-api.md", "v2.13.3"),
          "must state L4 Gateway API needs >= v2.13.3")
    check("no-bad-v27-gw-claim", "v2.7+ supports Gateway API" not in _read("steering/gateway-api.md"),
          "false 'v2.7+ supports Gateway API' claim")
    check("crd-version-correct", has("steering/gateway-api.md", "v1.3.0"))

    # rating model / structure
    check("impact-indicator", has("steering/report-generation.md", "Impact Indicator"))
    check("auto-mode", has("steering/ingress-discovery.md", "eks.amazonaws.com/alb"),
          "EKS Auto Mode awareness missing")
    check("eol-cve-check", has("steering/ingress-discovery.md", "CVE-2023-5044"),
          "controller EOL/CVE check missing")
    check("no-migration-planning-section",
          "## Migration Planning" not in _read("steering/report-generation.md"),
          "Migration Planning section should be removed")
    check("no-investigate-manually",
          "## Investigate Manually" not in _read("steering/report-generation.md"))

    # SKILL.md mirrors identical
    check("skill-mirror-sync",
          _read(".kiro/skills/ingressmigration/SKILL.md") ==
          _read(".claude/skills/ingressmigration/SKILL.md"),
          ".kiro and .claude SKILL.md differ — keep them in sync")

    # renderer NAV structure
    tool = _read("tools/report_to_html.py")
    check("nav-references-group", '"references"' in tool and "export-materials" in tool,
          "References group / Export Materials missing in NAV_SECTIONS")
    check("nav-no-migration-planning", "migration-planning" not in tool,
          "migration-planning still referenced in NAV_SECTIONS")


# ----------------------------------------------------------------- B. ACCURACY
# (anti context-skew: each practitioner/architect lesson must stay taught)
ACCURACY = [
    ("alb-migration.md basic-auth behavior change", "steering/alb-migration.md", "Behavior change"),
    ("alb-migration.md CORS/rate-limit High", "steering/alb-migration.md", "no faithful"),
    ("alb-migration.md class-switch new ALB", "steering/alb-migration.md", "new ALB"),
    ("alb-migration.md DNS cutover", "steering/alb-migration.md", "DNS cutover"),
    ("alb-migration.md internal-elb subnet check", "steering/alb-migration.md", "internal-elb"),
    ("alb-migration.md e2e TLS / backend encryption", "steering/alb-migration.md", "backend-protocol"),
    ("alb-migration.md blast radius", "steering/alb-migration.md", "blast radius"),
    ("migration-risk.md coexist != safe shift", "steering/migration-risk.md", "coexistence in the cluster"),
    ("migration-risk.md sticky-session rollback", "steering/migration-risk.md", "Sticky sessions"),
    ("traffic-routing.md path semantics", "steering/traffic-routing.md", "most specific path wins"),
    ("traffic-routing.md shadow/replay", "steering/traffic-routing.md", "shadow/replay"),
    ("traffic-routing.md snippet blind spot", "steering/traffic-routing.md", "Blind spot"),
    ("report-generation.md snippet manifest gate", "steering/report-generation.md", "INCOMPLETE"),
    ("report-generation.md controller-ownership pre-apply gate", "steering/report-generation.md", "Controller-ownership pre-apply gate"),
    ("ingress-discovery.md snippet-disable sequencing", "steering/ingress-discovery.md", "Remediation sequencing"),
    ("gateway-api.md ownership conflict", "steering/gateway-api.md", "ownership conflict"),
    ("gateway-api.md per-security-boundary", "steering/gateway-api.md", "per-security-boundary"),
    ("impact-indicator execution risk", "steering/report-generation.md", "Execution risk counts"),
    ("migration-plan.md timeline scales to blockers", "steering/migration-plan.md", "scale the timeline"),
]
def group_accuracy():
    for name, f, needle in ACCURACY:
        check("accuracy:" + name, has(f, needle, ci=True),
              f"missing guidance '{needle}' in {f}")


# ----------------------------------------------------------------- C. RENDERER
def group_renderer():
    tool = REPO / "tools" / "report_to_html.py"
    # compiles
    r = subprocess.run([sys.executable, "-m", "py_compile", str(tool)], capture_output=True, text=True)
    check("renderer-compiles", r.returncode == 0, r.stderr.strip())
    if r.returncode != 0:
        return
    d = REPO / "tests" / "eval_data"
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tf:
        out = tf.name
    r = subprocess.run([sys.executable, str(tool), str(d / "report.md"),
                        "--topology", str(d / "topology.json"),
                        "--manifests", str(d / "manifests"), "-o", out],
                       capture_output=True, text=True)
    check("renderer-runs", r.returncode == 0, r.stderr.strip())
    if r.returncode != 0:
        return
    html = pathlib.Path(out).read_text(encoding="utf-8")
    os.unlink(out)

    cases = [
        ("bold renders", "<strong>Controllers" in html),
        ("hot/red emphasis renders", 'class="hot">one is End-of-Life' in html),
        ("nested bullets render", "<ul><li>" in html),
        ("br not escaped literally", "&lt;br&gt;" not in html),
        ("bullet-in-cell renders", "<td><ul>" in html),
        ("orange impact badge renders", "badge orange" in html),
        ("no leftover DL tokens", "[[DL:" not in html),
        ("download buttons present", html.count("data:text/yaml;base64") >= 3),
        ("3D scene present", "UnrealBloomPass" in html and "buildController" in html),
        ("entity-iconic builders", all(b in html for b in ("buildNode", "buildIngress", "buildService"))),
        ("Export Materials section renders", 'data-section="export-materials"' in html),
        ("no Migration Planning", "Migration Planning" not in html),
        ("anchor scoped to cluster", 'href="#c0-blockers"' in html),
        ("controller-link no silent fallback", "||cN[0]" not in html),
    ]
    for name, ok in cases:
        check("renderer:" + name, ok)

    # optional: node --check the inline JS if node is available
    import shutil
    if shutil.which("node"):
        blocks = re.findall(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', html, re.S)
        js = "\n;\n".join(blocks)
        with tempfile.NamedTemporaryFile(suffix=".js", delete=False, mode="w") as jf:
            jf.write(js); jspath = jf.name
        r = subprocess.run(["node", "--check", jspath], capture_output=True, text=True)
        os.unlink(jspath)
        check("renderer:inline-JS-valid", r.returncode == 0, r.stderr.strip()[:200])


def main():
    group_invariants()
    group_accuracy()
    group_renderer()
    total = PASSES + len(FAILS)
    print(f"\nEKS Ingress Migration skill — eval harness")
    print(f"  passed: {PASSES}/{total}")
    if FAILS:
        print(f"  FAILED: {len(FAILS)}")
        for f in FAILS:
            print(f"    ✗ {f}")
        print("\nRESULT: FAIL — a change has dropped skill accuracy or skewed the model.")
        sys.exit(1)
    print("\nRESULT: PASS — skill invariants, accuracy guards, and renderer all intact.")


if __name__ == "__main__":
    main()
