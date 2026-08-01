## Why

Abusive HTTP traffic originating from specific IP subnet ranges (e.g., `X.X.X.0/25`) is hitting the service, taking up resources. We need to block abusive IP ranges at the GCP Load Balancer level using Cloud Armor security policies so that unwanted requests are rejected immediately at the edge with a 403 Forbidden status code, protecting Cloud Run compute and database resources.

## What Changes

- Add a GCP Cloud Armor security policy resource in OpenTofu/Terraform (`infra/gcp-domains/`) to block designated IP ranges with a 403 HTTP response.
- Attach the Cloud Armor security policy to the GCP Load Balancer's backend services (`google_compute_backend_service.default`).
- Expose configurable variables for the blocked IP CIDR ranges in `infra/gcp-domains/variables.tf` and `.auto.tfvars`.

## Capabilities

### New Capabilities

- `ip-range-blocking`: Support configuring and enforcing IP range blocklists at the load balancer level via Terraform.

### Modified Capabilities

(None)

## Impact

- **Infrastructure**: Updates OpenTofu/Terraform state and configuration in `infra/gcp-domains/`.
- **GCP Resources**: Provisions a `google_compute_security_policy` in GCP and links it to `google_compute_backend_service`.
- **Traffic**: Requests originating from IPs within blocked CIDR ranges will receive HTTP 403 Forbidden responses at the GCP edge load balancer prior to reaching Cloud Run.
