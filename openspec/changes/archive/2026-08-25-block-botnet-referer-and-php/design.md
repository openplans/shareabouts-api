## Context

The GCP domain and load balancing infrastructure is managed via OpenTofu/Terraform in `infra/gcp-domains/`. The Cloud Armor security policy resource `google_compute_security_policy.ip_blocklist` in `infra/gcp-domains/security.tf` is attached to backend services (including `shareabouts-api-prod-backend`).

Currently, `security.tf` only defines IP CIDR blocking (`var.blocked_ip_ranges`). To mitigate the active distributed scraper botnet and PHP exploit scanning, additional rules using Cloud Armor's Common Expression Language (CEL) must be added. To maintain clean separation and reusability, domain names and toggles must be passed via variables rather than hardcoded in the `.tf` resource files.

## Goals / Non-Goals

**Goals:**
- Add a Cloud Armor rule to block all HTTP requests targeting `.php` resources.
- Add a Cloud Armor rule to block HTTP requests to `/api/` endpoints that present self-referencing root referers matching configured API domains.
- Parameterize domains and rule toggles via Terraform variables (`var.blocked_referer_domains`, `var.block_php_requests`) in `variables.tf` and populate them in `.auto.tfvars`.
- Dynamically generate Cloud Armor CEL expressions from the input list of domains.
- Remove invalid link-local IP (`169.254.169.126/32`) from `.auto.tfvars`.

**Non-Goals:**
- Modifying Django application code or backend database tier (handled separately).
- Implementing rate-based bans or reCAPTCHA at this stage (can be added later if needed).

## Decisions

### 1. Dynamic CEL Expression Generation for Blocked Referers
Instead of hardcoding domain names in the rule definition, `security.tf` will iterate over `var.blocked_referer_domains` to construct a CEL expression:

```hcl
locals {
  referer_match_expr = length(var.blocked_referer_domains) > 0 ? format(
    "request.path.startsWith('/api/') && has(request.headers['referer']) && (%s)",
    join(" || ", [
      for d in var.blocked_referer_domains :
      "request.headers['referer'] == 'https://${d}' || request.headers['referer'] == 'http://${d}'"
    ])
  ) : ""
}
```

*Rationale:* This prevents domain hardcoding in `security.tf`, allows easy addition/removal of domains in `.auto.tfvars`, and strictly restricts blocking to `/api/` paths with bare-origin referers, ensuring `/admin/` and legitimate frontend clients remain unaffected.

### 2. Static Expression for PHP Scanning
Requests ending in `.php` are blocked using `request.path.endsWith('.php')`. Since this rule applies universally to any PHP extension probe across all domains, it is governed by a boolean toggle `var.block_php_requests` (defaulting to `true`).

### 3. Rule Priority Layout
To ensure predictable evaluation order:
- Priority `900`: PHP resource blocking (`request.path.endsWith('.php')`)
- Priority `910`: Abusive API referer filtering (`request.path.startsWith('/api/') && ...`)
- Priority `1000`: IP CIDR blocklist (`var.blocked_ip_ranges`)
- Priority `2147483647`: Default allow rule (`*`)

## Risks / Trade-offs

- **[Risk]** False positive blocks on legitimate API consumers  
  *Mitigation:* Legitimate third-party frontend apps (such as `https://pbideas.cambridgema.gov` or `https://participate.boston.gov`) send their own domain in the `Referer` header. Native mobile apps or API clients (curl, backend scripts) typically send no referer. The rule only matches requests to `/api/` that explicitly declare the API's own hostname as the referer.

- **[Risk]** Breaking Django Admin access  
  *Mitigation:* Django Admin traffic operates on `/admin/` and `/static/` paths and carries subpaths in its referer (e.g. `/admin/...`), so it does not match the `/api/` prefix or the bare origin string.
