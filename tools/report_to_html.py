#!/usr/bin/env python3
"""Convert Markdown ingress migration report to HTML dashboard with 3D topology and left nav."""

import argparse
import base64
import json
import re
import sys
import html as H
from pathlib import Path


def strip_bold(text: str) -> str:
    return re.sub(r"\*\*(.+?)\*\*", r"\1", text)


def badge_wrap(text: str) -> str:
    for r, cls in [("GREEN", "green"), ("AMBER", "amber"), ("RED", "red"), ("UNKNOWN", "unknown")]:
        text = text.replace(r, f'<span class="badge {cls}">{r}</span>')
    text = text.replace("🟢", '<span class="badge green">●</span>')
    text = text.replace("🟡", '<span class="badge amber">●</span>')
    text = text.replace("🔴", '<span class="badge red">●</span>')
    text = text.replace("⬜", '<span class="badge unknown">●</span>')
    text = text.replace("✅", '<span style="color:#788c5d">✓</span>')
    text = text.replace("❌", '<span style="color:#c44">✗</span>')
    text = text.replace("⚠️", '<span style="color:#d97706">⚠</span>')
    return text


def inline(text: str) -> str:
    t = strip_bold(H.escape(text))
    t = re.sub(r"`(.+?)`", r"<code>\1</code>", t)
    t = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2" target="_blank">\1</a>', t)
    return badge_wrap(t)


def md_table_to_html(lines: list[str]) -> str:
    headers = [c.strip() for c in lines[0].strip().strip("|").split("|")]
    col_count = len(headers)
    hdr = "".join(f"<th>{badge_wrap(strip_bold(H.escape(h)))}</th>" for h in headers)
    rows = ""
    for line in lines[2:]:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        while len(cells) < col_count:
            cells.append("")
        rows += "<tr>" + "".join(f"<td>{badge_wrap(strip_bold(H.escape(c)))}</td>" for c in cells) + "</tr>"
    return f'<div class="table-wrap"><table><thead><tr>{hdr}</tr></thead><tbody>{rows}</tbody></table></div>'


def is_table_sep(line: str) -> bool:
    return bool(re.match(r"^\|[\s\-:|]+\|$", line.strip()))


def convert_md(md_text: str, id_prefix: str = "") -> tuple[str, list[tuple[str, str]]]:
    """Convert markdown to HTML. id_prefix scopes element IDs per cluster (e.g. 'c0-')."""
    lines = md_text.split("\n")
    parts, toc = [], []
    sec = 0
    i = 0
    in_code = False

    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("```"):
            if not in_code:
                in_code = True
                lang = re.match(r"^```(\w+)?", line.strip())
                lang_cls = f' class="language-{lang.group(1)}"' if lang and lang.group(1) else ""
                i += 1
                code_lines = []
                while i < len(lines) and not lines[i].strip().startswith("```"):
                    code_lines.append(H.escape(lines[i]))
                    i += 1
                i += 1
                in_code = False
                parts.append(f'<pre><code{lang_cls}>{chr(10).join(code_lines)}</code></pre>')
                continue
            else:
                in_code = False; i += 1; continue
        if in_code: i += 1; continue
        if re.match(r"^\s{2,}[┌└├│─►┐┘┤┬┴┼\+\-\|]", line): i += 1; continue

        if "|" in line and i + 1 < len(lines) and is_table_sep(lines[i + 1]):
            tbl = [line]; i += 1
            while i < len(lines) and "|" in lines[i]: tbl.append(lines[i]); i += 1
            parts.append(md_table_to_html(tbl)); continue

        if line.startswith("# "):
            pass  # skip H1 — banner handles title
        elif line.startswith("## "):
            title = line[3:].strip()
            slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
            scoped_id = f"{id_prefix}{slug}"
            sec += 1; toc.append((slug, title))
            if sec > 1: parts.append("</div></details>")
            parts.append(
                f'<details class="section" open id="{scoped_id}" data-section="{slug}">'
                f'<summary><h2>{inline(title)}</h2><span class="toggle">▾</span></summary>'
                f'<div class="section-body">')
        elif line.startswith("### "): parts.append(f"<h3>{inline(line[4:])}</h3>")
        elif line.startswith("#### "): parts.append(f"<h4>{inline(line[5:])}</h4>")
        elif line.startswith("> "): parts.append(f'<blockquote>{inline(line[2:])}</blockquote>')
        elif line.startswith("---"): pass
        elif line.strip().startswith("- ") or line.strip().startswith("* "):
            items = []
            while i < len(lines) and (lines[i].strip().startswith("- ") or lines[i].strip().startswith("* ")):
                items.append(inline(lines[i].strip()[2:])); i += 1
            parts.append("<ul>" + "".join(f"<li>{it}</li>" for it in items) + "</ul>"); continue
        elif re.match(r"^\d+\.\s", line.strip()):
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s", lines[i].strip()):
                items.append(inline(re.sub(r"^\d+\.\s*", "", lines[i].strip()))); i += 1
            parts.append("<ol>" + "".join(f"<li>{it}</li>" for it in items) + "</ol>"); continue
        elif line.strip() == "": pass
        else: parts.append(f"<p>{inline(line)}</p>")
        i += 1

    if sec > 0: parts.append("</div></details>")
    return "\n".join(parts), toc


