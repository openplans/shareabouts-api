## 1. Terraform Configuration for Security Policy

- [x] 1.1 Declare the `blocked_ip_ranges` input variable in `infra/gcp-domains/variables.tf`.
- [x] 1.2 Create `infra/gcp-domains/security.tf` defining `google_compute_security_policy` with rules to deny blocked IP CIDR ranges with HTTP 403.
- [x] 1.3 Update `google_compute_backend_service.default` in `infra/gcp-domains/backend.tf` to reference the Cloud Armor security policy.

## 2. Validation & Deployment Setup

- [x] 2.1 Add example blocked IP configuration to `infra/gcp-domains/.auto.tfvars.example` and `.auto.tfvars`.
- [x] 2.2 Validate Terraform / OpenTofu syntax and formatting using `tofu fmt` / `tofu validate` or `terraform validate`.
