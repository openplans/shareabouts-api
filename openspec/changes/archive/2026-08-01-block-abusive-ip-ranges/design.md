## Context

The service infrastructure in `infra/gcp-domains/` manages a central GCP Global External Application Load Balancer using OpenTofu/Terraform. Backend services are defined as `google_compute_backend_service` connected to Cloud Run instances via Serverless Network Endpoint Groups (`google_compute_region_network_endpoint_group`). See `proposal.md` for motivation.

## Goals / Non-Goals

**Goals:**
- Add a GCP Cloud Armor Security Policy (`google_compute_security_policy`) in `infra/gcp-domains/`.
- Configure rule priorities to deny requests matching blocked IP CIDR ranges with a 403 response.
- Attach the security policy to `google_compute_backend_service.default`.
- Allow specifying blocked CIDR ranges via OpenTofu variables (`blocked_ip_ranges`).

**Non-Goals:**
- Application-level IP filtering in Django middleware.
- Dynamic IP blocking database/admin interfaces.
- Advanced Cloud Armor WAF rules (e.g., OWASP top 10 rulesets, reCAPTCHA enterprise) - focus specifically on IP range blocklists.

## Decisions

### Decision 1: GCP Cloud Armor Security Policy over Django Middleware
- **Rationale**: Cloud Armor drops traffic at GCP edge forwarding rules before requests reach Cloud Run, protecting compute resources, memory, and database connections.
- **Alternatives Considered**: Django middleware was rejected because requests would still trigger Cloud Run container invocations and consume backend resources.

### Decision 2: Managed via OpenTofu variables in `infra/gcp-domains/`
- **Rationale**: `infra/gcp-domains/` centralizes domain routing and load balancing backend services. Adding the security policy here keeps infrastructure definitions cohesive and version-controlled.
- **Implementation**:
  - Add `blocked_ip_ranges` variable (`list(string)`) in `infra/gcp-domains/variables.tf` (default `[]`).
  - Declare `google_compute_security_policy` in `infra/gcp-domains/security.tf` (or `main.tf`).
  - Attach `security_policy = google_compute_security_policy.ip_blocklist[0].id` to `google_compute_backend_service.default`.

## Risks / Trade-offs

- **[Risk] Accidental blocking of legitimate users in shared IP ranges** → **Mitigation**: Specify tight CIDR masks where possible, and document how to update or remove CIDR blocks in `.auto.tfvars`.
- **[Risk] Cloud Armor rule limit (standard tier limits rules per policy)** → **Mitigation**: Use CIDR ranges (`src_ip_ranges`) to group multiple IPs into concise rule blocks.