# 3D topology is built inline per cluster in build_html()


CSS = """
:root{--bg:#faf9f5;--surface:#fff;--border:#e8e6dc;--text:#141413;--text2:#b0aea5;--accent:#d97757;--green:#788c5d;--green-bg:#eef2e8;--amber:#d97706;--amber-bg:#fef3c7;--red:#c44;--red-bg:#fceaea;--gray:#b0aea5;--hdr-bg:#141413;--hdr-text:#faf9f5;--radius:6px;--code-bg:#f5f4f0;--nav-w:220px}
[data-theme="dark"]{--bg:#0d1117;--surface:#161b22;--border:#30363d;--text:#e6edf3;--text2:#8b949e;--accent:#ff9900;--green:#2ea043;--green-bg:rgba(46,160,67,.15);--amber:#d29922;--amber-bg:rgba(210,153,34,.15);--red:#f85149;--red-bg:rgba(248,81,73,.15);--gray:#8b949e;--hdr-bg:#010409;--hdr-text:#e6edf3;--code-bg:#1c2128}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Lora',Georgia,serif;background:var(--bg);color:var(--text);line-height:1.7;transition:background .3s,color .3s}
a{color:var(--accent)} a:hover{text-decoration:underline}
code{background:var(--code-bg);border:1px solid var(--border);padding:2px 6px;border-radius:4px;font-size:.85em;font-family:'Courier New',monospace}
pre{background:var(--hdr-bg);color:var(--hdr-text);padding:1rem;border-radius:var(--radius);overflow-x:auto;margin:1rem 0;font-size:.85em}
pre code{background:none;border:none;color:inherit;padding:0}
blockquote{border-left:3px solid var(--amber);padding:.5rem 1rem;margin:.5rem 0;color:var(--text2);background:var(--amber-bg);border-radius:0 var(--radius) var(--radius) 0;font-size:.9rem}
ul,ol{margin:.4rem 0 .4rem 1.5rem} li{margin:.2rem 0}
/* Layout */
.layout{display:flex;min-height:100vh}
.nav{width:var(--nav-w);position:fixed;top:0;left:0;height:100vh;background:var(--hdr-bg);color:var(--hdr-text);padding:1.2rem 0;overflow-y:auto;z-index:10;display:flex;flex-direction:column}
.nav-title{font-family:'Poppins',sans-serif;font-size:.95rem;font-weight:600;padding:0 1rem .8rem;border-bottom:1px solid rgba(255,255,255,.1);margin-bottom:.5rem}
.nav-sub{font-family:'Poppins',sans-serif;font-size:.6rem;text-transform:uppercase;letter-spacing:.08em;opacity:.5;margin-top:.15rem}
.nav-section{font-family:'Poppins',sans-serif;font-size:.6rem;text-transform:uppercase;letter-spacing:.1em;color:rgba(255,255,255,.35);padding:.8rem 1rem .3rem;margin-top:.3rem}
.nav a{display:block;padding:5px 1rem 5px 1.3rem;font-family:'Poppins',sans-serif;font-size:.78rem;color:rgba(255,255,255,.7);text-decoration:none;transition:all .15s;border-left:3px solid transparent}
.nav a:hover{color:#fff;background:rgba(255,255,255,.06);border-left-color:var(--accent)}
.nav a.active{color:#fff;border-left-color:var(--accent);background:rgba(255,255,255,.08)}
.nav-bottom{margin-top:auto;padding:.8rem 1rem;border-top:1px solid rgba(255,255,255,.1)}
.theme-toggle{background:none;border:1px solid rgba(255,255,255,.2);color:var(--hdr-text);padding:5px 10px;border-radius:16px;cursor:pointer;font-family:'Poppins',sans-serif;font-size:.7rem;font-weight:500;width:100%;transition:all .2s}
.theme-toggle:hover{border-color:rgba(255,255,255,.5);background:rgba(255,255,255,.08)}
.content{margin-left:var(--nav-w);flex:1;padding:2rem 2.5rem;max-width:1000px}
/* Sections */
details.section{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);margin:1rem 0;overflow:hidden;transition:background .3s,border-color .3s}
details.section summary{display:flex;align-items:center;justify-content:space-between;padding:.75rem 1rem;cursor:pointer;list-style:none;background:var(--bg);border-bottom:1px solid var(--border)}
details.section summary::-webkit-details-marker{display:none}
details.section summary h2{font-family:'Poppins',sans-serif;font-size:.8rem;font-weight:500;text-transform:uppercase;letter-spacing:.05em;color:var(--text2);margin:0}
.toggle{color:var(--text2);transition:transform .2s;font-size:.8rem} details.section[open] .toggle{transform:rotate(180deg)}
.section-body{padding:1rem}
h3{font-family:'Poppins',sans-serif;font-size:.95rem;color:var(--text);margin:1.2rem 0 .5rem;font-weight:600}
h4{font-family:'Poppins',sans-serif;font-size:.85rem;color:var(--text2);margin:1rem 0 .4rem;font-weight:500}
p{margin:.4rem 0;font-size:.95rem}
.table-wrap{overflow-x:auto;margin:.8rem 0}
table{border-collapse:collapse;width:100%;font-size:.85rem;border:1px solid var(--border);border-radius:var(--radius)}
th{background:var(--hdr-bg);color:var(--hdr-text);padding:10px 14px;text-align:left;font-family:'Poppins',sans-serif;font-weight:500;font-size:.75rem;text-transform:uppercase;letter-spacing:.03em;white-space:nowrap}
td{padding:8px 14px;border-bottom:1px solid var(--border);word-break:break-word}
td:first-child{white-space:nowrap;font-weight:500}
tr:hover td{background:var(--bg)}
.badge{display:inline-block;padding:2px 10px;border-radius:20px;font-family:'Poppins',sans-serif;font-size:.7rem;font-weight:600;letter-spacing:.03em;white-space:nowrap}
.green{background:var(--green-bg);color:var(--green)} .amber{background:var(--amber-bg);color:var(--amber)}
.red{background:var(--red-bg);color:var(--red)} .unknown{background:#f0f0ec;color:var(--gray)}
.hint{color:var(--text2);font-size:.8rem;margin-bottom:.5rem;font-style:italic}
.topo-info{margin-top:.5rem;padding:.5rem .8rem;font-size:.85rem;color:var(--text2);min-height:1.6em;background:var(--surface);border-radius:var(--radius);border:1px solid var(--border)}
.topo-legend{display:flex;flex-wrap:wrap;gap:1rem;margin-top:.5rem;font-family:'Poppins',sans-serif;font-size:.75rem;color:var(--text2)}
.dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:4px;vertical-align:middle}
footer{font-family:'Poppins',sans-serif;font-size:.75rem}
@media(max-width:768px){.nav{display:none}.content{margin-left:0;padding:1rem}}
@media print{.nav{display:none}.content{margin-left:0}details.section{break-inside:avoid}#topo-wrap{display:none}}
"""


