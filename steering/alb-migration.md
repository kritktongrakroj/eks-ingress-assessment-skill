# ALB Controller Migration Path

## Purpose
Guide migration from NGINX Ingress Controller to AWS Load Balancer Controller (ALB Ingress), converting all NGINX-specific annotations to their ALB equivalents.

## When to Recommend This Path

- Customer wants to stay on Ingress API (not ready for Gateway API)
- Customer needs ALB features (WAF, Cognito/OIDC, Shield)
- Customer has AWS Transform (ATX) access → fully automated migration
- Customer is on Classic Load Balancer via NGINX and wants ALB

## Annotation Mapping: NGINX → ALB

### Core Changes (Every Ingress)

| Step | Before (NGINX) | After (ALB) |
|------|----------------|-------------|
| IngressClass | `ingressClassName: nginx` | `ingressClassName: alb` |
| Deprecated class | `kubernetes.io/ingress.class: "nginx"` annotation | Remove annotation, add `spec.ingressClassName: alb` |
| Scheme | (implicit: CLB) | `alb.ingress.kubernetes.io/scheme: internet-facing` or `internal` |
| Target type | (implicit: NodePort) | `alb.ingress.kubernetes.io/target-type: ip` |

### URI Rewrite

| Before (NGINX) | After (ALB) |
|----------------|-------------|
| `nginx.ingress.kubernetes.io/use-regex: "true"` | Remove |
| `nginx.ingress.kubernetes.io/rewrite-target: /$2` | `alb.ingress.kubernetes.io/transforms.<svc>` with url-rewrite JSON |
| `path: /something(/\|$)(.*)` + `pathType: ImplementationSpecific` | `path: /something` + `pathType: Prefix` |

**Transforms JSON format:**
```yaml
alb.ingress.kubernetes.io/transforms.<service-name>: |
  [
    {
      "type": "url-rewrite",
      "urlRewriteConfig": {
        "rewrites": [
          {
            "regex": "^\\/something\\/(.*)$",
            "replace": "/$1"
          }
        ]
      }
    }
  ]
```

**Rules:**
- `<service-name>` must match the backend service name in `spec.rules`
- Forward slashes in regex must be escaped as `\\/` in JSON
- NGINX `$2` often becomes ALB `$1` (ALB doesn't need the separator capture group)
- Multi-path Ingress needs separate `transforms.<svc>` per backend service

### TLS / Certificates

| Before (NGINX) | After (ALB) |
|----------------|-------------|
| `spec.tls[].secretName: my-secret` | Remove `spec.tls` section entirely |
| K8s Secret with cert/key | `alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:...` |
| Multiple TLS secrets | Comma-separated ARNs, or `alb.ingress.kubernetes.io/certificate-discovery: "true"` |
| `nginx...ssl-redirect: "true"` | `alb.ingress.kubernetes.io/ssl-redirect: "443"` |
| (none) | `alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}, {"HTTPS": 443}]'` |
| (none) | `alb.ingress.kubernetes.io/ssl-policy: ELBSecurityPolicy-TLS13-1-2-2021-06` |

**Post-migration:** Remove orphaned K8s TLS Secrets that are no longer referenced.

### Proxy Timeouts

| Before (NGINX) | After (ALB) |
|----------------|-------------|
| `nginx...proxy-read-timeout: "120"` | `alb.ingress.kubernetes.io/target-group-attributes: idle_timeout.timeout_seconds=120` |
| `nginx...proxy-send-timeout: "120"` | (same — ALB uses single idle timeout) |

### CORS

| Before (NGINX) | After (ALB) |
|----------------|-------------|
| `nginx...enable-cors: "true"` | Remove — handle via AWS WAF or application-level |
| `nginx...cors-allow-origin` | Remove — handle via AWS WAF or application-level |
| `nginx...cors-allow-methods` | Remove — handle via AWS WAF or application-level |
| `nginx...cors-allow-headers` | Remove — handle via AWS WAF or application-level |

**Note:** Add comment in manifest: `# REMOVED: CORS — configure via AWS WAF rules or application middleware`

### Authentication

| Before (NGINX) | After (ALB) |
|----------------|-------------|
| `nginx...auth-url` + `nginx...auth-signin` | `alb.ingress.kubernetes.io/auth-type: oidc` |
| (external auth service) | `alb.ingress.kubernetes.io/auth-idp-oidc: '{"issuer":"...","authorizationEndpoint":"...","tokenEndpoint":"...","userInfoEndpoint":"...","secretName":"..."}'` |

### Body Size

| Before (NGINX) | After (ALB) |
|----------------|-------------|
| `nginx...proxy-body-size: "50m"` | Remove — no ALB annotation equivalent |

**Note:** Add comment: `# REMOVED: proxy-body-size — configure at application level`

### Access Control / Internal

| Before (NGINX) | After (ALB) |
|----------------|-------------|
| `nginx...whitelist-source-range: "10.0.0.0/8"` | `alb.ingress.kubernetes.io/scheme: internal` |
| (IP restriction) | Use ALB security groups for IP-based access control |

### ALB Grouping (Cost Optimization)

To share a single ALB across multiple Ingress resources:
```yaml
alb.ingress.kubernetes.io/group.name: shared-alb
alb.ingress.kubernetes.io/group.order: "10"
```

## Migration Phases (ALB Path)

### Phase 1: Prerequisites
1. Install AWS Load Balancer Controller (v2.7+)
2. Provision ACM certificates for all TLS hosts
3. Ensure IAM roles/policies for LB Controller

### Phase 2: Convert Manifests
1. Apply annotation mapping (above) to each Ingress
2. Use ATX for automated conversion (if available) — see `steering/atx-guide.md`
3. Validate with `kubectl apply --dry-run=client -f <file>`

### Phase 3: Deploy & Shift Traffic
1. Deploy migrated Ingress (creates new ALB)
2. Use DNS weighted routing to shift traffic CLB→ALB
3. Monitor error rates, latency

### Phase 4: Cleanup
1. Delete old NGINX Ingress resources
2. Remove NGINX Ingress Controller deployment
3. Remove orphaned TLS Secrets
4. Update IaC/GitOps references

## Checks to Execute

### ALB.1 — Annotation Conversion Completeness

**What to check:**
- All `nginx.ingress.kubernetes.io/*` annotations identified
- Each has a mapped ALB equivalent or documented removal reason

**Rating:**
- 🟢 GREEN: All annotations have clear ALB equivalents
- 🟡 AMBER: Most map cleanly, some need WAF/app-level handling (CORS, body-size)
- 🔴 RED: Heavy use of `configuration-snippet` or `server-snippet` (no ALB equivalent)
- ⬜ UNKNOWN: Cannot parse annotations

### ALB.2 — ACM Certificate Readiness

**What to check:**
- All TLS hosts have matching ACM certificates (or can use certificate-discovery)
- Certificates are in ISSUED state in the correct region

**Rating:**
- 🟢 GREEN: All certs available in ACM
- 🟡 AMBER: Some certs need provisioning
- 🔴 RED: Certs use private CA or non-standard issuance
- ⬜ UNKNOWN: Cannot check ACM

### ALB.3 — AWS LB Controller Readiness

**What to check:**
- AWS LB Controller installed and version ≥ 2.7
- IAM role with correct policy attached
- IngressClass `alb` exists

**Rating:**
- 🟢 GREEN: Controller installed, correct version, IAM ready
- 🟡 AMBER: Controller present but needs upgrade
- 🔴 RED: Controller not installed
- ⬜ UNKNOWN: Cannot determine
