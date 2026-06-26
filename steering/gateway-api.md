# Gateway API Prerequisites (input to Migration Options → Option 1)

> **Not a standalone rated section.** These findings feed **Option 1 (Gateway API)** in the report (`report-generation.md`). "Not yet installed" prerequisites are **🟡 Low impact** (easy to deploy) per the *Impact Indicator* — never a standalone blocker. All checks are **read-only** (`kubectl get/describe`, `aws … describe/list`).

## Version & naming facts (cite these)
- AWS LB Controller Gateway API support: **L4 (TCP/UDP/TLSRoute) ≥ v2.13.3**, **L7 (HTTPRoute/GRPCRoute) ≥ v2.14** (GA from the 2026 release line).
- GatewayClass `controllerName`: **`gateway.k8s.aws/alb`**. The LBC targets Gateway API CRDs **v1.3.0**.
- On **EKS Auto Mode**, Gateway API / load balancing is provided **built-in** via the `eks.amazonaws.com` API group — no self-managed LBC install needed.

## Caveats & Risks (MUST surface in Option 1)
- **L7 feature parity is still maturing** — verify the TLS handling and routing filters each route needs against the installed LBC version **before** cutover.
- **EKS Auto Mode + self-managed LBC ownership conflict** — if both run, two reconcilers contend for the same load balancer; scope distinct `GatewayClass`/`IngressClass` per controller, or reconcile to a single owner before any apply. Flag whenever both are present.
- **Blast radius** — prefer **per-security-boundary Gateways** (e.g. `public-gateway` for web, separate `private-gateway` for payments) over one shared Gateway, even at extra cost.

## Prerequisite checks (read-only — gather for Option 1, Phase 1)
1. **CRDs** — `kubectl get crd | grep gateway.networking.k8s.io`; need `GatewayClass`, `Gateway`, `HTTPRoute`, `ReferenceGrant` at v1. If missing → install `standard-install.yaml` **v1.3.0** (a low-impact Phase-1 step).
2. **Controller version** — `aws-load-balancer-controller` image tag **≥ v2.14** (L7) / **≥ v2.13.3** (L4); IRSA/Pod Identity present; healthy with 2+ replicas. `< v2.14` → upgrade in Phase 1. Built-in on Auto Mode.
3. **GatewayClass** — `spec.controllerName: gateway.k8s.aws/alb`, status `Accepted: True`. None → create in Phase 1.
4. **Adoption status** — list existing `Gateway`/`HTTPRoute`/`GRPCRoute` to tell greenfield from a partial migration (informational).

Record these as **Option 1 Phase-1 foundation steps**, not standalone high-impact findings.

## Automated path: `lbc-migrate` + dry-run equivalence (recommended execution for the Gateway API target)

> **Assessment stays read-only.** The skill never runs these tools — surface them as the **recommended execution path** the team can use once a Gateway API target is chosen. They make Option 1 safer and lower-effort than hand-rolling and eyeballing manifests.

AWS LB Controller now ships an official Ingress→Gateway API migration toolchain (LBC docs: *Ingress To Gateway Migration*). Two pieces:

- **`lbc-migrate` CLI** — translates Ingress resources (annotations, path rules, IngressGroups) into Gateway API YAML (`GatewayClass`, `Gateway`, `HTTPRoute`) plus LBC CRDs (`LoadBalancerConfiguration`, `TargetGroupConfiguration`, `ListenerRuleConfiguration`). Run `lbc-migrate --from-cluster --namespaces <ns> --output-dir ./gw/` for the most accurate output — file-based input misses Service-level annotations and IngressClassParams overrides. Default `--dry-run=true` stamps the generated Gateways with `gateway.k8s.aws/dry-run: "true"`.
- **Migration Console** (`lbc-migrate --console`, `http://localhost:8080`) — local **read-only** web UI that compares the **AWS resource plans** of the ingress controller vs the gateway controller field-by-field (LoadBalancer, Listeners, ListenerRules, TargetGroups, SecurityGroups) **before** any ALB is created. Uses the current kubeconfig; needs cluster-wide `list` on Gateways and Ingresses.