NAV_SECTIONS = [
    ("overview", "Overview", ["executive-summary"]),
    ("assessment", "Assessment Summary", ["assessment-summary", "current-configuration", "ingress-discovery"]),
    ("routing", "Routing Topology", ["routing-topology", "traffic-routing"]),
    ("migration", "Migration Approach", ["migration-options", "export-manifests"]),
    ("appendix", "Appendix", ["blockers", "recommendations", "investigate-manually", "ingress-resource-analysis", "dns-certificates", "migration-risk", "migration-planning", "aws-reference-links"]),
]


def _build_manifest_section(cluster_idx: int, cluster_name: str, manifests: dict) -> str:
    """Build HTML section with embedded manifest files and download buttons."""
    current_files = {k: v for k, v in manifests.items() if k.startswith("current/")}
    target_files = {k: v for k, v in manifests.items() if k.startswith("target/")}

    # Build file list tables
    current_rows = ""
    for fname, content in sorted(current_files.items()):
        short = fname.replace("current/", "")
        b64 = base64.b64encode(content.encode()).decode()
        current_rows += f'<tr><td><code>{H.escape(short)}</code></td><td><a href="data:text/yaml;base64,{b64}" download="{H.escape(short)}">⬇ Download</a></td></tr>'

    target_rows = ""
    for fname, content in sorted(target_files.items()):
        short = fname.replace("target/", "")
        b64 = base64.b64encode(content.encode()).decode()
        target_rows += f'<tr><td><code>{H.escape(short)}</code></td><td><a href="data:text/yaml;base64,{b64}" download="{H.escape(short)}">⬇ Download</a></td></tr>'

    # Combined zip-like download (all files concatenated with separators)
    all_target = ""
    for fname, content in sorted(target_files.items()):
        short = fname.replace("target/", "")
        all_target += f"---\n# Source: {short}\n{content}\n"
    all_b64 = base64.b64encode(all_target.encode()).decode() if all_target else ""

    download_all_btn = ""
    if all_b64:
        download_all_btn = f'<a href="data:text/yaml;base64,{all_b64}" download="{H.escape(cluster_name)}-gateway-api-manifests.yaml" style="display:inline-block;margin:.8rem 0;padding:8px 16px;background:var(--accent);color:#fff;border-radius:var(--radius);text-decoration:none;font-family:Poppins,sans-serif;font-size:.8rem;font-weight:500;">⬇ Download All Target Manifests</a>'

    return f'''<details class="section" data-section="export-manifests" open>
<summary><h2>Export Manifests</h2><span class="toggle">▼</span></summary>
<div class="section-body">
<p style="font-size:.9rem;color:var(--text2);margin-bottom:1rem;">Ready-to-apply YAML manifests generated from the assessment. Review before applying.</p>
{download_all_btn}
<h3>Current Ingress (backup)</h3>
{"<div class='table-wrap'><table><thead><tr><th>File</th><th>Action</th></tr></thead><tbody>" + current_rows + "</tbody></table></div>" if current_rows else "<p style='color:var(--text2);font-size:.85rem;'>No Ingress resources to export.</p>"}
<h3>Target Gateway API</h3>
{"<div class='table-wrap'><table><thead><tr><th>File</th><th>Action</th></tr></thead><tbody>" + target_rows + "</tbody></table></div>" if target_rows else "<p style='color:var(--text2);font-size:.85rem;'>No target manifests generated.</p>"}
<blockquote>Apply target manifests in order: <code>kubectl apply -f 00-gateway-api-crds.yaml</code> then <code>01-</code>, <code>02-</code>, etc.</blockquote>
</div>
</details>'''


