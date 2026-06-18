# EKS Ingress Migration Assessment Report

| Information | Value |
|-------------|-------|
| Cluster | eval-fixture |
| Region | ap-southeast-1 |

---

## Executive Summary

- **Controllers:** 1 — !!one is End-of-Life!!
  - alb `v2.15.0`
  - nginx `v1.3.0` !!(EOL)!!

---

## Impact Indicator

| Impact | Meaning |
|--------|---------|
| 🟡 1–2 Low | - low |
| 🟠 3–4 Medium | - medium |
| 🔴 5 High | - high |

---

## Assessment Summary

| Theme | Impact | Why |
|-------|--------|-----|
| Snippets | 🔴 5 | no equivalent |
| Routing | 🟠 3 | regex |

---

## Traffic & Routing

| Item | Impact | Current Config | Recommendation |
|------|--------|----------------|----------------|
| Mapping | 🟠 3 | [[DL:current]] | line-a<br>line-b |
| Features | 🔴 5 | [[DL:current]] | - redesign snippets<br>  - move modsecurity to WAF |

---

## Migration Options

### Option 1: Gateway API

> **What:** successor. **Routing config:** [[DL:gateway-api]]

| Step | Action |
|------|--------|
| 1 | Snippet routes have no equivalent — redesign (see [blocker](#blockers)) |

### Option 2: ALB

> **Routing config:** [[DL:alb]]

| Step | Action |
|------|--------|
| 1 | Convert |

---

## Blockers

| Finding | Impact | Action Required |
|---------|--------|-----------------|
| Snippets | 🔴 5 | - redesign<br>  - WAF |

---

## AWS Reference Links

| Topic | URL |
|-------|-----|
| Gateway API on EKS | https://docs.aws.amazon.com/eks/latest/userguide/gateway-api.html |
