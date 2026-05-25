# Gateway API Migration Plan

## Purpose
Generate a concrete, phased migration plan from Ingress to Gateway API based on assessment findings.

## Plan Structure

### Phase 1: Foundation (Week 1)

**Install/verify Gateway API prerequisites:**

1. Install Gateway API CRDs (if not present):
   ```bash
   kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.2.1/standard-install.yaml
   ```

2. Upgrade AWS LB Controller to v2.7+ (if needed):
   ```bash
   # EKS managed add-on
   aws eks update-addon --cluster-name <cluster> --addon-name aws-load-balancer-controller --addon-version <latest>
   # Or Helm
   helm upgrade aws-load-balancer-controller eks/aws-load-balancer-controller -n kube-system --set serviceAccount.create=false
   ```

3. Create GatewayClass:
   ```yaml
   apiVersion: gateway.networking.k8s.io/v1
   kind: GatewayClass
   metadata:
     name: aws-alb
   spec:
     controllerName: gateway.networking.k8s.aws/alb
   ```

4. Update external-dns to add `--source=gateway-httproute`

5. Update cert-manager to enable Gateway API support (if using cert-manager)

### Phase 2: Convert & Test (Week 2-3)

**For each Ingress resource, create an equivalent HTTPRoute:**

1. Start with lowest-risk routes (internal, low-traffic)
2. Create Gateway resource for each listener group:
   ```yaml
   apiVersion: gateway.networking.k8s.io/v1
   kind: Gateway
   metadata:
     name: main-gateway
     namespace: <namespace>
     annotations:
       alb.ingress.kubernetes.io/scheme: internet-facing
       alb.ingress.kubernetes.io/certificate-arn: <acm-arn>
   spec:
     gatewayClassName: aws-alb
     listeners:
       - name: https
         protocol: HTTPS
         port: 443
         tls:
           mode: Terminate
           certificateRefs:
             - name: <cert-secret>
   ```

3. Create HTTPRoute for each Ingress:
   ```yaml
   apiVersion: gateway.networking.k8s.io/v1
   kind: HTTPRoute
   metadata:
     name: <app-name>
     namespace: <namespace>
   spec:
     parentRefs:
       - name: main-gateway
     hostnames:
       - "<host>"
     rules:
       - matches:
           - path:
               type: PathPrefix
               value: "/<path>"
         backendRefs:
           - name: <service>
             port: <port>
   ```

4. Test each HTTPRoute independently (new ALB created by Gateway)
5. Validate DNS, TLS, routing, health checks

**Report output format:** In the report's "Target Config" column, show the equivalent Gateway API config as compact 1-liner:
`HTTPRoute/<name>: parentRef=<gateway>, hostnames=[<host>], path=<path> → <backend>:<port>`
Example: `HTTPRoute/shopping-app-route: parentRef=main-gateway, path=/* → frontend:80`
Example: `HTTPRoute/nginx-app-route: parentRef=main-gateway, hostnames=[app.example.com], path=/* → nginx-service:80`

### Phase 3: Traffic Cutover (Week 4)

1. Update DNS to point to new Gateway ALB (or use weighted DNS for gradual shift)
2. Monitor error rates, latency, 5xx responses
3. Keep old Ingress resources running as fallback

### Phase 4: Cleanup (Week 5)

1. Confirm all traffic flowing through Gateway API
2. Delete old Ingress resources
3. Remove old ingress controller (nginx, etc.) if no longer needed
4. Update IaC/GitOps to manage HTTPRoute resources instead of Ingress

## Checks to Execute

### 7.1 — Migration Scope

**What to check:**
- Total Ingress resources to convert
- Estimated HTTPRoute count (may differ — one Ingress can become multiple HTTPRoutes)
- ReferenceGrant resources needed (for cross-namespace routing)

**Rating:**
- 🟢 GREEN: <20 Ingress resources, straightforward 1:1 mapping
- 🟡 AMBER: 20-50 Ingress resources, some complex conversions
- 🔴 RED: >50 Ingress resources or heavy customization requiring redesign
- ⬜ UNKNOWN: Cannot determine scope

### 7.2 — Conversion Complexity per Route

**What to check:**
- Simple routes (host + path → backend): direct conversion
- Routes with rewrites: need HTTPRoute URLRewrite filter
- Routes with auth: need Gateway-level Cognito/OIDC annotation
- Routes with snippets: need redesign (no equivalent)

**Rating:**
- 🟢 GREEN: >80% of routes are simple direct conversions
- 🟡 AMBER: 50-80% simple, rest need filter configuration
- 🔴 RED: <50% simple — heavy customization throughout
- ⬜ UNKNOWN: Cannot assess conversion complexity

### 7.3 — Timeline Estimate

Based on findings, estimate:
- Phase 1 (Foundation): X days
- Phase 2 (Convert & Test): X days
- Phase 3 (Cutover): X days
- Phase 4 (Cleanup): X days
- Total: X weeks

**Rating:**
- 🟢 GREEN: Estimated <2 weeks total
- 🟡 AMBER: 2-4 weeks
- 🔴 RED: >4 weeks
- ⬜ UNKNOWN: Cannot estimate
