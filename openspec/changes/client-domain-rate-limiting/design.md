## Context

The `infra/gcp-domains` OpenTofu module manages the external HTTPS load balancer and its Cloud Armor security policy (`google_compute_security_policy.ip_blocklist`). Frontend client domains (such as `participate.boston.gov`, `pbideas.cambridgema.gov`, etc.) are routed through this load balancer. API requests are throttled at the Django level using `AnonymousIPThrottle`. To protect client frontend instances against scraping bursts and traffic spikes, rate limiting is introduced at the Cloud Armor layer specifically for client host domains.

See `proposal.md` for motivation and `specs/client-domain-rate-limiting/spec.md` for requirements.

## Goals / Non-Goals

**Goals:**
- Implement Cloud Armor rate limiting rule (`rate_limit_options`) on the shared security policy.
- Enforce rate limiting per client IP (e.g. 100 requests per 60 seconds) with an HTTP 429 response upon exceeding the limit.
- Exclude API domains (`shareaboutsapi.poepublic.com`, `shareaboutsapi-gcp-prod.poepublic.com`, `shareaboutsapi-gcp-dev.poepublic.com`) so backend API throttling remains handled by Django.
- Expose clear OpenTofu variables to customize the threshold count, time interval, and enabled status.

**Non-Goals:**
- Replace or modify Django's internal `AnonymousIPThrottle` implementation.
- Implement per-user or session-based rate limiting on static assets (this is pure IP-level rate limiting at the load balancer edge).

## Decisions

### Decision: Cloud Armor `rate_limit_options` Rule vs Backend Service Attachment
- **Choice**: Add a rate-limiting rule with priority 950 to the existing `google_compute_security_policy.ip_blocklist`.
- **Rationale**: The security policy is already attached to all backend services. Adding a rule with a CEL expression that matches client domain host headers allows central management in OpenTofu without needing multiple separate security policies.
- **Alternatives Considered**:
  - *Separate security policies per backend service*: Increases management overhead and duplication across backend services.
  - *Django middleware rate limiting for frontends*: Puts load on Cloud Run compute instances instead of dropping excessive traffic at Google's edge.

### Decision: Match Expression and API Domain Exclusion
- **Choice**: Match host headers that do not belong to the API domains, or explicitly match configured client host domains.
- **CEL Expression**: `!request.headers['host'].startsWith('shareaboutsapi')` (or parameterized check against API domains).
- **Rationale**: Ensures that API requests (which may arrive via client proxies or developer scripts) continue straight to Django for fine-grained application throttling.

### Decision: Rate Limiting Parameters
- **Choice**: Default to 100 requests per 60 seconds (`count = 100`, `interval_sec = 60`, `enforce_on_key = "IP"`, `exceed_action = "deny(429)"`, `conform_action = "allow"`).
- **Rationale**: 100 req/min provides generous headroom for human browsing and map tile/asset loading while blocking aggressive automated scrapers.

## Risks / Trade-offs

- **[Risk] Corporate/Institutional NAT**: Multiple users behind a single municipal or university NAT IP could collectively trigger the 100 req/min limit during peak events.
  - **Mitigation**: Threshold is configurable via `client_rate_limit_count` variable in `.auto.tfvars` and can be adjusted quickly if necessary.
- **[Risk] Preview vs Enforce**: Deploying a rate limit rule without verification might unexpectedly block valid traffic.
  - **Mitigation**: Support a `client_rate_limit_preview` boolean variable to allow previewing rate-limiting in Cloud Logging before enforcing.

## Migration Plan

1. Define variables in `infra/gcp-domains/variables.tf`.
2. Add dynamic rate limit rule in `infra/gcp-domains/security.tf`.
3. Configure default values in `infra/gcp-domains/.auto.tfvars`.
4. Run `tofu plan` and review changes.
5. Apply with `tofu apply`.