def build_html(clusters: list[dict]) -> str:
    """Build HTML with cluster dropdown if multiple clusters.
    clusters: list of {"name": str, "body": str, "toc": list, "topology_json": str|None}
    """
    multi = len(clusters) > 1

    # Build cluster selector
    selector_html = ""
    if multi:
        opts = "".join(f'<option value="{i}">{H.escape(c["name"])}</option>' for i, c in enumerate(clusters))
        selector_html = f'<div class="cluster-select"><label>Cluster</label><select id="cluster-sel" onchange="switchCluster(this.value)">{opts}</select></div>'

    # Build nav links from first cluster's TOC (structure is same for all)
    nav_links = ""
    toc = clusters[0]["toc"]
    for group_id, group_label, slugs in NAV_SECTIONS:
        nav_links += f'<div class="nav-section">{H.escape(group_label)}</div>\n'
        for slug, title in toc:
            if slug in slugs or any(slug.startswith(s) for s in slugs):
                nav_links += f'<a href="#{slug}">{H.escape(strip_bold(title))}</a>\n'
        if group_id == "overview":
            nav_links += '<a href="#topo-wrap">3D Architecture</a>\n'

    # Build per-cluster content divs
    cluster_divs = ""
    topo_data_array = []
    for i, c in enumerate(clusters):
        display = "block" if i == 0 else "none"
        topo_html = ""
        if c["topology_json"]:
            topo_html = f'<div id="c{i}-topo-wrap" data-section="topo-wrap"><p class="hint">Drag to orbit · Scroll to zoom · Click a node for details</p><div id="topo-{i}" class="topo-canvas" style="width:100%;height:520px;border-radius:8px;overflow:hidden;border:1px solid var(--border);background:#0a0e14;"></div><div class="topo-info"></div><div class="topo-legend"><span><span class="dot" style="background:#8b949e"></span> Node</span><span><span class="dot" style="background:#ff9900"></span> Controller</span><span><span class="dot" style="background:#58a6ff"></span> Ingress</span><span><span class="dot" style="background:#2ea043"></span> Service</span><span><span class="dot" style="background:#bc8cff"></span> Gateway API</span></div></div>'
            topo_data_array.append(c["topology_json"])
        else:
            topo_data_array.append("null")

        # Build manifest export section
        manifest_html = ""
        if c.get("manifests"):
            manifest_html = _build_manifest_section(i, c["name"], c["manifests"])

        cluster_divs += f'<div class="cluster-panel" id="cluster-{i}" style="display:{display}">\n{topo_html}\n{c["body"]}\n{manifest_html}\n</div>\n'

    # Topology JS data
    topo_js_array = "[" + ",".join(topo_data_array) + "]"

    # Manifests JS data
    manifests_data = []
    for c in clusters:
        manifests_data.append(json.dumps(c.get("manifests") or {}, ensure_ascii=False))
    manifests_js = "[" + ",".join(manifests_data) + "]"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Ingress Assessment &amp; Migration</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@500;600&family=Lora:wght@400;500&display=swap" rel="stylesheet">