### Applicability to this skill's multi-target scope (cite in Option 1)
- **Routes already on the ALB Ingress controller → Gateway API:** `lbc-migrate` is the **faithful** converter — recommend it directly. This is exactly the case the doc targets.
- **NGINX → Gateway API:** `lbc-migrate` translates **LBC/ALB** Ingress, **not** NGINX annotations. The skill still owns the NGINX→HTTPRoute mapping (`traffic-routing.md`, `alb-migration.md`). But the **dry-run equivalence check and parallel-ALB cutover practice below apply to any Gateway manifests** — hand-generated or tool-generated.
- **Other targets (ATX, future options):** unaffected — this is an additive enhancement to the Gateway API path only. Keep all options presented evenly.

### Dry-run equivalence verification (the key practice to adopt)
A pre-apply equivalence gate that creates **zero** AWS resources:
1. Enable controller feature gate `IngressPlanAnnotation=true` (Helm: `--set controllerConfig.featureGates.IngressPlanAnnotation=true`) — the ingress controller publishes its built plan to `alb.ingress.kubernetes.io/dry-run-plan` (for an IngressGroup, only the primary member by lowest `group.order` gets it).
2. Apply the generated Gateway manifests carrying `gateway.k8s.aws/dry-run: "true"` — the gateway controller writes its plan to `gateway.k8s.aws/dry-run-plan` **without provisioning an ALB**.
3. Run the Migration Console and review the field-by-field diff; proceed only when every "Changed / Added / Removed" is understood and accepted (known artifacts like naming/health-check defaults are filtered by default).

### Before you start — scan for known blockers (feed Migration Risk 6.4)
- **Not-supported annotations** — WAF **Classic** (`waf-acl-id` / `web-acl-id`) and all `frontend-nlb-*` have no Gateway equivalent. Resolve first (e.g. migrate WAF Classic → WAFv2).
- **Known differences from Ingress** — `group.order` priority handling and ALB rule count/priority differ; verify rule ordering after translation.
- **External Target Group references** in `actions.*` — only one ALB can own an external TG at a time, so the Gateway ALB cannot attach a TG the Ingress ALB is still using. Resolve ownership before apply.
- **Cross-namespace IngressGroups** — run `lbc-migrate` with `--all-namespaces` (or list every namespace the group spans), or the output is incomplete.

### Safe parallel-ALB cutover (6 steps, rollback at each)
1. **Translate** (`lbc-migrate`) → rollback: delete generated files.
2. **Dry-run preview** (console diff) → rollback: delete the dry-run Gateway.
3. **Apply Gateway manifests** → LBC creates **new ALBs alongside** the existing Ingress ALBs, pointing at the **same Services/Pods**; existing traffic is undisturbed → rollback: delete Gateway resources.
4. **Verify** new ALBs — `Programmed=True`, target health, listeners/SG/cert correct, CloudWatch 5xx/latency normal.
5. **Shift traffic** gradually (DNS / weighted) — apply the L4→L7 and stale-DNS caveats in `migration-risk.md` 6.1 → rollback: shift back.
6. **Cleanup** — delete old Ingress, disable `IngressPlanAnnotation`, remove any temporary traffic-management resources.

> **Cost caveat (surface in Migration Plan):** both the old Ingress ALBs and the new Gateway ALBs run in parallel through steps 3–5 — expect **duplicate ALB-hours + LCU-hours** until cleanup completes.

### References
- Ingress→Gateway Migration Guide: https://kubernetes-sigs.github.io/aws-load-balancer-controller/latest/guide/ingress2gateway/migrate_from_ingress/
- `lbc-migrate` reference (flags, annotation-support table, known differences): https://kubernetes-sigs.github.io/aws-load-balancer-controller/latest/guide/ingress2gateway/lbc_migrate_reference/
- Migration Console (UI, diff classification, RBAC): https://kubernetes-sigs.github.io/aws-load-balancer-controller/latest/guide/ingress2gateway/in_cluster_console/
