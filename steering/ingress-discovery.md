# Ingress Discovery

## Purpose
Discover all ingress controllers, IngressClass resources, and Ingress objects in the cluster.

## Checks to Execute

### 1.1 — Ingress Controllers Installed

**What to check:**
- Deployments/DaemonSets running ingress controllers
- Common controllers: nginx-ingress, AWS LB Controller, Traefik, HAProxy, Istio, Contour, Kong

**How to check:**
1. List Deployments across all namespaces → filter for ingress-related names
2. List DaemonSets across all namespaces → filter for ingress-related names
3. Check namespaces: `ingress-nginx`, `kube-system`, `aws-load-balancer-controller`
4. List pods with labels: `app.kubernetes.io/name=ingress-nginx`, `app.kubernetes.io/name=aws-load-balancer-controller`

**Rating:**
- 🟢 GREEN: Single modern controller (AWS LB Controller v2.x) installed and healthy
- 🟡 AMBER: Multiple controllers or legacy controller (nginx-ingress, ALB Ingress Controller v1)
- 🔴 RED: No controller found, or controller pods in CrashLoopBackOff
- ⬜ UNKNOWN: Cannot determine controller health

### 1.2 — IngressClass Resources

**What to check:**
- IngressClass resources defined in the cluster
- Default IngressClass annotation (`ingressclass.kubernetes.io/is-default-class: "true"`)
- Whether Ingress resources reference a specific IngressClass

**How to check:**
1. List IngressClass resources (networking.k8s.io/v1)
2. Check for default class annotation
3. Cross-reference with Ingress resources' `spec.ingressClassName`

**Rating:**
- 🟢 GREEN: IngressClass defined, default set, Ingress resources reference it explicitly
- 🟡 AMBER: IngressClass exists but Ingress resources use legacy annotation instead of `ingressClassName`
- 🔴 RED: No IngressClass defined, or multiple defaults causing conflicts
- ⬜ UNKNOWN: Cannot determine IngressClass usage

### 1.3 — Ingress Resource Inventory

**What to check:**
- Total Ingress resources across all namespaces
- Which namespaces have Ingress resources
- Ingress resources without an IngressClass (will use default)

**How to check:**
1. List all Ingress resources (networking.k8s.io/v1) across all namespaces
2. Count per namespace
3. Check each for `spec.ingressClassName` or `kubernetes.io/ingress.class` annotation

**Rating:**
- 🟢 GREEN: All Ingress resources have explicit IngressClass, manageable count (<50)
- 🟡 AMBER: Some Ingress resources missing IngressClass, or high count (50-200)
- 🔴 RED: >200 Ingress resources, or many without IngressClass assignment
- ⬜ UNKNOWN: Cannot list Ingress resources