<style>{CSS}
.cluster-select{{padding:.8rem 1rem;border-bottom:1px solid rgba(255,255,255,.1);margin-bottom:.3rem}}
.cluster-select label{{font-family:'Poppins',sans-serif;font-size:.6rem;text-transform:uppercase;letter-spacing:.1em;color:rgba(255,255,255,.4);display:block;margin-bottom:.4rem}}
.cluster-select select{{width:100%;background:#1a1a2e;color:#fff;border:1px solid rgba(255,255,255,.25);border-radius:6px;padding:8px 10px;font-family:'Poppins',sans-serif;font-size:.85rem;font-weight:600;cursor:pointer;appearance:none;-webkit-appearance:none;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23fff' d='M6 8L1 3h10z'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 10px center}}
.cluster-select select:hover{{border-color:var(--accent)}}
.cluster-select select:focus{{outline:none;border-color:var(--accent);box-shadow:0 0 0 2px rgba(217,119,87,.3)}}
.cluster-select select option{{background:#1a1a2e;color:#fff;padding:6px}}
.topo-canvas{{width:100%;height:520px}}
</style>
</head>
<body>
<div class="layout">
<nav class="nav">
  <div class="nav-title">Ingress Assessment<br>&amp; Migration<div class="nav-sub">EKS Cluster Report</div></div>
{selector_html}
{nav_links}
  <div class="nav-bottom"><button class="theme-toggle" onclick="exportManifests()" id="export-btn" style="margin-bottom:6px;background:var(--accent);border-color:var(--accent);color:#fff;">⬇ Export Manifests</button><button class="theme-toggle" onclick="toggleTheme()" id="theme-btn">🌙 Dark</button></div>
</nav>
<main class="content">
{cluster_divs}
<footer style="margin-top:2rem;padding-top:1rem;border-top:1px solid var(--border);color:var(--text2);">
Generated by EKS Ingress Migration Skill
</footer>
</main>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
<script>
const TOPOS={topo_js_array};
const MANIFESTS={manifests_js};
let activeCluster=0;
function exportManifests(){{
  const m=MANIFESTS[activeCluster];
  if(!m||!Object.keys(m).length){{alert('No manifests available for this cluster.');return;}}
  let content='';
  Object.keys(m).sort().forEach(k=>{{content+='---\\n# Source: '+k+'\\n'+m[k]+'\\n';}});
  const blob=new Blob([content],{{type:'text/yaml'}});
  const url=URL.createObjectURL(blob);
  const a=document.createElement('a');
  const name=(TOPOS[activeCluster]&&TOPOS[activeCluster].cluster)||'cluster';
  a.href=url;a.download=name+'-gateway-api-manifests.yaml';a.click();
  URL.revokeObjectURL(url);
}}
function switchCluster(idx){{
  activeCluster=parseInt(idx);
  document.querySelectorAll('.cluster-panel').forEach((p,i)=>p.style.display=i==activeCluster?'block':'none');
  initTopo(activeCluster);
  setupObserver();
}}
function getActivePanel(){{return document.getElementById('cluster-'+activeCluster);}}
function setupObserver(){{
  const links=document.querySelectorAll('.nav a[href^="#"]');
  links.forEach(l=>l.classList.remove('active'));
  const panel=getActivePanel();if(!panel)return;
  if(window._navObs)window._navObs.disconnect();
  window._navObs=new IntersectionObserver(entries=>{{
    entries.forEach(e=>{{if(e.isIntersecting){{
      const sec=e.target.getAttribute('data-section');
      if(!sec)return;
      links.forEach(l=>l.classList.remove('active'));
      const a=document.querySelector('.nav a[href="#'+sec+'"]');
      if(a)a.classList.add('active');
    }}}});
  }},{{threshold:0.3}});
  panel.querySelectorAll('[data-section]').forEach(el=>window._navObs.observe(el));
}}
function initTopo(idx){{
  const T=TOPOS[idx];if(!T)return;
  const cid='topo-'+idx,C=document.getElementById(cid);
  if(!C||C.dataset.init)return;C.dataset.init='1';
  const info=C.parentElement.querySelector('.topo-info');
  const W=C.clientWidth,HH=C.clientHeight;
  const scene=new THREE.Scene();scene.background=new THREE.Color(0x0a0e14);
  const cam=new THREE.PerspectiveCamera(50,W/HH,0.1,1000);cam.position.set(0,8,22);
  const R=new THREE.WebGLRenderer({{antialias:true}});R.setSize(W,HH);R.setPixelRatio(window.devicePixelRatio);C.appendChild(R.domElement);
  const ctrl=new THREE.OrbitControls(cam,R.domElement);ctrl.enableDamping=true;ctrl.dampingFactor=0.08;
  scene.add(new THREE.AmbientLight(0xffffff,0.6));
  const dl=new THREE.DirectionalLight(0xffffff,0.8);dl.position.set(5,10,7);scene.add(dl);
  const grid=new THREE.GridHelper(24,24,0x1a2030,0x1a2030);grid.position.y=-4;scene.add(grid);
  const meshes=[];
  function mat(col){{return new THREE.MeshStandardMaterial({{color:col,roughness:0.35,metalness:0.3,emissive:col,emissiveIntensity:0.12}});}}
  function mkN(x,y,z,col,shape,sz,ud){{let g;if(shape==='box')g=new THREE.BoxGeometry(sz*1.4,sz*1.4,sz*1.4);else if(shape==='sphere')g=new THREE.SphereGeometry(sz,24,24);else if(shape==='oct')g=new THREE.OctahedronGeometry(sz);else if(shape==='cone')g=new THREE.ConeGeometry(sz*0.7,sz*1.6,24);else g=new THREE.DodecahedronGeometry(sz);const m=new THREE.Mesh(g,mat(col));m.position.set(x,y,z);m.userData=ud;scene.add(m);meshes.push(m);return m;}}
  function pipe(a,b,col){{const dir=new THREE.Vector3().subVectors(b.position,a.position);const len=dir.length();const g=new THREE.CylinderGeometry(0.04,0.04,len,8);const m=new THREE.Mesh(g,new THREE.MeshStandardMaterial({{color:col,transparent:true,opacity:0.6}}));m.position.copy(a.position).add(dir.multiplyScalar(0.5));m.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),dir.normalize());scene.add(m);}}
  function txt(s,pos,col){{const c=document.createElement('canvas');c.width=512;c.height=64;const x=c.getContext('2d');x.font='bold 24px -apple-system,sans-serif';x.fillStyle=col||'#e6edf3';x.textAlign='center';x.fillText(s.length>30?s.slice(0,27)+'...':s,256,40);const t=new THREE.CanvasTexture(c);const sp=new THREE.Sprite(new THREE.SpriteMaterial({{map:t,transparent:true}}));sp.position.copy(pos);sp.position.y+=0.8;sp.scale.set(3,0.38,1);scene.add(sp);}}
  const nodes=T.nodes||[],ctrls_d=T.controllers||[],ings=T.ingresses||[],svcs=T.services||[],gw=T.gatewayApi||{{}};
  const LX_N=-12,LX_C=-6,LX_I=0,LX_S=6;
  const nN=[];nodes.forEach((n,i)=>{{const y=(i-(nodes.length-1)/2)*2.5;const m=mkN(LX_N,y,0,0x8b949e,'box',0.45,{{type:'Node',name:n.name,instanceId:n.instanceId,instanceType:n.instanceType,zone:n.zone}});txt(n.instanceId||n.name,m.position,'#8b949e');nN.push(m);}});
  const cN=[];ctrls_d.forEach((c,i)=>{{const y=(i-(ctrls_d.length-1)/2)*3;const m=mkN(LX_C,y,0,0xff9900,'sphere',0.55,{{type:'Controller',...c}});txt(c.name,m.position,'#ff9900');cN.push(m);nN.forEach(n=>pipe(n,m,0x8b949e));}});
  const iN=[];ings.forEach((ing,i)=>{{const y=(i-(ings.length-1)/2)*2.2;const m=mkN(LX_I,y,0,0x58a6ff,'oct',0.4,{{type:'Ingress',...ing}});txt((ing.hosts&&ing.hosts[0])||ing.name,m.position,'#58a6ff');iN.push(m);const cn=cN.find(c=>c.userData.name===ing.controller)||cN[0];if(cn)pipe(cn,m,0xff9900);}});
  const sN={{}};svcs.forEach((s,i)=>{{const y=(i-(svcs.length-1)/2)*2;const m=mkN(LX_S,y,0,0x2ea043,'cone',0.35,{{type:'Service',...s}});txt(s.name,m.position,'#2ea043');sN[s.namespace+'/'+s.name]=m;}});
  ings.forEach((ing,idx)=>{{(ing.paths||[]).forEach(p=>{{const k=(ing.namespace||'default')+'/'+p.backend;if(sN[k])pipe(iN[idx],sN[k],0x58a6ff);}});}});
  (gw.gateways||[]).forEach((g,i)=>{{mkN(LX_I,-((ings.length)/2+2+i*2.5),3,0xbc8cff,'dodec',0.45,{{type:'Gateway',...g}});}});
  (gw.httpRoutes||[]).forEach((r,i)=>{{mkN(LX_S-2,-((ings.length)/2+2+i*2),3,0xd2a8ff,'dodec',0.32,{{type:'HTTPRoute',...r}});}});
  const rc=new THREE.Raycaster(),mse=new THREE.Vector2();
  R.domElement.addEventListener('click',e=>{{const rect=R.domElement.getBoundingClientRect();mse.x=((e.clientX-rect.left)/rect.width)*2-1;mse.y=-((e.clientY-rect.top)/rect.height)*2+1;rc.setFromCamera(mse,cam);const h=rc.intersectObjects(meshes);if(h.length&&info){{const d=h[0].object.userData;let t='<strong>'+d.type+':</strong> '+(d.name||'');if(d.instanceId)t+=' · '+d.instanceId;if(d.instanceType)t+=' · '+d.instanceType;if(d.zone)t+=' · '+d.zone;if(d.namespace)t+=' <em>('+d.namespace+')</em>';if(d.version)t+=' · v'+d.version;if(d.hosts)t+=' · '+d.hosts.join(', ');if(d.ports)t+=' · ports: '+d.ports.join(', ');if(d.paths)t+=' · '+d.paths.length+' path(s)';info.innerHTML=t;}}}});
  function anim(){{requestAnimationFrame(anim);ctrl.update();R.render(scene,cam);}}anim();
  window.addEventListener('resize',()=>{{const w=C.clientWidth,h=C.clientHeight;cam.aspect=w/h;cam.updateProjectionMatrix();R.setSize(w,h);}});
}}
function toggleTheme(){{
  const h=document.documentElement,b=document.getElementById('theme-btn');
  if(h.getAttribute('data-theme')==='dark'){{h.removeAttribute('data-theme');b.textContent='🌙 Dark';localStorage.setItem('theme','light');}}
  else{{h.setAttribute('data-theme','dark');b.textContent='☀️ Light';localStorage.setItem('theme','dark');}}
}}
(function(){{
  const s=localStorage.getItem('theme');
  if(s==='dark'||(!s&&window.matchMedia('(prefers-color-scheme:dark)').matches)){{
    document.documentElement.setAttribute('data-theme','dark');
    document.getElementById('theme-btn').textContent='☀️ Light';
  }}
  initTopo(0);
  // Nav click: find matching section in active cluster panel
  document.querySelectorAll('.nav a[href^="#"]').forEach(link=>{{
    link.addEventListener('click',function(ev){{
      ev.preventDefault();
      const section=this.getAttribute('href').slice(1);
      const panel=getActivePanel();if(!panel)return;
      const el=panel.querySelector('[data-section="'+section+'"]');
      if(!el)return;
      if(el.tagName==='DETAILS'&&!el.open)el.open=true;
      const parent=el.closest('details');
      if(parent&&!parent.open)parent.open=true;
      setTimeout(()=>el.scrollIntoView({{behavior:'smooth',block:'start'}}),50);
    }});
  }});
  setupObserver();
}})();
</script>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description="Convert MD report(s) to HTML dashboard")
    parser.add_argument("reports", nargs="+", help="Path(s) to markdown report(s)")
    parser.add_argument("--topology", nargs="*", help="Path(s) to topology JSON file(s), one per report")
    parser.add_argument("--manifests", nargs="*", help="Path(s) to manifest directories, one per report")
    parser.add_argument("-o", "--output", help="Output HTML file path")
    args = parser.parse_args()

    topos = args.topology or []
    manifest_dirs = args.manifests or []
    clusters = []

    for i, report_path in enumerate(args.reports):
        md_path = Path(report_path)
        if not md_path.exists():
            print(f"File not found: {md_path}"); sys.exit(1)

        md_text = md_path.read_text(encoding="utf-8")
        body, toc = convert_md(md_text, id_prefix=f"c{i}-")

        # Extract cluster name: prefer topology JSON "cluster" field, fallback to filename
        name = None
        topology_json = None
        if i < len(topos):
            topo_path = Path(topos[i])
            if topo_path.exists():
                topology_json = topo_path.read_text(encoding="utf-8").strip()
                try:
                    name = json.loads(topology_json).get("cluster")
                except (json.JSONDecodeError, AttributeError):
                    pass
                print(f"📊 Topology loaded: {topo_path}")
        if not name:
            # Strip "EKS-Ingress-Migration-" prefix and date suffix (YYYY-MM-DD-HHMM)
            stem = md_path.stem.replace("EKS-Ingress-Migration-", "")
            name = re.sub(r"-\d{4}-\d{2}-\d{2}-\d{4}$", "", stem)

        # Load manifests
        manifests = {}
        if i < len(manifest_dirs):
            mdir = Path(manifest_dirs[i])
            if mdir.is_dir():
                for sub in ["current", "target"]:
                    sub_path = mdir / sub
                    if sub_path.is_dir():
                        for f in sorted(sub_path.glob("*.yaml")):
                            manifests[f"{sub}/{f.name}"] = f.read_text(encoding="utf-8")
                print(f"📦 Manifests loaded: {mdir} ({len(manifests)} files)")

        clusters.append({"name": name, "body": body, "toc": toc, "topology_json": topology_json, "manifests": manifests})

    html_out = build_html(clusters)
    out_path = Path(args.output) if args.output else Path(args.reports[0]).with_suffix(".html")
    out_path.write_text(html_out, encoding="utf-8")
    print(f"✅ HTML report: {out_path} ({len(clusters)} cluster(s))")


if __name__ == "__main__":
    main()
